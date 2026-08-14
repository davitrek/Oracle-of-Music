import re
from time import sleep, time

import requests
from rapidfuzz import fuzz, utils

import db_operations
import exceptions
import helpers
from config import Config
from data_classes import WebImage


# gets new Spotify access token
def get_spotify_access_token(max_retries: int = 5) -> None:
    print("Getting spotify access token.")

    url = Config.SPOTIFY_API_TOKEN_REQUEST_URL
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "grant_type": "client_credentials",
        "client_id": str(Config.SPOTIFY_CLIENT_ID),
        "client_secret": str(Config.SPOTIFY_CLIENT_SECRET),
    }

    for _ in range(max_retries):
        r = requests.post(url, headers=headers, data=params)

        try:
            r.raise_for_status()
            break
        except requests.HTTPError as e:
            print(
                "Error in trying to get Spotify access token:",
                e.errno,
                ":",
                e.response,
            )

            sleep(0.2)  # avoid re-requesting immediately
    else:
        print("Failed to get spotify access token!")
        raise exceptions.SpotifyTokenError(
            "Failed to get spotify access token!"
        )

    try:
        r = r.json()
        Config.SPOTIFY_ACCESS_TOKEN = r["access_token"]
        Config.SPOTIFY_ACCESS_TOKEN_EXPIRY_TIME = time() + r["expires_in"]
        Config.AUTHORISATION_HEADER["Authorization"] = (
            f"Bearer {Config.SPOTIFY_ACCESS_TOKEN}"
        )
    except KeyError:
        raise exceptions.SpotifyTokenError(
            "Failed to get spotify access token!"
        )


class ForTesting:
    qs = {}  # noqa: RUF012


def log_spotify_query(url: str, params: dict) -> None:
    s = "Querying Spotify: " + url
    if params:
        for k, v in params.items():
            s = s + ", " + str(k) + ": " + str(v)

    log_url = url
    if params:
        log_url = (
            log_url + str(params.get("q", "")) + str(params.get("offset", ""))
        )

    if ForTesting.qs.get(log_url, ""):
        print("Querying Spotify: Re-querying same url!")
    else:
        ForTesting.qs[url] = 1

    print(s)


# returns dictionary of search response from Spotify
# returns None on error
def search_spotify(
    url: str, params: dict | None = None, max_retries: int = 5
) -> dict:
    # if previous token expired (or is about to), get new one
    if time() > Config.SPOTIFY_ACCESS_TOKEN_EXPIRY_TIME - 60:
        get_spotify_access_token()

    for attempt in range(max_retries):
        log_spotify_query(url, params)

        r = requests.get(
            url, params=params, headers=Config.AUTHORISATION_HEADER
        )

        try:
            r.raise_for_status()
        except requests.HTTPError:
            # rate limited, call function again after delay
            if r.status_code == 429:
                retry_after_sec = int(r.headers["retry-after"])

                if not retry_after_sec:
                    retry_after_sec = (
                        2**attempt
                    )  # exponential backoff as backup

                if retry_after_sec > 60:
                    print(
                        "Query Spotify: Long delay before next attempt",
                        f"({retry_after_sec}s)",
                    )

                sleep(retry_after_sec)
                continue

            else:
                print(r.status_code, ": ", r.reason)
                return None

        sleep(0.2)  # wait per request to avoid rate-limiting

        response = r.json()

        return response


# returns a dictionary representing a Spotify Track JSON object
def fetch_track(track):
    artists = db_operations.get_track_artists(track)

    params = {
        "type": "track",
        "q": f"track:{track.name}",  # added below
        "limit": 10,
    }

    assert len(artists) > 0

    params["q"] = params["q"] + " artist:"
    for artist in artists:
        params["q"] = params["q"] + artist.name + " "

    params["q"] = params["q"][:-1]  # drop extraneous space at end, just in case

    # TODO: improve checking that its the same song
    # could use ISRC (requires import of new 'ISRC' table into DB)

    # check duration is similar or name is same
    TRACK_LENGTH_TOLERANCE_MS = 2000
    NAME_RATIO_MIN = 90

    def track_check_func(result):
        if track.length:
            return (
                abs(result["duration_ms"] - track.length)
                < TRACK_LENGTH_TOLERANCE_MS
            )
        else:
            return (
                track_name_similarity_ratio(result["name"], track.name)
                > NAME_RATIO_MIN
            )

    track = search_spotify_until_found(params, track_check_func, max_pages=2)

    if track:
        return track


def normalise_track_title(title):
    title = title.lower()
    title = re.sub(
        r"[\(\[](?!(?:[^\)\]]*\b(?:mix|live|edit)\b))[^\)\]]*[\)\]]",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return title


def track_name_similarity_ratio(title1, title2):
    title1 = normalise_track_title(title1)
    title2 = normalise_track_title(title2)

    return fuzz.WRatio(title1, title2, processor=utils.default_process)


def search_spotify_until_found(params, check_func, max_retries=5, max_pages=5):
    # one (and only one) type to search for must be specified
    assert len(str(params["type"]).split(",")) == 1

    obj_type = params["type"]

    for _ in range(max_pages):
        results = search_spotify(Config.SPOTIFY_SEARCH_URL, params, max_retries)
        for result in results[f"{obj_type}s"]["items"]:
            if check_func(result):
                return result

        # increase offset for next search
        params["offset"] = int(params.get("offset", 0)) + int(
            params.get("limit", 5)
        )


def search_spotify_until_found_artist(
    searched_name, url, params=None, max_retries=5, max_pages=5
):
    for _ in range(max_pages):
        params["offset"] = int(params.get("offset", 0)) + int(
            params.get("limit", 5)
        )
        results = search_spotify(url, params, max_retries)
        for result in results["artists"]["items"]:
            if result["name"] == searched_name:
                return result


def get_spotify_artist_by_id(artist_id, max_retries=5):
    artist_url = f"{Config.SPOTIFY_ARTISTS_URL}/{artist_id}"

    return search_spotify(artist_url, max_retries=max_retries)


# fetches full array of images for album
def fetch_all_album_images(spotify_id):
    url = f"{Config.SPOTIFY_ALBUMS_URL}/{spotify_id}"
    response = search_spotify(url)

    return response["images"]


# fetches full array of images for track's album
def fetch_all_track_images(spotify_id: str) -> list[dict] | None:
    url = f"{Config.SPOTIFY_TRACKS_URL}/{spotify_id}"
    response = search_spotify(url)

    if response:
        return response["album"]["images"]

    return None


def fetch_best_track_image(spotify_id: str) -> WebImage:
    spotify_images = fetch_all_track_images(spotify_id)

    images = []
    for i in spotify_images:
        images.append(helpers.convert_spotify_image_to_class(i))

    return helpers.select_best_image(images)


# fetches full array of images for track's album
def fetch_all_artist_images(spotify_id: str) -> list[dict] | None:
    url = f"{Config.SPOTIFY_ARTISTS_URL}/{spotify_id}"
    response = search_spotify(url)

    if response:
        return response["images"]

    return None


def select_best_artist_image(spotify_artist_obj: dict) -> WebImage | None:
    spotify_images = spotify_artist_obj["images"]

    if not spotify_images:
        return None

    images = []
    for i in spotify_images:
        images.append(helpers.convert_spotify_image_to_class(i))

    return helpers.select_best_image(images)


def fetch_best_artist_image(spotify_id: str) -> WebImage | None:
    spotify_images = fetch_all_artist_images(spotify_id)

    if not spotify_images:
        return None

    images = []
    for i in spotify_images:
        images.append(helpers.convert_spotify_image_to_class(i))

    return helpers.select_best_image(images)
