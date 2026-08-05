from models import Recording, ArtistCreditName, URL

from collections import defaultdict, deque

import sqlalchemy.exc
from sqlalchemy import select

from time import time

from db import db

import db_operations

import helpers

class ArtistImage:
    non_squareness = 0
    url = ''
    height = 0
    width = 0


def find_track_link_images(path_spotify_tracks):
    images = []
    for spotify_track in path_spotify_tracks:
        best_image = None

        spotify_track_images = spotify_track['album']['images'] 

        for img in spotify_track_images:
            if not best_image:
                best_image = img
                continue
            else:
                best_image = better_squarer_image(best_image, img)

        images.append(best_image['url'])

    return images


def find_artist_link_images(path_artists):
    images = []
    for artist in path_artists:
        best_image = None

        spotify_id = db_operations.get_artist_spotify_id(artist)
        spotify_artist = helpers.get_spotify_artist_by_id(spotify_id)
        artist_images = spotify_artist['images'] 

        for img in artist_images:
            if not best_image:
                best_image = img
                continue
            else:
                best_image = better_squarer_image(best_image, img)

        images.append(best_image['url'])

    return images


def better_squarer_image(img1, img2):
    non_squareness1 = image_non_squareness(img1['height'], img1['width'])
    non_squareness2 = image_non_squareness(img2['height'], img2['width'])

    if non_squareness1 < non_squareness1:
        return img1
    elif non_squareness1 > non_squareness2:
        return img2

    # images are both same non-squareness, return bigger image:
    if max(img1['height'], img1['width']) > max(img2['height'], img2['width']):
        return img1
    
    return img2


def image_non_squareness(height, width):
    return (height - width) / max(height, width)


# BFS for single connected component
def find_artist_link(adj, root, target):
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


def get_solved_path(parents, root, target):
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
