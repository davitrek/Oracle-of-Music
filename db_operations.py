from config import Config

from models import Artist, ArtistAlias, Recording, ArtistCredit, ArtistCreditName, Track, ReleaseStatus, Release, Medium, ReleaseGroup, ReleaseGroupPrimaryType, ReleaseGroupSecondaryType, ReleaseGroupSecondaryTypeJoin, URL, LinkArtistURL, Link, LinkType
from sqlalchemy.orm import aliased
from sqlalchemy import select, func

#from sqlalchemy.dialects.postgresql import insert

from collections import defaultdict

from config import Config

import sqlalchemy.exc

from time import time

from db import db

import re

import helpers


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
# def get_filtered_tracks():
#     # need to review whether filtering ReleaseGroupPrimaryType is even worthwhile
#     stmt = (
#         select(ReleaseGroupPrimaryType.id)
#         .where((ReleaseGroupPrimaryType.name == 'Album') 
#                | (ReleaseGroupPrimaryType.name == 'Single') 
#                | (ReleaseGroupPrimaryType.name == 'EP'))
#     )
#     release_group_primary_type_ids = db.session.execute(stmt).scalars().all()
# 
#     stmt = (
#         select(ReleaseStatus.id)
#         .where(ReleaseStatus.name == 'Official')
#     )
#     official_release_status_id = db.session.execute(stmt).scalar_one()
# 
#     tc0 = time()
#     release_group_stmt = (
#         select(ReleaseGroup.id)
#         .where(ReleaseGroup.type_id.in_(release_group_primary_type_ids))
#     )
#     tmp = db.session.execute(release_group_stmt).scalars().all()
#     tc1 = time()
#     ttc = tc1 - tc0
#     
#     td0 = time()
#     release_stmt = (
#         select(Release.id)
#         .where(Release.release_group_id.in_(release_group_stmt))
#         .where(Release.status_id == official_release_status_id)
#     )
#     tmp = db.session.execute(release_stmt).scalars().all()
#     td1 = time()
#     ttd = td1 - td0
# 
#     te0 = time()
#     stmt = (
#         select(Track.id)
#         .where(Track.medium_id.in_(release_stmt))
#         .limit(100000)                                         # NOTE: for testing only
#     )
#     s = db.session.execute(stmt).scalars().all()
#     te1 = time()
#     tte = te1 - te0
# 
#     return s


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
    # ... (connections & filters)
    # -> acn_collab
    # -> artist_collab
    
    # (connections & filters)
    # -> artist_credit
    # -> track
    # -> medium
    # -> release
    # -> release_group
    # -> release_group_primary_type - to filter for IN (Album, Single, EP)
    # -> release_status - to filter for = Official
    
    stmt = (
        select(artist_target.id, artist_collab.id)
        # --- target artist lookup ---
        .select_from(artist_target)
        .where(artist_target.id.in_(artist_ids))
        .join(acn_target,  acn_target.artist_id == artist_target.id)
        # --- connector ---
        .join(ArtistCredit,     ArtistCredit.id == acn_target.artist_credit_id)
        # --- collab artist lookup ---
        .join(acn_collab,             acn_collab.artist_credit_id == ArtistCredit.id)
        .join(artist_collab,                     artist_collab.id == acn_collab.artist_id)
        .where(artist_collab.id != artist_target.id)
        # --- to allow filtering ---
        .join(Track,     Track.artist_credit_id == ArtistCredit.id)
    )

    stmt = filter_tracks_for_official(stmt)
    
    artist_collabs_list = db.session.execute(stmt).all()

    adj = defaultdict(set)
    for i in artist_collabs_list:
        adj[i[0]].add(i[1])

    return adj


def get_artist_name_from_list(line_number):
    with open(Config.SCRAPED_NAMES_FILE_PATH) as f:
        for i, line in enumerate(f):
            if i == line_number - 1:
                return line[:-1]
    return None


def get_artist_spotify_id(artist):
    # URL
    # -> l_artist_url
    # -> (filters)
    # -> artist, id = artist(passed in parameter).id
    
    # filters:
    # -> link
    # -> link_type = 'free streaming'
    
    stmt = (
        select(URL)
        .join(LinkArtistURL, LinkArtistURL.url_id == URL.id)
        .join(Link, Link.id == LinkArtistURL.link_id)
        .join(LinkType, LinkType.id == Link.link_type_id)
        .where(LinkType.name == 'free streaming')
        .join(Artist)
        .where(Artist.id == artist.id)
    )

    urls = db.session.execute(stmt).scalars().all()

    # TODO: will return first spotify link but this might not be ideal
    #       e.g., Kanye has 3 spotify links - one for Kanye West account, one
    #       for Ye account, and one for DONDA account
    for url in urls:
        if 'spotify' in url.url:
            r = re.findall(r'artist\/([^\/]*)', url.url)
            return r[0]

    return None

