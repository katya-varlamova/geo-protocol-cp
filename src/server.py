import socket
import threading
import json
import time
from collections import deque
import requests
from geopy.geocoders import Nominatim
import random
import numpy as np
from filters import kalman_filter, sliding_window_filter
HOST = '0.0.0.0'
PORT = 5001
AUTHORIZED_CLIENTS = {"client1": "password1", "client2": "password2"}
positions = deque(maxlen=50)
mul = 1
latitude = 55.7482
longitude = 37.6171

small_noise_level=0.0005
large_noise_level=0.003
big_noise_level=0.02
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
    step = 0.001 * mul
    r = np.random.rand()
    if r < 0.1:
        noise_lat = np.random.uniform(-large_noise_level, large_noise_level)
        noise_lon = np.random.uniform(-large_noise_level, large_noise_level)
    elif r < 0.9:
        noise_lat = np.random.uniform(-small_noise_level, small_noise_level)
        noise_lon = np.random.uniform(-small_noise_level, small_noise_level)
    else:
        noise_lat = np.random.uniform(-big_noise_level, big_noise_level)
        noise_lon = np.random.uniform(-big_noise_level, big_noise_level)  
        
    dx = step + np.random.uniform(-noise_lat, noise_lat)
    dy = step + np.random.uniform(-noise_lon, noise_lon)
    mul += 1
    return {"latitude": latitude + dx,
            "longitude": longitude + dy}

def client_handler(conn, addr, get_location_data=get_fake_location_data, geofilter=sliding_window_filter):
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
            print(positions)
            filtered_position = geofilter(positions)
            print(filtered_position)
            smoothed_output = {
                "position_id": position_counter,
                "timestamp": time.time(),
                "latitude": filtered_position["latitude"],
                "longitude": filtered_position["longitude"]
            }

            conn.sendall((json.dumps(smoothed_output) + ";").encode())
            time.sleep(0.1)
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
