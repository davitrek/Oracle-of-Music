-- DO NOT USE

CREATE MATERIALIZED VIEW artist_collaborations AS
SELECT DISTINCT
    acn1.artist AS artist_id_1,
    acn2.artist AS artist_id_2
FROM artist_credit_name acn1
WHERE acn1.artist_credit IN (
    SELECT artist_credit
    FROM recording
)
JOIN artist_credit_name acn2
    ON acn1.artist_credit = acn2.artist_credit
    AND acn1.artist < acn2.artist


SELECT DISTINCT musicbrainz.artist_credit_name.artist 
FROM musicbrainz.artist_credit_name 
WHERE musicbrainz.artist_credit_name.artist_credit IN (SELECT musicbrainz.artist_credit_name.artist_credit 
FROM musicbrainz.artist_credit_name 
WHERE :param_1 = musicbrainz.artist_credit_name.artist AND musicbrainz.artist_credit_name.artist_credit IN (SELECT musicbrainz.recording.artist_credit 
FROM musicbrainz.recording)) AND (musicbrainz.artist_credit_name.artist != :artist_1 OR musicbrainz.artist_credit_name.artist IS NULL) AND musicbrainz.artist_credit_name.artist IS NOT NULL



CREATE MATERIALIZED VIEW artist_recordings AS
SELECT DISTINCT
    acn.artist AS artist_id,
    r.id AS recording_id,
    r.name AS recording_name
FROM artist_credit_name acn
JOIN artist_credit ac ON ac.id = acn.artist_credit
JOIN recording r ON r.artist_credit = ac.id;
