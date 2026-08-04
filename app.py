from collections import defaultdict

from config import Config

from time import time

from flask import Flask

from db import db

import db_operations

from flask import render_template, request

import adjacency_list

import find_path

valid_track_ids = []

adj_list = defaultdict(set)

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
def findpath():
    if request.method == 'GET':
        return render_template('findpath.html')

    # POST:
    name_start = request.form.get('start')
    name_end = request.form.get('end')

    artist_start = db_operations.get_db_artist_by_name(name_start)
    artist_end = db_operations.get_db_artist_by_name(name_end)

    if not artist_start or not artist_end:
        return render_template('findpath.html', error='Invalid artists start/end artist')


    path_artists = find_path.find_artist_link(adj_list, artist_start.id, artist_end.id)
    if path_artists:
        s = ''
        path_recordings = find_path.find_collaborated_recordings(path_artists)
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




with app.app_context():
    artist = db_operations.get_db_artist_by_name('Ye')

    tst = db_operations.get_artist_spotify_id(artist)
        
    # adj_list = adjacency_list.init_adjacency_list(count)

    #Config.SPOTIFY_ACCESS_TOKEN = helpers.get_spotify_access_token()
    #Config.AUTHORISATION_HEADER['Authorization'] = f'Bearer {Config.SPOTIFY_ACCESS_TOKEN}'
