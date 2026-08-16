import re

# from sqlalchemy.dialects.postgresql import insert
from collections import defaultdict

# from time import time
# import sqlalchemy.exc
from sqlalchemy import func, select, union
from sqlalchemy.orm import aliased

from config import Config
from db import db
from globals import Globals
from models import (
    URL,
    Artist,
    ArtistAlias,
    ArtistCredit,
    ArtistCreditName,
    Link,
    LinkArtistURL,
    LinkType,
    Medium,
    Recording,
    Release,
    ReleaseGroup,
    ReleaseGroupPrimaryType,
    ReleaseGroupSecondaryType,
    ReleaseGroupSecondaryTypeJoin,
    ReleaseLabel,
    ReleaseStatus,
    Track,
)

excluded_join_phrases = None


def get_artist_name_from_list(line_number):
    with open(Config.ARTIST_NAMES_FILE_PATH) as f:
        for i, line in enumerate(f):
            if i == line_number - 1:
                return line[:-1]
    return None


def get_db_artist_by_id(id):
    stmt = select(Artist).where(Artist.id == id)

    search_result = db.session.execute(stmt).scalar_one_or_none()

    return search_result


# returns None if no artist could be found
def get_db_artist_by_name(name):
    # NOTE: searching for hits on Artist.name, and only searching for hits on
    #       ArtistAlias.name could give incorrect results (see example below)
    #       however, it's done this way because it's A LOT faster than
    #       doing a JOIN and searching for both at the same time

    #       e.g.: Kanye West doesn't exist in MBDB, found instead under 'Ye'.
    #       if there's a different 'Kanye West' (not Ye) in MBDB, it would
    #       grab them instead as the artist
    # search by artist name
    stmt = select(Artist).where(
        func.lower(func.musicbrainz_unaccent(Artist.name))
        == func.lower(func.musicbrainz_unaccent(name))
    )

    search_result = db.session.execute(stmt).scalars().all()

    # if a direct name search doesn't find anything, search for artist aliases
    # as well
    if not search_result:
        sub_stmt = (
            select(ArtistAlias.artist_id)
            # using lower(musicbrainz_unaccent(name)) index on ArtistAlias
            .where(
                func.lower(func.musicbrainz_unaccent(ArtistAlias.name))
                == func.lower(func.musicbrainz_unaccent(name))
            )
        )
        stmt = select(Artist).where(Artist.id.in_(sub_stmt))

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

    # multiple artists still in running. try searching for which of these has a
    # linked Spotify page
    has_spotify_page = []
    for artist_result in possible_artists:
        if get_artist_spotify_id(artist_result):
            has_spotify_page.append(artist_result)

    if len(has_spotify_page) == 1:
        return has_spotify_page[0]
    # if there are multiple artists with a begin year, assume one I'm searching
    #   for is within that list, only continue filtering through those
    elif len(has_spotify_page) > 1:
        possible_artists = has_spotify_page

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
    # if there are multiple artists with a begin month, assume one I'm searching
    #   for is within that list, only continue filtering through those
    elif len(has_begin_month) > 1:
        possible_artists = has_begin_month

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
    sub_sub_stmt = select(ArtistCreditName.artist_credit_id).where(
        ArtistCreditName.artist == artist
    )

    # these are all artist_credit rows with my artist that have collaborators
    sub_stmt = (
        select(ArtistCredit.id)
        .where(ArtistCredit.id.in_(sub_sub_stmt))
        .where(ArtistCredit.artist_count > 1)
    )

    stmt = select(Recording).where(Recording.artist_credit_id.in_(sub_stmt))

    return db.session.execute(stmt).scalars().all()


# uses 'track' database table to get all tracks with collaborators where artist
# is credited, adding them to a list. Each list entry should have the
# collaborator id and recording id. If there is at least one track in that list,
# create entry in adjacency_list
#   -> {id_of artist in artist table: adjacent nodes list}
def get_artist_collaborators(artist_ids):
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

    acn_target = aliased(ArtistCreditName)
    acn_collab = aliased(ArtistCreditName)
    artist_target = aliased(Artist)
    artist_collab = aliased(Artist)

    stmt = (
        select(artist_target.id, artist_collab.id)
        # --- target artist lookup ---
        .select_from(artist_target)
        .where(artist_target.id.in_(artist_ids))
        .join(acn_target, acn_target.artist_id == artist_target.id)
        # --- connector ---
        .join(ArtistCredit, ArtistCredit.id == acn_target.artist_credit_id)
        # --- collab artist lookup ---
        .join(acn_collab, acn_collab.artist_credit_id == ArtistCredit.id)
        .join(artist_collab, artist_collab.id == acn_collab.artist_id)
        .where(artist_collab.id != artist_target.id)
        # --- to allow filtering ---
        .join(Track, Track.artist_credit_id == ArtistCredit.id)
    )

    stmt = apply_track_filters(stmt, acn_target, acn_collab)

    artist_collabs_list = db.session.execute(stmt).all()

    adj = defaultdict(set)
    for i in artist_collabs_list:
        adj[i[0]].add(i[1])
        adj[i[1]].add(i[0])

    return adj


def get_artist_spotify_id(artist: Artist) -> str | None:
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
        .where(LinkType.name == "free streaming")
        .join(Artist)
        .where(Artist.id == artist.id)
    )

    urls = db.session.execute(stmt).scalars().all()

    # TODO: will return first spotify link but this might not be ideal
    #       e.g., Kanye has 3 spotify links - one for Kanye West account, one
    #       for Ye account, and one for DONDA account
    for url in urls:
        if "spotify" in url.url and "artist" in url.url:
            r = re.findall(r"artist\/([^\/]*)", url.url)
            return r[0]

    return None


