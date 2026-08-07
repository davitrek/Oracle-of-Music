from collections import defaultdict

from flask import Flask, render_template, request

import adjacency_list
import db_operations
import find_path
import layout
import spotify
from config import Config
from db import db

valid_track_ids = []

adj_list = defaultdict(set)

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_ECHO"] = True
# initialize the app with Flask-SQLAlchemy extension
db.init_app(app)


count = 1000


@app.route("/")
def index():
    """Provide index"""
    return render_template("index.html")


@app.route("/findpath", methods=["GET", "POST"])
def findpath():
    if request.method == "GET":
        return render_template("findpath.html")

    # POST:
    name_start = request.form.get("start")
    name_end = request.form.get("end")

    artist_start = db_operations.get_db_artist_by_name(name_start)
    artist_end = db_operations.get_db_artist_by_name(name_end)

    if not artist_start or not artist_end:
        return render_template(
            "findpath.html", error="Invalid artists start/end artist"
        )

    # ---- find path ----
    # path_artists = find_path.find_artist_link(
    #     adj_list, artist_start.id, artist_end.id
    # )

    path_artists = find_path.build_artist_path(
        adj_list, artist_start.id, artist_end.id
    )

    if not path_artists:
        return render_template("findpath.html", error="No path found :(")

    path_tracks = find_path.build_track_path(path_artists)

    # ---- prepare for displaying webpage ----
    # pad = 0
    svg_width = 1000
    svg_height = 200
    # circle_radius = (svg_width - 2 * pad) / (3 * len(path_artists) - 2)
    circle_radius = 50
    # line_length = 25
    square_size = round(3 / 2 * circle_radius)

    # ---- set shape locations ----
    circle_centres = layout.circle_centres(len(path_artists), svg_width)

    square_centres = layout.square_centres(circle_centres)

    square_left_edges = layout.square_left_edges(square_centres, square_size)

    line_positions = layout.line_positions(
        circle_radius, square_size, circle_centres, square_centres
    )

    artist_name_location = []
    for name, location in zip(path_artists, circle_centres):
        artist_name_location.append((name.name, location))

    recording_name_location = []
    for name, location in zip(path_tracks, square_centres):
        recording_name_location.append((name.name, location))

    artist_shapes = []
    for artist_info, circle_pos, i in zip(
        path_artists, circle_centres, range(len(path_artists))
    ):
        artist_shapes.append((artist_info, circle_pos, i))

    track_shapes = []
    for track_info, square_pos, i in zip(
        path_tracks, square_left_edges, range(len(path_tracks))
    ):
        track_shapes.append((track_info, square_pos, i))

    return render_template(
        "findpath.html",
        svg_width=svg_width,
        svg_height=svg_height,
        circle_radius=circle_radius,
        square_positions=square_left_edges,
        square_size=square_size,
        line_positions=line_positions,
        artist_name_location=artist_name_location,
        recording_name_location=recording_name_location,
        track_shapes=track_shapes,
        artist_shapes=artist_shapes,
        spotify_artist_url=Config.SPOTIFY_USER_ARTIST_URL,
        spotify_track_url=Config.SPOTIFY_USER_TRACK_URL,
    )


with app.app_context():
    # artist = db_operations.get_db_artist_by_name("Ye")

    # tst = db_operations.get_artist_spotify_id(artist)

    adj_list = adjacency_list.build_adjacency_list(count)

    Config.SPOTIFY_ACCESS_TOKEN = spotify.get_spotify_access_token()
    Config.AUTHORISATION_HEADER["Authorization"] = (
        f"Bearer {Config.SPOTIFY_ACCESS_TOKEN}"
    )
