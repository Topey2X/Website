from dash import State, callback_context, html, callback, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask_login import current_user

links = [
    ('Dashboard',   '/'),
    ("Graph",       "/graph"),
    ("Reports",     "/reports"),
    ("Settings",    "/settings"),
]

def navbar():
    return html.Div([
        dbc.Navbar(
            dbc.Container([
                dbc.Button(
                    html.I(className="bi bi-list", style={"fontSize": "1.5em"}),
                    id="drawer-toggle",
                    color="link",
                    className="d-lg-none p-0 text-white",
                    style={"border": "none"}
                ),
                dbc.Nav(
                    [dbc.NavItem(dbc.NavLink(name, href=url)) for name, url in links],
                    navbar=True,
                    className="d-none d-lg-flex"
                ),
                html.Img(
                    src="/assets/FarmTrenz.svg", 
                    style={"height": "3em"},
                    className="position-absolute start-50 translate-middle-x"
                ),
                html.Div([
                    dbc.Button(
                        [html.I(className="bi bi-arrow-clockwise"), html.Span(" Refresh", className="d-none d-lg-inline")],
                        color="secondary",
                        id="refresh-btn",
                        className="me-2"
                    ),
                    dbc.DropdownMenu(
                        [dbc.DropdownMenuItem("Logout", href="/logout")],
                        label=[html.I(className="bi bi-person"), html.Span(f' {current_user.display_name}', className="d-none d-lg-inline")],
                        color="primary",
                        align_end=True,
                        menu_variant="dark",
                    ),
                ], className="d-flex align-items-center ms-auto"),
            ], fluid=True, className="d-flex align-items-center position-relative"),
            color='#001737',
            dark=True,
            sticky="top",
        ),
        html.Div(id="drawer-overlay", n_clicks=0, style={
            "position": "fixed", "top": 0, "left": 0, "width": "100%", "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.5)", "zIndex": 1040, "display": "none",
        }),
        html.Div([
            html.H5("FarmTrenz", className="text-white mb-4 px-3 pt-3"),
            dbc.Nav([dbc.NavItem(dbc.NavLink(name, href=url, className="text-white py-3")) for name, url in links], vertical=True),
            html.Div([
                html.Img(src="/assets/FarmTrenz.svg", style={"height": "3em", "marginBottom": "1rem"}),
                html.P("Contact us", className="text-white-50 mb-1", style={"fontSize": "0.9rem"}),
                html.P("support@farmtrenz.com", className="text-white-50", style={"fontSize": "0.85rem"}),
            ], className="mt-auto text-center px-3 pb-3"),
        ], id="drawer", style={
            "position": "fixed", "top": 0, "left": "-250px", "width": "250px", "height": "100%",
            "backgroundColor": "#001737", "zIndex": 1050, "transition": "left 0.3s ease",
            "display": "flex", "flexDirection": "column",
        }),
    ])

@callback(
    Output("drawer", "style"),
    Output("drawer-overlay", "style"),
    Input("drawer-toggle", "n_clicks"),
    Input("drawer-overlay", "n_clicks"),
    State("drawer", "style"),
    State("drawer-overlay", "style"),
)
def toggle_drawer(toggle_clicks, overlay_clicks, drawer_style, overlay_style):
    ctx_trigger = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None
    
    current_left = drawer_style.get("left", "-250px")
    is_open = current_left == "0px"
    
    if ctx_trigger in ["drawer-toggle", "drawer-overlay"]:
        is_open = not is_open
    
    drawer_style["left"] = "0px" if is_open else "-250px"
    overlay_style["display"] = "block" if is_open else "none"
    
    return drawer_style, overlay_style