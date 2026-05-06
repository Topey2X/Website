import dash
from dash import html, dcc, Input, Output, State, callback
from flask import session
from server import db
from auth import get_user_settings
from flask_login import current_user
import json
from models import UserModel

def settings_layout():
    user_settings = get_user_settings(current_user.id) if current_user.is_authenticated else {}
    return html.Div([
        html.H3("Settings"),
        html.P(id="settings-display"),
        dcc.Input(id="theme-input", placeholder="e.g. dark"),
        html.Button("Save setting", id="save-setting-btn", n_clicks=0),
        html.Div(id="setting-confirmation"),
    ])

dash.register_page("settings", path="/settings", layout=settings_layout)

@callback(
    Output("setting-confirmation", "children"),
    Output("settings-display", "children"),
    Input("save-setting-btn", "n_clicks"),
    Input("url", "pathname"),
    State("theme-input", "value"),
    prevent_initial_call=False,
)
def settings_callback(n_clicks, pathname, value):
    u = db.session.get(UserModel, current_user.id)
    if not u:
        return "User not found.", ""
    settings_text = f"Stored settings: {json.dumps(json.loads(u.settings))}"
    
    if dash.ctx.triggered_id == "save-setting-btn":
        u.set_setting("theme", value)
        db.session.commit()
        return f"Saved theme: {value}", settings_text

    return "", settings_text
