-- \set ON_ERROR_STOP 1
BEGIN;
    
\set artist_path :mbdump_location/mbdump/mbdump/artist
\set artist_alias_path :mbdump_location/mbdump/mbdump/artist_alias
\set recording_path :mbdump_location/mbdump/mbdump/recording
\set link_type_path :mbdump_location/mbdump/mbdump/link_type
\set link_path :mbdump_location/mbdump/mbdump/link
\set artist_credit_path :mbdump_location/mbdump/mbdump/artist_credit
\set artist_credit_name_path :mbdump_location/mbdump/mbdump/artist_credit_name
\set release_status_path :mbdump_location/mbdump/mbdump/release_status
\set release_group_path :mbdump_location/mbdump/mbdump/release_group
\set release_group_primary_type_path :mbdump_location/mbdump/mbdump/release_group_primary_type
\set track_path :mbdump_location/mbdump/mbdump/track
\set medium_path :mbdump_location/mbdump/mbdump/medium
\set release_path :mbdump_location/mbdump/mbdump/release
\set release_group_secondary_type_join_path :mbdump_location/mbdump/mbdump/release_group_secondary_type_join
\set release_group_secondary_type_path :mbdump_location/mbdump/mbdump/release_group_secondary_type
\set url_path :mbdump_location/mbdump/mbdump/url
\set l_artist_url_path :mbdump_location/mbdump/mbdump/l_artist_url
\set release_label_path :mbdump_location/mbdump/mbdump/release_label

COPY musicbrainz.artist FROM :'artist_path' WITH (FORMAT text);
COPY musicbrainz.artist_alias FROM :'artist_alias_path' WITH (FORMAT text);
COPY musicbrainz.recording FROM :'recording_path' WITH (FORMAT text);
COPY musicbrainz.link_type FROM :'link_type_path' WITH (FORMAT text);
COPY musicbrainz.link FROM :'link_path' WITH (FORMAT text);
COPY musicbrainz.artist_credit FROM :'artist_credit_path' WITH (FORMAT text);
COPY musicbrainz.artist_credit_name FROM :'artist_credit_name_path' WITH (FORMAT text);
COPY musicbrainz.release_status FROM :'release_status_path' WITH (FORMAT text);
COPY musicbrainz.release_group FROM :'release_group_path' WITH (FORMAT text);
COPY musicbrainz.release_group_primary_type FROM :'release_group_primary_type_path' WITH (FORMAT text);
COPY musicbrainz.track FROM :'track_path' WITH (FORMAT text);
COPY musicbrainz.medium FROM :'medium_path' WITH (FORMAT text);
COPY musicbrainz.release FROM :'release_path' WITH (FORMAT text);
COPY musicbrainz.release_group_secondary_type_join FROM :'release_group_secondary_type_join_path' WITH (FORMAT text);
COPY musicbrainz.release_group_secondary_type FROM :'release_group_secondary_type_path' WITH (FORMAT text);
COPY musicbrainz.url FROM :'url_path' WITH (FORMAT text);
COPY musicbrainz.l_artist_url FROM :'l_artist_url_path' WITH (FORMAT text);
COPY musicbrainz.release_label FROM :'release_label_path' WITH (FORMAT text);

COMMIT;
