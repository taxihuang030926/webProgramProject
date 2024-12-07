from flask import Flask, json, request, jsonify
import sys
import socket
import struct
import time

PORT = 55558
BUF_SIZE = 1024			# Receive buffer size
local_mp_list = []

def isPrime(number):
	if number < 2:
		return False
	elif number == 2:
		return True
	for i in range(2, int(number ** 0.5) + 1):
		if number % i == 0:
			return False
	return True


def lucasLehmerTest(prime):
    # Lucas-Lehmer test
    # m = 2^p - 1
	if prime == 2:
		return True
	s = 4
	m = 2 ** prime - 1
	for _ in range(prime - 2):
		s = ((s * s) - 2) % m
	return s == 0

def get_server_mp_list():
	pass

def main():
	# if(len(sys.argv) < 2):
	# 	print("Usage: python3 client.py ServerIP")
	# 	exit(1)

	# Get server IP
	serverIP = socket.gethostbyname('127.0.0.1')
	
	# Create a TCP client socket
	cSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	# Connect to server
	print('Connecting to %s port %s' % (serverIP, PORT))
	cSocket.connect((serverIP, PORT))
	
	# Send message to server
	try:
		client_msg = "Client hello!!"
		cSocket.send(client_msg.encode('utf-8'))
	
		# Receive server reply, buffer size = BUF_SIZE
		server_reply = cSocket.recv(BUF_SIZE) # name + ": Server Reply!!"
		print(server_reply.decode('utf-8'))
    
		print(f'Connected with server {serverIP}:{PORT} Waiting for server response...')
		
		# Listen for incoming response from server w\ start_num and window_size
		window_size = 0
		start_num = 0
		while True:
			try:
				server_reply = cSocket.recv(BUF_SIZE)
				unpacked_msg = struct.unpack('2s i i', server_reply)
				print(unpacked_msg)
				# receive start_num and window_size
				if server_reply and unpacked_msg[0].decode('utf-8') == 'rc':
					print('Received task from server')
					start_num = unpacked_msg[1]
					window_size = unpacked_msg[2]
					mp_status = 0
					print(f'Received task from server: {start_num}, {window_size}')
					# calculate mersenne prime number
					for i in range(window_size):
						prc_num = start_num + i 
						if isPrime(prc_num) and lucasLehmerTest(prc_num):
							mp_status = 1
						else:
							mp_status = 0
						# send result to server
						result = struct.pack('2s i i', b'ch', prc_num, mp_status)
						result_value = ('ch'.encode('utf-8'), prc_num, mp_status)
						print(f'Sending result to server: {result_value}')
						cSocket.send(result)
						time.sleep(1)
				
				client_msg = struct.pack('2s i i', b'ed', start_num, window_size)
				cSocket.send(client_msg)
				

				# send result to server by loop for window_size

			except socket.error as e:
				print('Socket error: %s' % str(e))
				break
			except KeyboardInterrupt as e:
				print('KeyboardInterrupt: %s' % str(e))
				break
			except Exception as e:
				print('Other exception: %s' % str(e))
				break
			
	except socket.error as e:
		print('Socket error: %s' % str(e))
	except KeyboardInterrupt as e:
		print('KeyboardInterrupt: %s' % str(e))
	except Exception as e:
		print('Other exception: %s' % str(e))
		

# end of main


if __name__ == '__main__':
	main()
