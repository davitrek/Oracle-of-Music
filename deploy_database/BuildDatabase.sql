\set ON_ERROR_STOP 1
\set mbdump_location '/var/lib/postgresql/data/here'
                    --/path/to/directory/containing/mbdump

BEGIN;

CREATE SCHEMA musicbrainz;
ALTER DATABASE musicbrainz SET search_path TO musicbrainz, public;

COMMIT;

-- run files (each in their own separate transaction, defined within file)
\ir script_files/1Extensions.sql
\ir script_files/2CreateTypes.sql
\ir script_files/3CreateCollations.sql
\ir script_files/4CreateTables.sql
\ir script_files/5ImportData.sql
\ir script_files/6SetSequences.sql
\ir script_files/7CreatePrimaryKeys.sql
\ir script_files/8CreateFKConstraints.sql
\ir script_files/9CreateFunctions.sql
\ir script_files/10CreateConstraints.sql
\ir script_files/11CreateIndexes.sql
\ir script_files/12CreateCollateIndexes.sql
