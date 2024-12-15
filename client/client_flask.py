import socket
import sys
import struct
import time
import threading
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

PORT = 55558
BUF_SIZE = 1024
SERVER_IP = '127.0.0.1'
current_task = {
    'start_num': 0,
    'window_size': 0,
    'is_running': False
}
mp_dict = {}
client_socket = None
calculation_thread = None

def connect_to_server():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, PORT))
    
    # Initial handshake
    client_socket.send("Client hello!!".encode('utf-8'))
    client_socket.recv(BUF_SIZE)
    return client_socket

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
    if prime == 2:
        return True
    s = 4
    m = 2 ** prime - 1
    for _ in range(prime - 2):
        s = ((s * s) - 2) % m
    return s == 0

def calculation_worker():
    global client_socket, current_task
    
    while current_task['is_running']:
        try:
            # Request task
            client_msg = struct.pack('2s i i', b'ts', 0, 0)
            client_socket.send(client_msg)
            
            # Receive task
            server_reply = client_socket.recv(BUF_SIZE)
            server_unpack = struct.unpack('2s i i', server_reply)
            
            if server_reply and server_unpack[0].decode('utf-8') == 'rc':
                current_task['start_num'] = server_unpack[1]
                current_task['window_size'] = server_unpack[2]
                
                # Calculate
                for i in range(current_task['window_size']):
                    if not current_task['is_running']:
                        break
                    
                    prc_num = current_task['start_num'] + i 
                    mp_status = 1 if isPrime(prc_num) and lucasLehmerTest(prc_num) else 0
                    
                    # Send result
                    result = struct.pack('2s i i', b'ch', prc_num, mp_status)
                    client_socket.send(result)
                    time.sleep(0.5)
                
                # End of window
                client_msg = struct.pack('2s i i', b'ed', current_task['start_num'], current_task['window_size'])
                client_socket.send(client_msg)
        
        except Exception as e:
            print(f"Calculation error: {e}")
            current_task['is_running'] = False

def fetch_mersenne_primes():
    global client_socket
    client_msg = struct.pack('2s i i', b'ft', 0, 0)
    client_socket.send(client_msg)

    server_reply = client_socket.recv(BUF_SIZE)
    server_unpack = struct.unpack('2s i i', server_reply)
    
    if server_reply and server_unpack[0].decode('utf-8') == 'rt':
        return server_unpack[1]
    return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calc', methods=['GET', 'POST'])
def calc():
    global client_socket, calculation_thread, current_task
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'start':
            if not client_socket:
                client_socket = connect_to_server()
            
            current_task['is_running'] = True
            calculation_thread = threading.Thread(target=calculation_worker)
            calculation_thread.start()
        
        elif action == 'pause':
            current_task['is_running'] = False
        
        elif action == 'resume':
            current_task['is_running'] = True
            calculation_thread = threading.Thread(target=calculation_worker)
            calculation_thread.start()
        
        elif action == 'stop':
            current_task['is_running'] = False
    
    return render_template('calc.html', 
                           start_num=current_task.get('start_num', 0), 
                           window_size=current_task.get('window_size', 0),
                           is_running=current_task.get('is_running', False))

@app.route('/show_mp')
def show_mp():
    global client_socket
    
    if not client_socket:
        client_socket = connect_to_server()
    
    mp_list_count = fetch_mersenne_primes()
    return render_template('showmp.html', mp_list_count=mp_list_count)

@app.route('/about')
def about():
    return render_template('about.html')

def main():
    if len(sys.argv) < 2:
        print('Usage: python client_flask.py <port>')
        sys.exit(1)
    cport = str(sys.argv[1])
    app.run(port=cport, debug=True)

if __name__ == '__main__':
    main()