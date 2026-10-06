-- De minimis aid with typed columns, one row per award: the last known
-- version of each in bdns-sync's minimis_busqueda table, withdrawn ones
-- included (see 04_versions.sql for how the last version is chosen).
-- De minimis records carry the aid's gross grant equivalent, not an amount.
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE minimis AS
WITH parsed AS (
    SELECT from_json(r, '{"idConcesion": "VARCHAR", "codigoConcesion": "VARCHAR", "fechaConcesion": "VARCHAR", "beneficiario": "VARCHAR", "idPersona": "VARCHAR", "ayudaEquivalente": "VARCHAR", "instrumento": "VARCHAR", "numeroConvocatoria": "VARCHAR", "convocante": "VARCHAR", "reglamento": "VARCHAR", "sectorActividad": "VARCHAR", "sectorProducto": "VARCHAR", "fechaRegistro": "VARCHAR"}') AS c, is_current
    FROM latest_versions('sync.minimis_busqueda')
)
SELECT
    CAST(c.idConcesion AS BIGINT)                         AS idConcesion,
    c.codigoConcesion                                     AS codigoConcesion,
    TRY_CAST(c.fechaConcesion AS DATE)                    AS fechaConcesion,
    c.beneficiario                                        AS beneficiario,
    beneficiary_kind(c.beneficiario)                      AS tipoPersona,
    TRY_CAST(c.idPersona AS BIGINT)                       AS idPersona,
    TRY_CAST(c.ayudaEquivalente AS DECIMAL(18, 2))        AS ayudaEquivalente,
    trim(c.instrumento)                                   AS instrumento,
    c.numeroConvocatoria                                  AS numeroConvocatoria,
    c.convocante                                          AS convocante,
    c.reglamento                                          AS reglamento,
    c.sectorActividad                                     AS sectorActividad,
    c.sectorProducto                                      AS sectorProducto,
    TRY_CAST(c.fechaRegistro AS DATE)                     AS fechaRegistro,
    NOT is_current                                            AS retirada
FROM parsed;
