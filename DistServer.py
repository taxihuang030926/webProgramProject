from flask import Flask, request, jsonify
from threading import Thread, Lock
import requests
import time
import random

app = Flask(__name__)

# 全局變數
tasks = list(range(100, 200))  
completed_results = {}
task_lock = Lock()

# Helper: 分配任務
def assign_task():
    global tasks
    with task_lock:
        if tasks:
            return tasks.pop(0)
    return None

# API 路徑：提交計算結果
@app.route('/submit_result', methods=['POST'])
def submit_result():
    data = request.json
    task_id = data.get('task_id')
    result = data.get('result')

    with task_lock:
        if task_id not in completed_results:
            completed_results[task_id] = result
            return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'duplicate'}), 409

# API 路徑：請求任務
@app.route('/request_task', methods=['GET'])
def request_task():
    task = assign_task()
    if task is not None:
        return jsonify({'task_id': task}), 200
    return jsonify({'status': 'no tasks available'}), 204

# 任務管理執行緒
def task_manager(client_id):
    while True:
        response = requests.get(f'http://localhost:5000/request_task')
        if response.status_code == 200:
            task_id = response.json()['task_id']
            print(f"[Server] Assigning task {task_id} to client {client_id}")
            
            success = send_task_to_client(client_id, task_id)
            if not success:
                print(f"[Server] Client {client_id} failed. Reassigning task {task_id}.")
                with task_lock:
                    tasks.append(task_id)
        else:
            break
        time.sleep(1)

# Client 通信模擬
def send_task_to_client(client_id, task_id):
    try:
        result = perform_mersenne_check(task_id)
        response = requests.post(f'http://localhost:5000/submit_result', json={'task_id': task_id, 'result': result})
        return response.status_code == 200
    except Exception as e:
        print(f"[Server] Error with client {client_id}: {e}")
        return False

# 檢查梅森質數的邏輯
def perform_mersenne_check(p):
    return (2 ** p - 1) % p == 0

# 啟動伺服器
if __name__ == '__main__':
    # 創建三個 client 管理執行緒
    for i in range(3):
        Thread(target=task_manager, args=(i,)).start()
    app.run(debug=True)
