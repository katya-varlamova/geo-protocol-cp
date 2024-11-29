import socket
import json
import time
from utils.encryption_utils import encrypt_data, decrypt_data
from utils.gps_utils import LocationService
def udp_sender(address, port, key, cur_token, seed):
    frame_num = 0
    ip = address.split(":")[0]
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_time = time.time()
    service = LocationService(seed)
    while time.time() - start_time < 20:
        frame_num += 1
        loc = service.get_location_data()
        data = {
            "frame_num": frame_num,
            **loc,
            "token" : cur_token
        }
        
        encrypted = encrypt_data(key, json.dumps(data))
        udp_socket.sendto(json.dumps({"data": encrypted}).encode(), (ip, port))
        time.sleep(0.15)

def udp_reciever(udp_receiver, key, partner_token, signal):
    start_time = time.time()
    udp_receiver.settimeout(1)
    last_fn = -1
    while time.time() - start_time < 20:
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
        except socket.timeout:
            break
        if not data:
            break
        
    udp_receiver.close()
