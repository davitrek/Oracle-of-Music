from models import Artist, ArtistAlias, Recording, LinkArtistArtist, LinkArtistRecording, LinkType, Link, ArtistCredit, ArtistCreditName, ArtistAdjacents, Track, ReleaseStatus, Release, Medium, ReleaseGroup, ReleaseGroupPrimaryType
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func

from sqlalchemy.dialects.postgresql import insert

from collections import defaultdict, deque

from config import Config

import sqlalchemy.exc

from time import time

from flask import Flask

from db import db

from flask import render_template, request

import helpers

valid_track_ids = []

adjacency_list = defaultdict(set)

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_ECHO"] = True
# initialize the app with Flask-SQLAlchemy extension
db.init_app(app)



count = 100


@app.route('/')
def index():
    """Provide index"""
    return render_template('index.html')




@app.route('/findpath', methods=['GET', 'POST'])
def find_path():
    if request.method == 'GET':
        return render_template('findpath.html')

    # POST:
    name_start = request.form.get('start')
    name_end = request.form.get('end')

    artist_start = get_db_artist_by_name(name_start)
    artist_end = get_db_artist_by_name(name_end)

    if not artist_start or not artist_end:
        return render_template('findpath.html', error='Invalid artists start/end artist')


    path_artists = find_artist_link(adjacency_list, artist_start.id, artist_end.id)
    if path_artists:
        s = ''
        path_recordings = find_collaborated_recordings(path_artists)
        for recording in path_recordings:
            s = s + str(recording.name) + '-' + str(recording.artist_credit.name) + '\n\n'
        print('\n\n\n\n')
        print(s)

        combined_path = []

        for artist, recording in zip(path_artists, path_recordings):
            combined_path.append({
                'type': 'artist',
                'name': artist.name
            })
            combined_path.append({
                'type': 'recording',
                'name': recording.name,
                'artist_credit': recording.artist_credit.name
            })

        combined_path.append({
            'type': 'artist',
            'name': path_artists[-1].name
        })

        pad = 0
        svg_width = 1000
        svg_height = 200
        #circle_radius = (svg_width - 2 * pad) / (3 * len(path_artists) - 2)
        circle_radius = 50
        line_length = 25
        square_size = round(3/2 * circle_radius)

        circle_centres = []
        for i in range(len(path_artists)):
            circle_centres.append(svg_width / (2 * len(path_artists)) * (2 * i + 1))

        square_centres = []
        for previous, current in zip(circle_centres, circle_centres[1:]):
            square_centres.append((current + previous) / 2)

        square_left_edges = []
        for square in square_centres:
            square_left_edges.append(square - square_size / 2)

        # square_positions = []
        # for previous, current in zip(circle_positions, circle_positions[1:]):
        #     square_positions.append((current + previous) / 2 - square_size / 2)
        
        # line_positions = []
        # for i in range(len(path_artists) - 1):
        #     line_positions.append((circle_positions[i] + circle_radius, circle_positions[i + 1] - circle_radius))

        line_positions = []
        for circle_first_pos, square_pos, circle_second_pos in zip(circle_centres, square_centres, circle_centres[1:]):
            line_positions.append((circle_first_pos + circle_radius, square_pos - square_size / 2))
            line_positions.append((square_pos + square_size / 2, circle_second_pos - circle_radius))

        artist_name_location = []
        for name, location in zip(path_artists, circle_centres):
            artist_name_location.append((name.name, location))

        recording_name_location = []
        for name, location in zip(path_recordings, square_centres):
            recording_name_location.append((name.name, location))

    
        # artist_images = []
        # for artist, recording in zip(path_artists, path_recordings):
        #     search_params = {
        #         #'q': f'artist:{artist.name} track:{recording.name}',
        #         'q': f'{artist.name}',
        #         'type': 'artist',
        #         'limit': '10'
        #     }
        #     result = helpers.search_spotify_until_found_artist(artist.name, Config.SPOTIFY_SEARCH_URL, search_params)
        #     artist_images.append(result['images'])

        return render_template(
            'findpath.html',
            svg_width=svg_width,
            svg_height=svg_height,
            path=combined_path,
            circle_radius=circle_radius,
            circle_positions=circle_centres,
            square_positions=square_left_edges,
            square_size=square_size,
            line_positions=line_positions,
            artist_name_location=artist_name_location,
            recording_name_location=recording_name_location,
        )

    else:
        return render_template('findpath.html', error='No path found :(')


