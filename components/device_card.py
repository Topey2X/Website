from dash import html
import dash_bootstrap_components as dbc
from datetime import datetime

def age_text(last_updated: datetime | None) -> tuple[str, bool]:
    """Converts a timestamp into a string representation how long ago it was 

    Args:
        last_updated (datetime | None): Timestamp

    Returns:
        tuple[str, bool]: (X minutes ago, [whether the data is considered active])
    """
    if last_updated is None:
        return "Never updated", False
    now = datetime.now(last_updated.tzinfo)
    diff = now - last_updated
    total_seconds = int(diff.total_seconds())
    
    minutes = (total_seconds % 3600) // 60
    if minutes < 1:
        return "Just now", True
    
    hours = (total_seconds % (3600*24)) // 3600
    days = total_seconds // (3600*24)
    
    if days > 365:
        return f"Over {days // 365} year{'s' if days >= (365*2) else ''} ago", False
    if days > 0:
        return f"{days} day{'s' if days >= 2 else ''} ago", False
    if hours > 0:
        return f"{hours} hr{'s' if hours >= 2 else ''},  {minutes} min{'s' if minutes >= 2 else ''} ago", False
    return f"{minutes} min{'s' if minutes >= 2 else ''} ago", total_seconds < (3600/2)

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

def alarm_text(text: str | list | None) -> list:
    if text is None:
        return []
    if isinstance(text, str):
        text = [text]
    return [
        html.Div([
            html.I(className="bi bi-exclamation-triangle me-1 text-danger"),
            html.Span(line, className="text-danger fw-bold")
        ]) for line in text
    ]

def message_text(text: str | list | None) -> list:
    if text is None:
        return []
    if isinstance(text, str):
        text = [text]
    return [html.Div(line, className="fw-bold") for line in text]

def device_card(
        name : str,
        last_updated : datetime | None,
        values : list[tuple[str, str, bool]],
        alarms : list[str],
        messages : list[str],
        alias : str | None = None,
        preText : str | list[str] | None = None,
        postText : str | list[str] | None = None,
        show_gps : bool = False,
        show_bar : bool = False,
        show_line : bool = False,
        show_edit : bool = False
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
    
    message_texts = [html.Hr(), *message_text(messages)] if len(messages) > 0 else []
    alarm_texts = [*alarm_text(alarms), html.Hr()] if len(alarms) > 0 else []
    
    timestamp_text, is_active = age_text(last_updated)

    if alias is not None:
        title = [
            html.H4(alias, className="text-left mb-0", style={"fontSize": "1.6rem"}),
            html.H6(name, className="text-left text-muted fs-6"),
        ]
    else:
        title = [
            html.H4(name, className="text-left", style={"fontSize": "1.6rem"}),
        ]
    
    return dbc.Card([
        dbc.CardHeader([
            dbc.Container([
                dbc.Row([
                    dbc.Col(title, className="pt-2 pb-0", width="auto"),
                    dbc.Col([
                        dbc.Row(action_cols),
                    ], width="auto", className="justify-content-end py-2")
                ], className="align-items-center pe-2", justify="between"),
            ], fluid=True, className="p-0 m-0"),
        ], className="py-0"),
        
        dbc.CardBody([
            *alarm_texts,
            *pre_text(preText),
            *value_text(values),
            *post_text(postText),
            *message_texts,
        ], className="card-text text-wrap"),
        
        dbc.CardFooter(timestamp_text, className="text-muted" if is_active else "text-danger")
    ], className=f"shadow {'border-dark' if is_active else 'border-danger'} mt-0 mb-3", style={"minHeight": "100%"})

# import random
# def device_card_example():
#     return device_card(
#         name="Device 1",
#         last_updated=datetime.now(),
#         preText="This is a device card example.",
#         values=[
#             random.choice([("Temperature", "25°C", False),
#             ("Humidity", "60%", False),
#             ("Online", "Yes", True)]) for _ in range(random.randint(4, 15))
#         ],
#         postText="Last maintenance: 2024-05-15",
#         alarms=[
#             "High temperature detected!",
#             "Low humidity detected!"
#         ],
#         show_bar=True,
#         show_line=True,
#         show_gps=True,
#         show_edit=True
#     )