import socket
import json
import time
from collections import deque

HOST = 'localhost'  # Адрес сервера
PORT = 5000  # Порт сервера
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
                break  # Выход, если соединение закрыто
            buf += data
            extracted, buf = extract_json_and_buffer(buf)
            print(extracted)

    finally:
        client.close()

if __name__ == "__main__":
    connect_to_server()
