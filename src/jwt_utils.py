import jwt
import datetime

SECRET_KEY = 'your_secret_key'

def generate_jwt(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def validate_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
