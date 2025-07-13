# auth.py
from werkzeug.security import generate_password_hash, check_password_hash
from quart_jwt_extended import create_access_token  # <-- ADD THIS

users_db = {}

def register_user(username, password):
    if not username or not password:
        return {"message": "Username and password required"}, 400

    if username in users_db:
        return {"message": "User already exists"}, 409

    hashed_pw = generate_password_hash(password)
    users_db[username] = hashed_pw
    return {"message": "User registered successfully"}, 201

def authenticate_user(username, password):
    stored_pw = users_db.get(username)
    if not stored_pw or not check_password_hash(stored_pw, password):
        return None

    # ✅ Return an actual JWT token string
    token = create_access_token(identity=username)
    return token
