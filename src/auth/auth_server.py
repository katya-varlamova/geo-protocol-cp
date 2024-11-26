import os
import json
import sqlite3
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from diffiehellman.diffiehellman import DiffieHellman
from utils.encryption_utils import encrypt_data, decrypt_data
from utils.jwt_utils import generate_jwt, validate_jwt
class Client:
    def __init__(self, client, token = None, key = None):
        self.client =  client
        self.token = token
        self.key = key
    def print(self):
        print(self.client, self.token, self.key)
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.urandom(24)
jwt = JWTManager(app)
CLIENT_DATA = {}
INSTANCE_DH_SERVER = DiffieHellman()
INSTANCE_DH_SERVER.generate_public_key()

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            address TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/register', methods=['POST'])
def register():
    username = request.get_json()["username"]
    if username not in CLIENT_DATA or not CLIENT_DATA[username].key:
        return jsonify({"msg": "Key-exchamge needed!"}), 400
    data = json.loads(decrypt_data(CLIENT_DATA[username].key, request.get_json()["data"]))
    username = data.get('username')
    password = data.get('password')
    address = data.get('address')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO users (username, password, address) VALUES (?, ?, ?)', (username, password, address))
        conn.commit()
        return jsonify({"msg": "User registered successfully!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"msg": "Username already exists!"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.get_json()["username"]
    if username not in CLIENT_DATA or not CLIENT_DATA[username].key:
        return jsonify({"msg": "Key-exchamge needed!"}), 400
    data = json.loads(decrypt_data(CLIENT_DATA[username].key, request.get_json()["data"]))
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = c.fetchone()
    print(user)
    if user:
        enc = encrypt_data(CLIENT_DATA[username].key,
                                    json.dumps({"token" : generate_jwt(username), "address" : user[3]}))

        data = enc
        return jsonify(data=data), 200
    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/check_token', methods=['GET'])
def check_token():
    username = request.get_json()["username"]
    if username not in CLIENT_DATA or not CLIENT_DATA[username].key:
        return jsonify({"msg": "Key-exchamge needed!"}), 400
    data = json.loads(decrypt_data(CLIENT_DATA[username].key, request.get_json()["token"]))
    res = validate_jwt(data.get('token'))
    if not res:
        return jsonify({"msg": "Bad JWT: expired or invalid"}), 401
    else:
        return jsonify({"msg": "Check OK!"}), 200

@app.route('/key_exchange', methods=['GET'])
def key_exchange():
    data = request.get_json()
    client_public_key = data["client_public_key"]
    client = data["username"]
    key = INSTANCE_DH_SERVER.generate_shared_secret(client_public_key, echo_return_key=True)
    CLIENT_DATA[client] = Client(client, key=key)
    return jsonify({"server_public_key": INSTANCE_DH_SERVER.public_key}), 200

@app.route('/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT username, address FROM users')
    users = cursor.fetchall()
    user_list = [{'username': user[0], 'address': user[1]} for user in users]
    conn.close()

    return jsonify(user_list)

if __name__ == '__main__':
    app.run(debug=True)
