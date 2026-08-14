from os import environ

from dotenv import load_dotenv

load_dotenv()


class Config:
    ARTISTS_TO_LOAD = 1000

    SQLALCHEMY_DATABASE_URI = environ["DATABASE_URL"]

    SPOTIFY_API_TOKEN_REQUEST_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_CLIENT_ID = environ["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = environ["SPOTIFY_CLIENT_SECRET"]

    # spotify API urls
    SPOTIFY_URL = "https://api.spotify.com/v1"
    SPOTIFY_SEARCH_URL = SPOTIFY_URL + "/search"
    SPOTIFY_ARTISTS_URL = SPOTIFY_URL + "/artists"
    SPOTIFY_ALBUMS_URL = SPOTIFY_URL + "/albums"
    SPOTIFY_TRACKS_URL = SPOTIFY_URL + "/tracks"

    # spotify client urls (i.e., accessible with browser)
    SPOTIFY_USER_URL = "https://open.spotify.com"
    SPOTIFY_USER_ARTIST_URL = SPOTIFY_USER_URL + "/artist"
    SPOTIFY_USER_TRACK_URL = SPOTIFY_USER_URL + "/track"

    # local path to artist names that should be included in algorithms
    ARTIST_NAMES_FILE_PATH = environ["ARTIST_NAMES_FILE_PATH"]

    # minimum recordings
    MIN_RECORDINGS_COUNT = 10

    # preferred square image size (320 -> 320px x 320px)
    IDEAL_IMAGE_SIZE = 320

    # max suggestions to provide in typeahead
    TYPEAHEAD_LIMIT = 10

    IS_TESTING = environ.get("IS_TESTING")

    # Track filtering:
    VALID_RELEASE_PRIMARY_TYPES = ("Album", "Single", "EP")
    VALID_RELEASE_SECONDARY_TYPES = ("Soundtrack", "Mixtape/Street", "Demo")
    OFFICIAL_STATUS = "Official"
    EXCLUDED_JOIN_PHRASES_LIKE = "vs"