def init_adjacency_list():
    t0 = time()
    # during testing to skip loading names again
    #loaded_adjacency_list = load_adjacency_list()
    global adjacency_list
    adjacency_list = create_adjacency_list(count)#, loaded_adjacency_list)
    
    #adjacency_list = create_adjacency_list(session, count)

    t1 = time()
    tt = t1 - t0
    print(tt)
    if len(adjacency_list) < count:
        print('check!!!')

    # saved adjacency list test to make sure it's functioning correctly
    
    # for k, v in adjacency_list.items():
    #     for i in v:
    #         if loaded_adjacency_list[k].__contains__(i):
    #             break
    #     else:
    #         assert 0

    # save_adjacency_list(adjacency_list)


def find_collaborated_recordings(path):
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

def load_adjacency_list():
    adjacency_list = defaultdict(set)
    t = db.session.execute(select(ArtistAdjacents)).scalars().all()

    for i in t:
        adjacency_list[i.artist0_id].add(i.artist1_id)

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
    path = [get_db_artist_by_id(target)]
    n = target
    while parents[n]:
        path.append(get_db_artist_by_id(parents[n]))
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


# def _main():
#     with Session(engine) as session:
#         # get artist
#         stmt = select(Artist).filter_by(name='Ye').filter(Artist.area_id.is_not(None))
#         artist = session.execute(stmt).scalar_one_or_none()
#         if artist:
#             print(artist.name +"'s tracks: ")

#         # get artist's mixing, mastering, or vocal credits through LinkArtistRecord
#         #   -> I probably don't actually want to use this
#         for assoc in artist.linked_records:
#             print(assoc.recording.name)
#         print('--------------------')

#         # get recording by name
#         stmt = select(Recording).filter_by(name='Neck & Wrist')
#         recording = session.execute(stmt).first()[0]
#         if recording:
#             print(recording.name, recording.comment)

#         # get credits and credit type on recording (mixing, mastering, vocals, etc)
#         stmt = select(LinkArtistRecording).filter_by(recording_id=recording.id)
#         artist_of_recording = session.execute(stmt).all()

#         for row in artist_of_recording:
#             stmt = select(Artist).filter_by(id=row[0].artist_id)
#             artist = session.execute(stmt).scalar_one_or_none()
#             link_type = row[0].link.link_type.name

#             print(artist.name, link_type)


#         # get artist of recording (the one I actually need)
#         recording_artist_credit = recording.artist_credit
#         print(recording_artist_credit.name, 'i.e., number of artists:', recording_artist_credit.artist_count)

#         for artist_credit_name in recording_artist_credit.artist_credit_names:
#             print(artist_credit_name.artist.name, 'position:', artist_credit_name.position)


def create_adjacency_list(count, loaded_adjacency_list=None):
    artist_ids_to_search = []
    with open('missingnames.txt', 'w') as f:
        if loaded_adjacency_list:
            adjacency_list = loaded_adjacency_list
        else:
            adjacency_list = defaultdict(set)

        for i in range(count):
            # get next artist name from scraped list
            name = get_artist_name_from_list(i + 1)
            if not name:
                # if name empty, means file read completely
                break

            # search database for artist
            artist = get_db_artist_by_name(name)
            if not artist:
                # write that artist could not be found
                f.write(name + '\n')
                continue
            
            # if loaded adjacency list already had this artist, skip
            if not adjacency_list[artist.id]:
                artist_ids_to_search.append(artist.id)

        adjacency_list = adjacency_list | get_artist_collaborators(artist_ids_to_search)
        return adjacency_list


def get_artist_name_from_list(line_number):
    with open(Config.SCRAPED_NAMES_FILE_PATH) as f:
        for i, line in enumerate(f):
            if i == line_number - 1:
                return line[:-1]
    return None


def get_db_artist_by_id(id):
    stmt = (
        select(Artist)
        .where(Artist.id == id)
    )

    search_result = db.session.execute(stmt).scalar_one_or_none()

    return search_result
            

# returns None if no artist could be found
def get_db_artist_by_name(name):
    # search by artist name
    stmt = (
        select(Artist)
        .where(Artist.name == name)
    )

    search_result = db.session.execute(stmt).scalars().all()

    # if a direct name search doesn't find anything, search for artist aliases
    # as well
    if not search_result:
        sub_stmt = (
            select(ArtistAlias.artist_id)
            # using lower(musicbrainz_unaccent(name)) index on ArtistAlias 
            .where(func.lower(func.musicbrainz_unaccent(ArtistAlias.name)) == func.lower(func.musicbrainz_unaccent(name)))
        )
        stmt = (
            select(Artist)
            .where(Artist.id.in_(sub_stmt))
        )

        search_result = db.session.execute(stmt).scalars().all()
    
    if len(search_result) == 1:
        artist = search_result[0]
        return artist
    elif len(search_result) == 0:
        return None
    else:
        return filter_db_artists(search_result, name)


