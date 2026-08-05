from time import sleep
import requests
from config import Config

import db_operations

from rapidfuzz import fuzz, utils

import re

# returns access token as dictionary
def get_spotify_access_token():
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {
        'grant_type': 'client_credentials',
        'client_id': str(Config.SPOTIFY_CLIENT_ID),
        'client_secret': str(Config.SPOTIFY_CLIENT_SECRET)
    }

    r = requests.post(url, headers=headers, data = params)
    
    return r.json()['access_token']

class ForTesting:
    qs = {}

# returns dictionary of search response from Spotify
# returns None on error
def search_spotify(url, params=None, max_retries=5):
    for attempt in range(max_retries):
        s = '---->querying: ' + url
        if params:
            for k,v in params.items():
                s = s + ', ' + str(k) + ': ' + str(v)
        
        debug_url = url
        if params:
            debug_url = debug_url + str(params.get('q', '')) + str(params.get('offset', ''))

        if ForTesting.qs.get(debug_url, ''):
            print('Re-querying same url!')
        else:
            ForTesting.qs[url] = 1

        print(s)

        sleep(.2) # wait per request to avoid rate-limiting

        if params:
            r = requests.get(url, params=params, headers=Config.AUTHORISATION_HEADER)
        else:
            r = requests.get(url, headers=Config.AUTHORISATION_HEADER)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            # TODO: probably not ideal, will hang here if rate limited
            if r.status_code == 429: # rate limited, call function again after delay
                retry_after_sec = int(r.headers['retry-after'])

                if not retry_after_sec:
                    retry_after_sec = 2 ** attempt # exponential backoff as backup
                
                sleep(retry_after_sec)
                
                continue
            else:
                print(r.status_code, ': ', r.reason)
                return None

        response = r.json()

        return response


def search_spotify_for_track(track):
    artists = db_operations.get_track_artists(track)
    
    params = {
        'type': 'track',
        'q': f'track:{track.name}', #added below
        'limit': 10
    }

    assert len(artists) > 0
    
    params['q'] = params['q'] + ' artist:'
    for artist in artists:
        params['q'] = params['q'] + artist.name + ' '

    params['q'] = params['q'][:-1] #drop extraneous space at end, just in case


    # TODO: improve checking that its the same song
    # could use ISRC (requires import of new 'ISRC' table into DB)

    #check duration is similar or name is same
    TRACK_LENGTH_TOLERANCE_MS = 2000
    NAME_RATIO_MIN = 90
    def track_check_func(result):
        if track.length:
            return abs(result['duration_ms'] - track.length) < TRACK_LENGTH_TOLERANCE_MS
        else:
            return track_name_similarity_ratio(result['name'], track.name) > NAME_RATIO_MIN

    track = search_spotify_until_found(params, track_check_func, max_pages=2)

    if track:
        return track


def normalise_track_title(title):
    title = title.lower()
    title = re.sub(
    r'[\(\[](?!(?:[^\)\]]*\b(?:mix|live|edit)\b))[^\)\]]*[\)\]]',
    '',
    title,
    flags=re.IGNORECASE
    )

    return title


def track_name_similarity_ratio(title1, title2):
    title1 = normalise_track_title(title1)
    title2 = normalise_track_title(title2)
    
    return fuzz.WRatio(title1, title2, processor=utils.default_process)


def search_spotify_until_found(params, check_func, max_retries=5, max_pages=5):
    # one (and only one) type to search for must be specified
    assert len(str(params['type']).split(',')) == 1

    obj_type = params['type']

    for _ in range(max_pages):
        results = search_spotify(Config.SPOTIFY_SEARCH_URL, params, max_retries)
        for result in results[f'{obj_type}s']['items']:
            if check_func(result):
                return result

        # increase offset for next search
        params['offset'] = int(params.get('offset', 0)) + int(params.get('limit', 5))


def search_spotify_until_found_artist(searched_name, url, params=None, max_retries=5, max_pages=5):
    for _ in range(max_pages):
        params['offset'] = int(params.get('offset', 0)) + int(params.get('limit', 5))
        results = search_spotify(url, params, max_retries)
        for result in results['artists']['items']:
            if result['name'] == searched_name:
                return result

            
def get_spotify_artist_by_id(artist_id, max_retries=5):
    artist_url = f'{Config.SPOTIFY_ARTISTS_URL}/{artist_id}'
    
    return search_spotify(artist_url, max_retries=max_retries)


def get_albums_of_artist(session, artist_id):
    artist = session.execute(select(Artists).filter_by(id=artist_id)).scalar_one_or_none()
    
    # no artist exists at that id
    if not artist:
        return None
    
    search_params = {
        'include_groups': 'album,single',
        'limit': '10'
    }
    
    #NOTE: Uncomment this and delete the two json lines below
    response = helpers.search_spotify(f'{Config.SPOTIFY_ARTISTS_URL}/{artist.spotify_id}/albums', search_params)
    
    #f = open('testcase.json')
    #response = json.load(f)

    while True:
        for response_album in response['items']:
            # search database for album with this ID, skip if so
            #   (i.e., do not add to DB if it's already in these)
            stmt = select(Albums).filter_by(spotify_id=response_album['id'])
            db_search = session.execute(stmt).scalar_one_or_none()

            if db_search:
                continue

            # album is not in DB yet, prepare to add if it ends up having tracks
            #   with collaborators
            album = Albums(
                spotify_id= response_album['id'],
                album_name= response_album['name'],
            )
            
            # TODO: review if these two lines are needed for tracks.album_id to work
            # session.add(album)
            # session.flush() # to ensure 
            
            # get tracks of album, and check whether there are any tracks with
            #   collaborators
            if not get_tracks_of_album_with_collabs(session, album):
                #session.rollback()
                # album DOESN'T have collaboration tracks, just keep its name
                #   so it's not re-scraped
                session.commit()
                continue
            
            # album has collaborators:

            # append each artist of album as related Artist class
            # will download a new Artists class from Spotify API if necessary
            for response_album_artist in response_album['artists']:
                album_artist = search_artist(session, spotify_id=response_album_artist['id'])
                if not album_artist:
                    print(f'error: could not find artist {album_artist} in neither db nor on Spotify API!')
                
                album.artists.append(album_artist)
                
            # need to commit here so future rollbacks don't undo this album
            session.add(album)
            session.commit()
        
        # if there are more pages of albums from this artist, get them as well
        if not response['next']:
            break

        response = helpers.search_spotify(response['next'])

    #stmt = insert(Albums).on_conflict_do_nothing(
    #    index_elements=[Albums.spotify_id]
    #    ) 
    #session.execute(stmt, albums_to_add)
