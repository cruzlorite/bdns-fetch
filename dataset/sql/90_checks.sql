-- The checks that stop the build before anything that could reveal a
-- natural person is published. Each one calls error(), which ends the run
-- with a message, as soon as it finds something; none cleans up, because a
-- finding points to a fault earlier in the build that has to be fixed.
-- See docs/adr/0020-anonymised-dataset.md.

-- The rows of a summary table with fewer people than any row needs, and
-- those whose 10th or 90th percentiles (any column ending in P10 or P90)
-- are published with fewer people than those need.
CREATE OR REPLACE MACRO rows_below_minimum(tbl) AS TABLE
    SELECT * FROM query_table(tbl) WHERE beneficiarios < min_beneficiaries();

CREATE OR REPLACE MACRO rows_with_tails_below(tbl) AS TABLE
    SELECT * FROM query_table(tbl)
    WHERE beneficiarios < min_beneficiaries_for_tails()
        AND concat_ws('', *COLUMNS('P(10|90)$')) <> '';

-- Record-level tables: only legal persons and public bodies, and no
-- personal tax ID anywhere.

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_juridicas: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.concesiones_personas_juridicas WHERE is_protected(tipoPersona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas_juridicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.concesiones_personas_juridicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudasestado_personas_juridicas: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.ayudasestado_personas_juridicas WHERE is_protected(tipoPersona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudasestado_personas_juridicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.ayudasestado_personas_juridicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_juridicas: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.minimis_personas_juridicas WHERE is_protected(tipoPersona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_personas_juridicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.minimis_personas_juridicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.partidospoliticos: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.partidospoliticos WHERE is_protected(tipoPersona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.partidospoliticos: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.partidospoliticos');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.grandesbeneficiarios: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.grandesbeneficiarios WHERE is_protected(tipoPersona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.grandesbeneficiarios: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.grandesbeneficiarios');

-- Calls, plans and catalogues: no personal tax ID anywhere.

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.convocatorias: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.convocatorias');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.planesestrategicos: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.planesestrategicos');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.catalogos: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.catalogos');

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
    'publish.ayudasestado_personas_fisicas: identifying columns: ' || string_agg(column_name, ', ')
) END
FROM information_schema.columns
WHERE table_schema = 'publish' AND table_name = 'ayudasestado_personas_fisicas' AND identifying_column(column_name);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudasestado_personas_fisicas: ' || count(*) || ' rows below ' || min_beneficiaries() || ' beneficiaries'
) END
FROM rows_below_minimum('publish.ayudasestado_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudasestado_personas_fisicas: ' || count(*) || ' rows with 10th or 90th percentiles below '
    || min_beneficiaries_for_tails() || ' beneficiaries'
) END
FROM rows_with_tails_below('publish.ayudasestado_personas_fisicas');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudasestado_personas_fisicas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.ayudasestado_personas_fisicas');

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
