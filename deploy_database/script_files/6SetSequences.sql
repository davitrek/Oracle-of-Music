-- Automatically generated, do not edit.
-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^

SELECT setval('artist_id_seq', COALESCE((SELECT MAX(id) FROM artist), 0) + 1, FALSE);
SELECT setval('artist_alias_id_seq', COALESCE((SELECT MAX(id) FROM artist_alias), 0) + 1, FALSE);
SELECT setval('artist_credit_id_seq', COALESCE((SELECT MAX(id) FROM artist_credit), 0) + 1, FALSE);
SELECT setval('l_artist_url_id_seq', COALESCE((SELECT MAX(id) FROM l_artist_url), 0) + 1, FALSE);
SELECT setval('link_id_seq', COALESCE((SELECT MAX(id) FROM link), 0) + 1, FALSE);
SELECT setval('link_type_id_seq', COALESCE((SELECT MAX(id) FROM link_type), 0) + 1, FALSE);
SELECT setval('medium_id_seq', COALESCE((SELECT MAX(id) FROM medium), 0) + 1, FALSE);
SELECT setval('recording_id_seq', COALESCE((SELECT MAX(id) FROM recording), 0) + 1, FALSE);
SELECT setval('release_id_seq', COALESCE((SELECT MAX(id) FROM release), 0) + 1, FALSE);
SELECT setval('release_label_id_seq', COALESCE((SELECT MAX(id) FROM release_label), 0) + 1, FALSE);
SELECT setval('release_status_id_seq', COALESCE((SELECT MAX(id) FROM release_status), 0) + 1, FALSE);
SELECT setval('release_group_id_seq', COALESCE((SELECT MAX(id) FROM release_group), 0) + 1, FALSE);
SELECT setval('release_group_primary_type_id_seq', COALESCE((SELECT MAX(id) FROM release_group_primary_type), 0) + 1, FALSE);
SELECT setval('release_group_secondary_type_id_seq', COALESCE((SELECT MAX(id) FROM release_group_secondary_type), 0) + 1, FALSE);
SELECT setval('track_id_seq', COALESCE((SELECT MAX(id) FROM track), 0) + 1, FALSE);
SELECT setval('url_id_seq', COALESCE((SELECT MAX(id) FROM url), 0) + 1, FALSE);
