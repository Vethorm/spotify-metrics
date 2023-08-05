# noqa: D100
import logging
import os
from datetime import datetime, timedelta
from typing import List

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import plotly.express as px
from werkzeug.middleware.proxy_fix import ProxyFix

from . import database

external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?" "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
    {
        "href": (
            "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
        ),
        "rel": "stylesheet",
    },
]

app = Dash(__name__, external_stylesheets=external_stylesheets)

# implemented from here
# https://trstringer.com/logging-flask-gunicorn-the-manageable-way/
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

logger = app.logger


server = app.server
server.wsgi_app = ProxyFix(server.wsgi_app)

spotify_db = database.SpotifyMetricsDB()


def create_dash_table(dataframe: pd.DataFrame) -> dash_table.DataTable:
    """Create dash tables for our frontend

    Args:
        dataframe (DataFrame): the dataframe we are transforming into a table

    Returns:
        DataTable: a dash DataTable
    """
    return dash_table.DataTable(
        dataframe.to_dict("records"),
        [{"name": i, "id": i} for i in dataframe.columns],
        style_cell={
            "text-align": "left",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "maxWidth": 0,
            "font-family": "Lato",
        },
        style_cell_conditional=[
            {"if": {"column_id": "Time played"}, "width": "20%"},
            {"if": {"column_id": "Track"}, "width": "40%"},
            {"if": {"column_id": "Artist(s)"}, "width": "40%"},
        ],
        style_table={"margin-top": 10, "margin-bottom": 10},
    )


def create_pie(title: str, labels: List[str], values: List[int]):
    """Creates a pie graph for our frontend

    Args:
        title (str): the title of the graph
        labels (List[str]): the labels for the graph
        values (List[str]): the values for the graph

    Returns
        Pie: a dash Pie graph
    """
    return go.Pie(
        title=title,
        labels=labels,
        values=values,
        hole=0.65,
        textinfo="none",
        marker_colors=["rgb(30, 215, 96)", "rgba(147,112,219,0.1)"],
        name="Energy",
        direction="clockwise",
        sort=False,
        showlegend=False,
    )


@app.callback(
    Output("recently-listened", "children"),
    [Input("interval-component", "n_intervals"), Input("history-length", "data")],
)
def update_recently_played(interval_count: int, history_length: int):
    """Updates the recently-listened table on the frontend. The table will be
        updated when either Input object is modified.

    Args:
        interval_count (int): the current interval count
        history_length (int): the amount of days we are going back in listen history

    Returns:
        List[dash objects]: a single dash table
    """
    logger.info(
        f"Triggering update interval {interval_count}, "
        f"history-length = {history_length} for recently played"
    )
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    recently_played = spotify_db.read_recently_played(after=after_time)
    logger.info(f"Loading {len(recently_played)} recently played tracks")
    return [create_dash_table(recently_played)]


@app.callback(
    Output("track-ids", "data"),
    [Input("interval-component", "n_intervals"), Input("history-length", "data")],
)
def update_track_list(interval_count: int, history_length: int) -> List[str]:
    """Updates the track-ids Storage on the frontend

    Args:
        interval_count (int): the current interval count
        history_length (int): the amount of days we are going back in listen history

    Returns:
        List[str]: the list of track ids for the current history length
    """
    logger.info(
        f"Triggering update interval {interval_count}, "
        f"history-length = {history_length} for track ids"
    )
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    track_ids = spotify_db.read_track_ids(after=after_time)
    logger.info(f"Updating track ids with {len(track_ids)} id(s)")
    return track_ids


@app.callback(
    Output("top-artists", "children"),
    [Input("interval-component", "n_intervals"), Input("history-length", "data")],
)
def update_top_artists(interval_count: int, history_length: int):
    """Updates the top-artists table on the frontend. The table will be
        updated when either Input object is modified.

    Args:
        data (List[str]): list of track ids

    Returns:
        List[dash objects]: a single dash table
    """
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    top_artists = spotify_db.read_top_artists(after_time)
    return [create_dash_table(top_artists)]


@app.callback(
    Output("top-genres", "children"),
    [Input("interval-component", "n_intervals"), Input("history-length", "data")],
)
def update_top_genres(interval_count: int, history_length: int):
    """Updates the top-genres table on the frontend. The table will be
        updated when either Input object is modified.

    Args:
        data (List[str]): list of track ids

    Returns:
        List[dash objects]: a single dash table
    """
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    top_genres = spotify_db.read_top_genres(after_time)
    return [create_dash_table(top_genres)]


