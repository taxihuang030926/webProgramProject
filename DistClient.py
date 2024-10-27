import tkinter as tk
import requests

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Distributed Computing Client")
        
        self.label = tk.Label(root, text="等待任務分配...")
        self.label.pack()
        
        self.result_label = tk.Label(root, text="")
        self.result_label.pack()
        
        self.start_button = tk.Button(root, text="開始接收任務", command=self.start_task)
        self.start_button.pack()
        
        self.task_id = None
        
    def start_task(self):
        self.label.config(text="請求任務中...")
        response = requests.get('http://localhost:5000/request_task')
        
        if response.status_code == 200:
            self.task_id = response.json().get('task_id')
            self.label.config(text=f"收到任務: 檢查梅森質數 p={self.task_id}")
            self.check_mersenne()
        else:
            self.label.config(text="目前無任務可分配")
    
    def check_mersenne(self):
        result = (2 ** self.task_id - 1) % self.task_id == 0
        self.result_label.config(text=f"計算結果: {result}")
        self.submit_result(result)
    
    def submit_result(self, result):
        response = requests.post('http://localhost:5000/submit_result', json={'task_id': self.task_id, 'result': result})
        if response.status_code == 200:
            self.label.config(text="結果已成功回傳！")
        else:
            self.label.config(text="結果回傳失敗，請重試。")

# 啟動 GUI
root = tk.Tk()
app = ClientApp(root)
root.mainloop()
