-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^

BEGIN;

ALTER TABLE artist        ADD CHECK (controlled_for_whitespace(comment));
ALTER TABLE medium        ADD CHECK (controlled_for_whitespace(name));
ALTER TABLE recording     ADD CHECK (controlled_for_whitespace(comment));
ALTER TABLE release       ADD CHECK (controlled_for_whitespace(comment));
ALTER TABLE release_group ADD CHECK (controlled_for_whitespace(comment));
ALTER TABLE release_label ADD CHECK (controlled_for_whitespace(catalog_number));
ALTER TABLE track         ADD CHECK (controlled_for_whitespace(number));

ALTER TABLE artist
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != ''),
  ADD CONSTRAINT control_for_whitespace_sort_name CHECK (controlled_for_whitespace(sort_name)),
  ADD CONSTRAINT only_non_empty_sort_name CHECK (sort_name != '');

ALTER TABLE artist_alias
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != ''),
  ADD CONSTRAINT control_for_whitespace_sort_name CHECK (controlled_for_whitespace(sort_name)),
  ADD CONSTRAINT only_non_empty_sort_name CHECK (sort_name != '');

ALTER TABLE artist_credit
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != '');

ALTER TABLE artist_credit_name
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != '');

ALTER TABLE release
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != '');

ALTER TABLE release_group
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != '');

ALTER TABLE track
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != '');

ALTER TABLE recording
  ADD CONSTRAINT control_for_whitespace CHECK (controlled_for_whitespace(name)),
  ADD CONSTRAINT only_non_empty CHECK (name != '');

ALTER TABLE artist
ADD CONSTRAINT group_type_implies_null_gender CHECK (
  (gender IS NULL AND type IN (2, 5, 6))
  OR type NOT IN (2, 5, 6)
  OR type IS NULL
);

ALTER TABLE release_label
ADD CHECK (catalog_number IS NOT NULL OR label IS NOT NULL);

ALTER TABLE release_label
  ADD CONSTRAINT no_empty_string_catalog_number
  CHECK (catalog_number != '');

ALTER TABLE release_label
  ADD CONSTRAINT release_label_uniq
  UNIQUE NULLS NOT DISTINCT (release, label, catalog_number)
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE artist ADD CONSTRAINT artist_va_check
    CHECK (id <> 1 OR
           (type = 3 AND
            gender IS NULL AND
            area IS NULL AND
            begin_area IS NULL AND
            end_area IS NULL AND
            begin_date_year IS NULL AND
            begin_date_month IS NULL AND
            begin_date_day IS NULL AND
            end_date_year IS NULL AND
            end_date_month IS NULL AND
            end_date_day IS NULL));

ALTER TABLE medium ADD CONSTRAINT medium_uniq
    UNIQUE (release, position) DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE track ADD CONSTRAINT track_uniq_medium_position
    UNIQUE (medium, position) DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE l_artist_url ADD CONSTRAINT control_for_whitespace_entity0_credit CHECK (controlled_for_whitespace(entity0_credit));
ALTER TABLE l_artist_url ADD CONSTRAINT control_for_whitespace_entity1_credit CHECK (controlled_for_whitespace(entity1_credit));

COMMIT;