@app.callback(
    Output("pie-charts", "children"),
    [Input("interval-component", "n_intervals"), Input("history-length", "data")],
)
def update_pies(interval_count: int, history_length: int):
    """Updates the energy and popularity pies on the frontend. The table will
        be updated when either Input object is modified.

    Args:
        data (List[str]): list of track ids

    Returns:
        List[dash objects]: a single dash table
    """
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    energy_score = spotify_db.read_energy_score(after_time)
    popularity_score = spotify_db.read_popularity(after_time)
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])
    fig.add_trace(
        create_pie(
            f"Popularity</br></br>{int(popularity_score)}",
            ["popularity", "empty"],
            [popularity_score, 100 - popularity_score],
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        create_pie(
            f"Energy</br></br>{int(energy_score)}",
            ["energy", "empty"],
            [energy_score, 100 - energy_score],
        ),
        row=1,
        col=2,
    )
    fig.update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20})
    return [dcc.Graph(id="pies", figure=fig, className="pies")]


@app.callback(Output("history-length", "data"), Input("time-slider", "value"))
def update_history_length(value: int) -> int:
    """Updates the history length value stored on the frontend when the
        time-slider changes

    Args:
        value (int): the current history length in days

    Returns:
        int: the history length in days to store
    """
    logger.info(f"Updating history-length to {value}")
    return value


@app.callback(Output("view-window", "children"), Input("time-slider", "value"))
def update_view_window(value: int) -> str:
    """Updates the text about history length on the frontend when the
        time-slider changes

    Args:
        value (int): the current history length in days

    Returns:
        str: the text about history length in days
    """
    logger.info(f"Updating history-length to {value}")
    return f"Viewing the last {value} day(s)!"


@app.callback(
    Output("listen-time-container", "children"),
    [Input("interval-component", "n_intervals"), Input("history-length", "data")],
)
def update_listen_time(interval: int, history_length: int) -> dcc.Graph:
    current_date = datetime.utcnow().date()
    time_delta = timedelta(days=history_length - 1)
    start_date = current_date - time_delta
    df = spotify_db.read_listen_time_aggregation(start=start_date, end=current_date)

    fig = px.bar(df, x="date", y="listen_time", labels={"date": "", "listen_time": ""})

    graph = dcc.Graph(figure=fig)

    return graph


app.layout = html.Div(
    [
        dcc.Store(id="history-length", data=1),
        dcc.Store(id="track-ids"),
        dcc.Interval(id="interval-component", interval=1000 * 120, n_intervals=0),
        html.Div(
            children=[
                html.H1(
                    children="My Spotify Recently Played Metrics !",
                    className="header-title",
                ),
                html.P(
                    children=("See what I've been listening to !"),
                    className="header-description",
                ),
                html.P(
                    children=(
                        "Disclaimer: I might not have been listening to music recently !"  # noqa: E501
                    ),
                    className="header-disclaimer",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                # Time slider
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.P(
                                    id="view-window",
                                    className="content-header",
                                ),
                                dcc.Slider(
                                    1, 7, 1, value=1, marks=None, id="time-slider"
                                ),
                            ],
                            className="day-slider col-11 card",
                        )
                    ],
                    className="row",
                ),
                # Recently played
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.P(
                                    "Recently played tracks !", className="card-header"
                                ),
                                html.Div(id="recently-listened", className="card-body"),
                            ],
                            className="col-12 card",
                        ),
                    ],
                    className="row",
                ),
                # Listen time
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.P("Listen time !", className="card-header"),
                                html.Div(
                                    id="listen-time-container", className="card-body"
                                ),
                            ],
                            className="col-12 card",
                        )
                    ],
                    className="row",
                ),
                # Pie charts for popularity/energy
                html.Div(
                    children=[
                        html.Div(
                            id="pie-charts",
                            className="col-12 card",
                        ),
                    ],
                    className="row",
                ),
                # Top artist/genre
                html.Div(
                    children=[
                        html.Div(
                            id="top-artists-card",
                            children=[
                                html.P("Top Artists !", className="card-header"),
                                html.Div(id="top-artists", className="card-body"),
                            ],
                            className="col-5 card",
                        ),
                        html.Div(
                            id="top-genres-card",
                            children=[
                                html.P("Top Genres !", className="card-header"),
                                html.Div(id="top-genres", className="card-body"),
                            ],
                            className="col-5 card",
                        ),
                    ],
                    className="row",
                ),
            ],
            className="wrapper",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0")
