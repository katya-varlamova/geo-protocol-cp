from flask import Flask, render_template, request, jsonify
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
MAX_BUFFER_SIZE = 5
username = None
password = None
auth = False

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
    while not auth:
        pass
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.sendall(f"{username},{password}".encode())
    response = client.recv(1024).decode()

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


@app.route("/login", methods=["POST"])
def login():
    global username
    global password
    global auth
    username = "client1" #request.form["username"]
    password = "password1" #request.form["password"]
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.sendall(f"{username},{password}".encode())
    response = client.recv(1024).decode()
    client.close()
    if response == "Authorized":
        auth = True
        return render_template('index.html')
    else:
        return render_template("login.html")

@app.route('/')
def index():
    if auth:
        return render_template('index.html')
    else:
        return render_template("login.html")

if __name__ == '__main__':
    threading.Thread(target=connect_to_server).start()
    socketio.run(app)

