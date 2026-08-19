-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^
BEGIN;
    
SET maintenance_work_mem = '1GB';

CREATE UNIQUE INDEX artist_idx_gid ON artist (gid);
CREATE INDEX artist_idx_name ON artist (name);
CREATE INDEX artist_idx_sort_name ON artist (sort_name);
CREATE INDEX artist_idx_area ON artist (area);
CREATE INDEX artist_idx_begin_area ON artist (begin_area);
CREATE INDEX artist_idx_end_area ON artist (end_area);
CREATE UNIQUE INDEX artist_idx_null_comment ON artist (name) WHERE comment IS NULL;
CREATE UNIQUE INDEX artist_idx_uniq_name_comment ON artist (name, comment) WHERE comment IS NOT NULL;

CREATE INDEX artist_alias_idx_artist ON artist_alias (artist);
CREATE UNIQUE INDEX artist_alias_idx_primary ON artist_alias (artist, locale) WHERE primary_for_locale = TRUE AND locale IS NOT NULL;

CREATE UNIQUE INDEX artist_credit_idx_gid ON artist_credit (gid);

CREATE INDEX artist_credit_name_idx_artist ON artist_credit_name (artist);
CREATE INDEX artist_credit_name_idx_join_phrase ON artist_credit_name (join_phrase);

-- Entity indexes

CREATE UNIQUE INDEX l_artist_url_idx_uniq ON l_artist_url (entity0, entity1, link, link_order);
CREATE INDEX l_artist_url_idx_entity1 ON l_artist_url (entity1);

CREATE UNIQUE INDEX link_type_idx_gid ON link_type (gid);

CREATE INDEX link_idx_type_attr ON link (link_type, attribute_count);

CREATE UNIQUE INDEX medium_idx_gid ON medium (gid);

CREATE UNIQUE INDEX recording_idx_gid ON recording (gid);
CREATE INDEX recording_idx_name ON recording (name);
CREATE INDEX recording_idx_artist_credit ON recording (artist_credit);

CREATE UNIQUE INDEX release_idx_gid ON release (gid);
CREATE INDEX release_idx_name ON release (name);
CREATE INDEX release_idx_release_group ON release (release_group);
CREATE INDEX release_idx_artist_credit ON release (artist_credit);

CREATE INDEX release_label_idx_release ON release_label (release);

CREATE UNIQUE INDEX release_status_idx_gid ON release_status (gid);

CREATE UNIQUE INDEX release_group_idx_gid ON release_group (gid);
CREATE INDEX release_group_idx_name ON release_group (name);
CREATE INDEX release_group_idx_artist_credit ON release_group (artist_credit);

CREATE UNIQUE INDEX release_group_primary_type_idx_gid ON release_group_primary_type (gid);
CREATE UNIQUE INDEX release_group_secondary_type_idx_gid ON release_group_secondary_type (gid);

CREATE UNIQUE INDEX track_idx_gid ON track (gid);

CREATE INDEX track_idx_recording ON track (recording);
CREATE INDEX track_idx_artist_credit ON track (artist_credit);

CREATE UNIQUE INDEX url_idx_gid ON url (gid);
CREATE UNIQUE INDEX url_idx_url ON url (url);

-- indexes for /ws/js/check_duplicates
CREATE INDEX artist_idx_lower_unaccent_name_comment ON artist (lower(musicbrainz_unaccent(name)), lower(musicbrainz_unaccent(comment)));
CREATE INDEX artist_alias_idx_lower_unaccent_name ON artist_alias (lower(musicbrainz_unaccent(name)));

SET maintenance_work_mem = '64MB';

COMMIT;

-- vi: set ts=4 sw=4 et :
