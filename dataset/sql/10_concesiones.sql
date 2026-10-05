-- Awards with typed columns, one row per award: the last known version of
-- each in bdns-sync's concesiones_busqueda table, including awards the API
-- has since withdrawn. That is what makes the history worth publishing.
-- Columns keep the API's names in snake_case; the ones added here are in
-- Spanish too, like all the data.
--
-- How the last version is chosen is in 04_versions.sql.
--
-- This table still holds personal data (beneficiario, id_persona,
-- url_br...) and never leaves the private build. The published tables are
-- built from it, and the privacy checks run on those.

CREATE OR REPLACE TABLE concesiones AS
SELECT
    CAST(r->>'id' AS BIGINT)                                  AS id,
    r->>'codConcesion'                                        AS cod_concesion,
    TRY_CAST(r->>'fechaConcesion' AS DATE)                    AS fecha_concesion,
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipo_persona,
    TRY_CAST(r->>'idPersona' AS BIGINT)                       AS id_persona,
    TRY_CAST(r->>'importe' AS DECIMAL(18, 2))                 AS importe,
    TRY_CAST(r->>'ayudaEquivalente' AS DECIMAL(18, 2))        AS ayuda_equivalente,
    trim(r->>'instrumento')                                   AS instrumento,
    r->>'numeroConvocatoria'                                  AS numero_convocatoria,
    r->>'convocatoria'                                        AS convocatoria,
    r->>'nivel1'                                              AS nivel1,
    r->>'nivel2'                                              AS nivel2,
    r->>'nivel3'                                              AS nivel3,
    r->>'urlBR'                                               AS url_br,
    TRY_CAST(r->>'fechaAlta' AS DATE)                         AS fecha_alta,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.concesiones_busqueda');
