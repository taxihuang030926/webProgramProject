import socket
import struct
import threading
import time

PORT = 55558
backlog = 5
BUF_SIZE = 1024			# Receive buffer size
mp_dict = {} # eg. {2: 3, 3: 7, 5: 31, 7: 127, 13: 8191, 17: 131071, 19: 524287, 31: 2147483647}

start_num = 1
WINDOW_SIZE = 10 # TODO: larger if function test done
mp_list = [0] * WINDOW_SIZE
prc_list = [0] * WINDOW_SIZE

class ServerThread(threading.Thread):
	def __init__(self, t_name, client_sc, rip, rport):
		super().__init__(name = t_name)
		self.client = client_sc
		self.rip = rip
		self.rport = rport
		self.start()		# Start the thread when it is created
	# end for __init__()
	
	def run(self):
		name = threading.current_thread().name
		print(f'{name}: In run()')

		# receive connection confirmation
		client_msg = self.client.recv(BUF_SIZE)
		if client_msg:
			msg = name + ": Receive message: " + client_msg.decode('utf-8') + "; from " + str(self.rip) + ":" + str(self.rport)
			print(msg)
			# wait for 5 second
			time.sleep(2)
			server_reply = name + ": Server Reply!!"
			self.client.send(server_reply.encode('utf-8'))

		global start_num
		global WINDOW_SIZE
		global mp_dict
		global mp_list
		global prc_list
		
		while True:
			try:
				# svr recv cli request for task
				client_msg = self.client.recv(BUF_SIZE)
				client_unpack = struct.unpack('2s i i', client_msg)
				if client_msg and client_unpack[0].decode('utf-8') == 'ts':

					# send task
					server_msg = struct.pack('2s i i', b'rc', start_num, WINDOW_SIZE)
					server_unpacked = ('d'.encode('utf-8'), start_num, WINDOW_SIZE)
					print(f'Sending task to {name}: {server_unpacked}')
					self.client.send(server_msg)
					print(f'{name}: Sent task to client')

					for _ in range(WINDOW_SIZE + 1):
						# receive result
						client_msg = self.client.recv(BUF_SIZE)
						client_unpack = struct.unpack('2s i i', client_msg)
						if client_msg and client_unpack[0].decode('utf-8') == 'ch':
							print(f'{name}: Received message: {client_unpack}')
							# update prc_list
							prc_list[client_unpack[1] - start_num] += 1
							# check mp_status then add to mp_list for threshold calc
							if client_unpack[1] >= start_num and client_unpack[2] == 1:
								mp_list[client_unpack[1] - start_num] += 1
								print(f'would be 2^({client_unpack[1]}) - 1: {2 ** client_unpack[1] - 1}')

						elif client_msg and client_unpack[0].decode('utf-8') == 'ed':
							print(f'{name}: Received message: {client_unpack}')
							print(f'{name}: prc_list: {prc_list}')
							print(f'{name}: mp_list: {mp_list}')
							threshold_flag = 0
							for i in range(WINDOW_SIZE):
								if prc_list[i] < 10:
									threshold_flag = 1
									break
							
							if threshold_flag == 0:
								# calculate threshold
								for i in range(WINDOW_SIZE):
									if mp_list[i] >= 10:
										mp_dict[len(mp_dict) + 1] = {
											"id": len(mp_dict) + 1,
											"p": start_num + i,
											"value": 2 ** (start_num + i) - 1
										}
								print(f'mp_dict: {mp_dict}')
								# update start_num
								start_num += WINDOW_SIZE
								# reset prc_list and mp_list
								prc_list = [0] * WINDOW_SIZE
								mp_list = [0] * WINDOW_SIZE
						
					# wait for new response

				elif client_msg and client_unpack[0].decode('utf-8') == 'ft':
					print(f'{name}: Received message: {client_unpack}')
					# send mp_list to client
					server_msg = struct.pack('2s i i', b'rt', len(mp_dict))
					server_unpacked = ('rt'.encode('utf-8'), len(mp_dict), 0)
					print(f'Sending mp_list to {name}: {server_unpacked}')
					self.client.send(server_msg)
					print(f'{name}: Sent mp_list to client')
					
			except socket.error as e:
				print(f'Socket error: {e}')
				break
			except struct.error as e:
				# print(f'lost connection')
				break
			except Exception as e:
				print(f'Other exception: {e}')
				# break
		
		self.client.close()
		print(name, 'Thread closed')
	# end run()

# end for ServerThread

def main():
	# Create a TCP Server socket
	srvSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	srvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	
	print('Starting up server on port: %s' % (PORT))
	srvSocket.bind(('', PORT))
	srvSocket.listen(backlog)
	
	global i
	i = 0
	rcounts = [0] * WINDOW_SIZE
	try:
		while True:
			t_name = 'Thread ' + str(i)
			print('Number of threads: %d' % threading.active_count())
			print('Waiting to receive message from client')
			client, (rip, rport) = srvSocket.accept()
			print('Got connection. Create thread: %s' % t_name)
			t = ServerThread(t_name, client, rip, rport)
			i += 1
	except KeyboardInterrupt as e:
		print('KeyboardInterrupt: %s' % str(e))
		client.close()
		
	srvSocket.close()
# end of main

if __name__ == '__main__':
	main()
