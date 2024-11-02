import socket
import json
import time
import threading
from utils import udp_reciever, udp_sender
from auth_client import AuthClient
from encryption_utils import send_to_sock_encrypted, recv_from_sock_encrypted
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

    def work(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(('localhost', 8000))
        tcp_socket.listen(1)
        
        print("Ожидание подключения...")
        conn, addr = tcp_socket.accept()
        
        with conn:
            token = self.auth_client.login(self.username, self.password)
            request = json.loads(conn.recv(4096).decode())
            if "username_initiator" not in request or "public_key_initiator" not in request:
                conn.close()
                tcp_socket.close()
                return


            conn.sendall(json.dumps({'username_reciever': self.username,
                                    'public_key_reciever': self.auth_client.get_instance().public_key}).encode())
            
            un_initiator = request["username_initiator"]
            pk_initiator = request["public_key_initiator"]
            key = self.auth_client.get_instance().generate_shared_secret(pk_initiator, echo_return_key=True)


            data = recv_from_sock_encrypted(key, conn)

            if not data or "token" not in data or not self.auth_client.check_token(data["token"], self.username):
                print("Ошибка авторизации")
                conn.close()
                tcp_socket.close()
                return


            want_share = int(input(f"Вы хотите делиться геопозицией с пользователем {un_initiator} ?"))
            if not want_share:
                conn.sendall(json.dumps({'error': "refused to share"}).encode())
                conn.close()
                tcp_socket.close()
                return
            
            send_to_sock_encrypted(key, conn, {"token" : token})

            self.client_data[un_initiator] = Client(un_initiator, key=key, token=data["token"])

            for cl in self.client_data:
                self.client_data[cl].print()


            data = recv_from_sock_encrypted(key, conn)
            want_get = False
            if not data or "action" not in data:
                conn.sendall(json.dumps({'error': "refused to share"}).encode())
                print("Ошибка авторизации")
            else:
                want_get = int(input(f"Вы хотите получать геопозицию пользователя {un_initiator} ?"))
                type_conn = "single"
                if want_get:
                    type_conn = "duplex"
                    send_to_sock_encrypted(key, conn, {"action" : type_conn})
                else:
                    conn.sendall(json.dumps({'error': "refused to share"}).encode())
            tcp_socket.close()
            udp_sender_thread = threading.Thread(target=udp_sender, args=(6001, bytes(key), token,))
            udp_sender_thread.start()
        
            if want_get:
                udp_reciever_thread = threading.Thread(target=udp_reciever, args=(6002, bytes(key), self.client_data[un_initiator].token,))
                udp_reciever_thread.start()
                udp_reciever_thread.join()
            udp_sender_thread.join()
        tcp_socket.close()

            
class Initiator:
    def __init__(self, username, password):
        self.client_data = {}
        self.username = username
        self.password = password
        self.auth_client = AuthClient()
    def work(self):
        token = self.auth_client.login(self.username, self.password)
        if not token:
            return
        
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect(('localhost', 8000))
        tcp_socket.sendall(json.dumps({'username_initiator': self.username, 'public_key_initiator': self.auth_client.get_instance().public_key}).encode())
        
        response = json.loads(tcp_socket.recv(4096).decode())

        if 'username_reciever' not in response or "public_key_reciever" not in response:
            print("Ошибка обмена ключами")
            tcp_socket.close()
            return
        
        un_reciever = response["username_reciever"]
        pk_reciever = response["public_key_reciever"]
        key = self.auth_client.get_instance().generate_shared_secret(pk_reciever, echo_return_key=True)

        send_to_sock_encrypted(key, tcp_socket, {"token" : token})

        data = recv_from_sock_encrypted(key, tcp_socket)
        
        if not data or "token" not in data or not self.auth_client.check_token(data["token"], self.username):
            print("Ошибка авторизации")
            tcp_socket.close()
            return

        self.client_data[un_reciever] = Client(un_reciever, key=key, token=data["token"])
        for cl in self.client_data:
            self.client_data[cl].print()

        want_share = int(input(f"Вы хотите делиться геопозицией с пользователем {un_reciever} ?"))
        duplex = want_share
        if want_share:
            send_to_sock_encrypted(key, tcp_socket, {"action" : "duplex"})
            data = recv_from_sock_encrypted(key, tcp_socket)    
            if not data or "action" not in data:
                print("Ошибка авторизации")
                tcp_socket.close()
                duplex = False
        else:
            tcp_socket.sendall(json.dumps({'error': "refused to share"}).encode())

        tcp_socket.close()


        udp_reciever_thread = threading.Thread(target=udp_reciever, args=(6001, bytes(key), self.client_data[un_reciever].token, ))
        udp_reciever_thread.start()

        if duplex:
            udp_sender_thread = threading.Thread(target=udp_sender, args=(6002, bytes(key), token, ))
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
        Initiator(USERNAME, PASSWORD).work()
    else:
        Reciever(USERNAME, PASSWORD).work()

    
