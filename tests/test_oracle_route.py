import re
from html.parser import HTMLParser
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


class PathParser(HTMLParser):
    """Collects the Path's data-hops, its Nodes (kind and --i index), each
    Connector's --i index paired with the --i of the Node before it, and each
    Node's secondary text."""

    def __init__(self):
        super().__init__()
        self.hops = None
        self.nodes = []
        self.connectors = []
        self.subtexts = []
        self.tags = set()
        self._in_subtext = False

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if "path" in classes:
            self.hops = attrs.get("data-hops")
        index = re.search(r"--i:\s*(\d+)", attrs.get("style") or "")
        for kind in ("artist", "track"):
            if f"path-node-{kind}" in classes:
                self.nodes.append((kind, int(index.group(1))))
                self.subtexts.append([])
        if "path-connector" in classes:
            self.connectors.append((int(index.group(1)), self.nodes[-1][1]))
        if "node-subtext" in classes:
            self._in_subtext = True
            self.subtexts[-1].append("")

    def handle_endtag(self, tag):
        self._in_subtext = False

    def handle_data(self, data):
        if self._in_subtext:
            self.subtexts[-1][-1] += data.strip()


def parse_path(html):
    parser = PathParser()
    parser.feed(html)
    return parser


def test_multi_hop_path_renders_nodes_in_path_order(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [PUSHA, KANYE, JAY_Z], [RUNAWAY, SO_APPALLED])

    path = parse_path(post_oracle(client, "Pusha T", "Jay-Z"))

    assert path.hops == "2"
    assert path.nodes == [
        ("artist", 0),
        ("track", 1),
        ("artist", 2),
        ("track", 3),
        ("artist", 4),
    ]


def test_connectors_reveal_with_the_node_before_them(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [PUSHA, KANYE, JAY_Z], [RUNAWAY, SO_APPALLED])

    path = parse_path(post_oracle(client, "Pusha T", "Jay-Z"))

    assert len(path.connectors) == 4
    for connector_index, node_before_index in path.connectors:
        assert connector_index == node_before_index


def test_one_node_path_has_a_single_artist_node_and_zero_hops(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [KANYE], [])

    path = parse_path(post_oracle(client, "Kanye West", "Kanye West"))

    assert path.hops == "0"
    assert path.nodes == [("artist", 0)]


def test_track_nodes_show_artist_credit_as_secondary_text(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [PUSHA, KANYE, JAY_Z], [RUNAWAY, SO_APPALLED])

    path = parse_path(post_oracle(client, "Pusha T", "Jay-Z"))

    track_subtexts = [
        subtexts
        for (kind, _), subtexts in zip(path.nodes, path.subtexts)
        if kind == "track"
    ]
    assert "Kanye West feat. Pusha T" in track_subtexts[0]
    assert (
        "Kanye West feat. Jay-Z, Pusha T, Prynce Cy Hi, Swizz Beatz and RZA"
        in track_subtexts[1]
    )


def test_every_node_has_not_on_spotify_secondary_text(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [PUSHA, KANYE], [RUNAWAY])

    path = parse_path(post_oracle(client, "Pusha T", "Kanye West"))

    assert len(path.subtexts) == 3
    for subtexts in path.subtexts:
        assert "(Not on Spotify)" in subtexts


def body_classes(html):
    body = re.search(r"<body([^>]*)>", html).group(1)
    match = re.search(r'class="([^"]*)"', body)
    return match.group(1).split() if match else []


def test_only_the_index_page_is_non_scrolling(
    client, known_artists, monkeypatch
):
    stub_path(monkeypatch, [PUSHA, KANYE], [RUNAWAY])

    index_html = client.get("/").get_data(as_text=True)
    results_html = post_oracle(client, "Pusha T", "Kanye West")

    assert "no-scroll" in body_classes(index_html)
    assert "no-scroll" not in body_classes(results_html)
