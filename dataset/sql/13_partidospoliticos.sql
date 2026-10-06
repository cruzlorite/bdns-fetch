-- Awards to political parties and their foundations, from bdns-sync's
-- partidospoliticos_busqueda table, read like awards (see
-- 10_concesiones.sql). All of them are legal persons, and are published
-- record by record.

-- Private, like concesiones.
CREATE OR REPLACE TABLE partidospoliticos AS
SELECT
    * EXCLUDE (is_current) REPLACE (trim(instrumento) AS instrumento),
    beneficiary_kind(beneficiario) AS tipoPersona,
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, PARTIDOSPOLITICOS_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.partidospoliticos_busqueda')
);

-- Record by record, without urlBR; should a protected beneficiary ever
-- turn up, it is left out.
CREATE OR REPLACE TABLE publish.partidospoliticos AS
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
    tieneProyecto,
    numeroConvocatoria,
    idConvocatoria,
    convocatoria,
    nivel1,
    nivel2,
    nivel3,
    retirada
FROM partidospoliticos
WHERE NOT is_protected_beneficiary(tipoPersona, beneficiario);
