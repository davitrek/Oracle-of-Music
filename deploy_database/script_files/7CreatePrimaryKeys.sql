-- Automatically generated, do not edit.
-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^

ALTER TABLE artist ADD CONSTRAINT artist_pkey PRIMARY KEY (id);
ALTER TABLE artist_alias ADD CONSTRAINT artist_alias_pkey PRIMARY KEY (id);
ALTER TABLE artist_credit ADD CONSTRAINT artist_credit_pkey PRIMARY KEY (id);
ALTER TABLE artist_credit_name ADD CONSTRAINT artist_credit_name_pkey PRIMARY KEY (artist_credit, position);
ALTER TABLE link ADD CONSTRAINT link_pkey PRIMARY KEY (id);
ALTER TABLE link_type ADD CONSTRAINT link_type_pkey PRIMARY KEY (id);
ALTER TABLE medium ADD CONSTRAINT medium_pkey PRIMARY KEY (id);
ALTER TABLE recording ADD CONSTRAINT recording_pkey PRIMARY KEY (id);
ALTER TABLE release ADD CONSTRAINT release_pkey PRIMARY KEY (id);
ALTER TABLE release_group ADD CONSTRAINT release_group_pkey PRIMARY KEY (id);
ALTER TABLE release_group_primary_type ADD CONSTRAINT release_group_primary_type_pkey PRIMARY KEY (id);
ALTER TABLE release_group_secondary_type ADD CONSTRAINT release_group_secondary_type_pkey PRIMARY KEY (id);
ALTER TABLE release_group_secondary_type_join ADD CONSTRAINT release_group_secondary_type_join_pkey PRIMARY KEY (release_group, secondary_type);
ALTER TABLE release_label ADD CONSTRAINT release_label_pkey PRIMARY KEY (id);
ALTER TABLE release_status ADD CONSTRAINT release_status_pkey PRIMARY KEY (id);
ALTER TABLE track ADD CONSTRAINT track_pkey PRIMARY KEY (id);
ALTER TABLE url ADD CONSTRAINT url_pkey PRIMARY KEY (id);
