-- De minimis aid with typed columns, one row per award: the last known
-- version of each in bdns-sync's minimis_busqueda table, withdrawn ones
-- included (see 04_versions.sql for how the last version is chosen).
-- De minimis records carry the aid's gross grant equivalent, not an amount.
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE minimis AS
SELECT
    CAST(r->>'idConcesion' AS BIGINT)                         AS idConcesion,
    r->>'codigoConcesion'                                     AS codigoConcesion,
    TRY_CAST(r->>'fechaConcesion' AS DATE)                    AS fechaConcesion,
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipoPersona,
    TRY_CAST(r->>'idPersona' AS BIGINT)                       AS idPersona,
    TRY_CAST(r->>'ayudaEquivalente' AS DECIMAL(18, 2))        AS ayudaEquivalente,
    trim(r->>'instrumento')                                   AS instrumento,
    r->>'numeroConvocatoria'                                  AS numeroConvocatoria,
    r->>'convocante'                                          AS convocante,
    r->>'reglamento'                                          AS reglamento,
    r->>'sectorActividad'                                     AS sectorActividad,
    r->>'sectorProducto'                                      AS sectorProducto,
    TRY_CAST(r->>'fechaRegistro' AS DATE)                     AS fechaRegistro,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.minimis_busqueda');
