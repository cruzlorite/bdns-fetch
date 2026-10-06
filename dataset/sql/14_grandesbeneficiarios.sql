-- The BDNS list of large beneficiaries: each one's total gross grant
-- equivalent in a year, one row per beneficiary and year, from bdns-sync's
-- grandesbeneficiarios_busqueda table (see 04_versions.sql).
--
-- Private: the list also names natural persons and communities of
-- property. Only legal persons are published (27_grandesbeneficiarios.sql);
-- a summary of the rest would add nothing, since each row is already one
-- beneficiary's total.

CREATE OR REPLACE TABLE grandesbeneficiarios AS
SELECT
    r->>'beneficiario'                                        AS beneficiario,
    beneficiary_kind(r->>'beneficiario')                      AS tipoPersona,
    TRY_CAST(r->>'idPersona' AS BIGINT)                       AS idPersona,
    TRY_CAST(r->>'ejercicio' AS INTEGER)                      AS ejercicio,
    TRY_CAST(r->>'ayudaETotal' AS DECIMAL(18, 2))             AS ayudaETotal,
    NOT is_current                                            AS retirada
FROM latest_versions('sync.grandesbeneficiarios_busqueda');
