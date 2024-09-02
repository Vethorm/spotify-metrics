# noqa: D100
import logging

from dash import Dash, dcc, html
from werkzeug.middleware.proxy_fix import ProxyFix


from . import callbacks  # noqa: F401

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
                            id='time-selector',
                            children=[
                                html.P(
                                    id="view-window",
                                    className="content-header",
                                ),
                                dcc.RadioItems(
                                    options=[7, 14, 30],
                                    value=7,
                                    inline=True,
                                    id="time-dropdown",
                                    inputStyle={'padding-right' : '5px'},
                                    labelStyle={'padding-right' : '5px'},
                                ),
                            ],
                            className="card",
                        )
                    ],
                    className="flex-row",
                ),
                html.Div(
                    id="charts",
                    children=[
                        # listen/popularity
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        html.P(
                                            "Listen time !", className="card-header"
                                        ),
                                        html.Div(
                                            id="listen-time-container",
                                            className="card-body",
                                        ),
                                    ],
                                    className="card col-6 flex-column bar-chart",
                                ),
                                html.Div(
                                    children=[
                                        html.P(
                                            "Average song popularity by day !",
                                            className="card-header",
                                        ),
                                        html.Div(
                                            id="popularity-container",
                                            className="card-body",
                                        ),
                                    ],
                                    className="card col-6 flex-column bar-chart",
                                ),
                            ],
                            className="flex-row",
                        ),
                        # energy/danceability
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        html.P(
                                            "Average song energy by day !",
                                            className="card-header",
                                        ),
                                        html.Div(
                                            id="energy-container", className="card-body"
                                        ),
                                    ],
                                    className="card col-6 flex-column bar-chart",
                                ),
                                html.Div(
                                    children=[
                                        html.P(
                                            "Average song danceability by day !",
                                            className="card-header",
                                        ),
                                        html.Div(
                                            id="danceability-container",
                                            className="card-body",
                                        ),
                                    ],
                                    className="card col-6 flex-column bar-chart",
                                ),
                            ],
                            className="flex-row",
                        ),
                    ],
                ),
                html.Div(
                    id="top-lists",
                    children=[
                        # Top artist/genre
                        html.Div(
                            children=[
                                html.Div(
                                    id="top-artists-card",
                                    children=[
                                        html.P(
                                            "Top Artists !", className="card-header"
                                        ),
                                        html.Div(
                                            id="top-artists", className="card-body"
                                        ),
                                    ],
                                    className="card col-6 flex-column",
                                ),
                                html.Div(
                                    id="top-genres-card",
                                    children=[
                                        html.P("Top Genres !", className="card-header"),
                                        html.Div(
                                            id="top-genres", className="card-body"
                                        ),
                                    ],
                                    className="card col-6 flex-column",
                                ),
                            ],
                            className="flex-row",
                        ),
                    ],
                ),
            ],
            className="wrapper",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0")
