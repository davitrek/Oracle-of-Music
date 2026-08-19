-- Automatically generated, do not edit.
-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^

ALTER TABLE artist_alias
   ADD CONSTRAINT artist_alias_fk_artist
   FOREIGN KEY (artist)
   REFERENCES artist(id);

ALTER TABLE artist_credit_name
   ADD CONSTRAINT artist_credit_name_fk_artist_credit
   FOREIGN KEY (artist_credit)
   REFERENCES artist_credit(id)
   ON DELETE CASCADE;

ALTER TABLE artist_credit_name
   ADD CONSTRAINT artist_credit_name_fk_artist
   FOREIGN KEY (artist)
   REFERENCES artist(id)
   ON DELETE CASCADE;

ALTER TABLE l_artist_url
   ADD CONSTRAINT l_artist_url_fk_link
   FOREIGN KEY (link)
   REFERENCES link(id);

ALTER TABLE l_artist_url
   ADD CONSTRAINT l_artist_url_fk_entity0
   FOREIGN KEY (entity0)
   REFERENCES artist(id);

ALTER TABLE l_artist_url
   ADD CONSTRAINT l_artist_url_fk_entity1
   FOREIGN KEY (entity1)
   REFERENCES url(id);

ALTER TABLE link
   ADD CONSTRAINT link_fk_link_type
   FOREIGN KEY (link_type)
   REFERENCES link_type(id);

ALTER TABLE link_type
   ADD CONSTRAINT link_type_fk_parent
   FOREIGN KEY (parent)
   REFERENCES link_type(id);

ALTER TABLE medium
   ADD CONSTRAINT medium_fk_release
   FOREIGN KEY (release)
   REFERENCES release(id);

ALTER TABLE recording
   ADD CONSTRAINT recording_fk_artist_credit
   FOREIGN KEY (artist_credit)
   REFERENCES artist_credit(id);

ALTER TABLE release
   ADD CONSTRAINT release_fk_artist_credit
   FOREIGN KEY (artist_credit)
   REFERENCES artist_credit(id);

ALTER TABLE release
   ADD CONSTRAINT release_fk_release_group
   FOREIGN KEY (release_group)
   REFERENCES release_group(id);

ALTER TABLE release
   ADD CONSTRAINT release_fk_status
   FOREIGN KEY (status)
   REFERENCES release_status(id);

ALTER TABLE release_group
   ADD CONSTRAINT release_group_fk_artist_credit
   FOREIGN KEY (artist_credit)
   REFERENCES artist_credit(id);

ALTER TABLE release_group
   ADD CONSTRAINT release_group_fk_type
   FOREIGN KEY (type)
   REFERENCES release_group_primary_type(id);

ALTER TABLE release_group_primary_type
   ADD CONSTRAINT release_group_primary_type_fk_parent
   FOREIGN KEY (parent)
   REFERENCES release_group_primary_type(id);

ALTER TABLE release_group_secondary_type
   ADD CONSTRAINT release_group_secondary_type_fk_parent
   FOREIGN KEY (parent)
   REFERENCES release_group_secondary_type(id);

ALTER TABLE release_group_secondary_type_join
   ADD CONSTRAINT release_group_secondary_type_join_fk_release_group
   FOREIGN KEY (release_group)
   REFERENCES release_group(id);

ALTER TABLE release_group_secondary_type_join
   ADD CONSTRAINT release_group_secondary_type_join_fk_secondary_type
   FOREIGN KEY (secondary_type)
   REFERENCES release_group_secondary_type(id);

ALTER TABLE release_label
   ADD CONSTRAINT release_label_fk_release
   FOREIGN KEY (release)
   REFERENCES release(id);

ALTER TABLE release_status
   ADD CONSTRAINT release_status_fk_parent
   FOREIGN KEY (parent)
   REFERENCES release_status(id);

ALTER TABLE track
   ADD CONSTRAINT track_fk_recording
   FOREIGN KEY (recording)
   REFERENCES recording(id);

ALTER TABLE track
   ADD CONSTRAINT track_fk_medium
   FOREIGN KEY (medium)
   REFERENCES medium(id);

ALTER TABLE track
   ADD CONSTRAINT track_fk_artist_credit
   FOREIGN KEY (artist_credit)
   REFERENCES artist_credit(id);
