-- De minimis aid with typed columns, one row per award: the last known
-- version of each in bdns-sync's minimis_busqueda table, withdrawn ones
-- included (see 10_concesiones.sql for how the last version is chosen).
-- De minimis records carry the aid's gross grant equivalent, not an amount.
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE minimis AS
WITH ultimas AS (
    SELECT CAST(payload AS JSON) AS r, CAST(_is_current AS BOOLEAN) AS vigente
    FROM sync.minimis_busqueda
    QUALIFY row_number() OVER (PARTITION BY _natural_key ORDER BY _valid_from DESC) = 1
)
SELECT
    CAST(r->>'idConcesion' AS BIGINT)                         AS id_concesion,
    r->>'codigoConcesion'                                     AS cod_concesion,
    TRY_CAST(r->>'fechaConcesion' AS DATE)                    AS fecha_concesion,
    year(TRY_CAST(r->>'fechaConcesion' AS DATE))              AS anio,
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipo_beneficiario,
    TRY_CAST(r->>'idPersona' AS BIGINT)                       AS id_persona,
    TRY_CAST(r->>'ayudaEquivalente' AS DECIMAL(18, 2))        AS ayuda_equivalente,
    trim(r->>'instrumento')                                   AS instrumento,
    r->>'numeroConvocatoria'                                  AS numero_convocatoria,
    r->>'convocante'                                          AS convocante,
    r->>'reglamento'                                          AS reglamento,
    r->>'sectorActividad'                                     AS sector_actividad,
    r->>'sectorProducto'                                      AS sector_producto,
    TRY_CAST(r->>'fechaRegistro' AS DATE)                     AS fecha_registro,
    NOT vigente                                               AS retirada
FROM ultimas;
