import socket
import threading
import json
import time
from collections import deque
import requests
from geopy.geocoders import Nominatim
HOST = '0.0.0.0'
PORT = 5001
AUTHORIZED_CLIENTS = {"client1": "password1", "client2": "password2"}
positions = deque(maxlen=10)
mul = 1

def get_real_location_data():
    try:
        response = requests.get("http://ip-api.com/json/")
        response.raise_for_status()
        location_data = response.json()
        
        latitude = location_data.get("lat")
        longitude = location_data.get("lon")

        return {"latitude": latitude,
                "longitude": longitude}
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения местоположения: {e}")
    return None

def get_fake_location_data():
    global mul
    latitude = 55.7482
    longitude = 37.6171
    x = 0.0001
    y = 0.0001
    mul += 1
    return {"latitude": latitude + x * mul,
            "longitude": longitude + x * mul}

def client_handler(conn, addr, get_location_data=get_fake_location_data):
    position_counter = 0
    print(f"Подключен клиент: {addr}")

    try:
        credentials = conn.recv(1024).decode()
        username, password = credentials.split(',')
        if AUTHORIZED_CLIENTS.get(username) != password:
            conn.sendall(b"Unauthorized")
            return

        conn.sendall(b"Authorized")
        
        while True:
            loc_data = get_location_data()
            if not loc_data:
                continue
            position_counter += 1
            output_data = {
                "position_id": position_counter,
                "timestamp": time.time(),
                **loc_data
            }
            positions.append(output_data)

            avg_latitude = sum(pos["latitude"] for pos in positions) / len(positions)
            avg_longitude = sum(pos["longitude"] for pos in positions) / len(positions)

            smoothed_output = {
                "position_id": position_counter,
                "timestamp": time.time(),
                "latitude": avg_latitude,
                "longitude": avg_longitude
            }

            conn.sendall((json.dumps(smoothed_output) + ";").encode())
            time.sleep(0.01)
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Сервер запущен на {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=client_handler, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
