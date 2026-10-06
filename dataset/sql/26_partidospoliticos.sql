-- Awards to political parties and their foundations, record by record.
-- All of them are legal persons; should a protected beneficiary ever turn
-- up, it is left out, and the checks would flag any personal ID. Without
-- urlBR, like the other record-level tables.

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
