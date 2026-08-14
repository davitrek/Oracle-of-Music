from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

import db_operations
from db import db
from models import ArtistAdjacents


def build_adjacency_list(number_artists: int) -> defaultdict[set]:
    # during testing to skip loading names again
    loaded_adjacency_list = load_adjacency_list()
    adjacency_list = create_adjacency_list(
        number_artists, loaded_adjacency_list
    )

    if len(adjacency_list) < number_artists:
        print("Some artists may have failed to be found in database")

    save_adjacency_list(adjacency_list, loaded_adjacency_list)

    return adjacency_list


def save_adjacency_list(
    adj: defaultdict[set], loaded_adj: defaultdict[set]
) -> None:
    loaded_artists = loaded_adj.keys()

    added = []
    i = 0
    for artist, adjacents in adj.items():
        for adjacent_artist in adjacents:
            # save artist adjacent pair to DB only if it wasn't already in DB
            # before, as reflected by loaded_adj
            if (
                artist not in loaded_artists
                or not adjacent_artist in loaded_adj[artist]
            ):
                added.append(
                    {"artist0_id": artist, "artist1_id": adjacent_artist}
                )
                i = i + 1
                # to avoid hitting SQLAlchemy's item limit
                if i == 30000:
                    db.session.execute(
                        insert(ArtistAdjacents)
                        .values(added)
                        .on_conflict_do_nothing()
                    )
                    db.session.commit()
                    i = 0
                    added = []

    if added:
        db.session.execute(
            insert(ArtistAdjacents).values(added).on_conflict_do_nothing()
        )
        db.session.commit()


def load_adjacency_list() -> defaultdict[set]:
    adjacency_list = defaultdict(set)
    t = db.session.execute(select(ArtistAdjacents)).scalars().all()

    for i in t:
        adjacency_list[i.artist0_id].add(i.artist1_id)

    return adjacency_list


def create_adjacency_list(
    count: int, loaded_adjacency_list: defaultdict[set] | None = None
) -> defaultdict[set]:
    artist_ids_to_search = []
    with open("missingnames.txt", "w") as f:
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
                f.write(name + "\n")
                continue

            # if loaded adjacency list already had this artist, skip
            if not adjacency_list[artist.id]:
                artist_ids_to_search.append(artist.id)

        adjacency_list = (
            adjacency_list
            | db_operations.get_artist_collaborators(artist_ids_to_search)
        )
        return adjacency_list
