# noqa: D100
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Output, Input
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from werkzeug.middleware.proxy_fix import ProxyFix

from typing import List

import mongo_read

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

server = app.server
server.wsgi_app = ProxyFix(server.wsgi_app)


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
    print(
        f"Triggering update interval {interval_count}, history-length =", history_length
    )
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    recently_played = mongo_read.read_recently_played(after=after_time)
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
    print(
        f"Triggering update interval {interval_count}, history-length =", history_length
    )
    current_time = datetime.utcnow()
    time_delta = timedelta(days=history_length)
    after_time = current_time - time_delta
    track_ids = mongo_read.read_track_ids(after=after_time)
    return track_ids


@app.callback(
    Output("top-artists", "children"),
    [Input("track-ids", "data")],
)
def update_top_artists(data: List[str]):
    """Updates the top-artists table on the frontend. The table will be
        updated when either Input object is modified.

    Args:
        data (List[str]): list of track ids

    Returns:
        List[dash objects]: a single dash table
    """
    top_artists = mongo_read.read_top_artists(data)
    return [create_dash_table(top_artists)]


@app.callback(
    Output("top-genres", "children"),
    [Input("track-ids", "data")],
)
def update_top_genres(data: List[str]):
    """Updates the top-genres table on the frontend. The table will be
        updated when either Input object is modified.

    Args:
        data (List[str]): list of track ids

    Returns:
        List[dash objects]: a single dash table
    """
    top_genres = mongo_read.read_top_genres(data)
    return [create_dash_table(top_genres)]


@app.callback(
    Output("pie-charts", "children"),
    [Input("track-ids", "data")],
)
def update_pies(data: List[str]):
    """Updates the energy and popularity pies on the frontend. The table will
        be updated when either Input object is modified.

    Args:
        data (List[str]): list of track ids

    Returns:
        List[dash objects]: a single dash table
    """
    energy_score = mongo_read.read_energy_score(data)
    popularity_score = mongo_read.read_popularity(data)
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
    print("Updating history-length to", value)
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
    print("Updating history-length to", value)
    return f"Viewing the last {value} day(s)!"


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
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.P("Recently played tracks !", className='card-header'),
                                html.Div(
                                    id="recently-listened",
                                    className='card-body'
                                ),
                            ],
                            className="col-12 card",
                        ),
                    ],
                    className="row",
                ),
                html.Div(
                    children=[
                        html.Div(
                            id="pie-charts",
                            className="col-12 card",
                        ),
                    ],
                    className="row",
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.P("Top Artists !", className='card-header'),
                                html.Div(
                                    id="top-artists",
                                    className='card-body'
                                ),
                            ],
                            className="col-5 card",
                        ),
                        html.Div(
                            children=[
                                html.P("Top Genres !", className='card-header'),
                                html.Div(
                                    id="top-genres",
                                    className='card-body'
                                ),
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
