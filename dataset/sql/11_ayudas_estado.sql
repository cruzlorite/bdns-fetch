-- State aid with typed columns, one row per award: the last known version
-- of each in bdns-sync's ayudasestado_busqueda table, withdrawn ones
-- included (see 04_versions.sql for how the last version is chosen).
-- tipo_beneficiario is the BDNS's own category (SME, large company...);
-- tipo_persona is this dataset's classification.
--
-- Private: it still holds personal data, like concesiones.

CREATE OR REPLACE TABLE ayudas_estado AS
SELECT
    CAST(r->>'idConcesion' AS BIGINT)                         AS id_concesion,
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
    r->>'convocante'                                          AS convocante,
    r->>'reglamento'                                          AS reglamento,
    trim(r->>'objetivo')                                      AS objetivo,
    r->>'tipoBeneficiario'                                    AS tipo_beneficiario,
    r->>'region'                                              AS region,
    r->>'sectores'                                            AS sectores,
    r->>'ayudaEstado'                                         AS ayuda_estado,
    r->>'urlAyudaEstado'                                      AS url_ayuda_estado,
    r->>'entidad'                                             AS entidad,
    r->>'intermediario'                                       AS intermediario,
    TRY_CAST(r->>'fechaAlta' AS DATE)                         AS fecha_alta,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.ayudasestado_busqueda');
