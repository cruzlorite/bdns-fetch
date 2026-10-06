-- Awards to natural persons and to those protected like them, only as
-- one summary per call: the rules are in 05_summaries.sql. The same holds
-- for state aid (23) and de minimis aid (25).

-- Each protected award, in the shape call_summaries() takes. Private.
CREATE OR REPLACE TABLE concesiones_protegidas AS
SELECT
    numero_convocatoria,
    instrumento,
    coalesce(CAST(id_persona AS VARCHAR), beneficiario) AS persona,
    fecha_concesion,
    importe,
    ayuda_equivalente,
    struct_pack(convocatoria, nivel1, nivel2, nivel3) AS etiqueta
FROM concesiones
WHERE is_protected_beneficiary(tipo_persona, beneficiario);

-- A call title shaped like a personal tax ID is blanked; the checks
-- would stop the build otherwise.
CREATE OR REPLACE TABLE publish.concesiones_personas_fisicas AS
SELECT
    numero_convocatoria,
    CASE WHEN has_personal_id(etiqueta.convocatoria) THEN NULL ELSE etiqueta.convocatoria END AS convocatoria,
    etiqueta.nivel1 AS nivel1,
    etiqueta.nivel2 AS nivel2,
    etiqueta.nivel3 AS nivel3,
    instrumento,
    es_resto,
    ejercicio,
    concesiones,
    beneficiarios,
    importe.total      AS importe_total,
    importe.media      AS importe_media,
    importe.desviacion AS importe_desviacion,
    importe.p10        AS importe_p10,
    importe.p25        AS importe_p25,
    importe.mediana    AS importe_mediana,
    importe.p75        AS importe_p75,
    importe.p90        AS importe_p90,
    ayuda_equivalente.total      AS ayuda_equivalente_total,
    ayuda_equivalente.media      AS ayuda_equivalente_media,
    ayuda_equivalente.desviacion AS ayuda_equivalente_desviacion,
    ayuda_equivalente.p10        AS ayuda_equivalente_p10,
    ayuda_equivalente.p25        AS ayuda_equivalente_p25,
    ayuda_equivalente.mediana    AS ayuda_equivalente_mediana,
    ayuda_equivalente.p75        AS ayuda_equivalente_p75,
    ayuda_equivalente.p90        AS ayuda_equivalente_p90,
    fecha.p10        AS fecha_p10,
    fecha.p25        AS fecha_p25,
    fecha.mediana    AS fecha_mediana,
    fecha.p75        AS fecha_p75,
    fecha.p90        AS fecha_p90
FROM call_summaries('concesiones_protegidas');
