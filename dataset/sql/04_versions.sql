-- The last known version of each record in a bdns-sync table: its current
-- one or, if the API stopped serving it, its last one. A corrected record
-- always has a newer version, so the newest is not the current one only
-- when the record was withdrawn. It comes with the moment bdns-sync stored
-- it (_valid_from), which 80_schema_drift.sql uses.
--
-- It reads the table twice on purpose. The first pass takes only the keys
-- and their newest date, which are small; the second streams the payloads
-- past them and keeps the matching ones. A window over the whole table
-- would hold every payload at once, and a long history does not fit in
-- memory. bdns-sync never writes two versions of a record at the same
-- instant, so each key matches one row.
--
-- Call it once per statement. With DuckDB's BigQuery extension, a
-- statement that calls it for several tables gets the first table every
-- time (see 17_catalogos.sql).

CREATE OR REPLACE MACRO latest_versions(tbl) AS TABLE
    WITH newest AS (
        SELECT _natural_key, max(_valid_from) AS valid_from
        FROM query_table(tbl)
        GROUP BY _natural_key
    )
    SELECT CAST(s.payload AS JSON) AS r, CAST(s._is_current AS BOOLEAN) AS is_current, s._valid_from
    FROM query_table(tbl) s
    WHERE EXISTS (
        SELECT 1 FROM newest n
        WHERE n._natural_key = s._natural_key AND n.valid_from = s._valid_from
    );
