-- The BDNS list of large beneficiaries: each one's total gross grant
-- equivalent in a year, one row per beneficiary and year, from bdns-sync's
-- grandesbeneficiarios_busqueda table (see 04_versions.sql).
--
-- Private: the list also names natural persons and communities of
-- property. Only legal persons are published (27_grandesbeneficiarios.sql);
-- a summary of the rest would add nothing, since each row is already one
-- beneficiary's total.

CREATE OR REPLACE TABLE grandesbeneficiarios AS
WITH parsed AS (
    SELECT from_json(r, '{"beneficiario": "VARCHAR", "idPersona": "VARCHAR", "ejercicio": "VARCHAR", "ayudaETotal": "VARCHAR"}') AS c, is_current
    FROM latest_versions('sync.grandesbeneficiarios_busqueda')
)
SELECT
    c.beneficiario                                        AS beneficiario,
    beneficiary_kind(c.beneficiario)                      AS tipoPersona,
    TRY_CAST(c.idPersona AS BIGINT)                       AS idPersona,
    TRY_CAST(c.ejercicio AS INTEGER)                      AS ejercicio,
    TRY_CAST(c.ayudaETotal AS DECIMAL(18, 2))             AS ayudaETotal,
    NOT is_current                                            AS retirada
FROM parsed;
