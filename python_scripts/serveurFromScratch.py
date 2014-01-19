import socket
import subprocess
import picamera

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
print "Waiting for client..."
connection = server_socket.accept()[0].makefile('rb')
print "Client connected!"
try:
	# Initialisation of the camera
	with picamera.PiCamera() as camera:
	camera.resolution(640, 480)
	camera.start_preview()
	time.sleep(2)

	# Start recording, sending data on connected client
	camera.start_recording(connection, format='mjpeg')
	camera.wait_recording(60)
	camera.stop_recording()
finally:
	connection.close()
	server_socket.close()
	print "Connection closed"
