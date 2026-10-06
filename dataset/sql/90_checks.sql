-- The checks that stop the build before anything that could reveal a
-- natural person is published. Each one calls error(), which ends the run
-- with a message, as soon as it finds something; none cleans up, because a
-- finding points to a fault earlier in the build that has to be fixed.
-- See docs/adr/0020-anonymised-dataset.md.
--
-- They are not written table by table: the tables to check are found in
-- the publish database, and each kind by its columns, so a table added
-- later is checked without anyone having to remember it.

-- The reads are over, so bdns-sync is detached: nothing from here on touches
-- the source database. It also lets the checks list the published tables,
-- which fails while DuckDB's BigQuery extension has a database attached.
DETACH DATABASE IF EXISTS sync;

-- The rows of a summary table with fewer people than any row needs, and
-- those whose 10th or 90th percentiles (any column ending in P10 or P90)
-- are published with fewer people than those need.
CREATE OR REPLACE MACRO rows_below_minimum(tbl) AS TABLE
    SELECT * FROM query_table(tbl) WHERE beneficiarios < MIN_BENEFICIARIES();

CREATE OR REPLACE MACRO rows_with_tails_below(tbl) AS TABLE
    SELECT * FROM query_table(tbl)
    WHERE beneficiarios < MIN_BENEFICIARIES_FOR_TAILS()
        AND concat_ws('', *COLUMNS('P(10|90)$')) <> '';

-- Every published table, and what kind it is: record by record about legal
-- persons (it has tipoPersona), or a summary about natural persons (it has
-- beneficiarios). Calls, plans and catalogues are neither.
CREATE OR REPLACE TEMP TABLE published AS
SELECT
    'publish.' || table_name                    AS tabla,
    bool_or(column_name = 'tipoPersona')        AS record_level,
    bool_or(column_name = 'beneficiarios')      AS summary
FROM duckdb_columns()
WHERE database_name = 'publish'
GROUP BY table_name;

-- One query per table, run together: '{}' in the template is the table.
CREATE OR REPLACE MACRO per_table(template, kind) AS (
    SELECT coalesce(
        string_agg(replace(template, '{}', tabla), ' UNION ALL '),
        'SELECT NULL::VARCHAR AS tabla, 0 AS filas'
    )
    FROM published
    WHERE CASE kind WHEN 'record_level' THEN record_level WHEN 'summary' THEN summary ELSE true END
);

SET VARIABLE check_personal_ids = per_table(
    'SELECT ''{}'' AS tabla, count(*) AS filas FROM rows_with_personal_ids(''{}'')', 'all');
SET VARIABLE check_protected = per_table(
    'SELECT ''{}'' AS tabla, count(*) AS filas FROM {} WHERE is_protected(tipoPersona)', 'record_level');
SET VARIABLE check_below_minimum = per_table(
    'SELECT ''{}'' AS tabla, count(*) AS filas FROM rows_below_minimum(''{}'')', 'summary');
SET VARIABLE check_tails = per_table(
    'SELECT ''{}'' AS tabla, count(*) AS filas FROM rows_with_tails_below(''{}'')', 'summary');

-- Record-level tables: only legal persons and public bodies.
SELECT CASE WHEN count(*) > 0 THEN error(
    string_agg(tabla || ': ' || filas || ' rows of protected beneficiaries', '; ')
) END
FROM query(getvariable('check_protected')) WHERE filas > 0;

-- No personal tax ID anywhere, in any published table.
SELECT CASE WHEN count(*) > 0 THEN error(
    string_agg(tabla || ': ' || filas || ' rows with something shaped like a personal tax ID', '; ')
) END
FROM query(getvariable('check_personal_ids')) WHERE filas > 0;

-- Summaries: no column that identifies people, no row below the minimum,
-- and tails only in rows with enough people.
SELECT CASE WHEN count(*) > 0 THEN error(
    string_agg('publish.' || table_name || ': identifying columns: ' || column_name, '; ')
) END
FROM duckdb_columns()
WHERE database_name = 'publish'
    AND 'publish.' || table_name IN (SELECT tabla FROM published WHERE summary)
    AND identifying_column(column_name);

SELECT CASE WHEN count(*) > 0 THEN error(
    string_agg(tabla || ': ' || filas || ' rows below ' || MIN_BENEFICIARIES() || ' beneficiaries', '; ')
) END
FROM query(getvariable('check_below_minimum')) WHERE filas > 0;

SELECT CASE WHEN count(*) > 0 THEN error(
    string_agg(tabla || ': ' || filas || ' rows with 10th or 90th percentiles below '
        || MIN_BENEFICIARIES_FOR_TAILS() || ' beneficiaries', '; ')
) END
FROM query(getvariable('check_tails')) WHERE filas > 0;
