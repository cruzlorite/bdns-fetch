-- State aid with typed columns, one row per award: the last known version
-- of each in bdns-sync's ayudasestado_busqueda table, withdrawn ones
-- included (see 04_versions.sql for how the last version is chosen).
-- tipoBeneficiario is the BDNS's own category (SME, large company...);
-- tipoPersona is this dataset's classification.
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE ayudasestado AS
SELECT
    CAST(r->>'idConcesion' AS BIGINT)                         AS idConcesion,
    r->>'codConcesion'                                        AS codConcesion,
    TRY_CAST(r->>'fechaConcesion' AS DATE)                    AS fechaConcesion,
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipoPersona,
    TRY_CAST(r->>'idPersona' AS BIGINT)                       AS idPersona,
    TRY_CAST(r->>'importe' AS DECIMAL(18, 2))                 AS importe,
    TRY_CAST(r->>'ayudaEquivalente' AS DECIMAL(18, 2))        AS ayudaEquivalente,
    trim(r->>'instrumento')                                   AS instrumento,
    r->>'numeroConvocatoria'                                  AS numeroConvocatoria,
    r->>'convocatoria'                                        AS convocatoria,
    r->>'convocante'                                          AS convocante,
    r->>'reglamento'                                          AS reglamento,
    trim(r->>'objetivo')                                      AS objetivo,
    r->>'tipoBeneficiario'                                    AS tipoBeneficiario,
    r->>'region'                                              AS region,
    r->>'sectores'                                            AS sectores,
    r->>'ayudaEstado'                                         AS ayudaEstado,
    r->>'urlAyudaEstado'                                      AS urlAyudaEstado,
    r->>'entidad'                                             AS entidad,
    r->>'intermediario'                                       AS intermediario,
    TRY_CAST(r->>'fechaAlta' AS DATE)                         AS fechaAlta,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.ayudasestado_busqueda');
