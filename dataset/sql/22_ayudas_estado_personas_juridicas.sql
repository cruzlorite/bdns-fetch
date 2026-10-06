-- State aid to legal persons, public bodies included, record by record
-- (see 20_concesiones_personas_juridicas.sql). The link to the European
-- Commission's case is about the aid scheme, not the beneficiary, so it
-- stays.

CREATE OR REPLACE TABLE publish.ayudas_estado_personas_juridicas AS
SELECT
    id_concesion,
    cod_concesion,
    fecha_concesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipo_persona,
    tipo_beneficiario,
    importe,
    ayuda_equivalente,
    instrumento,
    numero_convocatoria,
    convocatoria,
    convocante,
    reglamento,
    objetivo,
    region,
    sectores,
    ayuda_estado,
    url_ayuda_estado,
    entidad,
    intermediario,
    fecha_alta,
    retirada
FROM ayudas_estado
WHERE NOT is_protected_beneficiary(tipo_persona, beneficiario);
