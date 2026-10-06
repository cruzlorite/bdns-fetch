-- Warnings about fields the API has stopped sending. If the API renames or
-- drops a field listed in 05_schemas.sql, or changes its format so that it
-- no longer fits its type, from_json() reads it as empty, and the dataset
-- would publish an empty column without anyone noticing. This step lists,
-- for each table read from the API, the fields that came empty in every
-- record bdns-sync stored in that table's last 30 days, and build.sql
-- prints them. It is a warning, not an error, since a rare field can stay
-- empty for a month.

-- The fields of one table that are empty in all its recent records: the
-- records stored in the 30 days before its newest one, and, for each field,
-- how many of them have it filled. The columns the dataset adds itself
-- are left out, and so is an empty table (an entity bdns-sync has not
-- synced).
CREATE OR REPLACE MACRO empty_fields(tbl) AS TABLE
    WITH recent AS (
        SELECT * FROM query_table(tbl)
        WHERE _valid_from >= (SELECT max(_valid_from) FROM query_table(tbl)) - INTERVAL 30 DAY
    ),
    filled AS (
        UNPIVOT (
            SELECT count(COLUMNS(lambda c: c NOT IN ('_valid_from', 'retirada', 'tipoPersona')))
            FROM recent
        )
        ON COLUMNS(*) INTO NAME campo VALUE registros
    )
    SELECT tbl AS tabla, campo
    FROM filled
    WHERE registros = 0 AND EXISTS (SELECT 1 FROM recent);

CREATE OR REPLACE TABLE campos_vacios AS
          SELECT * FROM empty_fields('concesiones')
UNION ALL SELECT * FROM empty_fields('ayudasestado')
UNION ALL SELECT * FROM empty_fields('minimis')
UNION ALL SELECT * FROM empty_fields('partidospoliticos')
UNION ALL SELECT * FROM empty_fields('grandesbeneficiarios')
UNION ALL SELECT * FROM empty_fields('convocatorias')
UNION ALL SELECT * FROM empty_fields('planesestrategicos');
