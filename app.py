from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

import adjacency_list
import db_operations
import find_path
import layout
import spotify
from config import Config
from data_classes import ArtistHTMLData, SVGLocation, TrackHTMLData
from db import db
from globals import Globals

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_ECHO"] = True
# initialize the app with Flask-SQLAlchemy extension
db.init_app(app)

# make app aware of proxy in front of it (on prod server)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# @app.route("/")
# def index():
#     """Provide index"""
#     return render_template("index.html")


# @app.route("/findpath", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
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
    #     Globals.adj_list, artist_start.id, artist_end.id
    # )

    path_artists = find_path.build_artist_path(
        Globals.adj_list, artist_start.id, artist_end.id
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
    circle_y_position = 100

    square_centres = layout.square_centres(circle_centres)
    square_y_position = circle_y_position - square_size / 2

    square_left_edges = layout.square_left_edges(square_centres, square_size)

    line_positions = layout.line_positions(
        circle_radius, square_size, circle_centres, square_centres
    )

    artist_name_y_position = 100 + circle_radius + 20
    artist_name_x_postions = circle_centres

    track_name_y_position = 100 - circle_radius - 20
    track_name_x_positions = square_centres

    # ---- pack info for html ----
    artist_html_data = []
    for artist, artist_name_x_pos, artist_circle_x_pos, i in zip(
        path_artists,
        artist_name_x_postions,
        circle_centres,
        range(len(path_artists)),
    ):
        artist_html_data.append(
            ArtistHTMLData(
                artist=artist,
                name_pos=SVGLocation(
                    x=artist_name_x_pos,
                    y=artist_name_y_position,
                ),
                circle_pos=SVGLocation(
                    x=artist_circle_x_pos,
                    y=circle_y_position,
                ),
                circle_rad=circle_radius,
                path_index=2 * i,
            )
        )

    track_html_data = []
    for track, track_name_x_pos, track_square_x_pos, i in zip(
        path_tracks,
        track_name_x_positions,
        square_left_edges,
        range(len(path_tracks)),
    ):
        track_html_data.append(
            TrackHTMLData(
                track=track,
                name_pos=SVGLocation(
                    x=track_name_x_pos, y=track_name_y_position
                ),
                square_pos=SVGLocation(
                    x=track_square_x_pos, y=square_y_position
                ),
                square_size=square_size,
                path_index=2 * i + 1,
            )
        )

    return render_template(
        "findpath.html",
        is_found_path=True,
        svg_width=svg_width,
        svg_height=svg_height,
        artist_datas=artist_html_data,
        track_datas=track_html_data,
        line_positions=line_positions,
        spotify_artist_url=Config.SPOTIFY_USER_ARTIST_URL,
        spotify_track_url=Config.SPOTIFY_USER_TRACK_URL,
        line_first_begin=line_positions[0][0],
        line_last_end=line_positions[-1][-1],
    )


@app.route("/api/artist_search", methods=["GET"])
def artist_search():
    query = request.args.get("q")

    return db_operations.fetch_artist_typeahead(query)


with app.app_context():
    # artist = db_operations.get_db_artist_by_name("Ye")

    # tst = db_operations.get_artist_spotify_id(artist)

    Globals.adj_list = adjacency_list.build_adjacency_list(
        Config.ARTISTS_TO_LOAD
    )

    Config.SPOTIFY_ACCESS_TOKEN = spotify.get_spotify_access_token()
    Config.AUTHORISATION_HEADER["Authorization"] = (
        f"Bearer {Config.SPOTIFY_ACCESS_TOKEN}"
    )

    print("Server running!")
