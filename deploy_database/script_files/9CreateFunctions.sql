-- tbh, probably don't need to bother with these functions, as worst case
-- scenario I can just DELETE FROM all tables and reimport from files directly
-- -> because I don't alter the data from within the tables, I don't use funcs

-- \set ON_ERROR_STOP 1
--\set ON_ERROR_ROLLBACK 1
-- will skip duplicates ^^

BEGIN;

CREATE OR REPLACE FUNCTION _median(INTEGER[]) RETURNS INTEGER AS $$
  WITH q AS (
      SELECT val
      FROM unnest($1) val
      WHERE VAL IS NOT NULL
      ORDER BY val
  )
  SELECT val
  FROM q
  LIMIT 1
  -- Subtracting (n + 1) % 2 creates a left bias
  OFFSET greatest(0, floor((select count(*) FROM q) / 2.0) - ((select count(*) + 1 FROM q) % 2));
$$ LANGUAGE sql IMMUTABLE;

CREATE AGGREGATE median(INTEGER) (
  SFUNC=array_append,
  STYPE=INTEGER[],
  FINALFUNC=_median,
  INITCOND='{}'
);

-- Generates UUID version 4 (random-based)
CREATE OR REPLACE FUNCTION generate_uuid_v4() RETURNS uuid
    AS $$
DECLARE
    value VARCHAR(36);
