-- The large beneficiaries that are legal persons, public bodies included:
-- their total gross grant equivalent per year. Without idPersona, like the
-- other record-level tables.

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
