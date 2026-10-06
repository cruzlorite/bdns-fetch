-- The checks that stop the build before anything that could reveal a
-- natural person is published. Each one calls error(), which ends the run
-- with a message, as soon as it finds something; none cleans up, because a
-- finding points to a fault earlier in the build that has to be fixed.
-- See docs/adr/0020-anonymised-dataset.md.

-- The rows of a summary table with fewer people than any row needs, and
-- those whose 10th or 90th percentiles (any column ending in _p10 or _p90)
-- are published with fewer people than those need.
CREATE OR REPLACE MACRO rows_below_minimum(tbl) AS TABLE
    SELECT * FROM query_table(tbl) WHERE beneficiarios < min_beneficiaries();

CREATE OR REPLACE MACRO rows_with_tails_below(tbl) AS TABLE
    SELECT * FROM query_table(tbl)
    WHERE beneficiarios < min_beneficiaries_for_tails()
        AND concat_ws('', *COLUMNS('_p(10|90)$')) <> '';

-- Record-level tables: only legal persons and public bodies, and no
-- personal tax ID anywhere.

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_juridicas: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.concesiones_personas_juridicas WHERE is_protected(tipo_persona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_juridicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.concesiones_personas_juridicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_personas_juridicas: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.ayudas_estado_personas_juridicas WHERE is_protected(tipo_persona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_personas_juridicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.ayudas_estado_personas_juridicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_juridicas: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.minimis_personas_juridicas WHERE is_protected(tipo_persona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_juridicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.minimis_personas_juridicas');

-- Summaries: no column that identifies people, no row below the minimum,
-- tails only in rows with enough people, and no personal tax ID anywhere.

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_fisicas: identifying columns: ' || string_agg(column_name, ', ')
) END
FROM information_schema.columns
WHERE table_schema = 'publish' AND table_name = 'concesiones_personas_fisicas' AND identifying_column(column_name);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_fisicas: ' || count(*) || ' rows below ' || min_beneficiaries() || ' beneficiaries'
) END
FROM rows_below_minimum('publish.concesiones_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_fisicas: ' || count(*) || ' rows with 10th or 90th percentiles below '
    || min_beneficiaries_for_tails() || ' beneficiaries'
) END
FROM rows_with_tails_below('publish.concesiones_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_fisicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.concesiones_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_personas_fisicas: identifying columns: ' || string_agg(column_name, ', ')
) END
FROM information_schema.columns
WHERE table_schema = 'publish' AND table_name = 'ayudas_estado_personas_fisicas' AND identifying_column(column_name);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_personas_fisicas: ' || count(*) || ' rows below ' || min_beneficiaries() || ' beneficiaries'
) END
FROM rows_below_minimum('publish.ayudas_estado_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_personas_fisicas: ' || count(*) || ' rows with 10th or 90th percentiles below '
    || min_beneficiaries_for_tails() || ' beneficiaries'
) END
FROM rows_with_tails_below('publish.ayudas_estado_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_personas_fisicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.ayudas_estado_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_fisicas: identifying columns: ' || string_agg(column_name, ', ')
) END
FROM information_schema.columns
WHERE table_schema = 'publish' AND table_name = 'minimis_personas_fisicas' AND identifying_column(column_name);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_fisicas: ' || count(*) || ' rows below ' || min_beneficiaries() || ' beneficiaries'
) END
FROM rows_below_minimum('publish.minimis_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_fisicas: ' || count(*) || ' rows with 10th or 90th percentiles below '
    || min_beneficiaries_for_tails() || ' beneficiaries'
) END
FROM rows_with_tails_below('publish.minimis_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_fisicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.minimis_personas_fisicas');
