-- Awards to natural persons and to those protected like them, only as
-- one summary per call: the rules are in 05_summaries.sql. The same holds
-- for state aid (23) and de minimis aid (25).

-- Each protected award, in the shape call_summaries() takes. Private.
CREATE OR REPLACE TABLE concesiones_protegidas AS
SELECT
    numeroConvocatoria,
    instrumento,
    coalesce(CAST(idPersona AS VARCHAR), beneficiario) AS persona,
    fechaConcesion,
    importe,
    ayudaEquivalente,
    struct_pack(convocatoria, nivel1, nivel2, nivel3) AS etiqueta
FROM concesiones
WHERE is_protected_beneficiary(tipoPersona, beneficiario);

-- A call title shaped like a personal tax ID is blanked; the checks
-- would stop the build otherwise.
CREATE OR REPLACE TABLE publish.concesiones_personas_fisicas AS
SELECT
    numeroConvocatoria,
    without_personal_id(etiqueta.convocatoria) AS convocatoria,
    etiqueta.nivel1 AS nivel1,
    etiqueta.nivel2 AS nivel2,
    etiqueta.nivel3 AS nivel3,
    instrumento,
    esResto,
    ejercicio,
    concesiones,
    beneficiarios,
    importe.total      AS importeTotal,
    importe.media      AS importeMedia,
    importe.desviacion AS importeDesviacion,
    importe.p10        AS importeP10,
    importe.p25        AS importeP25,
    importe.mediana    AS importeMediana,
    importe.p75        AS importeP75,
    importe.p90        AS importeP90,
    ayudaEquivalente.total      AS ayudaEquivalenteTotal,
    ayudaEquivalente.media      AS ayudaEquivalenteMedia,
    ayudaEquivalente.desviacion AS ayudaEquivalenteDesviacion,
    ayudaEquivalente.p10        AS ayudaEquivalenteP10,
    ayudaEquivalente.p25        AS ayudaEquivalenteP25,
    ayudaEquivalente.mediana    AS ayudaEquivalenteMediana,
    ayudaEquivalente.p75        AS ayudaEquivalenteP75,
    ayudaEquivalente.p90        AS ayudaEquivalenteP90,
    fechaConcesion.p10     AS fechaConcesionP10,
    fechaConcesion.p25     AS fechaConcesionP25,
    fechaConcesion.mediana AS fechaConcesionMediana,
    fechaConcesion.p75     AS fechaConcesionP75,
    fechaConcesion.p90     AS fechaConcesionP90
FROM call_summaries('concesiones_protegidas');
