import dash
from dash import html, dcc, Input, Output, State, callback
from auth import get_user_settings
from flask_login import current_user
import dash_bootstrap_components as dbc

def device_components() -> dbc.Card:
    """Settings for overriding device components enable / disable

    Returns:
        dbc.Card: Card to be added to the settings page
    """
    ...









def settings_layout():
    return dbc.Container(
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Settings"),
                    dbc.CardBody([
                        html.P("Placeholder content for settings.")
                    ])
                ])
            ], width=6)
        ]), 
        fluid=True
    )

dash.register_page("settings", path="/settings", layout=settings_layout)