from . import database

from typing import List

import pandas as pd

from dash import dash_table, Input, Output, dcc, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


from datetime import datetime, timedelta

import logging

logger = logging.getLogger("callbacks")


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


@callback(
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


@callback(
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


@callback(
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


@callback(
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


@callback(
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


@callback(Output("history-length", "data"), Input("time-slider", "value"))
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


@callback(Output("view-window", "children"), Input("time-slider", "value"))
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


@callback(
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
