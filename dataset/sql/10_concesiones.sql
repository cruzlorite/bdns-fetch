-- Awards: all of them, from bdns-sync's concesiones_busqueda table, with the
-- last known version of each (04_versions.sql), withdrawn ones included;
-- that is what makes the history worth publishing. Legal persons are
-- published record by record and natural persons only summarised (06),
-- see docs/adr/0020-anonymised-dataset.md.

-- Private: every award, with the fields in 05_schemas.sql, the kind of
-- beneficiary and whether the API has withdrawn it. It still holds personal
-- data (beneficiario, idPersona, urlBR) and never leaves the private build.
CREATE OR REPLACE TABLE concesiones AS
SELECT
    * EXCLUDE (is_current) REPLACE (trim(instrumento) AS instrumento),
    beneficiary_kind(beneficiario) AS tipoPersona,
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, CONCESIONES_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.concesiones_busqueda')
);

-- Legal persons, public bodies included, record by record: without the fields
-- that lead to people (urlBR, idPersona, the beneficiario field itself),
-- and without any beneficiary protected like a natural person.
CREATE OR REPLACE TABLE publish.concesiones_personas_juridicas AS
SELECT
    id,
    codConcesion,
    fechaConcesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    importe,
    ayudaEquivalente,
    instrumento,
    numeroConvocatoria,
    convocatoria,
    nivel1,
    nivel2,
    nivel3,
    fechaAlta,
    retirada
FROM concesiones
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);

-- Natural persons and those protected like them: the per-call summary
-- (06_summaries.sql).
CREATE OR REPLACE TABLE concesiones_protegidas AS
SELECT
    numeroConvocatoria,
    instrumento,
    coalesce(CAST(idPersona AS VARCHAR), beneficiario) AS persona,
    fechaConcesion,
    importe,
    ayudaEquivalente,
    struct_pack(convocatoria, nivel1, nivel2, nivel3) AS etiqueta
FROM concesiones
WHERE is_protected_beneficiary(tipoPersona, beneficiario);

-- A call title shaped like a personal tax ID is blanked; the checks
-- would stop the build otherwise.
CREATE OR REPLACE TABLE publish.concesiones_personas_fisicas AS
SELECT
    numeroConvocatoria,
    without_personal_id(etiqueta.convocatoria) AS convocatoria,
    etiqueta.nivel1 AS nivel1,
    etiqueta.nivel2 AS nivel2,
    etiqueta.nivel3 AS nivel3,
    instrumento,
    esResto,
    ejercicio,
    concesiones,
    beneficiarios,
    importe.total      AS importeTotal,
    importe.media      AS importeMedia,
    importe.desviacion AS importeDesviacion,
    importe.p10        AS importeP10,
    importe.p25        AS importeP25,
    importe.mediana    AS importeMediana,
    importe.p75        AS importeP75,
    importe.p90        AS importeP90,
    ayudaEquivalente.total      AS ayudaEquivalenteTotal,
    ayudaEquivalente.media      AS ayudaEquivalenteMedia,
    ayudaEquivalente.desviacion AS ayudaEquivalenteDesviacion,
    ayudaEquivalente.p10        AS ayudaEquivalenteP10,
    ayudaEquivalente.p25        AS ayudaEquivalenteP25,
    ayudaEquivalente.mediana    AS ayudaEquivalenteMediana,
    ayudaEquivalente.p75        AS ayudaEquivalenteP75,
    ayudaEquivalente.p90        AS ayudaEquivalenteP90,
    fechaConcesion.p10     AS fechaConcesionP10,
    fechaConcesion.p25     AS fechaConcesionP25,
    fechaConcesion.mediana AS fechaConcesionMediana,
    fechaConcesion.p75     AS fechaConcesionP75,
    fechaConcesion.p90     AS fechaConcesionP90
FROM call_summaries('concesiones_protegidas');
