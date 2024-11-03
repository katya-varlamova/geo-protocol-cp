import socket
import json
import time
from encryption_utils import encrypt_data, decrypt_data
from gps_utils import LocationService
def udp_sender(port, key, cur_token):
    frame_num = 0
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_time = time.time()
    service = LocationService()
    while time.time() - start_time < 10:
        frame_num += 1
        loc = service.get_location_data()
        data = {
            "frame_num": frame_num,
            **loc,
            "token" : cur_token
        }
        
        encrypted = encrypt_data(key, json.dumps(data))
        udp_socket.sendto(json.dumps({"data": encrypted}).encode(), ('localhost', port))

        fn = data["frame_num"]
        #print(f"Отправлено по UDP: {fn} {loc}")
        time.sleep(0.3)

def udp_reciever(port, key, partner_token, signal):
    udp_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_receiver.bind(('localhost', port))
    start_time = time.time()
    udp_receiver.settimeout(5)
    last_fn = -1
    while time.time() - start_time < 15:
        data = None
        try:
            data, _ = udp_receiver.recvfrom(1024)
            rec = json.loads(data.decode())
            if "data" not in rec:
                print("error auth or data")
                break
            decrypted = decrypt_data(key, rec["data"])
            data = json.loads(decrypted)

            if not data or partner_token != data["token"]:
                print("error auth or data")
                break
            fn = data["frame_num"]
            loc = (data["latitude"], data["longitude"])
            if int(fn) > last_fn:
                signal.update_geoposition(loc)
                last_fn = int(fn)
                #print(f"Получено по UDP: {fn} {loc}")
        except socket.timeout:
            break
        if not data:
            break
        
    udp_receiver.close()
