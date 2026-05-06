from server import db
from datetime import datetime, timezone
import json
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_model):
        self.id = user_model.username
        self.display_name = user_model.display_name

class UserModel(db.Model):
    __tablename__ = "farms"
    esp           = db.Column(db.Integer, nullable=False) 
    username      = db.Column(db.Text, primary_key=True)
    display_name  = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    site_address  = db.Column(db.Integer, nullable=False)
    supply        = db.Column(db.Text, nullable=False)
    settings      = db.Column(db.Text, default="{}")  # JSON blob
    created_at    = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    sub_active    = db.Column(db.Boolean, default=True)
    sub_expiry    = db.Column(db.DateTime, nullable=True)
    account       = db.Column(db.Integer, nullable=True)
    last_login    = db.Column(db.DateTime)

    def get_setting(self, key, default=None):
        data = json.loads(self.settings or "{}")
        return data.get(key, default)

    def set_setting(self, key, value):
        data = json.loads(self.settings or "{}")
        data[key] = value
        self.settings = json.dumps(data)


# Flask-Session will create its own `sessions` table — we extend it with expires_at
# by subclassing. Flask-Session looks for SESSION_SQLALCHEMY_TABLE if you want to
# rename it, but the default 'sessions' is fine.

class DeviceReferenceModel(db.Model):
    __tablename__ = "device_reference"
    device = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.Text, nullable=False)
    has_line = db.Column(db.Boolean, default=False)
    has_bar = db.Column(db.Boolean, default=False)
    has_gps = db.Column(db.Boolean, default=False)
    hidden = db.Column(db.Boolean, default=False)
    

class DeviceDefsModel(db.Model):
    __tablename__ = "device_defs"
    id_ = db.Column('id', db.Integer, primary_key=True)
    device = db.Column(db.Integer, db.ForeignKey('device_reference.device'), nullable=False)
    tag = db.Column(db.Text, nullable=False)
    conversion = db.Column(db.Integer, nullable=False)
    args = db.Column(db.Text, nullable=True)
    label = db.Column(db.Text, nullable=False)
    default = db.Column(db.Boolean, default=True) # enabled by default
    unit = db.Column(db.Text, nullable=True)
    type_ = db.Column('type', db.Integer, default=0) # 0 = value, 1 = alarm
    
class DevicesModel(db.Model):
    __tablename__ = "devices"
    id_ = db.Column('id', db.Integer, primary_key=True)
    device = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Integer, nullable=False)
    alias = db.Column(db.Text, nullable=True)
    esp = db.Column(db.Integer, db.ForeignKey('farms.esp'), nullable=False)
    installed = db.Column(db.DateTime, nullable=True)
    info = db.Column(db.Text, nullable=True)
    