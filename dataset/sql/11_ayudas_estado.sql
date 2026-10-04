-- State aid with typed columns, one row per award: the last known version
-- of each in bdns-sync's ayudasestado_busqueda table, withdrawn ones
-- included (see 10_concesiones.sql for how the last version is chosen).
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE ayudas_estado AS
WITH ultimas AS (
    SELECT CAST(payload AS JSON) AS r, CAST(_is_current AS BOOLEAN) AS vigente
    FROM sync.ayudasestado_busqueda
    QUALIFY row_number() OVER (PARTITION BY _natural_key ORDER BY _valid_from DESC) = 1
)
SELECT
    CAST(r->>'idConcesion' AS BIGINT)                         AS id_concesion,
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
    r->>'convocante'                                          AS convocante,
    r->>'reglamento'                                          AS reglamento,
    trim(r->>'objetivo')                                      AS objetivo,
    -- The BDNS's own category of beneficiary (SME, large company...).
    r->>'tipoBeneficiario'                                    AS categoria_beneficiario,
    r->>'region'                                              AS region,
    r->>'sectores'                                            AS sectores,
    r->>'ayudaEstado'                                         AS ayuda_estado,
    r->>'urlAyudaEstado'                                      AS url_ayuda_estado,
    r->>'entidad'                                             AS entidad,
    r->>'intermediario'                                       AS intermediario,
    TRY_CAST(r->>'fechaAlta' AS DATE)                         AS fecha_alta,
    NOT vigente                                               AS retirada
FROM ultimas;
