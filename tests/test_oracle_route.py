from types import SimpleNamespace

import pytest
from data import db_operations
from data_classes import ArtistInfo, TrackInfo
from graph import find_path

KANYE = ArtistInfo(mbid=1, spotify_id=None, name="Kanye West", picture=None)
PUSHA = ArtistInfo(mbid=2, spotify_id=None, name="Pusha T", picture=None)
JAY_Z = ArtistInfo(mbid=3, spotify_id=None, name="Jay-Z", picture=None)

RUNAWAY = TrackInfo(
    mbid=10,
    spotify_id=None,
    name="Runaway",
    artist_credit="Kanye West feat. Pusha T",
    album_art=None,
)
SO_APPALLED = TrackInfo(
    mbid=11,
    spotify_id=None,
    name="So Appalled",
    artist_credit="Kanye West feat. Jay-Z, Pusha T, Prynce Cy Hi, Swizz Beatz and RZA",
    album_art=None,
)

START_NOT_FOUND = "Could not find start artist of that name."
END_NOT_FOUND = "Could not find end artist of that name."
NO_PATH_FOUND = "No path found."
ERROR_MESSAGES = (START_NOT_FOUND, END_NOT_FOUND, NO_PATH_FOUND)


@pytest.fixture
def known_artists(monkeypatch):
    """The database knows KANYE, PUSHA and JAY_Z by name, and no one else."""
    by_name = {
        artist.name: SimpleNamespace(id=artist.mbid)
        for artist in (KANYE, PUSHA, JAY_Z)
    }
    monkeypatch.setattr(db_operations, "get_db_artist_by_name", by_name.get)


def stub_path(monkeypatch, artists, tracks):
    monkeypatch.setattr(
        find_path, "build_artist_path", lambda adj, start, end: artists
    )
    monkeypatch.setattr(find_path, "build_track_path", lambda path: tracks)


def post_oracle(client, start, end):
    response = client.post("/oracle", data={"start": start, "end": end})
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_multi_hop_path_shows_artists_tracks_and_artist_credits(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [PUSHA, KANYE, JAY_Z], [RUNAWAY, SO_APPALLED])

    html = post_oracle(client, "Pusha T", "Jay-Z")

    for name in ("Pusha T", "Kanye West", "Jay-Z", "Runaway", "So Appalled"):
        assert name in html
    assert "Kanye West feat. Pusha T" in html
    assert (
        "Kanye West feat. Jay-Z, Pusha T, Prynce Cy Hi, Swizz Beatz and RZA"
        in html
    )


def test_one_node_path_when_start_artist_is_end_artist(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [KANYE], [])

    html = post_oracle(client, "Kanye West", "Kanye West")

    assert "Kanye West" in html
    for error in ERROR_MESSAGES:
        assert error not in html


def test_unknown_start_artist_shows_error(client, known_artists):
    html = post_oracle(client, "Nobody Real", "Jay-Z")

    assert START_NOT_FOUND in html


def test_unknown_end_artist_shows_error(client, known_artists):
    html = post_oracle(client, "Jay-Z", "Nobody Real")

    assert END_NOT_FOUND in html


def test_no_path_found_shows_error(client, known_artists, monkeypatch):
    stub_path(monkeypatch, None, [])

    html = post_oracle(client, "Kanye West", "Jay-Z")

    assert NO_PATH_FOUND in html
