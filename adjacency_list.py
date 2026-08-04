from models import ArtistAdjacents
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from collections import defaultdict

from time import time

from db import db

import db_operations


def init_adjacency_list(number_artists):
    t0 = time()
    # during testing to skip loading names again
    loaded_adjacency_list = load_adjacency_list()
    adjacency_list = create_adjacency_list(number_artists, loaded_adjacency_list)

    t1 = time()
    tt = t1 - t0
    print(tt)
    if len(adjacency_list) < number_artists:
        print('check!!!')

    # saved adjacency list test to make sure it's functioning correctly
    # for k, v in adjacency_list.items():
    #     for i in v:
    #         if loaded_adjacency_list[k].__contains__(i):
    #             break
    #     else:
    #         assert 0

    save_adjacency_list(adjacency_list)

    return adjacency_list


def save_adjacency_list(adj):
    # the i-related stuff is just to avoid hitting SQLAlchemy's item limit
    added = []
    i = 0
    for k,v in adj.items():
        for artist in v:
            added.append({'artist0_id': k, 'artist1_id': artist})
            i = i + 1
            if i == 30000:
                db.session.execute(insert(ArtistAdjacents).values(added).on_conflict_do_nothing())
                db.session.commit()
                i = 0
                added = []

    db.session.execute(insert(ArtistAdjacents).values(added).on_conflict_do_nothing())
    db.session.commit()

    
def load_adjacency_list():
    adjacency_list = defaultdict(set)
    t = db.session.execute(select(ArtistAdjacents)).scalars().all()

    for i in t:
        adjacency_list[i.artist0_id].add(i.artist1_id)

    return adjacency_list


def create_adjacency_list(count, loaded_adjacency_list=None):
    artist_ids_to_search = []
    with open('missingnames.txt', 'w') as f:
        if loaded_adjacency_list:
            adjacency_list = loaded_adjacency_list
        else:
            adjacency_list = defaultdict(set)

        for i in range(count):
            # get next artist name from scraped list
            name = db_operations.get_artist_name_from_list(i + 1)
            if not name:
                # if name empty, means file read completely
                break

            # search database for artist
            artist = db_operations.get_db_artist_by_name(name)
            if not artist:
                # write that artist could not be found
                f.write(name + '\n')
                continue
            
            # if loaded adjacency list already had this artist, skip
            if not adjacency_list[artist.id]:
                artist_ids_to_search.append(artist.id)

        adjacency_list = adjacency_list | db_operations.get_artist_collaborators(artist_ids_to_search)
        return adjacency_list
