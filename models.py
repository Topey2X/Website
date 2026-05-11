from server import db
from datetime import datetime, timezone
import json
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_model):
        self.id = user_model.username
        self.display_name = user_model.display_name
        self.esp = user_model.esp
        self.site_address = user_model.site_address
        
        # Calculated fields
        self.farm_path = f"farmtrenz/ESP_{self.esp:05d}"
        self.tagdb_path = f"{self.farm_path}/SiteAdd_{self.site_address:02x}h_{self.site_address:02d}/TagDB"
        

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
    name = db.Column(db.Text, nullable=False)
    tag_name = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.Text, nullable=False)
    has_line = db.Column(db.Boolean, default=False)
    has_bar = db.Column(db.Boolean, default=False)
    has_gps = db.Column(db.Boolean, default=False)
    hidden = db.Column(db.Boolean, default=False)
    tag_defs = db.Column(db.Text, nullable=True)  # JSON blob of list of dicts
    
    def get_tag_defs(self):
        return json.loads(self.tag_defs or "[]")
    
class DevicesModel(db.Model):
    __tablename__ = "devices"
    id_ = db.Column('id', db.Integer, primary_key=True)
    device = db.Column(db.Integer, db.ForeignKey('device_reference.device'), nullable=False)
    code = db.Column(db.Integer, nullable=False)
    alias = db.Column(db.Text, nullable=True)
    esp = db.Column(db.Integer, db.ForeignKey('farms.esp'), nullable=False)
    installed = db.Column(db.DateTime, nullable=True)
    info = db.Column(db.Text, nullable=True)
    settings = db.Column(db.Text, nullable=True) # JSON blob for user overrides of component settings
    
    device_ref = db.relationship("DeviceReferenceModel")
    
    def get_tag_states(self) -> dict:
        return json.loads(self.settings or "{}").get("device_overrides", {})
    
    def set_tag_state(self, tag_name, state) -> None:
        data = json.loads(self.settings or "{}")
        data.setdefault("device_overrides", {})  # ensures the key exists
        data["device_overrides"][tag_name] = state
        self.settings = json.dumps(data)
    
    def reset_tag_state(self, tag_name) -> bool:
        data = json.loads(self.settings or "{}")
        if "device_overrides" in data and tag_name in data["device_overrides"]:
            del data["device_overrides"][tag_name]
            self.settings = json.dumps(data)
        # Need to return the original state so we can update the UI accordingly
        default_tags = self.device_ref.get_tag_defs()
        for tag in default_tags:
            if tag.get("IniRef", None) == tag_name:
                return tag.get("Default", True) # Default to enabled if not specified
        return True # If we can't find the tag definition, default to enabled (this shouldn't happen)
        