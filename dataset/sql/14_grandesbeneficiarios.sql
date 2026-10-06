-- The BDNS list of large beneficiaries: each one's total gross grant
-- equivalent in a year, from bdns-sync's grandesbeneficiarios_busqueda
-- table. The list also names natural persons and communities of property;
-- only legal persons are published, and a summary of the rest would add
-- nothing, since each row is already one beneficiary's total.

-- Private, like concesiones.
CREATE OR REPLACE TABLE grandesbeneficiarios AS
SELECT
    * EXCLUDE (is_current),
    beneficiary_kind(beneficiario) AS tipoPersona,
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, GRANDESBENEFICIARIOS_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.grandesbeneficiarios_busqueda')
);

-- Legal persons, public bodies included, without idPersona.
CREATE OR REPLACE TABLE publish.grandesbeneficiarios AS
SELECT
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    ejercicio,
    ayudaETotal,
    retirada
FROM grandesbeneficiarios
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);