def fetch_excluded_join_phrases():
    global excluded_join_phrases
    stmt = (
        select(ArtistCreditName.join_phrase)
        .distinct()
        .where(
            ArtistCreditName.join_phrase.like(
                "%" + Config.EXCLUDED_JOIN_PHRASES_LIKE + "%"
            )
        )
    )

    excluded_join_phrases = db.session.execute(stmt).scalars().all()


def apply_track_filters(stmt, acn_target, acn_collab):
    stmt = filter_tracks_for_official(stmt)
    stmt = filter_tracks_by_artist_credit_name(stmt, acn_target, acn_collab)

    return stmt


def filter_tracks_by_artist_credit_name(stmt, acn_target, acn_collab):
    if not excluded_join_phrases:
        fetch_excluded_join_phrases()

    return stmt.where(
        acn_target.join_phrase.not_in(excluded_join_phrases)
    ).where(acn_collab.join_phrase.not_in(excluded_join_phrases))


# filter tracks to try remove illegitimate musicbrainz entries
def filter_tracks_for_official(stmt):
    # (track filters for officialness)
    # -> medium
    # -> release
    # -> release_group
    # -> release_group_primary_type - to filter for IN (Album, Single, EP)
    # -> release_status - to filter for = Official

    return (
        stmt.join(Medium, Medium.id == Track.medium_id)
        .join(Release, Release.id == Medium.release_id)
        .join(ReleaseGroup, ReleaseGroup.id == Release.release_group_id)
        .join(
            ReleaseGroupPrimaryType,
            ReleaseGroupPrimaryType.id == ReleaseGroup.type_id,
        )
        .where(
            ReleaseGroupPrimaryType.name.in_(Config.VALID_RELEASE_PRIMARY_TYPES)
        )
        .join(ReleaseStatus, ReleaseStatus.id == Release.status_id)
        .where(ReleaseStatus.name == Config.OFFICIAL_STATUS)
        .join(
            ReleaseGroupSecondaryTypeJoin,
            ReleaseGroupSecondaryTypeJoin.release_group_id == ReleaseGroup.id,
            isouter=True,
        )
        .join(
            ReleaseGroupSecondaryType,
            ReleaseGroupSecondaryType.id
            == ReleaseGroupSecondaryTypeJoin.secondary_type_id,
            isouter=True,
        )
        .where(
            (
                ReleaseGroupSecondaryType.name.in_(
                    Config.VALID_RELEASE_SECONDARY_TYPES
                )
            )
            # do not exclude albums without a secondary type
            | (ReleaseGroupSecondaryType.name == None)
        )
        .join(ReleaseLabel, ReleaseLabel.release_id == Release.id)
        .where(ReleaseLabel.label_id != Config.NO_LABEL_ID)
    )


# returns MusicBrainz database Track objects that have both artists credited
def fetch_collaborated_tracks(artist_id1: int, artist_id2: int) -> list[Track]:
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

    stmt = (
        select(Track)
        # --- target artist lookup ---
        .select_from(artist_target)
        .where(artist_target.id == artist_id1)
        .join(acn_target, acn_target.artist_id == artist_target.id)
        # --- connectors ---
        .join(ArtistCredit, ArtistCredit.id == acn_target.artist_credit_id)
        # --- collab artist lookup ---
        .join(acn_collab, acn_collab.artist_credit_id == ArtistCredit.id)
        .join(artist_collab, artist_collab.id == acn_collab.artist_id)
        .where(artist_collab.id == artist_id2)
        # --- to get tracks ---
        .join(Track, Track.artist_credit_id == ArtistCredit.id)
    )

    stmt = apply_track_filters(stmt, acn_target, acn_collab)

    tracks = db.session.execute(stmt).scalars().all()

    assert len(tracks) > 0

    return tracks


def get_track_artists(track):
    stmt = (
        select(Artist)
        .select_from(Track)
        .where(Track.id == track.id)
        .join(ArtistCredit, ArtistCredit.id == Track.artist_credit_id)
        .join(
            ArtistCreditName,
            ArtistCreditName.artist_credit_id == ArtistCredit.id,
        )
        .join(Artist, Artist.id == ArtistCreditName.artist_id)
    )

    return db.session.execute(stmt).scalars().all()


# returns None if no artist could be found
def fetch_artist_typeahead(query: str) -> list[dict]:
    possible_artists = []

    artist_search_stmt = (
        select(Artist.id, Artist.name, Artist.comment)
        .where(
            func.lower(func.musicbrainz_unaccent(Artist.name)).startswith(
                func.lower(func.musicbrainz_unaccent(query))
            )
        )
        .where(Artist.id.in_(list(Globals.adj_list.keys())))
        .limit(Config.TYPEAHEAD_LIMIT)
    )

    alias_search_stmt = (
        select(
            Artist.id,
            ArtistAlias.name,
            Artist.comment,
        )
        .join(Artist, Artist.id == ArtistAlias.artist_id)
        .where(
            func.lower(func.musicbrainz_unaccent(ArtistAlias.name)).startswith(
                func.lower(func.musicbrainz_unaccent(query))
            )
        )
        .where(Artist.id.in_(list(Globals.adj_list.keys())))
        .distinct(Artist.id)
        .limit(Config.TYPEAHEAD_LIMIT)
    )

    stmt = union(artist_search_stmt, alias_search_stmt).limit(
        Config.TYPEAHEAD_LIMIT
    )

    results = db.session.execute(stmt).all()

    for result in results:
        possible_artists.append(
            {
                "mbid": result[0],
                "name": result[1],
            }
        )

    return possible_artists


def fetch_track_by_id(id: int) -> Track:
    stmt = select(Track).where(Track.id == id)
    return db.session.execute(stmt).scalar_one_or_none()
