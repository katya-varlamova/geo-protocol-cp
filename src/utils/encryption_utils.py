from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64
import os
import json
def send_to_sock_encrypted(key, socket, json_dict):
    encrypted = encrypt_data(key, json.dumps(json_dict))
    socket.sendall(json.dumps({"data": encrypted}).encode())

def recv_from_sock_encrypted(key, socket):
    rec = json.loads(socket.recv(4096).decode())
    if "data" not in rec:
        return None
    
    decrypted = decrypt_data(key, rec["data"])
    data = json.loads(decrypted)
    return data

def encrypt_data(key: bytes, plaintext: str) -> str:
    iv = os.urandom(16)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    return base64.b64encode(iv + ciphertext).decode('utf-8')


def decrypt_data(key: bytes, encrypted_data: str) -> str:
    decoded_data = base64.b64decode(encrypted_data)
    
    iv = decoded_data[:16]
    ciphertext = decoded_data[16:]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    
    return plaintext.decode()