# filter tracks to try remove illegitimate musicbrainz entries
def filter_tracks_for_official(stmt):
    # (track filters for officialness)
    # -> medium
    # -> release
    # -> release_group
    # -> release_group_primary_type - to filter for IN (Album, Single, EP)
    # -> release_status - to filter for = Official

    valid_release_primary_types = ['Album', 'Single', 'EP']
    valid_release_secondary_types = ['Soundtrack', 'Mixtape/Street', 'Demo']
    official_status = 'Official'

    new_stmt = (
        stmt
        .join(Medium,                 Medium.id == Track.medium_id)
        .join(Release,               Release.id == Medium.release_id)
        .join(ReleaseGroup,     ReleaseGroup.id == Release.release_group_id)
        .join(ReleaseGroupPrimaryType, ReleaseGroupPrimaryType.id == ReleaseGroup.type_id)
        .where(ReleaseGroupPrimaryType.name.in_(valid_release_primary_types))
        .join(ReleaseStatus,                     ReleaseStatus.id == Release.status_id)
        .where(ReleaseStatus.name == official_status)
        .join(ReleaseGroupSecondaryTypeJoin, ReleaseGroupSecondaryTypeJoin.release_group_id == ReleaseGroup.id, isouter=True)
        .join(ReleaseGroupSecondaryType, ReleaseGroupSecondaryType.id == ReleaseGroupSecondaryTypeJoin.secondary_type_id, isouter=True)
        .where(
            (ReleaseGroupSecondaryType.name.in_(valid_release_secondary_types))
        # do not exclude albums without a secondary type
            | (ReleaseGroupSecondaryType.name == None))
    )

    return new_stmt


def find_collaborated_tracks(path):
    acn_target = aliased(ArtistCreditName)
    acn_collab = aliased(ArtistCreditName)
    artist_target = aliased(Artist)
    artist_collab = aliased(Artist)
    
    # track
    # -> (track filters for containing both artists)
    # -> (track filters for officialness)
    
    
    # (track filters for containing both artists)
    # -> artist_credit
    # -> artist_credit_name, target
    # -> artist, target -> id == artist_id
    # -> artist_credit_name, collab
    # -> artist, collab -> id == collab_id

    path_tracks = []
    path_spotify_tracks = []
    for artist, collab in zip(path, path[1:]):
        stmt = (
            select(Track)
            # --- target artist lookup ---
            .select_from(artist_target)
            .where(artist_target.id == artist.id)
            .join(acn_target,  acn_target.artist_id == artist_target.id)
            # --- connectors ---
            .join(ArtistCredit,     ArtistCredit.id == acn_target.artist_credit_id)
            # --- collab artist lookup ---
            .join(acn_collab,             acn_collab.artist_credit_id == ArtistCredit.id)
            .join(artist_collab,                     artist_collab.id == acn_collab.artist_id)
            .where(artist_collab.id == collab.id)
            # --- to get tracks ---
            .join(Track,     Track.artist_credit_id == ArtistCredit.id)
        )

        stmt = filter_tracks_for_official(stmt)
        
        tracks = db.session.execute(stmt).scalars().all()

        assert len(tracks) > 0

        for track in tracks:
            spotify_track = helpers.search_spotify_for_track(track)
            if spotify_track:
                path_tracks.append(track)
                path_spotify_tracks.append(spotify_track)
                break
        else:
            assert 0 # no tracks in MusicBrainz DB could be found on Spotify!
            path_tracks.append(track)
            path_spotify_tracks.append(None)

    
    return (path_tracks, path_spotify_tracks)

def get_track_artists(track):
    stmt = (
        select(Artist)
        .select_from(Track)
        .where(Track.id == track.id)
        .join(ArtistCredit, ArtistCredit.id == Track.artist_credit_id)
        .join(ArtistCreditName, ArtistCreditName.artist_credit_id == ArtistCredit.id)
        .join(Artist, Artist.id == ArtistCreditName.artist_id)
    )

    return db.session.execute(stmt).scalars().all()
