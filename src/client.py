import socket
import json
import time
import threading
from utils.udp_utils import udp_reciever, udp_sender
from auth.auth_client import AuthClient
from utils.encryption_utils import send_to_sock_encrypted, recv_from_sock_encrypted
import sys

class Client:
    def __init__(self, client, token = None, key = None):
        self.client =  client
        self.token = token
        self.key = key
    def print(self):
        print(self.client, self.token, self.key)

class Reciever:
    def __init__(self, username, password):
        self.client_data = {}
        self.username = username
        self.password = password
        self.auth_client = AuthClient()
        self.conn = None
        self.tcp_socket = None
        self.active = False
        self.want_get = False
        self.want_share = False
        self.address = ""
        self.initiator_address = ""

    def get_conn(self):
        self.token, self.address = self.auth_client.login(self.username, self.password)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = int(self.address.split(":")[1])
        self.ip = self.address.split(":")[0]
        try:
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind(('localhost', int(self.port)))
        except:
            return False, "Ошибка подключения"
        self.tcp_socket.listen(1)
        
        print("Ожидание подключения...")
        self.conn, addr = self.tcp_socket.accept()
        self.active = True
        request = json.loads(self.conn.recv(4096).decode())
        if "username_initiator" not in request or "public_key_initiator" not in request:
            self.conn.close()
            self.active = False
            return False, "Неправильный запрос от инициатора"
        self.initiator_name = request["username_initiator"]
        self.initiator_address = [el["address"]  for el in self.auth_client.get_users() if el["username"] == self.initiator_name][0]

        pk_initiator = request["public_key_initiator"]
        self.key = self.auth_client.get_instance().generate_shared_secret(pk_initiator, echo_return_key=True)
        return True, ""

    def exchange(self):
        with self.conn:
            self.conn.sendall(json.dumps({'username_reciever': self.username,
                                    'public_key_reciever': self.auth_client.get_instance().public_key}).encode())
            


            data = recv_from_sock_encrypted(self.key, self.conn)

            if not data or "token" not in data or not self.auth_client.check_token(data["token"], self.username):
                self.conn.close()
                self.active = False
                return False, "Ошибка авторизации"

            
            send_to_sock_encrypted(self.key, self.conn, {"token" : self.token})

            self.client_data[self.initiator_name] = Client(self.initiator_name, key=self.key, token=data["token"])

            for cl in self.client_data:
                self.client_data[cl].print()


            data = recv_from_sock_encrypted(self.key, self.conn)
 
             #want_share = int(input(f"Вы хотите делиться геопозицией с пользователем {un_initiator} ?"))
            if not self.want_share or not data or "action" not in data  or "port" not in data:
                send_to_sock_encrypted(self.key, self.conn, {"error" : "refused to share"})
                self.conn.close()
                self.active = False
                return False, "Отказ делиться геопозицией"
            else:
                type_conn = data["action"]
                self.sender_port = data["port"]
                if not self.want_get or not type_conn == "duplex":
                    self.want_get = False
                    type_conn = "single"
                    send_to_sock_encrypted(self.key, self.conn, {"action" : type_conn})
                else:
                    self.udp_socket_reciever = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.udp_socket_reciever.bind(('', 0))
                    self.udp_socket_reciever_port = self.udp_socket_reciever.getsockname()[1]
                    self.want_get = True
                    send_to_sock_encrypted(self.key, self.conn, {"action" : type_conn, "port" : self.udp_socket_reciever_port})
                
            self.tcp_socket = None
            self.active = False
            self.tcp_socket.close()
            return True, "Success"

    def exchange_geoposition(self, signal):
        udp_sender_thread = threading.Thread(target=udp_sender, args=(self.initiator_address, self.sender_port, bytes(self.key), self.token, 54820))
        udp_sender_thread.start()
    
        if self.want_get:
            udp_reciever_thread = threading.Thread(target=udp_reciever, args=(self.udp_socket_reciever, bytes(self.key), self.client_data[self.initiator_name].token, signal))
            udp_reciever_thread.start()
            udp_reciever_thread.join()
        udp_sender_thread.join()


            
