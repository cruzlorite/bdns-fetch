-- Awards to political parties and their foundations, with typed columns,
-- one row per award: the last known version of each in bdns-sync's
-- partidospoliticos_busqueda table, withdrawn ones included (see
-- 04_versions.sql).
--
-- Private, like concesiones: the beneficiary field is classified here, and
-- only legal persons are published (26_partidospoliticos.sql).

CREATE OR REPLACE TABLE partidospoliticos AS
SELECT
    CAST(r->>'id' AS BIGINT)                                  AS id,
    r->>'codConcesion'                                        AS codConcesion,
    TRY_CAST(r->>'fechaConcesion' AS DATE)                    AS fechaConcesion,
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipoPersona,
    TRY_CAST(r->>'importe' AS DECIMAL(18, 2))                 AS importe,
    TRY_CAST(r->>'ayudaEquivalente' AS DECIMAL(18, 2))        AS ayudaEquivalente,
    trim(r->>'instrumento')                                   AS instrumento,
    TRY_CAST(r->>'tieneProyecto' AS BOOLEAN)                  AS tieneProyecto,
    r->>'numeroConvocatoria'                                  AS numeroConvocatoria,
    TRY_CAST(r->>'idConvocatoria' AS BIGINT)                  AS idConvocatoria,
    r->>'convocatoria'                                        AS convocatoria,
    r->>'nivel1'                                              AS nivel1,
    r->>'nivel2'                                              AS nivel2,
    r->>'nivel3'                                              AS nivel3,
    r->>'urlBR'                                               AS urlBR,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.partidospoliticos_busqueda');
