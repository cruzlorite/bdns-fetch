-- The checks that stop the build before anything that could reveal a
-- natural person is published. Each one calls error(), which ends the run
-- with a message, as soon as it finds something; none cleans up, because a
-- finding points to a fault earlier in the build that has to be fixed.
-- See docs/adr/0002-anonymised-dataset.md.

-- Record-level tables: only legal persons and public bodies, and no
-- personal tax ID anywhere.
SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_entidades: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.concesiones_entidades WHERE is_protected(tipo_persona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_entidades: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.concesiones_entidades');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_entidades: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.ayudas_estado_entidades WHERE is_protected(tipo_persona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.ayudas_estado_entidades: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.ayudas_estado_entidades');

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_entidades: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publish.minimis_entidades WHERE is_protected(tipo_persona);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.minimis_entidades: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.minimis_entidades');

-- concesiones_personas: no column that identifies people, no row below
-- the minimum, tails only in rows with enough people, and no personal tax
-- ID anywhere.
SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas: identifying columns: ' || string_agg(column_name, ', ')
) END
FROM information_schema.columns
WHERE table_schema = 'publish' AND table_name = 'concesiones_personas' AND identifying_column(column_name);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas: ' || count(*) || ' rows below ' || min_beneficiaries() || ' beneficiaries'
) END
FROM publish.concesiones_personas WHERE beneficiarios < min_beneficiaries();

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas: ' || count(*) || ' rows with 10th or 90th percentiles below '
    || min_beneficiaries_for_tails() || ' beneficiaries'
) END
FROM publish.concesiones_personas
WHERE beneficiarios < min_beneficiaries_for_tails()
    AND (importe_p10 IS NOT NULL OR importe_p90 IS NOT NULL OR fecha_p10 IS NOT NULL OR fecha_p90 IS NOT NULL);

SELECT CASE WHEN count(*) > 0 THEN error(
    'publish.concesiones_personas: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publish.concesiones_personas');
