-- De minimis aid to legal persons, public bodies included, record by
-- record (see 20_concesiones_personas_juridicas.sql).

CREATE OR REPLACE TABLE publish.minimis_personas_juridicas AS
SELECT
    idConcesion,
    codigoConcesion,
    fechaConcesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    ayudaEquivalente,
    instrumento,
    numeroConvocatoria,
    convocante,
    reglamento,
    sectorActividad,
    sectorProducto,
    fechaRegistro,
    retirada
FROM minimis
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);