class Initiator:
    def __init__(self, username, password):
        self.client_data = {}
        self.username = username
        self.password = password
        self.auth_client = AuthClient()
        self.want_get = True
        self.want_share = False
        self.reciever_name = ""
        self.address = ""
        self.reciever_address = ""
    def exchange(self, reciever):
        self.token, self.address = self.auth_client.login(self.username, self.password)
        self.reciever_address = reciever
        self.reciever_port = int(self.reciever_address.split(":")[1])
        self.reciever_ip = self.reciever_address.split(":")[0]
        if not self.token or not self.reciever_address:
            return

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tcp_socket.connect((self.reciever_ip, self.reciever_port))
        except:
            return False, "Ошибка подключения к пользователю"
        tcp_socket.sendall(json.dumps({'username_initiator': self.username, 'public_key_initiator': self.auth_client.get_instance().public_key}).encode())
        
        response = json.loads(tcp_socket.recv(4096).decode())

        if 'username_reciever' not in response or "public_key_reciever" not in response:
            tcp_socket.close()
            return False, "Ошибка обмена ключами"
        
        un_reciever = response["username_reciever"]
        self.reciever_name = un_reciever
        pk_reciever = response["public_key_reciever"]
        self.key = self.auth_client.get_instance().generate_shared_secret(pk_reciever, echo_return_key=True)

        send_to_sock_encrypted(self.key, tcp_socket, {"token" : self.token})

        data = recv_from_sock_encrypted(self.key, tcp_socket)
        
        if not data or "token" not in data or not self.auth_client.check_token(data["token"], self.username):
            tcp_socket.close()
            return False, "Ошибка авторизации"

        self.client_data[un_reciever] = Client(un_reciever, key=self.key, token=data["token"])
        for cl in self.client_data:
            self.client_data[cl].print()

        self.udp_socket_reciever = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket_reciever.bind(('', 0))
        self.udp_socket_reciever_port = self.udp_socket_reciever.getsockname()[1]
        act = "single"
        if self.want_share:
            act = "duplex"
        send_to_sock_encrypted(self.key, tcp_socket, {"action" : act, "port" : self.udp_socket_reciever_port})

        data = recv_from_sock_encrypted(self.key, tcp_socket)
          
        if not data or "action" not in data:
            tcp_socket.close()
            self.udp_socket_reciever.close()
            return False, "Ошибка авторизации"
        else:
            act = data["action"]
            if act == "single":
                self.want_share = False
            else:
                if "port" not in data:
                    tcp_socket.close()
                    self.udp_socket_reciever.close()
                    return False, "Ошибка авторизации"
                else:
                    self.udp_socket_sender_port = data["port"]
        tcp_socket.close()
        return True, "Success"

    def exchange_geoposition(self, signal):
        udp_reciever_thread = threading.Thread(target=udp_reciever, args=(self.udp_socket_reciever, bytes(self.key), self.client_data[self.reciever_name].token, signal ))
        udp_reciever_thread.start()

        if self.want_share:
            udp_sender_thread = threading.Thread(target=udp_sender, args=(self.reciever_address, self.udp_socket_sender_port, bytes(self.key), self.token, 13904 ))
            udp_sender_thread.start()
            udp_sender_thread.join()
        udp_reciever_thread.join()

if __name__ == "__main__":
    USERNAME = sys.argv[1]
    PASSWORD = sys.argv[2]
    auth = AuthClient()
    auth.change_keys(USERNAME)
    auth.register(USERNAME, PASSWORD)

    if sys.argv[3] == "i":
        init = Initiator(USERNAME, PASSWORD)
        init.want_get = True
        init.want_share = True
        print(init.exchange())
        print(init.exchange_geoposition())
        
    else:
        rec = Reciever(USERNAME, PASSWORD)
        rec.want_share = True
        rec.want_get = True
        print(rec.get_conn())
        print(rec.exchange())
        print(rec.exchange_geoposition())

    
