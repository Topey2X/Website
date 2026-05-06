from dash import Dash, dcc, Input, Output, page_container
from flask_login import current_user, logout_user
from server import create_server, db
from components.navbar import navbar
import dash_bootstrap_components as dbc
from auth import do_logout

server = create_server()

app = Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    use_pages=True,
    pages_folder="pages",
    suppress_callback_exceptions=True,
)

# Import pages after app is created so register_page() has an app instance
from pages.login import login_layout
import importlib, os

for f in os.listdir("pages"):
    if f.endswith(".py") and not f.startswith("_"):
        importlib.import_module(f"pages.{f[:-3]}")

app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        dbc.Container(
            id="page-content", fluid=True, className="p-0"
        ),
    ],
    fluid=True,
    className="py-0 px-3",
    style={"backgroundColor": "#001737", "minHeight": "100vh"},
)


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def route(pathname):
    if pathname == "/logout":
        do_logout()
        return dcc.Location(href="/login", id="redirect-login")

    if pathname == "/login":
        return login_layout()

    if not current_user.is_authenticated:
        return dcc.Location(href="/login", id="force-login")

    return dbc.Container(
        [
            navbar(),
            page_container,
        ],
        fluid=True,
        className="p-0",
        style={
            "minHeight": "100vh",
        },
    )


if __name__ == "__main__":
    with server.app_context():
        db.create_all()
    app.run(debug=True)
