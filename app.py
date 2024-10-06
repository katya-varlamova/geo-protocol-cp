from flask import Flask, render_template
from flask_socketio import SocketIO
import random
import time
import threading
import socket
import json
import time
from collections import deque


app = Flask(__name__)
socketio = SocketIO(app)

HOST = 'localhost'
PORT = 5001
USERNAME = "client1"
PASSWORD = "password1"
MAX_BUFFER_SIZE = 5


def extract_json_and_buffer(input_string):
    if ";" not in input_string:
        return None, input_string
    arr = input_string.split(";")
    objs = []
    for i in range(len(arr) - 1):
        objs.append(json.loads(arr[i]))
    end = arr[-1]
    return objs, end

def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.sendall(f"{USERNAME},{PASSWORD}".encode())
    response = client.recv(1024).decode()
    if response != "Authorized":
        print("Authorization failed")
        return

    print("Connected to the server")

    try:
        buf = ""
        last = 0
        while True:
            data = client.recv(1024).decode()
            if not data:
                break
            buf += data
            extracted, buf = extract_json_and_buffer(buf)
            for ext in extracted:
                latitude = float(ext["latitude"])
                longitude = float(ext["longitude"])
                socketio.emit('new_position', {'lat': latitude, 'lon': longitude})

    finally:
        client.close()
        
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=connect_to_server).start()
    socketio.run(app)

