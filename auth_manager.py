import os
import json
import hashlib
from cryptography.fernet import Fernet

# ---------------------------
# Files
# ---------------------------
USER_FILE = "users.dat"
MASTER_FILE = "master.dat"
KEY_FILE = "key.key"

# ---------------------------
# Initialize encryption key
# ---------------------------
def init_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

fernet = init_key()

# ---------------------------
# Initialize storage
# ---------------------------
def init_storage():
    # kreira USER_FILE ako ne postoji
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "wb") as f:
            f.write(fernet.encrypt(b"[]"))

    # kreira MASTER_FILE samo ako ne postoji
    if not os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, "wb") as f:
            f.write(b"")

# ---------------------------
# Hashing card IDs
# ---------------------------
def hash_id(card_id):
    return hashlib.sha256(card_id.encode()).hexdigest()

# ---------------------------
# Master
# ---------------------------
def save_master(card_id):
    h = hash_id(card_id)
    with open(MASTER_FILE, "wb") as f:
        f.write(fernet.encrypt(h.encode()))

def verify_master(card_id):
    if not os.path.exists(MASTER_FILE) or os.path.getsize(MASTER_FILE) == 0:
        return False
    with open(MASTER_FILE, "rb") as f:
        stored_hash = fernet.decrypt(f.read()).decode()
    return stored_hash == hash_id(card_id)

# ---------------------------
# Users
# ---------------------------
def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "rb") as f:
        decrypted = fernet.decrypt(f.read())
        return json.loads(decrypted)

def save_users(users):
    data = json.dumps(users).encode()
    encrypted = fernet.encrypt(data)
    with open(USER_FILE, "wb") as f:
        f.write(encrypted)

def add_user(card_id, name=None):
    users = load_users()
    h = hash_id(card_id)
    if not name:
        name = f"User {len(users)+1}"
    users.append({"id": h, "name": fernet.encrypt(name.encode()).decode()})
    save_users(users)

def delete_user(index):
    users = load_users()
    if 0 <= index < len(users):
        users.pop(index)
        save_users(users)

def verify_user(card_id):
    users = load_users()
    h = hash_id(card_id)
    for u in users:
        if u["id"] == h:
            return True
    return False

def get_user_name(card_id):
    users = load_users()
    h = hash_id(card_id)
    for u in users:
        if u["id"] == h:
            return fernet.decrypt(u["name"].encode()).decode()
    return None
