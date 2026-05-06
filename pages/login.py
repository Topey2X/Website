import dash
from dash import html, dcc, Input, Output, State, callback
from auth import verify_password, do_login

def login_layout():
    return html.Div([
        html.H2("Login"),
        dcc.Input(id="username", placeholder="Username", type="text"),
        dcc.Input(id="password", placeholder="Password", type="password"),
        html.Button("Login", id="login-btn", n_clicks=0),
        html.Div(id="login-error", style={"color": "red"}),
        dcc.Location(id="login-redirect"),
    ])
    
@callback(
    Output("login-redirect", "href"),
    Output("login-error", "children"),
    Input("login-btn", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password):
    if verify_password(username, password):
        do_login(username)
        return "/", ""
    return None, "Invalid credentials."