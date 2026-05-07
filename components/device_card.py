from dash import html
import dash_bootstrap_components as dbc

def pre_text(text: str | list | None):
    if text is None:
        return []
    if isinstance(text, str):
        text = [text]
    return [html.Div(line) for line in text]

def value_text(values : list[tuple[str, str, bool]] | tuple[str, str, bool] | None):
    if values is None:
        return []
    if isinstance(values, tuple):
        values = [values]    
    return [
        html.Div([
            f"{name}: ", html.Span(
                value, className = "text-primary fw-bold" if not is_bool 
                else "text-primary fw-bold border border-dark rounded px-1 text-uppercase"
            )
        ]) for name, value, is_bool in values
    ]
    
def post_text(text: str | list | None):
    if text is None:
        return []
    if isinstance(text, str):
        text = [text]
    return [html.Div(line) for line in text]

def alarm_text(text: str | list | None):
    if text is None:
        return []
    if isinstance(text, str):
        text = [text]
    return [html.Div(line, className="text-danger fw-bold") for line in text]

def device_card(
        name,
        last_updated,
        values : list[tuple[str, str, bool]],
        alarms : list[str],
        alias=None,
        preText=None,
        postText=None,
        show_gps=False,
        show_bar=False,
        show_line=False,
        show_edit=False
    ):
    actions : list[tuple[str, str, str]] = []
    if show_gps:
        actions.append(("GPS Plot", "bi bi-geo-alt", "#"))
    if show_bar:
        actions.append(("Bar Chart", "bi bi-bar-chart-line", "#"))
    if show_line:
        actions.append(("Line Chart", "bi bi-graph-up-arrow", "#"))
    if show_edit:
        ...
        # actions.append(("Notes", "bi bi-pencil-square", "#")) # TODO: Implement notes (popup?)
        
                 # dcc.Link(html.I(className="bi bi-geo-alt"), href=f"/gps?device={name}"),
    # Convert to colmns with auto width and some spacing             
    action_cols = [
        dbc.Col(
            dbc.Button(
                [
                    html.I(className=icon),
                    html.Span(label),
                ],
                href=href,
                color="primary",
                outline=True,
                className="d-flex align-items-center gap-1",
            ),
            width="auto",
            className="px-1",
        )
        for label, icon, href in actions
    ]
    
    alarm_texts = [html.Hr(), *alarm_text(alarms)] if len(alarms) > 0 else []
    
    return dbc.Card([
        dbc.CardHeader([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        html.H3(name, className="text-center fs-4"),
                        className="pt-2",
                        width="auto"
                    ),
                    dbc.Col([
                        dbc.Row(action_cols),
                    ],  className="ms-auto", width="auto")
                ], className="align-items-center", justify="between"),
            ], fluid=True, className="pl-2 pr-5"),
        ], className="px-2 py-9"),
        
        dbc.CardBody([
            *pre_text(preText),
            *value_text(values),
            *post_text(postText),
            *alarm_texts,
        ], className="card-text text-wrap"),
        
        dbc.CardFooter("2 hrs, 3 mins, 15 secs ago", className="text-muted") # TODO: last_updated calculation
    ], className="shadow border-dark mt-0 mb-3")

import random
def device_card_example():
    return device_card(
        name="Device 1",
        last_updated="2024-06-01T12:00:00Z",
        preText="This is a device card example.",
        values=[
            random.choice([("Temperature", "25°C", False),
            ("Humidity", "60%", False),
            ("Online", "Yes", True)]) for _ in range(random.randint(4, 15))
        ],
        postText="Last maintenance: 2024-05-15",
        alarms=[
            "High temperature detected!",
            "Low humidity detected!"
        ],
        show_bar=True,
        show_line=True,
        show_gps=True,
        show_edit=True
    )