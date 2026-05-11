import dash
from dash import html
from flask import session
from server import db

def reports_layout():
    # Placeholder coming soon text
    return html.Div([
        html.H1("Reports (Coming Soon)", className="text-center text-light mt-5")
    ])

dash.register_page("reports", path="/reports", layout=reports_layout)