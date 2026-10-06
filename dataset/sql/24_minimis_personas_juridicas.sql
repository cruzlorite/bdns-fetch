-- De minimis aid to legal persons, public bodies included, record by
-- record (see 20_concesiones_personas_juridicas.sql).

CREATE OR REPLACE TABLE publish.minimis_personas_juridicas AS
SELECT
    id_concesion,
    codigo_concesion,
    fecha_concesion,
    beneficiary_id(beneficiario)   AS nif,
    beneficiary_name(beneficiario) AS nombre,
    tipo_persona,
    ayuda_equivalente,
    instrumento,
    numero_convocatoria,
    convocante,
    reglamento,
    sector_actividad,
    sector_producto,
    fecha_registro,
    retirada
FROM minimis
WHERE NOT is_protected_beneficiary(tipo_persona, beneficiario);
