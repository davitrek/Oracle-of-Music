import re
from time import sleep, time

import exceptions
import helpers
import requests
from config import Config
from data import db_operations
from data_classes import WebImage
from rapidfuzz import fuzz, utils
from requests import Response


class SpotifyRequestManager:
    def __init__(self):
        self.access_token: str = None
        self.token_expires_at: float = 0
        self.authorisation_header: dict = {}

        self.next_valid_request_time: float = 0

        self._get_access_token()

    # returns dictionary of search response from Spotify
    # returns None on error or request timeout
    def search_spotify(
        self, url: str, params: dict | None = None, max_retries: int = 5
    ) -> dict | None:
        # if previous token expired (or is about to), get new one
        self._get_access_token()

        for attempt in range(max_retries):
            log_spotify_query(url, params)

            # avoid re-requesting immediately.
            # intentionally BEFORE request to ensure if this function called on
            # multiple workers at once it doesn't spam Spotify
            if not self._wait_to_request():
                return None

            r = requests.get(
                url,
                params=params,
                headers=self.authorisation_header,
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

                    self.next_valid_request_time = time() + retry_after_sec
                    continue

                else:
                    print(r.status_code, ": ", r.reason)
                    return None

            response = r.json()

            return response

    # gets new Spotify access token
    def _get_access_token(self, max_retries: int = 5) -> None:
        if not self._is_expired():
            return

        # avoid re-requesting immediately.
        # intentionally BEFORE request to ensure if this function called on
        # multiple workers at once it doesn't spam Spotify
        self._wait_to_request(True)

        print("Getting spotify access token.")

        for _ in range(max_retries):
            r = self._request_token()
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

        else:
            print("Failed to get spotify access token!")
            raise exceptions.SpotifyTokenError(
                "Failed to get spotify access token!"
            )

        try:
            r = r.json()
            self.access_token = r["access_token"]
            self.token_expires_at = time() + r["expires_in"]
            self.authorisation_header["Authorization"] = (
                f"Bearer {self.access_token}"
            )
        except KeyError:
            raise exceptions.SpotifyTokenError(
                "Failed to get spotify access token!"
            )

    def _is_expired(self) -> bool:
        return time() > (self.token_expires_at - 60)

    # returns False if wait time is too long and skipping search is preferable,
    # unless false=True, in which case will always wait.
    # returns True otherwise
    def _wait_to_request(self, force: bool = False) -> bool:
        time_now = time()
        wait_time = self.next_valid_request_time - time_now

        if not force and wait_time > Config.REQUEST_TIMEOUT_S:
            return False

        if wait_time > 0:
            print(f"Hit wait time, waiting {wait_time}")
            sleep(wait_time)

        self.next_valid_request_time = time() + Config.REQUEST_DELAY_S
        return True

    def _request_token(self) -> Response:
        url = Config.SPOTIFY_API_TOKEN_REQUEST_URL
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": "client_credentials",
            "client_id": str(Config.SPOTIFY_CLIENT_ID),
            "client_secret": str(Config.SPOTIFY_CLIENT_SECRET),
        }

        return requests.post(url, headers=headers, data=params)


spotify_request_manager = SpotifyRequestManager()


def search_spotify(
    url: str, params: dict | None = None, max_retries: int = 5
) -> dict:
    return spotify_request_manager.search_spotify(url, params, max_retries)


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

    print(s)


# returns a dictionary representing a Spotify Track JSON object
def fetch_track(track):
    artists = db_operations.get_track_artists(track)

    artist_names = []
    for artist in artists:
        if str(artist.name).isascii():
            artist_names.append(artist.name)
        else:
            # if artist name is non-ascii, use the string the artist_credit_name
            # instead.
            # E.g., Yours Eternally - ***U2 feat. Ed Sheeran & Taras Topolia***
            # string between stars is the artist_credit, and the
            # artist_credit_names are 'U2', 'Ed Sheeran', 'Taras Topolia'.
            # HOWEVER, Taras Topolia's actual name in the MusicBrainz DB is
            # 'Тарас Тополя' which is NOT how they're credited on Spotify which
            # means Spotify doesn't find the track when using 'Тарас Тополя'
            for artist_credit_name in track.artist_credit.artists:
                if artist_credit_name.artist is artist:
                    artist_names.append(artist_credit_name.name)
                    break

    params = {
        "type": "track",
        "q": f"track:{track.name}",  # added below
        "limit": 10,
    }

    params["q"] = params["q"] + " artist:"
    for artist_name in artist_names:
        params["q"] = params["q"] + artist_name + " "

    params["q"] = params["q"][:-1]  # drop extraneous space at end, just in case

    # TODO: improve checking that its the same song
    # could use ISRC (requires import of new 'ISRC' table into DB)

    # check duration is similar or name is same
    TRACK_LENGTH_TOLERANCE_MS = 2000
    NAME_RATIO_MIN = 90

    def track_check_func(result) -> bool:
        if track.length and (
            abs(result["duration_ms"] - track.length)
            < TRACK_LENGTH_TOLERANCE_MS
        ):
            return True

        # if track length doesn't match, still check for name similarity

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
        if not results:
            return None

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


def select_best_track_image(spotify_artist_obj: dict) -> WebImage | None:
    spotify_images = spotify_artist_obj["album"]["images"]

    if not spotify_images:
        return None

    images = []
    for i in spotify_images:
        images.append(helpers.convert_spotify_image_to_class(i))

    return helpers.select_best_image(images)


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
