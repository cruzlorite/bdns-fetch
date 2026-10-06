-- Awards with typed columns, one row per award: the last known version of
-- each in bdns-sync's concesiones_busqueda table, including awards the API
-- has since withdrawn. That is what makes the history worth publishing.
-- Columns keep the API's names in snake_case; the ones added here are in
-- Spanish too, like all the data.
--
-- How the last version is chosen is in 04_versions.sql.
-- Each record is parsed once, into the fields it uses: extracting each
-- field with ->> would parse it again for every one, and thirty million
-- awards run out of memory that way. The other entities do the same.
--
-- This table still holds personal data (beneficiario, idPersona,
-- urlBR...) and never leaves the private build. The published tables are
-- built from it, and the privacy checks run on those.

CREATE OR REPLACE TABLE concesiones AS
WITH parsed AS (
    SELECT from_json(r, '{"id": "VARCHAR", "codConcesion": "VARCHAR", "fechaConcesion": "VARCHAR", "beneficiario": "VARCHAR", "idPersona": "VARCHAR", "importe": "VARCHAR", "ayudaEquivalente": "VARCHAR", "instrumento": "VARCHAR", "numeroConvocatoria": "VARCHAR", "convocatoria": "VARCHAR", "nivel1": "VARCHAR", "nivel2": "VARCHAR", "nivel3": "VARCHAR", "urlBR": "VARCHAR", "fechaAlta": "VARCHAR"}') AS c, is_current
    FROM latest_versions('sync.concesiones_busqueda')
)
SELECT
    CAST(c.id AS BIGINT)                                  AS id,
    c.codConcesion                                        AS codConcesion,
    TRY_CAST(c.fechaConcesion AS DATE)                    AS fechaConcesion,
    c.beneficiario                                        AS beneficiario,
    beneficiary_kind(c.beneficiario)                      AS tipoPersona,
    TRY_CAST(c.idPersona AS BIGINT)                       AS idPersona,
    TRY_CAST(c.importe AS DECIMAL(18, 2))                 AS importe,
    TRY_CAST(c.ayudaEquivalente AS DECIMAL(18, 2))        AS ayudaEquivalente,
    trim(c.instrumento)                                   AS instrumento,
    c.numeroConvocatoria                                  AS numeroConvocatoria,
    c.convocatoria                                        AS convocatoria,
    c.nivel1                                              AS nivel1,
    c.nivel2                                              AS nivel2,
    c.nivel3                                              AS nivel3,
    c.urlBR                                               AS urlBR,
    TRY_CAST(c.fechaAlta AS DATE)                         AS fechaAlta,
    NOT is_current                                            AS retirada
FROM parsed;
