from flask import Flask, json, request, jsonify
import sys
import socket
import struct
import time

PORT = 55558
BUF_SIZE = 1024			# Receive buffer size
local_mp_dict = {}

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

def show_mp(cSocket):
	print("in show_mp()")
	# get mp list from server
	fetch_svr_mp_dict(cSocket)
	# render info to html page
	print(f"loacal mp: {local_mp_dict}")

def fetch_svr_mp_dict(cSocket):
	global local_mp_dict

	print("in fetch_svr_mp_dict()")
	client_msg = struct.pack('2s i i', b'ft', 0, 0)
	client_msg_value = 'ft'.encode('utf-8'), 0, 0
	cSocket.send(client_msg)
	print(f'Sent request to server for mp list: {client_msg_value}')

	server_reply = cSocket.recv(BUF_SIZE)
	server_unpack = struct.unpack('2s i i', server_reply)
	print(f'server_unpack: {server_reply}')
	if server_reply and server_unpack[0].decode('utf-8') == 'rt':
		print(f'Received mp list len from server: {server_unpack[1]}')
		mp_list_len = server_unpack[1]
		for i in range(1, mp_list_len + 1):
			server_reply = cSocket.recv(BUF_SIZE)
			print(f'server_reply: {server_reply}')
			server_unpack = struct.unpack('2s i i', server_reply)
			if server_reply and server_unpack[0].decode('utf-8') == 'mp':
				mp_p = server_unpack[1]
				mp = server_unpack[2]
				local_mp_dict[i] = {"id": i, "p": mp_p, "value": mp}
				print(f'Received mp {i} from server: {mp_p}, {mp}')
	

def calc_process(cSocket):
	# request task to server
	client_msg = struct.pack('2s i i', b'ts', 0, 0)
	cSocket.send(client_msg)
	# receive task from server
	server_reply = cSocket.recv(BUF_SIZE)
	server_unpack = struct.unpack('2s i i', server_reply) # 'rc', start_num, window_size 
	if server_reply and server_unpack[0].decode('utf-8') == 'rc':
		print('Received task from server')
		start_num = server_unpack[1]
		window_size = server_unpack[2]
		mp_status = 0
		print(f'Received task from server: {start_num}, {window_size}')
		# calculate
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
			time.sleep(0.5)

		client_msg = struct.pack('2s i i', b'ed', start_num, window_size)
		cSocket.send(client_msg)

def select_mode():
	while True:
		flag = input("(A)calc process, (B)exit: ")
		if flag == "A" or flag == "a":
			print("calc process!")
			break
		elif flag == "S" or flag == "s":
			print("show MP!")
			break
		elif flag == "B" or flag == "b":
			print("exit!")
			break
		else:
			print("Invalid input. Please try again.")

	return flag

def main():
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
		while True:
			flag = select_mode()
			if flag == "A" or flag == "a":
				calc_process(cSocket)
			if flag == "S" or flag == "s":
				show_mp(cSocket)
			elif flag == "B" or flag == "b":
				exit(1)

	except socket.error as e:
		print('Socket error: %s' % str(e))
	except KeyboardInterrupt as e:
		print('KeyboardInterrupt: %s' % str(e))
	except Exception as e:
		print('Other exception: %s' % str(e))
		

# end of main


if __name__ == '__main__':
	main()
