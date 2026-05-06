import random

import dash
from dash import html, dcc, Input, Output, State, callback
from flask import session
from flask_login import current_user
from server import db
import dash_bootstrap_components as dbc
from components.device_card import device_card_example, device_card
from models import DevicesModel, UserModel

def dashboard_layout():
    # Query database for relevent devices
    esp = db.session.execute(db.select(UserModel.esp).where(UserModel.username == current_user.id)).scalar_one_or_none()
    if esp is None:
        return html.Div("Error: User not found.") # TODO: error handling
    selection = db.select(DevicesModel) \
        .where(DevicesModel.esp == esp) \
        .options(db.joinedload(DevicesModel.device)) # eager load device_ref relationship
        
    devices = db.session.execute(selection).scalars().all()
    if not devices or len(devices) == 0:
        return html.Div("Error: No devices found for this user.") # TODO: error handling
    
    cards = []
    for device in devices:
        device_card(
            name=f"{device.name} {device.id}", # TODO: Alias
            last_updated="2024-06-01T12:00:00Z", # TODO: device.last_updated
            values=[ # TODO: lookup values
            random.choice([("Temperature", "25°C", False),
                ("Humidity", "60%", False),
                ("Online", "Yes", True)]) for _ in range(random.randint(4, 15))
            ],
            alarms=[ # TODO: lookup alarms
                "High temperature detected!",
                "Low humidity detected!"
            ],
            show_bar=device.has_bar,
            show_line=device.has_line,
            show_gps=device.has_gps,
            # show_edit=True
        )

    return dbc.Container(dbc.Row([
        dbc.Col(card) for card in cards
    ]), fluid=True, className="pb-2")
    
dash.register_page("dashboard", path="/", layout=dashboard_layout)