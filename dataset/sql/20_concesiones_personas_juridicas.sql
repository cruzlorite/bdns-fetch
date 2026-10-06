-- Awards to legal persons, public bodies included, record by record. They
-- are not personal data, and who receives what from whom is what the
-- dataset is most useful for. A company whose field carries a natural
-- person's tax ID is left out, and summarised with the natural persons
-- (is_protected_beneficiary, in 02_privacy.sql). The same holds for state
-- aid (22) and de minimis aid (24).
-- See docs/adr/0020-anonymised-dataset.md.
--
-- Left out even here: urlBR, since the bulletin it links to usually lists
-- natural persons among the beneficiaries, and idPersona, a BDNS internal
-- identifier that adds nothing the tax ID does not already give.

CREATE OR REPLACE TABLE publish.concesiones_personas_juridicas AS
SELECT
    id,
    codConcesion,
    fechaConcesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    importe,
    ayudaEquivalente,
    instrumento,
    numeroConvocatoria,
    convocatoria,
    nivel1,
    nivel2,
    nivel3,
    fechaAlta,
    retirada
FROM concesiones
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);
