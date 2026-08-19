-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^

BEGIN;
    
SET maintenance_work_mem = '1GB';
    
CREATE INDEX release_idx_musicbrainz_collate ON release (name COLLATE musicbrainz.musicbrainz);
CREATE INDEX release_group_idx_musicbrainz_collate ON release_group (name COLLATE musicbrainz.musicbrainz);
CREATE INDEX artist_idx_musicbrainz_collate ON artist (name COLLATE musicbrainz.musicbrainz);
CREATE INDEX artist_credit_idx_musicbrainz_collate ON artist_credit (name COLLATE musicbrainz.musicbrainz);
CREATE INDEX artist_credit_name_idx_musicbrainz_collate ON artist_credit_name (name COLLATE musicbrainz.musicbrainz);
CREATE INDEX recording_idx_musicbrainz_collate ON recording (name COLLATE musicbrainz.musicbrainz);

SET maintenance_work_mem = '64MB';

COMMIT;
