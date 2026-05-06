from server import db, login_manager
from models import User, UserModel
from datetime import datetime, timezone
from flask_login import login_user, logout_user
from flask import session
import json, bcrypt

@login_manager.user_loader
def load_user(username):
    u = db.session.get(UserModel, username)
    if u:
        return User(u)
    return None

def verify_password(username, password):
    u = db.session.get(UserModel, username)
    if not u:
        return False
    if u.password_hash is None:
        # No password set, use `u.supply` to generate a temporary password
        new_password = bcrypt.hashpw(u.supply.encode(), bcrypt.gensalt()).decode()
        u.password_hash = new_password
        db.session.commit()
        # Continue to verify the provided password against the new hash

    return bcrypt.checkpw(password.encode(), u.password_hash.encode())

def get_user_settings(username):
    u = db.session.get(UserModel, username)
    return json.loads(u.settings) if u else {}

def do_login(username):
    u = db.session.get(UserModel, username)
    if u:
        u.last_login = datetime.now(timezone.utc)
        db.session.commit()
        login_user(User(u), remember=True)
        
def do_logout():
    logout_user()
    session.clear()