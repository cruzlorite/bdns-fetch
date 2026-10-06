-- Calls for applications, from bdns-sync's convocatorias table (each call's
-- detail), with the last known version of each (04_versions.sql), withdrawn
-- ones included. Fields keep the API's names and shape: organo stays an
-- object, and lists stay lists of objects (05_schemas.sql).
--
-- A call is the administration's own announcement, not a person's data,
-- but its texts are written by hand and a nominative grant sometimes names
-- its beneficiary: any text with something shaped like a personal tax ID
-- is published empty. So is the link to the regulatory bases when it has
-- that shape, which some bulletins' file names do (eight digits and a
-- letter): a false alarm, most likely, but the rule is to protect what is
-- in doubt. The documents and the bulletin announcements, whose files and
-- texts often list the beneficiaries, are not even read, and neither is
-- the portal's standard legal notice (advertencia).

-- Private: every call, with the fields in 05_schemas.sql.
CREATE OR REPLACE TABLE convocatorias AS
SELECT
    * EXCLUDE (is_current),
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, CONVOCATORIAS_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.convocatorias')
);

CREATE OR REPLACE TABLE publish.convocatorias AS
SELECT
    id,
    codigoBDNS,
    fechaRecepcion,
    organo,
    sedeElectronica,
    without_personal_id(descripcion)                AS descripcion,
    without_personal_id(descripcionLeng)            AS descripcionLeng,
    tipoConvocatoria,
    presupuestoTotal,
    mrr,
    instrumentos,
    tiposBeneficiarios,
    sectores,
    regiones,
    descripcionFinalidad,
    without_personal_id(descripcionBasesReguladoras) AS descripcionBasesReguladoras,
    without_personal_id(urlBasesReguladoras)        AS urlBasesReguladoras,
    sePublicaDiarioOficial,
    abierto,
    fechaInicioSolicitud,
    fechaFinSolicitud,
    without_personal_id(textInicio)                 AS textInicio,
    without_personal_id(textFin)                    AS textFin,
    ayudaEstado,
    urlAyudaEstado,
    fondos,
    reglamento,
    objetivos,
    sectoresProductos,
    retirada
FROM convocatorias;
