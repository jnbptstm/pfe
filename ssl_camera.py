import io
import socket
import ssl
import picamera
import time
import threading
import struct
import os
import numpy as np
from PIL import Image, ImageChops
from time import gmtime, strftime

host = '192.168.2.1'
port = 8020
prior_image = None
threshold = 2
timestamp = None

def send_msg(sock, msg):
	# Prefix each message with a 4-byte length (network byte order)
	msg = struct.pack('>I', len(msg)) + msg
	sock.sendall(msg)

def recvall(sock, n):
	# Helper function to recv n bytes or return None if EOF is hit
	data = ''
	while len(data) < n:
		packet = sock.recv(n - len(data))
		if not packet:
			return None
		data += packet
	return data

def recv_msg(sock):
	# Read message length and unpack it into an integer
	raw_msglen = recvall(sock, 4)
	if not raw_msglen:
		return None
	msglen = struct.unpack('>I', raw_msglen)[0]
	# Read the message data
	return recvall(sock, long(msglen))

# Motion detection algorithm: it compares images and if the difference
# is higher than the choosen threshold, motion is detected
def detect_motion(img):
	global prior_image
	stream = io.BytesIO()
	camera.capture(stream, format='jpeg', use_video_port=False)
	stream.seek(0)
	if prior_image is None:
		prior_image = Image.open(stream)
		return False
	else:
		print 'Comparing img... ',
		current_image = Image.open(stream)
		img = ImageChops.difference(prior_image, current_image)
		w,h = img.size
		a = np.array(img.convert('RGB')).reshape((w*h,3))
		h,e = np.histogramdd(a, bins=(16,)*3, range=((0,256),)*3)
		prob = h/np.sum(h) # normalize
		prob = prob[prob>0] # remove zeros

		# Comparing with the threshold
		print -np.sum(prob*np.log2(prob)) > threshold
		print -np.sum(prob*np.log2(prob))
		return -np.sum(prob*np.log2(prob)) > threshold

def write_before(stream):
    # Write the entire content of the circular buffer to disk. No need to
    # lock the stream here as we're definitely not writing to it
    # simultaneously
    global timestamp
    with io.open('before'+timestamp+'.h264', 'wb') as output:
        for frame in stream.frames:
            if frame.header:
                stream.seek(frame.position)
                break
        while True:
            buf = stream.read1()
            if not buf:
                break
            output.write(buf)
    # Wipe the circular stream once we're done
    stream.seek(0)
    stream.truncate()
	
	
# The connection between the host with camera and the server is secured with SSL Socket.
# The certificates have already been generated
socket_on_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = ssl.wrap_socket(socket_on_server, keyfile=None, certfile=None, \
                        server_side=False, cert_reqs=ssl.CERT_NONE, \
                        ssl_version=ssl.PROTOCOL_SSLv3, ca_certs='cert_cam', \
                        do_handshake_on_connect=True, suppress_ragged_eofs=True)
print 'Trying to connect ...',
ssl_sock.connect((host, port))
print 'Connected!'
print 'Informations about cipher: ', repr(ssl_sock.cipher())

print 'Waiting for request ...'
request = ssl_sock.read(1)
print 'Request received: ', request

# Sending the video live at the server using SSL Socket.
if request == '1': # Streaming
	with picamera.PiCamera() as camera:
		camera.resolution = (800, 600)
		camera.start_recording(ssl_sock, format='h264', bitrate=1000000)
		camera.wait_recording(60)

else: # Motion detection
	with picamera.PiCamera() as camera:
		camera.resolution = (800, 600)
		stream = picamera.PiCameraCircularIO(camera, seconds=5)
		camera.start_recording(stream, format='h264', bitrate=5000000)
		try:
			while True:
				camera.wait_recording(0.5)
				if detect_motion(camera):
					global timestamp
					timestamp = strftime("%d%m%Y%H%M%S", gmtime())
					print('Motion detected!')
					# As soon as we detect motion, split the recording to
					# record the frames "after" motion
					camera.split_recording('after'+timestamp+'.h264')
					# Write the 10 seconds "before" motion to disk as well
					write_before(stream)
					# Wait until motion is no longer detected, then split
					# recording back to the in-memory circular buffer
					while detect_motion(camera):
						camera.wait_recording(1)
					print('Motion stopped!')
					camera.split_recording(stream)
					print 'Sending saved videos to server ...',
					send_msg(ssl_sock,timestamp)
					send_msg(ssl_sock, open('before'+timestamp+'.h264','rb').read())
					send_msg(ssl_sock, open('after'+timestamp+'.h264','rb').read())
					print 'Sent'
					os.remove('before'+timestamp+'.h264')
					os.remove('after'+timestamp+'.h264')
					
		finally:
			camera.stop_recording()
