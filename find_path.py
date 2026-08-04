from models import Recording, ArtistCreditName, URL

from collections import defaultdict, deque

import sqlalchemy.exc
from sqlalchemy import select

from time import time

from db import db

import db_operations


def find_collaborated_tracks(path):
    path_tracks = []
    for previous, current in zip(path, path[1:]):
        sub_stmt_collab = (
            select(ArtistCreditName.artist_credit_id)
            .where(ArtistCreditName.artist_id == previous.id)
        )
        sub_stmt_main = (
            select(ArtistCreditName.artist_credit_id)
            .where(ArtistCreditName.artist_id == current.id)
        )
        stmt = (
            select(Recording)
            .where(Recording.artist_credit_id.in_(sub_stmt_collab))
            .where(Recording.artist_credit_id.in_(sub_stmt_main))
        )

        t = db.session.execute(stmt).scalars().all()

        assert len(t) > 0

        path_tracks.append(t[0])

    return path_tracks


def find_artist_link_images(path):
    for artist in path:
        spotify_id = db_operations.get_artist_spotify_id(artist)
        # TODO
        


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
