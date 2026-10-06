-- State aid to legal persons, public bodies included, record by record
-- (see 20_concesiones_personas_juridicas.sql). The link to the European
-- Commission's case is about the aid scheme, not the beneficiary, so it
-- stays.

CREATE OR REPLACE TABLE publish.ayudasestado_personas_juridicas AS
SELECT
    idConcesion,
    codConcesion,
    fechaConcesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipoPersona,
    tipoBeneficiario,
    importe,
    ayudaEquivalente,
    instrumento,
    numeroConvocatoria,
    convocatoria,
    convocante,
    reglamento,
    objetivo,
    region,
    sectores,
    ayudaEstado,
    urlAyudaEstado,
    entidad,
    intermediario,
    fechaAlta,
    retirada
FROM ayudasestado
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);
