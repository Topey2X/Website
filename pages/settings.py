import json

import dash
from dash import MATCH, ctx, html, dcc, Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate
from auth import get_user_settings
from flask_login import current_user
import dash_bootstrap_components as dbc
from server import db
from models import DevicesModel, DeviceReferenceModel
import random

def get_all_components() -> dict:
    # Returns a dictionary:
    # {
    #     "device_name": (
    #         device_id,
    #         {
    #             "component_name": (enabled, override), # Where override is whether the settings have altered from the default
    esp = current_user.esp    
    selection = db.select(DevicesModel) \
    .where(DevicesModel.esp == esp) \
    .options(db.joinedload(DevicesModel.device_ref)) # eager load device_ref relationship
    devices = db.session.execute(selection).scalars().all()
    
    result = {}
    # devices holds all DeviceModel entries with the ReferenceModel attached.
    for device in devices:
        # We want two things from these: The tags (which contains default settings) and the overrides in the user settings.
        default_tags = device.device_ref.get_tag_defs()        
        device_name = device.device_ref.name
        device_code = device.code
        device_friendly_name = device.alias if device.alias else f"{device_name} {device_code}"
        overrides = device.get_all_tags() # Overrides specific to this device, keyed by tag name. This allows per-device overrides instead of just global ones.
        
        device_settings = {}
        # We need to go through the default tags and then apply overrides if available.
        for tag in default_tags:
            tag_name = tag.get("IniRef", None);
            default = tag.get("Default", True) # Default to enabled if not specified
            if not tag_name:
                continue # Skip tags without an IniRef, as we have no way to identify them
            override = overrides.get(tag_name, None)
            enabled = override if override is not None else default
            override_flag = override is not None
            device_settings[tag_name] = (enabled, override_flag)
    
        result[device_friendly_name] = (device.id_, device_settings)        
        
    return result

def device_components():
    components = get_all_components()

    def create_categories(device_name, device_id, tags):
        rows = []
        for tag_name, (enabled, override) in tags.items():
            rows.append(
                dbc.Row([
                    dbc.Col(dbc.Checkbox(
                        id={"type": "tag-checkbox", "device_id": device_id, "tag_name": tag_name},
                        value=enabled,
                    ), width="auto"),
                    dbc.Col(html.Span(
                        tag_name,
                        id = {"type": "tag-label", "device_id": device_id, "tag_name": tag_name},
                        className="fw-bold" if override else ""),
                        width="auto"
                    ),
                    dbc.Col(dbc.Button(
                        html.I(className="bi bi-arrow-counterclockwise"),
                        id={"type": "tag-reset-btn", "device_id": device_id, "tag_name": tag_name},
                        size="sm", color="#000000",
                        style={"visibility": "visible" if override else "hidden"}
                    ), width="auto"),
                ], align="center", className="gy-3 gx-0 justify-content-start")
            )
        return rows

    return [
        dbc.Col([
            html.H2(device_name, className="fs-4"),
            *create_categories(device_name, device_id, tags)
        ]) for device_name, (device_id, tags) in components.items()
    ]


def settings_layout():
    return dbc.Container(
        [
            html.H1("Settings", className="mb-3 fs-3"),
            dbc.Col([
                dbc.Row(device_components()),
            ]),
        ], 
        fluid=True,
        style={"backgroundColor": "#ffffff", "minHeight": "100vh"},
        className="p-3"
    )

dash.register_page("settings", path="/settings", layout=settings_layout)

@callback(
    Output({"type": "tag-reset-btn", "device_id": MATCH, "tag_name": MATCH}, "style"),
    Output({"type": "tag-label", "device_id": MATCH, "tag_name": MATCH}, "className"),
    Output({"type": "tag-checkbox", "device_id": MATCH, "tag_name": MATCH}, "value"),
    Input({"type": "tag-checkbox", "device_id": MATCH, "tag_name": MATCH}, "value"),
    Input({"type": "tag-reset-btn", "device_id": MATCH, "tag_name": MATCH}, "n_clicks"),
    State({"type": "tag-checkbox", "device_id": MATCH, "tag_name": MATCH}, "id"),
    prevent_initial_call=True
)
def update_component(checkbox_value, _, id):
    device_id = id["device_id"]
    tag_name = id["tag_name"]

    device = db.session.get(DevicesModel, device_id)
    if not device:
        return {"visibility": "hidden"}, "", no_update

    if ctx.triggered_id and ctx.triggered_id["type"] == "tag-reset-btn":
        checkbox_value = device.reset_tag_override(tag_name)
        db.session.commit()
        return {"visibility": "hidden"}, "", checkbox_value

    device.set_tag_override(tag_name, checkbox_value)
    db.session.commit()
    return {"visibility": "visible"}, "fw-bold", no_update