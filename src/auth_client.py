import requests
import json
from diffiehellman.diffiehellman import DiffieHellman
from encryption_utils import encrypt_data, decrypt_data
class AuthClient:
    def __init__(self, url='http://127.0.0.1:5000'):
        self.instance_dh = DiffieHellman()
        self.instance_dh.generate_public_key()

        self.auth_server_key = None
        self.base_url = url

    def change_keys(self, username):
        response = requests.get(f'{self.base_url}/key_exchange', json={'username': username, 'client_public_key': self.instance_dh.public_key})
        if response.status_code != 200:
            print("Key exchange failed:", response.json())
            return None
        self.auth_server_key = self.instance_dh.generate_shared_secret(response.json()['server_public_key'], echo_return_key=True)

    def register(self, username, password):
        self.change_keys(username)
        response = requests.post(f'{self.base_url}/register',
                    json= {'username': username,
                            "data": encrypt_data(self.auth_server_key, json.dumps({'username': username, 'password': password}))} )
        if response.status_code == 201:
            print("Register successful!")
            return "OK"
        else:
            print("Register failed:", response.json())
            return None

    def login(self, username, password):
        self.change_keys(username)
        response = requests.post(f'{self.base_url}/login',
                                json= {'username': username,
                                        "data": encrypt_data(self.auth_server_key, json.dumps({'username': username, 'password': password}))} )
        
        if response.status_code == 200:
            print("Login successful!")
            a = response.json()['access_token']
            return json.loads(decrypt_data(self.auth_server_key, a))["token"]
        else:
            print("Login failed:", response.json())
            return None

    def check_token(self, token, username):
        self.change_keys(username)
        response = requests.get(f'{self.base_url}/check_token',
                                json= {'username': username,
                                    "token": encrypt_data(self.auth_server_key, json.dumps({'token': token}))} )
        
        return response.status_code == 200
    def get_instance(self):
        return self.instance_dh
    
if __name__ == "__main__":
    client = AuthClient()
    client.change_keys("test_katya_")
    client.register("test_katya_", "testpassword")
    client.change_keys("test_katya")
    token = client.login("test_katya", "testpassword")
    client.check_token(token, "test_katya_")

