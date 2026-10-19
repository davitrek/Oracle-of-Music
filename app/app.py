import globals
from config import Config
from data import db_operations
from db import db
from flask import Flask, render_template, request
from graph import adjacency_list, find_path
from integrations import spotify
from werkzeug.middleware.proxy_fix import ProxyFix

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI

if Config.IS_TESTING:
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_ECHO"] = True

# initialize the app with Flask-SQLAlchemy extension
db.init_app(app)

# make app aware of proxy in front of it
if not app.config.get("TESTING"):
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/oracle", methods=["GET", "POST"])
def findpath():
    if request.method == "GET":
        return render_template("findpath.html")

    # POST:
    name_start = request.form.get("start")
    name_end = request.form.get("end")

    artist_start = db_operations.get_db_artist_by_name(name_start)
    artist_end = db_operations.get_db_artist_by_name(name_end)

    if not artist_start:
        return render_template(
            "findpath.html",
            error_message="Could not find start artist of that name.",
        )
    if not artist_end:
        return render_template(
            "findpath.html",
            error_message="Could not find end artist of that name.",
        )

    path_artists = find_path.build_artist_path(
        globals.adj_list, artist_start.id, artist_end.id
    )

    if not path_artists:
        return render_template("findpath.html", error_message="No path found.")

    path_tracks = find_path.build_track_path(path_artists)

    return render_template(
        "findpath.html",
        is_found_path=True,
        path_artists=path_artists,
        path_tracks=path_tracks,
        hops=len(path_tracks),
    )


@app.route("/api/artist_search", methods=["GET"])
def artist_search():
    query = request.args.get("q")

    return db_operations.fetch_artist_typeahead(query)


# get artist spotify link and image
@app.route("/api/artist_spotify_info")
def artist_spotify_info():
    mbid = request.args.get("mbid")

    db_artist = db_operations.get_db_artist_by_id(int(mbid))
    if not db_artist:
        print(
            "Musicbrainz database fetch failure: artist not found in MusicBrainz database"
        )
        return {"error": "Artist not found in MusicBrainz database"}

    spotify_artist = find_path.find_spotify_artist(db_artist)

    if not spotify_artist:
        print("Spotify query failure: artist not found on Spotify")
        return {"error": "Artist not found on Spotify"}

    image = spotify.select_best_artist_image(spotify_artist)

    artist_spotify_url = (
        f"{Config.SPOTIFY_USER_ARTIST_URL}/{spotify_artist['id']}"
    )

    return {"image_url": image.url, "artist_url": artist_spotify_url}


# get artist spotify link and image
@app.route("/api/track_spotify_info")
def track_spotify_info():
    mbid = request.args.get("mbid")

    db_track = db_operations.fetch_track_by_id(int(mbid))
    if not db_track:
        print(
            "Musicbrainz database fetch failure: track not found in MusicBrainz database"
        )
        return {"error": "Track not found in MusicBrainz database"}

    spotify_track = spotify.fetch_track(db_track)

    if not spotify_track:
        print("Spotify query failure: track not found on Spotify")
        return {"error": "Track not found on Spotify"}

    image = spotify.select_best_track_image(spotify_track)

    track_spotify_url = f"{Config.SPOTIFY_USER_TRACK_URL}/{spotify_track['id']}"

    return {"image_url": image.url, "track_url": track_spotify_url}


with app.app_context():
    globals.adj_list = adjacency_list.build_adjacency_list(
        Config.ARTISTS_TO_LOAD
    )

    print("Server running!")