def filter_db_artists(search_results, name):
    possible_artists = search_results

    
    # multiple artists found, try filter by which one has an 'area_id'
    has_area_id = []
    for artist_result in possible_artists:
        if artist_result.area_id != None:
            has_area_id.append(artist_result)
    
    if len(has_area_id) == 1:
        artist = has_area_id[0]
        return artist
    # if there are multiple artists with an area, assume one I'm searching
    #   for is within that list, only continue filtering through those
    elif len(has_area_id) > 1:
        possible_artists = has_area_id

    # multiple or no artists found filtering by area. filter by begin_year
    has_begin_year = []
    for artist_result in possible_artists:
        if artist_result.begin_date_year != None:
            has_begin_year.append(artist_result)
    
    if len(has_begin_year) == 1:
        artist = has_begin_year[0]
        return artist
    # if there are multiple artists with a begin year, assume one I'm searching
    #   for is within that list, only continue filtering through those
    elif len(has_begin_year) > 1:
        possible_artists = has_begin_year

    # multiple or no artists found filtering by begin year. filter by begin_area
    has_begin_area = []
    for artist_result in possible_artists:
        if artist_result.begin_area_id != None:
            has_begin_area.append(artist_result)
    
    if len(has_begin_area) == 1:
        artist = has_begin_area[0]
        return artist
    # if there are multiple artists with a begin year, assume one I'm searching
    #   for is within that list, only continue filtering through those
    elif len(has_begin_area) > 1:
        possible_artists = has_begin_area

    # multiple or no artists found filtering by begin_area. filter by begin_month
    has_begin_month = []
    for artist_result in possible_artists:
        if artist_result.begin_date_month != None:
            has_begin_month.append(artist_result)

    if len(has_begin_month) == 1:
        artist = has_begin_month[0]
        return artist

    # see if any of the search_results' Artist.name is name (i.e., select ones
    #   that were NOT found via an alias)
    has_searched_for_name = []
    for artist_result in possible_artists:
        if artist_result.name == name:
            has_searched_for_name.append(artist_result)
    
    if len(has_searched_for_name) == 1:
        artist = has_searched_for_name[0]
        return artist
    # -> do NOT update possible_artists, as the artist I want could very well
    #   have renamed themselves -> Artist.name =/= name, instead would've been
    #   found via an alias
    # elif len(has_area_id) > 1:
    #     possible_artists = has_area_id

    # if none of these basic filters work, check which artist has more recordings:

    has_sufficient_recordings = []
    for artist in possible_artists:
        artist_recordings = get_artist_recordings(artist)
        if len(artist_recordings) >= Config.MIN_RECORDINGS_COUNT:
            has_sufficient_recordings.append(artist)

    if len(has_sufficient_recordings) == 1:
        return has_sufficient_recordings[0]

    # more filtering possible here

    return None


def get_artist_recordings(artist):
    sub_sub_stmt = (
        select(ArtistCreditName.artist_credit_id)
        .where(ArtistCreditName.artist == artist)
    )

    # these are all artist_credit rows with my artist that have collaborators
    sub_stmt = (
        select(ArtistCredit.id)
        .where(ArtistCredit.id.in_(sub_sub_stmt))
        .where(ArtistCredit.artist_count > 1)
    )

    stmt = (
        select(Recording)
         .where(Recording.artist_credit_id.in_(sub_stmt))
    )

    return db.session.execute(stmt).scalars().all()


