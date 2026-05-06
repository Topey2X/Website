from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from config import SECRET_KEY, DATABASE_URI, SESSION_LIFETIME_MINUTES
from datetime import timedelta

server = Flask(__name__)
db = SQLAlchemy()
login_manager = LoginManager()

def create_server():
    # Flask config
    server.secret_key = SECRET_KEY

    # SQLAlchemy config
    server.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Flask-Session config — SQLAlchemy backend
    server.config["SESSION_TYPE"] = "sqlalchemy"
    server.config["SESSION_SQLALCHEMY"] = db
    server.config["SESSION_PERMANENT"] = True
    server.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=SESSION_LIFETIME_MINUTES)

    db.init_app(server)
    login_manager.init_app(server)
    Session(server)

    return server