-- State aid with typed columns, one row per award: the last known version
-- of each in bdns-sync's ayudasestado_busqueda table, withdrawn ones
-- included (see 04_versions.sql for how the last version is chosen).
-- tipoBeneficiario is the BDNS's own category (SME, large company...);
-- tipoPersona is this dataset's classification.
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE ayudasestado AS
WITH parsed AS (
    SELECT from_json(r, '{"idConcesion": "VARCHAR", "codConcesion": "VARCHAR", "fechaConcesion": "VARCHAR", "beneficiario": "VARCHAR", "idPersona": "VARCHAR", "importe": "VARCHAR", "ayudaEquivalente": "VARCHAR", "instrumento": "VARCHAR", "numeroConvocatoria": "VARCHAR", "convocatoria": "VARCHAR", "convocante": "VARCHAR", "reglamento": "VARCHAR", "objetivo": "VARCHAR", "tipoBeneficiario": "VARCHAR", "region": "VARCHAR", "sectores": "VARCHAR", "ayudaEstado": "VARCHAR", "urlAyudaEstado": "VARCHAR", "entidad": "VARCHAR", "intermediario": "VARCHAR", "fechaAlta": "VARCHAR"}') AS c, is_current
    FROM latest_versions('sync.ayudasestado_busqueda')
)
SELECT
    CAST(c.idConcesion AS BIGINT)                         AS idConcesion,
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
    c.convocante                                          AS convocante,
    c.reglamento                                          AS reglamento,
    trim(c.objetivo)                                      AS objetivo,
    c.tipoBeneficiario                                    AS tipoBeneficiario,
    c.region                                              AS region,
    c.sectores                                            AS sectores,
    c.ayudaEstado                                         AS ayudaEstado,
    c.urlAyudaEstado                                      AS urlAyudaEstado,
    c.entidad                                             AS entidad,
    c.intermediario                                       AS intermediario,
    TRY_CAST(c.fechaAlta AS DATE)                         AS fechaAlta,
    NOT is_current                                            AS retirada
FROM parsed;
