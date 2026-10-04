-- The checks that stop the build before anything that could reveal a
-- natural person is published. Each one calls error(), which ends the run
-- with a message, as soon as it finds something; none cleans up, because a
-- finding points to a fault earlier in the build that has to be fixed.
-- See docs/adr/0002-anonymised-dataset.md.

-- Awards published record by record are only to legal persons and public bodies.
SELECT CASE WHEN count(*) > 0 THEN error(
    'publicar.concesiones_entidades: ' || count(*) || ' rows of protected beneficiaries'
) END
FROM publicar.concesiones_entidades
WHERE is_protected(tipo_beneficiario);

-- No published value looks like a natural person's tax ID.
SELECT CASE WHEN count(*) > 0 THEN error(
    'publicar.concesiones_entidades: ' || count(*) || ' rows with something shaped like a personal tax ID'
) END
FROM rows_with_personal_ids('publicar.concesiones_entidades');
