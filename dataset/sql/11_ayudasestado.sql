-- State aid, from bdns-sync's ayudasestado_busqueda table, read and
-- published like awards (see 10_concesiones.sql). tipoBeneficiario is the
-- BDNS's own category (SME, large company...); tipoPersona is this
-- dataset's classification.

-- Private, like concesiones.
CREATE OR REPLACE TABLE ayudasestado AS
SELECT
    * EXCLUDE (is_current) REPLACE (trim(instrumento) AS instrumento, trim(objetivo) AS objetivo),
    beneficiary_kind(beneficiario) AS tipoPersona,
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, AYUDASESTADO_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.ayudasestado_busqueda')
);

-- Legal persons, record by record (see 10_concesiones.sql). The link to the
-- European Commission's case is about the aid scheme, not the beneficiary,
-- so it stays.
CREATE OR REPLACE TABLE publish.ayudasestado_personas_juridicas AS
SELECT
    idConcesion,
    codConcesion,
    fechaConcesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    tipoBeneficiario,
    importe,
    ayudaEquivalente,
    instrumento,
    numeroConvocatoria,
    convocatoria,
    convocante,
    reglamento,
    objetivo,
    region,
    sectores,
    ayudaEstado,
    urlAyudaEstado,
    entidad,
    intermediario,
    fechaAlta,
    retirada
FROM ayudasestado
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);

-- Natural persons and those protected like them: the per-call summary
-- (06_summaries.sql).
CREATE OR REPLACE TABLE ayudasestado_protegidas AS
SELECT
    numeroConvocatoria,
    instrumento,
    coalesce(CAST(idPersona AS VARCHAR), beneficiario) AS persona,
    fechaConcesion,
    importe,
    ayudaEquivalente,
    struct_pack(convocatoria, convocante) AS etiqueta
FROM ayudasestado
WHERE is_protected_beneficiary(tipoPersona, beneficiario);

-- A call title shaped like a personal tax ID is blanked; the checks
-- would stop the build otherwise.
CREATE OR REPLACE TABLE publish.ayudasestado_personas_fisicas AS
SELECT
    numeroConvocatoria,
    without_personal_id(etiqueta.convocatoria) AS convocatoria,
    etiqueta.convocante AS convocante,
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
FROM call_summaries('ayudasestado_protegidas');
