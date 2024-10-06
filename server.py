import socket
import threading
import json
import time
from collections import deque
from gps3 import gps3

HOST = '0.0.0.0'  # Сервер будет слушать на всех интерфейсах
PORT = 5000
AUTHORIZED_CLIENTS = {"client1": "password1", "client2": "password2"}  # Авторизация клиентов
positions = deque(maxlen=10)  # Храним последние 10 позиций для сглаживания

gpsd_socket = gps3.GPSDSocket()
data_stream = gps3.DataStream()
gpsd_socket.connect()
gpsd_socket.watch()



def get_gps_data():
    for new_data in gpsd_socket:
        if new_data:
            data_stream.unpack(new_data)
            longitude = data_stream.TPV['alt']
            latitude = data_stream.TPV['lat']
            print(f"Широта: {latitude}, Долгота: {longitude}")
            return {
                "latitude": latitude,
                "longitude": longitude,
            }
    return None

def client_handler(conn, addr):
    position_counter = 0
    print(f"Подключен клиент: {addr}")

    try:
        # Запрос авторизации от клиента
        credentials = conn.recv(1024).decode()
        username, password = credentials.split(',')
        if AUTHORIZED_CLIENTS.get(username) != password:
            conn.sendall(b"Unauthorized")
            return

        conn.sendall(b"Authorized")
        
        while True:
            gps_data = get_gps_data()
            if not gps_data:
                continue
            position_counter += 1
            output_data = {
                "position_id": position_counter,
                "timestamp": time.time(),
                **gps_data
            }
            positions.append(output_data)

            # Сглаживание данных (скользящее среднее)
            avg_latitude = sum(pos["latitude"] for pos in positions) / len(positions)
            avg_longitude = sum(pos["longitude"] for pos in positions) / len(positions)

            smoothed_output = {
                "position_id": position_counter,
                "timestamp": time.time(),
                "latitude": avg_latitude,
                "longitude": avg_longitude
            }
            #print(smoothed_output)

            conn.sendall((json.dumps(smoothed_output) + ";").encode())  # Отправляем данные клиенту
            time.sleep(0.00001)  # Пауза 1 секунда между отправками
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
