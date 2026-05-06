import dash
from dash import html, dcc, Input, Output, State, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc


def markov_bool_sequence(n, p_change=0.1, seed=None):
    rng = np.random.default_rng(seed)
    changes = rng.random(n - 1) < p_change
    first = rng.random() < 0.5
    out = np.empty(n, dtype=bool)
    out[0] = first
    # XOR each element with whether it changed
    np.logical_xor.accumulate(np.concatenate([[first], changes]), out=out)
    return out


def generate_fake_data(start, end) -> tuple[dict, dict]:
    np.random.seed(1)
    fake_data_size_days = (end - start).days
    n = fake_data_size_days * 24 * 6  # 30 days of 10 minutely data
    lines = ("temperature", "pressure", "speed", "flow")
    bools = (
        "Pump",
        "Valve",
        # "Agitator",
        # "Valve 2",
        # "Heater",
        # "Cooler",
        # "Alarm",
        # "Light",
        # "Fan",
        # "Motor",
    )  # Add more bool signals to test scaling

    line_data = {}
    for line in lines:
        # Generate time and values for each line
        # Timestamps should have jitter and be different per line
        timestamps = [
            start
            + timedelta(minutes=i * 10)
            + timedelta(seconds=np.random.randint(-300, 300))
            for i in range(n)
        ]
        values = 20 + np.cumsum(
            np.random.randn(n)
        )  # Just some random walk data for demonstration
        values = np.round(values, 0)  # Round to integer
        line_data[line] = (timestamps, values)

    bool_data = {}
    for j, signal in enumerate(bools):
        timestamps = [
            start
            + timedelta(minutes=i * 10)
            + timedelta(seconds=np.random.randint(-300, 300))
            for i in range(n)
        ]
        values = markov_bool_sequence(
            n, p_change=0.01, seed=j
        )  # Random on/off sequence with some persistence
        bool_data[signal] = (timestamps, values)

    return line_data, bool_data


start = datetime(2024, 1, 1)
end = datetime(2024, 1, 4)
line_data, bool_data = generate_fake_data(start, end)


def build_figure(line_data, bool_data, title="Graph 2", xrange=None):
    second_ratio = 0.035 * (len(bool_data) + 1)
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[1 - second_ratio, second_ratio],
        shared_xaxes=True,
        vertical_spacing=0.03,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
    )

    # --- Lines ---
    for line, (timestamps, values) in line_data.items():
        fig.add_trace(
            go.Scattergl(
                x=timestamps,
                y=values,
                name=line.capitalize(),
                line=dict(width=2),
            ),
            row=1,
            col=1,
        )  # Pressure on secondary Y axis for demonstration

    # --- Bool bars ---
    y_values = [
        (1 / (len(bool_data) * 2)) * ((i * 2) + 1)
        for i in reversed(range(len(bool_data)))
    ]
    for i, (signal, (timestamps, values)) in enumerate(bool_data.items()):
        x, y = [], []
        for j, (t, v) in enumerate(zip(timestamps, values)):
            if v and (j == 0 or not values[j - 1]):
                x += [t, t]
                y += [y_values[i], y_values[i]]
            elif v:
                x.append(t)
                y.append(y_values[i])
            elif not v and j > 0 and values[j - 1]:
                x += [t, None]
                y += [y_values[i], None]

        if values[-1]:
            x += [timestamps[-1], None]
            y += [y_values[i], None]

        fig.add_trace(
            go.Scattergl(
                x=x,
                y=y,
                mode="lines",
                line=dict(width=20),
                name=signal,
                hoverinfo="skip",
            ),
            row=2,
            col=1,
        )

    fig.update_yaxes(fixedrange=True)
    fig.update_yaxes(
        row=2,
        col=1,
        range=[0, 1],
        tickvals=y_values,
        ticktext=[signal for signal, _ in bool_data.items()],
        showgrid=False,
    )
    fig.update_xaxes(showgrid=False, row=2, col=1)

    layout_args = dict(
        title=title,
        autosize=True,
        hovermode="x unified",
        dragmode="pan",
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        margin=dict(l=0, r=0, t=0, b=0),
    )
    if xrange:
        layout_args["xaxis"] = dict(range=xrange)
    fig.update_xaxes(minallowed=start, maxallowed=end)

    fig.update_layout(layout_args)

    return fig


def graph_layout():
    return dbc.Container(
        dbc.Card(
            [
                dbc.CardHeader(html.H3("Test Graph", className="mb-0")),
                dbc.CardBody(
                    dcc.Loading(
                        dcc.Graph(
                            id="graph-main",
                            config={
                                "scrollZoom": True,
                                "displayModeBar": False,
                                "responsive": True,
                            },
                            style={"height": "calc(60vh - 50px)"},
                        ),
                        type="circle",
                    ),
                    className="p-3",
                ),
                dbc.CardFooter("Last updated: just now", className="text-muted"),
            ],
            className="shadow border-dark mt-2 mb-3",
        ),
        className="px-3",  # Adjust px-3 for more/less padding
        fluid=True,
    )


dash.register_page("graph", path="/graph", layout=graph_layout)


@callback(
    Output("graph-main", "figure"),
    Input("graph-main", "id"),  # Fires once on mount
)
def load_figure(_):
    return build_figure(line_data, bool_data, xrange=[start, end])
