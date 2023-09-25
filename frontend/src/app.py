# noqa: D100
import logging

from dash import Dash, dcc, html
from werkzeug.middleware.proxy_fix import ProxyFix


from . import callbacks # noqa: F401

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
