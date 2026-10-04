-- Awards with typed columns, one row per award: the last known version of
-- each, as extract.py copied it into raw_concesiones_busqueda, including
-- awards the API has since withdrawn (withdrawn = true).
--
-- This table still holds personal data (beneficiario, idPersona, urlBR...)
-- and never leaves the private build. The published tables are built from
-- it, and the privacy checks run on those.

CREATE OR REPLACE TABLE concesiones AS
SELECT
    CAST(payload->>'id' AS BIGINT)                 AS id,
    payload->>'codConcesion'                       AS cod_concesion,
    TRY_CAST(payload->>'fechaConcesion' AS DATE)   AS fecha_concesion,
    year(TRY_CAST(payload->>'fechaConcesion' AS DATE)) AS anio,
    payload->>'beneficiario'                       AS beneficiario,
    beneficiary_kind(payload->>'beneficiario')     AS tipo_beneficiario,
    CAST(payload->>'idPersona' AS BIGINT)          AS id_persona,
    TRY_CAST(payload->>'importe' AS DECIMAL(18, 2)) AS importe,
    TRY_CAST(payload->>'ayudaEquivalente' AS DECIMAL(18, 2)) AS ayuda_equivalente,
    trim(payload->>'instrumento')                  AS instrumento,
    payload->>'numeroConvocatoria'                 AS numero_convocatoria,
    payload->>'convocatoria'                       AS convocatoria,
    payload->>'nivel1'                             AS nivel1,
    payload->>'nivel2'                             AS nivel2,
    payload->>'nivel3'                             AS nivel3,
    payload->>'urlBR'                              AS url_br,
    TRY_CAST(payload->>'fechaAlta' AS DATE)        AS fecha_alta,
    -- A key's last version is not the current one only when the API
    -- stopped serving it: a corrected key would have a newer version.
    NOT is_current                                 AS retirada
FROM raw_concesiones_busqueda;
