-- Calls for applications, record by record: the last known version of
-- each call's detail in bdns-sync's convocatorias table, withdrawn ones
-- included (see 04_versions.sql). Fields keep the API's names and shape:
-- organo stays an object, and lists stay lists of objects.
--
-- A call is the administration's own announcement, not a person's data,
-- but its texts are written by hand and a nominative grant sometimes names
-- its beneficiary: any text with something shaped like a personal tax ID
-- is published empty. So is the link to the regulatory bases when it has
-- that shape, which some bulletins' file names do (eight digits and a
-- letter): a false alarm, most likely, but the rule is to protect what is
-- in doubt. Left out: the documents and the bulletin announcements, whose
-- files and texts often list the beneficiaries, and the portal's standard
-- legal notice (advertencia).

-- Each call is parsed once, into the fields that are published: a call
-- with thousands of documents would otherwise be parsed again for every
-- field, and a long history runs out of memory.
CREATE OR REPLACE TABLE publish.convocatorias AS
WITH parsed AS (
    SELECT
        from_json(r, '{"id": "BIGINT", "codigoBDNS": "VARCHAR", "fechaRecepcion": "VARCHAR", "organo": {"nivel1": "VARCHAR", "nivel2": "VARCHAR", "nivel3": "VARCHAR"}, "sedeElectronica": "VARCHAR", "descripcion": "VARCHAR", "descripcionLeng": "VARCHAR", "tipoConvocatoria": "VARCHAR", "presupuestoTotal": "VARCHAR", "mrr": "BOOLEAN", "instrumentos": [{"descripcion": "VARCHAR"}], "tiposBeneficiarios": [{"descripcion": "VARCHAR"}], "sectores": [{"codigo": "VARCHAR", "descripcion": "VARCHAR"}], "regiones": [{"descripcion": "VARCHAR"}], "descripcionFinalidad": "VARCHAR", "descripcionBasesReguladoras": "VARCHAR", "urlBasesReguladoras": "VARCHAR", "sePublicaDiarioOficial": "BOOLEAN", "abierto": "BOOLEAN", "fechaInicioSolicitud": "VARCHAR", "fechaFinSolicitud": "VARCHAR", "textInicio": "VARCHAR", "textFin": "VARCHAR", "ayudaEstado": "VARCHAR", "urlAyudaEstado": "VARCHAR", "fondos": [{"descripcion": "VARCHAR"}], "reglamento": {"descripcion": "VARCHAR", "orden": "VARCHAR"}, "objetivos": [{"descripcion": "VARCHAR"}], "sectoresProductos": [{"descripcion": "VARCHAR"}]}') AS c,
        is_current
    FROM latest_versions('sync.convocatorias')
)
SELECT
    c.id                                            AS id,
    c.codigoBDNS                                    AS codigoBDNS,
    TRY_CAST(c.fechaRecepcion AS DATE)              AS fechaRecepcion,
    c.organo                                        AS organo,
    c.sedeElectronica                               AS sedeElectronica,
    without_personal_id(c.descripcion)              AS descripcion,
    without_personal_id(c.descripcionLeng)          AS descripcionLeng,
    c.tipoConvocatoria                              AS tipoConvocatoria,
    TRY_CAST(c.presupuestoTotal AS DECIMAL(18, 2))  AS presupuestoTotal,
    c.mrr                                           AS mrr,
    c.instrumentos                                  AS instrumentos,
    c.tiposBeneficiarios                            AS tiposBeneficiarios,
    c.sectores                                      AS sectores,
    c.regiones                                      AS regiones,
    c.descripcionFinalidad                          AS descripcionFinalidad,
    without_personal_id(c.descripcionBasesReguladoras) AS descripcionBasesReguladoras,
    without_personal_id(c.urlBasesReguladoras)      AS urlBasesReguladoras,
    c.sePublicaDiarioOficial                        AS sePublicaDiarioOficial,
    c.abierto                                       AS abierto,
    TRY_CAST(c.fechaInicioSolicitud AS DATE)        AS fechaInicioSolicitud,
    TRY_CAST(c.fechaFinSolicitud AS DATE)           AS fechaFinSolicitud,
    without_personal_id(c.textInicio)               AS textInicio,
    without_personal_id(c.textFin)                  AS textFin,
    c.ayudaEstado                                   AS ayudaEstado,
    c.urlAyudaEstado                                AS urlAyudaEstado,
    c.fondos                                        AS fondos,
    c.reglamento                                    AS reglamento,
    c.objetivos                                     AS objetivos,
    c.sectoresProductos                             AS sectoresProductos,
    NOT is_current                                  AS retirada
FROM parsed;
