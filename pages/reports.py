import dash
from dash import html
from flask import session
from server import db

def reports_layout():
    number = session.get("saved_number", "No number saved yet.")
    return html.Div([
        html.H3("Reports"),
        html.P(f"Number from session: {number}"),
    ])

dash.register_page("reports", path="/reports", layout=reports_layout)