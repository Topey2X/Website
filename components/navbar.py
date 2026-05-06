from dash import html, callback, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask_login import current_user

links = [
    ('Dashboard',   '/'),
    ("Graph",       "/graph"),
    ("Reports",     "/reports"),
    ("Settings",    "/settings"),
]

def navbar():
    return dbc.Navbar(
        dbc.Container([
            # Left zone - links
            dbc.Nav([dbc.NavItem(dbc.NavLink(link[0], href=link[1])) for link in links], navbar=True),
            # Center zone - logo (absolute positioned)
            html.Img(
                src="/assets/FarmTrenz.svg", 
                style={"height": "3em", "position": "absolute", "left": "50%", "transform": "translateX(-50%)"}
            ),
            # Right zone - actions
            html.Div([
                dbc.Button(
                    [html.I(className="bi bi-arrow-clockwise"), " Refresh"],
                    color="secondary",
                    id="refresh-btn",
                    n_clicks=0,
                    className="me-2"
                ),
                dbc.DropdownMenu(
                    [dbc.DropdownMenuItem("Logout", href="/logout")],
                    label=[
                        html.I(className="bi bi-person", style={"fontSize": "1em"}),
                        f' {current_user.display_name}',
                    ],
                    color="primary",
                    align_end=True,
                ),
            ], className="d-flex align-items-center ms-auto"),
        ], fluid=True, className="d-flex align-items-center position-relative"),
        color='#001737',
        dark=True,
        sticky="top",
    )