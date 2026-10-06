-- De minimis aid to natural persons, most of them self-employed, and to
-- those protected like them, only as one summary per call (see
-- 21_concesiones_personas_fisicas.sql). De minimis records carry only the
-- aid's gross grant equivalent.

-- Each protected award, in the shape call_summaries() takes. Private.
CREATE OR REPLACE TABLE minimis_protegidas AS
SELECT
    numero_convocatoria,
    instrumento,
    coalesce(CAST(id_persona AS VARCHAR), beneficiario) AS persona,
    fecha_concesion,
    NULL::DECIMAL(18, 2) AS importe,
    ayuda_equivalente,
    struct_pack(convocante) AS etiqueta
FROM minimis
WHERE is_protected_beneficiary(tipo_persona, beneficiario);

-- De minimis records name no call title, only the calling body.
CREATE OR REPLACE TABLE publish.minimis_personas_fisicas AS
SELECT
    numero_convocatoria,
    etiqueta.convocante AS convocante,
    instrumento,
    es_resto,
    ejercicio,
    concesiones,
    beneficiarios,
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
FROM call_summaries('minimis_protegidas');
