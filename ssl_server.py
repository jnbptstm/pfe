import sys
import socket
import ssl
import struct
import pickle
import threading
import os
from time import gmtime, strftime
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import ElGamal
from Crypto.Random import get_random_bytes


cipher_encrypt = None
cipher_decrypt = None
key = None
guardian = None
timestamp = None


host_to_cam = '192.168.2.1'
host_to_client = '192.168.1.3'
port = 8020

# Hashtable linking Guardian Id with its password
id_password = { 'guardianA': 'passA',\
				'guardianB': 'passB',\
				'guardianC': 'passC' }

# Hashtable gathering Guardian Id with its public key
id_pubKey = dict()

# Checking if password associated to guardian is correct
def verif(guardian, password):
	if str(id_password[str(guardian)]) == str(password):
		return 1
	else:
		return 0

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


# Checking user
def authentification():
	correct = 0
	while not correct:
		global guardian
		guardian = recv_msg(connection_with_client)
		password = recv_msg(connection_with_client)
		public_key_guardian = recv_msg(connection_with_client)

		correct = verif(guardian, password)
		send_msg(connection_with_client, str(correct))

#--------------------------------------------------------------------------------------------------#
# This part uses the El Gamal algorithm to share a secret key.                                     #
#--------------------------------------------------------------------------------------------------#

	# Saving guardian public key in El Gamal key
	setattr(el_gamal_key, 'y', long(public_key_guardian))
	id_pubKey[guardian] = long(public_key_guardian)

	# Transmitting El Gamal attributes
	print 'Receiving El Gamal attributes'
	print '\tModulus... ',
	setattr(el_gamal_key, 'p', long(recv_msg(connection_with_client)))
	print 'Received'

	print '\tGenerator... ',
	setattr(el_gamal_key, 'g', long(recv_msg(connection_with_client)))
	print 'Received'

	print '\tServer\'s public key...',
	send_msg(connection_with_client, public_key_guardian)
	print 'Sent'


	# Sending ciphered secret key
	print 'Sending cipher... '

	# Secret should be random-generated
	secret_key = '16-Bytes Secret_'
	secret_key2 = '16-Bytes Secret-'
	(ciphered_secret_key_part_one, ciphered_secret_key_part_two) = \
											el_gamal_key.encrypt(secret_key, 4567)
	print '\tSending 1st part... ',
	send_msg(connection_with_client, ciphered_secret_key_part_one)
	print 'Sent\n\tSending 2nd part... ',
	send_msg(connection_with_client, ciphered_secret_key_part_two)
	print 'Sent'

#--------------------------------------------------------------------------------------------------#
# This part uses the AES algorithm to cipher and decipher data between guardian and server.        #
#--------------------------------------------------------------------------------------------------#

	# Cipher configuration
	global key
	key = secret_key
	block_size = 16
	mode = AES.MODE_CFB
	iv = Random.new().read(block_size)
	global cipher_encrypt
	global cipher_encrypt2
	cipher_encrypt = AES.new(key, mode, iv)
	cipher_encrypt2 = AES.new(secret_key2, mode, iv)
	global cipher_decrypt
	cipher_decrypt = AES.new(key, mode, iv)
	print 'AES cipher configured'
	
	
# Establishing connections

# The connection between the host with camera and the server is secured with SSL Socket.
# The certificates have already been generated
socket_on_cam = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_socket_on_cam = ssl.wrap_socket(socket_on_cam, \
                                    keyfile='key_server', \
									certfile='cert_server', server_side=True, \
									cert_reqs=ssl.CERT_NONE, 
									ssl_version=ssl.PROTOCOL_SSLv23, \
									ca_certs='cert_server', \
									do_handshake_on_connect=True, \
									suppress_ragged_eofs=True)
ssl_socket_on_cam.bind((host_to_cam, port))
ssl_socket_on_cam.listen(0)

print 'Waiting connection from RPi ...'
connection_with_rpi = ssl_socket_on_cam.accept()[0]
print 'Informations about cipher: ', repr(connection_with_rpi.cipher())


socket_on_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_on_client.bind((host_to_client, port))
socket_on_client.listen(0)

print 'Waiting for client to connect...',
connection_with_client = socket_on_client.accept()[0]
print 'Client connected'

el_gamal_key = pickle.load(open('el_gamal_key_server', 'rb'))
public_key_server = repr(getattr(el_gamal_key, 'y')) 



	
	
print 'Authentification'
authentification()

print 'Waiting for guardian\'s choice ...',
request = connection_with_client.recv(1)
print 'Choice: ', str(request)

if request == '1':
	# Sending request to the camera
	connection_with_rpi.send(request)
	data = None
	while True:
                # Receiving video from camera
		s = strftime("%S", gmtime())
		if int(s)>30:
			data = cipher_encrypt.encrypt(connection_with_rpi.read(1024))
		else: 
			data = cipher_encrypt2.encrypt(connection_with_rpi.read(1024))

                # Sending video (ciphered) to guardian
		connection_with_client.send(data)
		if not data:
			print 'Not data'
			break

elif request == '2':
	send_msg(connection_with_rpi, request)
	print 'Receiving videos...'
	
	# global timestamp
	timestamp = recv_msg(connection_with_rpi)

    # Saving video just before motion detection
	open('before'+timestamp+'.h264','wb').write(recv_msg(connection_with_rpi))
    # Saving video while motion is detected
	open('after'+timestamp+'.h264','wb').write(recv_msg(connection_with_rpi))
	print 'Received'
	send_msg(connection_with_client, cipher_encrypt.encrypt("Okay"))

else:
        # Send motion-detected videos to guardian
	print 'Gonna send video to guardian'
	for fic in os.listdir('/home/pi'):
		if fic[0:6] == 'before':
			timestamp = fic[6:-5]
	send_msg(connection_with_client,timestamp)
	send_msg(connection_with_client, open('before'+timestamp+'.h264','rb').read())
	send_msg(connection_with_client, open('after'+timestamp+'.h264','rb').read())
	print 'Sent'
