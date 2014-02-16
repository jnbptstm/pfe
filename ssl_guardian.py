import socket
import subprocess
import ssl
import sys
import struct
import pickle
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import ElGamal
from Crypto.Random import get_random_bytes

cipher_encrypt = None
cipher_decrypt = None
public_key = None
el_gamal_key = None
key = None
request = None

# Basic menu. The user can choose between:
#       - get the stream (live)
#       - enable motion detection
#       - get and watch motion detected videos
def menu():
	global request
	while request != '1' and request != '2' and request != '3':
		request = str(raw_input('Available services :\
								\n\t1) Stream\
								\n\t2) Motion detection\
								\n\t3) Get motion detected videos\
								\nChoice? '))
				
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
	return recvall(sock, msglen)


# Dictionary linking a Guardian ID with its public key
id_keyPair = { 'guardianA' : open('el_gamal_key_guardianA', 'rb'), \
			   'guardianB' : open('el_gamal_key_guardianB', 'rb'), \
			   'guardianC' : open('el_gamal_key_guardianC', 'rb') }
			   
			   
# Identification of the guardian
def authentification():
	correct = 0
	global public_key
	public_key = None
	while not correct:
		login_password = False
		while not login_password:
			print 'Please, enter login and password'
			guardian = str(raw_input("\tLogin: "))
			password = str(raw_input("\tPassword: "))
			# Checking if current user got a public key
			if id_keyPair.get(guardian) != None:
				login_password = True
			else:
				print 'Wrong id or passwd'

#--------------------------------------------------------------------------------------------------#
# This part uses the El Gamal algorithm to share a secret key.                                     #
#--------------------------------------------------------------------------------------------------#

		# Retrieving El Gamal attributes for the current guardian
		# These attributes have been generated and saved in a file
		global el_gamal_key
		el_gamal_key = pickle.load(open('el_gamal_key_'+guardian, 'rb'))

		# Getting public key of the guardian
		# Its public key is an attribute of the El Gamal key
		global public_key
		public_key = str(getattr(el_gamal_key, 'y'))

                # Sending informations about guardian to server
                # The server will check if these informations are correct
		send_msg(socket_on_server, guardian)
		send_msg(socket_on_server, password)
		send_msg(socket_on_server, public_key)

		# The server will check if the password is correct
		correct = int(recv_msg(socket_on_server))
		
		if not correct:
			print 'Permission denied, please try again.'
		
	# Sharing El Gamal attributes to be able to cipher and decipher
	print 'Transmitting El Gamal attributes'

	print '\tModulus... ',
	send_msg(socket_on_server, str(getattr(el_gamal_key, 'p')))
	print 'Sent'

	print '\tGenerator... ',
	send_msg(socket_on_server, str(getattr(el_gamal_key, 'g')))
	print 'Sent'

	print '\tServer\'s public key... ',
	global server_public_key
	server_public_key = recv_msg(socket_on_server)
	setattr(el_gamal_key, 'y', server_public_key)
	print 'Received'


	# Exchanging the secret key that will be used for ciphering and deciphering data between guardian and server
	print 'Waiting for server to send ciphered... ',
	ciphered_secret_key_part_one = recv_msg(socket_on_server)
	ciphered_secret_key_part_two = recv_msg(socket_on_server)
	print 'Deciphering... ',
	decipher_eg = el_gamal_key.decrypt((ciphered_secret_key_part_one, \
										ciphered_secret_key_part_two))
	print 'Deciphered: ', str(decipher_eg)

#--------------------------------------------------------------------------------------------------#
# This part uses the AES algorithm to cipher and decipher data between guardian and server.        #
#--------------------------------------------------------------------------------------------------#

	# Cipher configuration
	print 'Configuring AES cipher ...',
	global key
	key = str(decipher_eg)
	block_size = 16

	# AES mode
	mode = AES.MODE_CFB

	# Initialisation Vector
	iv = Random.new().read(block_size)
	global cipher_encrypt

	# Object that will encrypt data 
	cipher_encrypt = AES.new(key, mode, iv)

        # Object that will decrypt data
	global cipher_decrypt
	cipher_decrypt = AES.new(key, mode, iv)



#--------------------------------------------------------------------------------------------------#
# Beginning of the program                                                                         #
#--------------------------------------------------------------------------------------------------#	
	
# Connection to server
host = '192.168.1.3'
port = 8020
socket_on_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print 'Trying to connect to server ...',
socket_on_server.connect((host, port))
print 'Connected'


print 'Authentification'
authentification()
menu()
print 'Sending choice ...', type(request)
socket_on_server.send(request)
print 'Sent'

if request == '1': # Stream
        # VLC video player is used to watch the stream
	vlc = subprocess.Popen(['vlc', '--demux', 'h264', '-'], stdin=subprocess.PIPE)
	while True: 
		# Repeatedly read 1k of data from the connection and write it to VLC's stdin
		data = cipher_decrypt.decrypt(socket_on_server.recv(1024))
		if not data :
			print 'NOT DATA'
			break
		vlc.stdin.write(data)
		
elif request == '2': # Motion detection
	print 'Processing...',
	cipher_decrypt.decrypt(socket_on_server.recv(1024))
	print 'Done'

else: # Get videos
	print 'Waiting for videos ...',
	timestamp = recv_msg(socket_on_server)
	open('video_guardian/before'+timestamp+'.h264','wb').write(recv_msg(socket_on_server))
	open('video_guardian/after'+timestamp+'.h264','wb').write(recv_msg(socket_on_server))
	print 'Received'
