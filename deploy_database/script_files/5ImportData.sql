-- \set ON_ERROR_STOP 1
BEGIN;

COPY musicbrainz.artist FROM ':mbdump_location/mbdump/mbdump/artist' WITH (FORMAT text);
COPY musicbrainz.artist_alias FROM ':mbdump_location/mbdump/mbdump/artist_alias' WITH (FORMAT text);
COPY musicbrainz.recording FROM ':mbdump_location/mbdump/mbdump/recording' WITH (FORMAT text);
COPY musicbrainz.link_type FROM ':mbdump_location/mbdump/mbdump/link_type' WITH (FORMAT text);
COPY musicbrainz.link FROM ':mbdump_location/mbdump/mbdump/link' WITH (FORMAT text);
COPY musicbrainz.artist_credit FROM ':mbdump_location/mbdump/mbdump/artist_credit' WITH (FORMAT text);
COPY musicbrainz.artist_credit_name FROM ':mbdump_location/mbdump/mbdump/artist_credit_name' WITH (FORMAT text);
COPY musicbrainz.release_status FROM ':mbdump_location/mbdump/mbdump/release_status' WITH (FORMAT text);
COPY musicbrainz.release_group FROM ':mbdump_location/mbdump/mbdump/release_group' WITH (FORMAT text);
COPY musicbrainz.release_group_primary_type FROM ':mbdump_location/mbdump/mbdump/release_group_primary_type' WITH (FORMAT text);
COPY musicbrainz.track FROM ':mbdump_location/mbdump/mbdump/track' WITH (FORMAT text);
COPY musicbrainz.medium FROM ':mbdump_location/mbdump/mbdump/medium' WITH (FORMAT text);
COPY musicbrainz.release FROM ':mbdump_location/mbdump/mbdump/release' WITH (FORMAT text);
COPY musicbrainz.release_group_secondary_type_join FROM ':mbdump_location/mbdump/mbdump/release_group_secondary_type_join' WITH (FORMAT text);
COPY musicbrainz.release_group_secondary_type FROM ':mbdump_location/mbdump/mbdump/release_group_secondary_type' WITH (FORMAT text);
COPY musicbrainz.url FROM ':mbdump_location/mbdump/mbdump/url' WITH (FORMAT text);
COPY musicbrainz.l_artist_url FROM ':mbdump_location/mbdump/mbdump/l_artist_url' WITH (FORMAT text);

COMMIT;
