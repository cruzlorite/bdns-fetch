-- Awards to legal persons and public bodies, record by record. They are
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
    trim(substr(trim(beneficiario), length(split_part(trim(beneficiario), ' ', 1)) + 1)) AS nombre,
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
