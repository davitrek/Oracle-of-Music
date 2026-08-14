from collections import defaultdict, deque
from itertools import pairwise

import db_operations
import helpers
import spotify
from data_classes import ArtistInfo, TrackInfo
from models import Artist

# import sqlalchemy.exc # for errors


class ArtistImage:
    non_squareness = 0
    url = ""
    height = 0
    width = 0


def find_track_images(path_spotify_tracks):
    images = []
    for spotify_track in path_spotify_tracks:
        best_image = None

        spotify_track_images = spotify_track["album"]["images"]

        for img in spotify_track_images:
            if not best_image:
                best_image = img
                continue
            else:
                best_image = helpers.better_squarer_image(best_image, img)

        images.append(best_image["url"])

    return images


def find_spotify_artist(artist: Artist) -> dict:
    spotify_id = db_operations.get_artist_spotify_id(artist)
    spotify_artist = spotify.get_spotify_artist_by_id(spotify_id)

    return spotify_artist


def find_artist_link_images(path_artists):
    images = []
    for artist in path_artists:
        best_image = None

        spotify_artist = find_spotify_artist(artist)
        artist_images = spotify_artist["images"]

        for img in artist_images:
            if not best_image:
                best_image = helpers.convert_spotify_image_to_class(img)
                continue
            else:
                best_image = helpers.better_squarer_image(
                    best_image, helpers.convert_spotify_image_to_class(img)
                )

        images.append(best_image)

    return images


# BFS for single connected component
# returns list of MusicBrainz ORM Artist objects that make up the path from
# root to target
def find_artist_link(adj, root, target) -> list[Artist] | None:
    parents = defaultdict(str)
    explored = defaultdict(bool)
    #  2      let Q be a queue
    q = deque()

    #  3      label root as explored
    explored[root] = True

    #  4      Q.enqueue(root)
    q.append(root)

    #  5      while Q is not empty do
    while q:
        #  6          v := Q.dequeue()
        artist = q.popleft()
        #  7          if v is the goal then
        if artist == target:
            return get_solved_path(parents, root, target)
        #  9          for all edges from v to w in G.adjacentEdges(v) do
        for collaborator in adj[artist]:
            # 10              if w is not labeled as explored then
            if not explored[collaborator]:
                # 11                  label w as explored
                explored[collaborator] = True
                # 12                  w.parent := v
                parents[collaborator] = artist
                # 13                  Q.enqueue(w)
                q.append(collaborator)

    return None


def get_solved_path(parents, root, target) -> list[Artist]:
    path = [db_operations.get_db_artist_by_id(target)]
    n = target
    while parents[n]:
        path.append(db_operations.get_db_artist_by_id(parents[n]))
        n = parents[n]

    return path


def bfs(adj, root, target):
    V = len(adj)
    visited = [False] * V
    res = []

    src = 0
    q = deque()
    visited[src] = True
    q.append(src)

    while q:
        curr = q.popleft()
        res.append(curr)

        # visit all the unvisited
        # neighbours of current node
        for x in adj[curr]:
            if not visited[x]:
                visited[x] = True
                q.append(x)

    return res


# BFS for a single connected component
def bfsConnected(adj, src, visited, res, target):
    q = deque()
    visited[src] = True
    q.append(src)

    while q:
        curr = q.popleft()
        res.append(curr)

        # visit all the unvisited
        # neighbours of current node
        for x in adj[curr]:
            if x is target:
                res.append(x)
                return True
            if not visited[x]:
                visited[x] = True
                q.append(x)


# creates list of TrackInfo that can be used to traverse corresponding artist path
# from root to target
def build_track_path(artist_path: list[ArtistInfo]) -> list[TrackInfo]:
    track_path = []

    for artist1, artist2 in pairwise(artist_path):
        collab_tracks = db_operations.fetch_collaborated_tracks(
            artist1.mbid, artist2.mbid
        )
        for collab_track in collab_tracks:
            spotify_track = spotify.fetch_track(collab_track)

            # if spotify has an equivalent to this MusicBrainz track, use it for
            # the path that will be displayed
            if spotify_track:
                track_path.append(
                    TrackInfo(
                        mbid=collab_track.id,
                        spotify_id=spotify_track["id"],
                        name=collab_track.name,
                        artists=collab_track.artist_credit.name,
                        album_art=spotify.fetch_best_track_image(
                            spotify_track["id"]
                        ),
                    )
                )
                break
        else:
            # assert 0  # no tracks in MusicBrainz DB could be found on Spotify!
            track_path.append(
                TrackInfo(
                    mbid=collab_tracks[0].id,
                    spotify_id=None,
                    name=collab_tracks[0].name,
                    artists=collab_tracks[0].artist_credit.name,
                    album_art=None,
                )
            )

    return track_path


def build_artist_path(
    adj_list: defaultdict[set], artist_start_id: int, artist_end_id: int
) -> list[ArtistInfo] | None:
    artist_path = []

    db_artist_link = find_artist_link(adj_list, artist_start_id, artist_end_id)

    if not db_artist_link:
        return None

    for db_artist in db_artist_link:
        spotify_artist = find_spotify_artist(db_artist)
        artist_info = ArtistInfo(
            mbid=db_artist.id,
            name=db_artist.name,
            spotify_id=None,
            picture=None,
        )

        if spotify_artist:
            artist_info.spotify_id = spotify_artist["id"]
            artist_info.picture = spotify.select_best_artist_image(
                spotify_artist
            )

        artist_path.append(artist_info)

    return artist_path
