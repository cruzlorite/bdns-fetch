-- Awards to political parties and their foundations, with typed columns,
-- one row per award: the last known version of each in bdns-sync's
-- partidospoliticos_busqueda table, withdrawn ones included (see
-- 04_versions.sql).
--
-- Private, like concesiones: the beneficiary field is classified here, and
-- only legal persons are published (26_partidospoliticos.sql).

CREATE OR REPLACE TABLE partidospoliticos AS
WITH parsed AS (
    SELECT from_json(r, '{"id": "VARCHAR", "codConcesion": "VARCHAR", "fechaConcesion": "VARCHAR", "beneficiario": "VARCHAR", "importe": "VARCHAR", "ayudaEquivalente": "VARCHAR", "instrumento": "VARCHAR", "tieneProyecto": "VARCHAR", "numeroConvocatoria": "VARCHAR", "idConvocatoria": "VARCHAR", "convocatoria": "VARCHAR", "nivel1": "VARCHAR", "nivel2": "VARCHAR", "nivel3": "VARCHAR", "urlBR": "VARCHAR"}') AS c, is_current
    FROM latest_versions('sync.partidospoliticos_busqueda')
)
SELECT
    CAST(c.id AS BIGINT)                                  AS id,
    c.codConcesion                                        AS codConcesion,
    TRY_CAST(c.fechaConcesion AS DATE)                    AS fechaConcesion,
    c.beneficiario                                        AS beneficiario,
    beneficiary_kind(c.beneficiario)                      AS tipoPersona,
    TRY_CAST(c.importe AS DECIMAL(18, 2))                 AS importe,
    TRY_CAST(c.ayudaEquivalente AS DECIMAL(18, 2))        AS ayudaEquivalente,
    trim(c.instrumento)                                   AS instrumento,
    TRY_CAST(c.tieneProyecto AS BOOLEAN)                  AS tieneProyecto,
    c.numeroConvocatoria                                  AS numeroConvocatoria,
    TRY_CAST(c.idConvocatoria AS BIGINT)                  AS idConvocatoria,
    c.convocatoria                                        AS convocatoria,
    c.nivel1                                              AS nivel1,
    c.nivel2                                              AS nivel2,
    c.nivel3                                              AS nivel3,
    c.urlBR                                               AS urlBR,
    NOT is_current                                            AS retirada
FROM parsed;
