-- Awards, state aid and de minimis aid to legal persons and public bodies,
-- record by record. They are
-- not personal data, and who receives what from whom is what the dataset
-- is most useful for. See docs/adr/0002-anonymised-dataset.md.
--
-- Left out even here: url_br, since the bulletin it links to usually lists
-- natural persons among the beneficiaries, and id_persona, a BDNS internal
-- identifier that adds nothing the tax ID does not already give.

CREATE OR REPLACE TABLE publicar.concesiones_entidades AS
SELECT
    id,
    cod_concesion,
    fecha_concesion,
    anio,
    beneficiary_id(beneficiario)                            AS nif,
    beneficiary_name(beneficiario)                          AS nombre,
    tipo_beneficiario,
    importe,
    ayuda_equivalente,
    instrumento,
    numero_convocatoria,
    convocatoria,
    nivel1,
    nivel2,
    nivel3,
    fecha_alta,
    retirada
FROM concesiones
WHERE NOT is_protected(tipo_beneficiario);

-- State aid to legal persons and public bodies. The link to the European
-- Commission's case (url_ayuda_estado) is about the aid scheme, not the
-- beneficiary, so it stays.
CREATE OR REPLACE TABLE publicar.ayudas_estado_entidades AS
SELECT
    id_concesion,
    cod_concesion,
    fecha_concesion,
    anio,
    beneficiary_id(beneficiario)                            AS nif,
    beneficiary_name(beneficiario)                          AS nombre,
    tipo_beneficiario,
    categoria_beneficiario,
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
WHERE NOT is_protected(tipo_beneficiario);

-- De minimis aid to legal persons and public bodies.
CREATE OR REPLACE TABLE publicar.minimis_entidades AS
SELECT
    id_concesion,
    cod_concesion,
    fecha_concesion,
    anio,
    beneficiary_id(beneficiario)                            AS nif,
    beneficiary_name(beneficiario)                          AS nombre,
    tipo_beneficiario,
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
WHERE NOT is_protected(tipo_beneficiario);
