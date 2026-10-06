-- De minimis aid, from bdns-sync's minimis_busqueda table, read and
-- published like awards (see 10_concesiones.sql). De minimis records carry
-- the aid's gross grant equivalent, not an amount.

-- Private, like concesiones.
CREATE OR REPLACE TABLE minimis AS
SELECT
    * EXCLUDE (is_current) REPLACE (trim(instrumento) AS instrumento),
    beneficiary_kind(beneficiario) AS tipoPersona,
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, MINIMIS_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.minimis_busqueda')
);

-- Legal persons, record by record (see 10_concesiones.sql).
CREATE OR REPLACE TABLE publish.minimis_personas_juridicas AS
SELECT
    idConcesion,
    codigoConcesion,
    fechaConcesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    ayudaEquivalente,
    instrumento,
    numeroConvocatoria,
    convocante,
    reglamento,
    sectorActividad,
    sectorProducto,
    fechaRegistro,
    retirada
FROM minimis
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);

-- Natural persons and those protected like them: the per-call summary
-- (06_summaries.sql).
CREATE OR REPLACE TABLE minimis_protegidas AS
SELECT
    numeroConvocatoria,
    instrumento,
    coalesce(CAST(idPersona AS VARCHAR), beneficiario) AS persona,
    fechaConcesion,
    NULL::DECIMAL(18, 2) AS importe,
    ayudaEquivalente,
    struct_pack(convocante) AS etiqueta
FROM minimis
WHERE is_protected_beneficiary(tipoPersona, beneficiario);

-- De minimis records name no call title, only the calling body.
CREATE OR REPLACE TABLE publish.minimis_personas_fisicas AS
SELECT
    numeroConvocatoria,
    etiqueta.convocante AS convocante,
    instrumento,
    esResto,
    ejercicio,
    concesiones,
    beneficiarios,
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
FROM call_summaries('minimis_protegidas');