# return only tracks that are on releases labelled as 'Official' AND ('Album',
# 'EP', or 'Single')
def get_filtered_tracks():
    # need to review whether filtering ReleaseGroupPrimaryType is even worthwhile
    stmt = (
        select(ReleaseGroupPrimaryType.id)
        .where((ReleaseGroupPrimaryType.name == 'Album') 
               | (ReleaseGroupPrimaryType.name == 'Single') 
               | (ReleaseGroupPrimaryType.name == 'EP'))
    )
    release_group_primary_type_ids = db.session.execute(stmt).scalars().all()

    stmt = (
        select(ReleaseStatus.id)
        .where(ReleaseStatus.name == 'Official')
    )
    official_release_status_id = db.session.execute(stmt).scalar_one()

    tc0 = time()
    release_group_stmt = (
        select(ReleaseGroup.id)
        .where(ReleaseGroup.type_id.in_(release_group_primary_type_ids))
    )
    tmp = db.session.execute(release_group_stmt).scalars().all()
    tc1 = time()
    ttc = tc1 - tc0
    
    td0 = time()
    release_stmt = (
        select(Release.id)
        .where(Release.release_group_id.in_(release_group_stmt))
        .where(Release.status_id == official_release_status_id)
    )
    tmp = db.session.execute(release_stmt).scalars().all()
    td1 = time()
    ttd = td1 - td0

    te0 = time()
    stmt = (
        select(Track.id)
        .where(Track.medium_id.in_(release_stmt))
        .limit(100000)                                         # NOTE: for testing only
    )
    s = db.session.execute(stmt).scalars().all()
    te1 = time()
    tte = te1 - te0

    return s


# ALTERNATIVE ALTERNATIVE. this one uses track table instead of recording table
# get all tracks with collaborators where artist is credited, adding them to a list
#   each list entry should have the collaborator id and recording id
#   if there is at least one track in that list, create entry in adjacency_list 
#   -> {id_of artist in artist table: adjacent nodes list}
def get_artist_collaborators(artist_ids):
    acn_target = aliased(ArtistCreditName)
    acn_collab = aliased(ArtistCreditName)
    artist_target = aliased(Artist)
    artist_collab = aliased(Artist)
    
    # artist_target
    # -> acn_target
    # -> artist_credit
    # ... (A)
    # -> acn_collab
    # -> artist_collab
    
    valid_release_types = ['Album', 'Single', 'EP']
    official_status = 'Official'
    
    stmt = (
        select(artist_target.id, artist_collab.id)
        # --- target artist lookup ---
        .select_from(artist_target)
        .where(artist_target.id.in_(artist_ids))
        .join(acn_target,  acn_target.artist_id == artist_target.id)
        # --- connectors ---
        .join(ArtistCredit,     ArtistCredit.id == acn_target.artist_credit_id)
        .join(Track,     Track.artist_credit_id == ArtistCredit.id)
        .join(Medium,                 Medium.id == Track.medium_id)
        .join(Release,               Release.id == Medium.release_id)
        .join(ReleaseGroup,     ReleaseGroup.id == Release.release_group_id)
        # --- filters ---
        .join(ReleaseGroupPrimaryType, ReleaseGroupPrimaryType.id == ReleaseGroup.type_id)
        .where(ReleaseGroupPrimaryType.name.in_(valid_release_types))
        .join(ReleaseStatus,                     ReleaseStatus.id == Release.status_id)
        .where(ReleaseStatus.name == official_status)
        # --- collab artist lookup ---
        .join(acn_collab,             acn_collab.artist_credit_id == ArtistCredit.id)
        .join(artist_collab,                     artist_collab.id == acn_collab.artist_id)
        .where(artist_collab.id != artist_target.id)
    )
    
    # print(stmt)

    artist_collabs_list = db.session.execute(stmt).all()

    adj = defaultdict(set)
    for i in artist_collabs_list:
        adj[i[0]].add(i[1])

    return adj


# ALTERNATIVE. this one skips get_artist_recordings
def _get_artist_collaborators(artist):
    sub_sub_stmt = (
        select(Recording.artist_credit_id)
    )

    sub_stmt = (
        select(ArtistCreditName.artist_credit_id)
        .where(ArtistCreditName.artist == artist)
        .where(ArtistCreditName.artist_credit_id.in_(sub_sub_stmt))
    )

    stmt = (
        select(ArtistCreditName.artist_id)
        .where(ArtistCreditName.artist_credit_id.in_(sub_stmt))
        .where(ArtistCreditName.artist != artist)
        .where(ArtistCreditName.artist != None)
        .distinct()
    )

    s = db.session.execute(stmt).scalars().all()

    return s


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


with app.app_context():
    # artist = get_db_artist_by_name('Kendrick Lamar')
    # get_artist_collaborators(artist_ids)
    
    init_adjacency_list()
    #Config.SPOTIFY_ACCESS_TOKEN = helpers.get_spotify_access_token()
    #Config.AUTHORISATION_HEADER['Authorization'] = f'Bearer {Config.SPOTIFY_ACCESS_TOKEN}'
