-- Awards with typed columns, one row per award: the last known version of
-- each in bdns-sync's concesiones_busqueda table, including awards the API
-- has since withdrawn. That is what makes the history worth publishing.
--
-- A key's newest version is its current one or, if the API stopped
-- serving it, its last one; a corrected key always has a newer version,
-- so the newest version is not the current one only when it was withdrawn.
--
-- This table still holds personal data (beneficiario, id_persona,
-- url_br...) and never leaves the private build. The published tables are
-- built from it, and the privacy checks run on those.

CREATE OR REPLACE TABLE concesiones AS
WITH ultimas AS (
    SELECT CAST(payload AS JSON) AS r, CAST(_is_current AS BOOLEAN) AS vigente
    FROM sync.concesiones_busqueda
    QUALIFY row_number() OVER (PARTITION BY _natural_key ORDER BY _valid_from DESC) = 1
)
SELECT
    CAST(r->>'id' AS BIGINT)                                  AS id,
    r->>'codConcesion'                                        AS cod_concesion,
    TRY_CAST(r->>'fechaConcesion' AS DATE)                    AS fecha_concesion,
    year(TRY_CAST(r->>'fechaConcesion' AS DATE))              AS anio,
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipo_beneficiario,
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
    NOT vigente                                               AS retirada
FROM ultimas;
