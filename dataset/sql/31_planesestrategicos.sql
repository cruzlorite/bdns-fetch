-- Strategic subsidy plans, record by record: the last known version of each
-- plan's detail in bdns-sync's planesestrategicos table (see
-- 04_versions.sql). They are the administrations' own documents. Left out:
-- the attached documents and the portal's standard legal notice.

CREATE OR REPLACE TABLE publish.planesestrategicos AS
SELECT
    CAST(r->>'idPES' AS BIGINT)                               AS idPES,
    without_personal_id(r->>'descripcion')                    AS descripcion,
    without_personal_id(r->>'descripcionCooficial')           AS descripcionCooficial,
    r->>'tipoPlan'                                            AS tipoPlan,
    TRY_CAST(r->>'vigenciaDesde' AS INTEGER)                  AS vigenciaDesde,
    TRY_CAST(r->>'vigenciaHasta' AS INTEGER)                  AS vigenciaHasta,
    TRY_CAST(r->>'fechaAprobacion' AS DATE)                   AS fechaAprobacion,
    CAST(r->'ambitos' AS VARCHAR[])                           AS ambitos,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.planesestrategicos');