BEGIN
    value =          lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || '-';
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || '-';
    value = value || lpad((to_hex((ceil(random() * 255)::int & 15) | 64)), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || '-';
    value = value || lpad((to_hex((ceil(random() * 255)::int & 63) | 128)), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || '-';
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    value = value || lpad(to_hex(ceil(random() * 255)::int), 2, '0');
    RETURN value::uuid;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION from_hex(t text) RETURNS integer
    AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN EXECUTE 'SELECT x'''||t||'''::integer AS hex' LOOP
        RETURN r.hex;
    END LOOP;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- NameSpace_URL = '6ba7b8119dad11d180b400c04fd430c8'
CREATE OR REPLACE FUNCTION generate_uuid_v3(namespace varchar, name varchar) RETURNS uuid
    AS $$
DECLARE
    value varchar(36);
    bytes varchar;
BEGIN
    bytes = md5(decode(namespace, 'hex') || decode(name, 'escape'));
    value = substr(bytes, 1+0, 8);
    value = value || '-';
    value = value || substr(bytes, 1+2*4, 4);
    value = value || '-';
    value = value || lpad(to_hex((from_hex(substr(bytes, 1+2*6, 2)) & 15) | 48), 2, '0');
    value = value || substr(bytes, 1+2*7, 2);
    value = value || '-';
    value = value || lpad(to_hex((from_hex(substr(bytes, 1+2*8, 2)) & 63) | 128), 2, '0');
    value = value || substr(bytes, 1+2*9, 2);
    value = value || '-';
    value = value || substr(bytes, 1+2*10, 12);
    return value::uuid;
END;
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION inc_ref_count(tbl varchar, row_id integer, val integer) RETURNS void AS $$
BEGIN
    -- increment ref_count for the new name
    EXECUTE 'SELECT ref_count FROM ' || tbl || ' WHERE id = ' || row_id || ' FOR UPDATE';
    EXECUTE 'UPDATE ' || tbl || ' SET ref_count = ref_count + ' || val || ' WHERE id = ' || row_id;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION dec_ref_count(tbl varchar, row_id integer, val integer) RETURNS void AS $$
DECLARE
    ref_count integer;
BEGIN
    -- decrement ref_count for the old name,
    -- or prepare it for deletion if ref_count would drop to 0
    EXECUTE 'SELECT ref_count FROM ' || tbl || ' WHERE id = ' || row_id || ' FOR UPDATE' INTO ref_count;
    IF ref_count <= val THEN
        EXECUTE 'INSERT INTO unreferenced_row_log (table_name, row_id) VALUES ($1, $2)' USING tbl, row_id;
    END IF;
    EXECUTE 'UPDATE ' || tbl || ' SET ref_count = ref_count - ' || val || ' WHERE id = ' || row_id;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION integer_date(year SMALLINT, month SMALLINT, day SMALLINT)
RETURNS INTEGER AS $$
    -- Returns an integer representation of the given date, keeping
    -- NULL values sorted last.
    SELECT (
        CASE
            WHEN year IS NULL AND month IS NULL AND day IS NULL
            THEN NULL
            ELSE (
                coalesce(year::TEXT, '9999') ||
                lpad(coalesce(month::TEXT, '99'), 2, '0') ||
                lpad(coalesce(day::TEXT, '99'), 2, '0')
            )::INTEGER
        END
    )
$$ LANGUAGE SQL IMMUTABLE PARALLEL SAFE;


-----------------------------------------------------------------------
-- artist_credit triggers
-----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION b_upd_artist_credit_name() RETURNS trigger AS $$
BEGIN
    -- Artist credits are assumed to be immutable. When changes need to
    -- be made, we `find_or_insert` the new artist credits and swap
    -- them with the old ones rather than mutate existing entries.
    --
    -- This simplifies a lot of assumptions we can make about their
    -- cacheability, and the consistency of materialized tables like
    -- artist_release_group.
    RAISE EXCEPTION 'Cannot update artist_credit_name';
END;
$$ LANGUAGE 'plpgsql';


-----------------------------------------------------------------------
-- recording triggers
-----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION median_track_length(recording_id integer)
RETURNS integer AS $$
  SELECT median(track.length) FROM track WHERE recording = $1;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION b_upd_recording() RETURNS TRIGGER AS $$
BEGIN
  IF OLD.length IS DISTINCT FROM NEW.length
    AND EXISTS (SELECT TRUE FROM track WHERE recording = NEW.id)
    AND NEW.length IS DISTINCT FROM median_track_length(NEW.id)
  THEN
    NEW.length = median_track_length(NEW.id);
  END IF;

  NEW.last_updated = now();
  RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION a_upd_recording() RETURNS trigger AS $$
BEGIN
    IF NEW.artist_credit != OLD.artist_credit THEN
        PERFORM dec_ref_count('artist_credit', OLD.artist_credit, 1);
        PERFORM inc_ref_count('artist_credit', NEW.artist_credit, 1);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION a_del_recording() RETURNS trigger AS $$
BEGIN
    PERFORM dec_ref_count('artist_credit', OLD.artist_credit, 1);
    RETURN NULL;
END;
$$ LANGUAGE 'plpgsql';


-----------------------------------------------------------------------
-- alternative tracklist triggers
-----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION inc_nullable_artist_credit(row_id integer) RETURNS void AS $$
BEGIN
    IF row_id IS NOT NULL THEN
        PERFORM inc_ref_count('artist_credit', row_id, 1);
    END IF;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION dec_nullable_artist_credit(row_id integer) RETURNS void AS $$
BEGIN
    IF row_id IS NOT NULL THEN
        PERFORM dec_ref_count('artist_credit', row_id, 1);
    END IF;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';


-----------------------------------------------------------------------
-- lastupdate triggers
-----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION b_upd_last_updated_table() RETURNS trigger AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';


------------------------
-- CD Lookup
------------------------

CREATE OR REPLACE FUNCTION create_cube_from_durations(durations INTEGER[]) RETURNS cube AS $$
DECLARE
    point    cube;
    str      VARCHAR;
    i        INTEGER;
    count    INTEGER;
    dest     INTEGER;
    dim      CONSTANT INTEGER = 6;
    selected INTEGER[];
BEGIN

    count = array_upper(durations, 1);
    FOR i IN 0..dim LOOP
        selected[i] = 0;
    END LOOP;

    IF count < dim THEN
        FOR i IN 1..count LOOP
            selected[i] = durations[i];
        END LOOP;
    ELSE
        FOR i IN 1..count LOOP
            dest = (dim * (i-1) / count) + 1;
            selected[dest] = selected[dest] + durations[i];
        END LOOP;
    END IF;

    str = '(';
    FOR i IN 1..dim LOOP
        IF i > 1 THEN
            str = str || ',';
        END IF;
        str = str || cast(selected[i] as text);
    END LOOP;
    str = str || ')';

    RETURN str::cube;
END;
$$ LANGUAGE 'plpgsql' IMMUTABLE;

CREATE OR REPLACE FUNCTION create_bounding_cube(durations INTEGER[], fuzzy INTEGER) RETURNS cube AS $$
DECLARE
    point    cube;
    str      VARCHAR;
    i        INTEGER;
    dest     INTEGER;
    count    INTEGER;
    dim      CONSTANT INTEGER = 6;
    selected INTEGER[];
    scalers  INTEGER[];
BEGIN

    count = array_upper(durations, 1);
    IF count < dim THEN
        FOR i IN 1..dim LOOP
            selected[i] = 0;
            scalers[i] = 0;
        END LOOP;
        FOR i IN 1..count LOOP
            selected[i] = durations[i];
            scalers[i] = 1;
        END LOOP;
    ELSE
        FOR i IN 1..dim LOOP
            selected[i] = 0;
            scalers[i] = 0;
        END LOOP;
        FOR i IN 1..count LOOP
            dest = (dim * (i-1) / count) + 1;
            selected[dest] = selected[dest] + durations[i];
            scalers[dest] = scalers[dest] + 1;
        END LOOP;
    END IF;

    str = '(';
    FOR i IN 1..dim LOOP
        IF i > 1 THEN
            str = str || ',';
        END IF;
        str = str || cast((selected[i] - (fuzzy * scalers[i])) as text);
    END LOOP;
    str = str || '),(';
    FOR i IN 1..dim LOOP
        IF i > 1 THEN
            str = str || ',';
        END IF;
        str = str || cast((selected[i] + (fuzzy * scalers[i])) as text);
    END LOOP;
    str = str || ')';

    RETURN str::cube;
END;
$$ LANGUAGE 'plpgsql' IMMUTABLE;


-------------------------------------------------------------------
-- Maintain musicbrainz.recording_first_release_date
-------------------------------------------------------------------

CREATE OR REPLACE FUNCTION deny_special_purpose_deletion() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Attempted to delete a special purpose row';
END;
$$ LANGUAGE 'plpgsql';


--------------------------------------------------------------------------------
-- Remove unused link rows when a relationship is changed
--------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION simplify_search_hints()
RETURNS trigger AS $$
BEGIN
    IF NEW.type::int = TG_ARGV[0]::int THEN
        NEW.sort_name := NEW.name;
        NEW.begin_date_year := NULL;
        NEW.begin_date_month := NULL;
        NEW.begin_date_day := NULL;
        NEW.end_date_year := NULL;
        NEW.end_date_month := NULL;
        NEW.end_date_day := NULL;
        NEW.end_date_day := NULL;
        NEW.ended := FALSE;
        NEW.locale := NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION end_date_implies_ended()
RETURNS trigger AS $$
BEGIN
    IF NEW.end_date_year IS NOT NULL OR
       NEW.end_date_month IS NOT NULL OR
       NEW.end_date_day IS NOT NULL
    THEN
        NEW.ended = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION end_area_implies_ended()
RETURNS trigger AS $$
BEGIN
    IF NEW.end_area IS NOT NULL
    THEN
        NEW.ended = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION padded_by_whitespace(TEXT) RETURNS boolean AS $$
  SELECT btrim($1) <> $1;
$$ LANGUAGE SQL IMMUTABLE;

CREATE OR REPLACE FUNCTION controlled_for_whitespace(TEXT) RETURNS boolean AS $$
  SELECT NOT padded_by_whitespace($1);
$$ LANGUAGE SQL IMMUTABLE SET search_path = musicbrainz, public;

CREATE OR REPLACE FUNCTION deny_deprecated_links()
RETURNS trigger AS $$
BEGIN
  IF (SELECT is_deprecated FROM link_type WHERE id = NEW.link_type)
  THEN
    RAISE EXCEPTION 'Attempt to create a relationship with a deprecated type';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION check_has_dates()
RETURNS trigger AS $$
BEGIN
    IF (NEW.begin_date_year IS NOT NULL OR
       NEW.begin_date_month IS NOT NULL OR
       NEW.begin_date_day IS NOT NULL OR
       NEW.end_date_year IS NOT NULL OR
       NEW.end_date_month IS NOT NULL OR
       NEW.end_date_day IS NOT NULL OR
       NEW.ended = TRUE)
       AND NOT (SELECT has_dates FROM link_type WHERE id = NEW.link_type)
  THEN
    RAISE EXCEPTION 'Attempt to add dates to a relationship type that does not support dates.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

COMMIT;


-----------------------------------------------------------------------
-- Edit data helpers
-----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION edit_data_type_info(data JSONB) RETURNS TEXT AS $$
BEGIN
    CASE jsonb_typeof(data)
    WHEN 'object' THEN
        RETURN '{' ||
            (SELECT string_agg(
                to_json(key) || ':' ||
                edit_data_type_info(jsonb_extract_path(data, key)),
                ',' ORDER BY key)
               FROM jsonb_object_keys(data) AS key) ||
            '}';
    WHEN 'array' THEN
        RETURN '[' ||
            (SELECT string_agg(
                DISTINCT edit_data_type_info(item),
                ',' ORDER BY edit_data_type_info(item))
               FROM jsonb_array_elements(data) AS item) ||
            ']';
    WHEN 'string' THEN
        RETURN '1';
    WHEN 'number' THEN
        RETURN '2';
    WHEN 'boolean' THEN
        RETURN '4';
    WHEN 'null' THEN
        RETURN '8';
    END CASE;
    RETURN '';
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE STRICT;


-----------------------------------------------------------------------
-- Relationship triggers
-----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION b_upd_link() RETURNS trigger AS $$
BEGIN
    -- Like artist credits, links are shared across many entities
    -- (relationships) and so are immutable: they can only be inserted
    -- or deleted.
    --
    -- This helps ensure the data integrity of relationships and other
    -- materialized tables that rely on their immutability, like
    -- area_containment.
    RAISE EXCEPTION 'link rows are immutable';
END;
$$ LANGUAGE 'plpgsql';

-- vi: set ts=4 sw=4 et :
