from dataclasses import dataclass


@dataclass
class WebImage:
    url: str
    height: int  # px
    width: int  # px


@dataclass
class ArtistInfo:
    mbid: int  # id (not gid) of artist in MusicBrainz 'artist' table
    spotify_id: str | None  # id of artist on Spotify

    name: str

    picture: WebImage | None


@dataclass
class TrackInfo:
    mbid: int  # id (not gid) of track in MusicBrainz 'track' table
    spotify_id: str | None  # id of track on Spotify

    name: str
    artists: str  # full artist credit (e.g., Kanye West, Pusha T feat. Jay-Z)

    album_art: WebImage | None
