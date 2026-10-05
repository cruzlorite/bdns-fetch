-- Awards to natural persons, communities of property, civil partnerships,
-- unrecognised beneficiaries and companies whose field carries a person's
-- tax ID, only as one summary row per call (and
-- per instrument, should a call mix several): how many awards, to how many
-- people, and how their amounts and dates are distributed. No row says
-- anything about a single person. See docs/adr/0020-anonymised-dataset.md.
--
-- The rules, with their thresholds as macros in 02_privacy.sql:
--
-- * A row is published only if it is_publishable(): enough people, none
--   of them holding most of its amount. A person is counted once, by their
--   BDNS identifier, or by the beneficiary field where it is missing.
-- * The smallest and largest amount or date are never published: each is
--   one person's. The 10th and 90th percentiles, which sit close to them,
--   only from min_beneficiaries_for_tails() people.
-- * Amount percentiles are interpolated; date percentiles are real award
--   dates (quantile_disc), since a date between two others means nothing.
-- * What is suppressed goes into one rest row per year (ejercicio: the
--   year of its calls' median award date), published only if it gathers at
--   least two suppressed calls (otherwise it would be that call, plain to
--   see) and is_publishable() itself.
--
-- Every statistic covers every award in its row, and no other table
-- summarises these awards, so nothing can be learnt by subtraction.

-- Each protected award, with the call it belongs to. Private.
CREATE OR REPLACE TABLE concesiones_protegidas AS
SELECT
    numero_convocatoria,
    instrumento,
    coalesce(CAST(id_persona AS VARCHAR), beneficiario) AS persona,
    importe,
    fecha_concesion,
    convocatoria,
    nivel1,
    nivel2,
    nivel3
FROM concesiones
WHERE is_protected_beneficiary(tipo_persona, beneficiario);

-- A row's amount statistics, the same for a call and for a rest row.
CREATE OR REPLACE MACRO amount_summary(amount) AS STRUCT_PACK(
    total := sum(amount),
    media := avg(amount),
    desviacion := stddev_samp(amount),
    p10 := quantile_cont(amount, 0.10),
    p25 := quantile_cont(amount, 0.25),
    mediana := quantile_cont(amount, 0.50),
    p75 := quantile_cont(amount, 0.75),
    p90 := quantile_cont(amount, 0.90)
);

-- Each call, whether it may be published, and the year its awards go to
-- if it may not. Private.
CREATE OR REPLACE TABLE convocatorias_protegidas AS
WITH per_person AS (
    SELECT numero_convocatoria, instrumento, persona, sum(importe) AS share
    FROM concesiones_protegidas
    GROUP BY ALL
),
people AS (
    SELECT
        numero_convocatoria,
        instrumento,
        count(*) AS beneficiarios,
        is_publishable(count(*), sum(share), max(share)) AS publishable
    FROM per_person
    GROUP BY ALL
)
SELECT
    c.numero_convocatoria,
    c.instrumento,
    any_value(c.convocatoria)                       AS convocatoria,
    any_value(c.nivel1)                             AS nivel1,
    any_value(c.nivel2)                             AS nivel2,
    any_value(c.nivel3)                             AS nivel3,
    count(*)                                        AS concesiones,
    any_value(p.beneficiarios)                      AS beneficiarios,
    any_value(p.publishable)                        AS publishable,
    amount_summary(c.importe)                       AS importe,
    quantile_disc(c.fecha_concesion, [0.10, 0.25, 0.50, 0.75, 0.90]) AS fechas,
    year(quantile_disc(c.fecha_concesion, 0.50))    AS ejercicio
FROM concesiones_protegidas c
JOIN people p
    ON  c.numero_convocatoria IS NOT DISTINCT FROM p.numero_convocatoria
    AND c.instrumento IS NOT DISTINCT FROM p.instrumento
GROUP BY c.numero_convocatoria, c.instrumento;

-- The rest of each year: the awards of its suppressed calls. Private.
CREATE OR REPLACE TABLE resto_protegido AS
WITH suppressed AS (
    SELECT c.*, v.ejercicio
    FROM concesiones_protegidas c
    JOIN convocatorias_protegidas v
        ON  c.numero_convocatoria IS NOT DISTINCT FROM v.numero_convocatoria
        AND c.instrumento IS NOT DISTINCT FROM v.instrumento
    WHERE NOT v.publishable
),
per_person AS (
    SELECT ejercicio, persona, sum(importe) AS share FROM suppressed GROUP BY ALL
),
people AS (
    SELECT ejercicio, count(*) AS beneficiarios, is_publishable(count(*), sum(share), max(share)) AS publishable
    FROM per_person
    GROUP BY ejercicio
),
calls AS (
    SELECT ejercicio, count(*) AS suppressed_calls
    FROM convocatorias_protegidas WHERE NOT publishable GROUP BY ejercicio
)
SELECT
    s.ejercicio,
    count(*)                                        AS concesiones,
    any_value(p.beneficiarios)                      AS beneficiarios,
    any_value(p.publishable) AND any_value(c.suppressed_calls) >= 2 AS publishable,
    amount_summary(s.importe)                       AS importe,
    quantile_disc(s.fecha_concesion, [0.10, 0.25, 0.50, 0.75, 0.90]) AS fechas
FROM suppressed s
JOIN people p ON s.ejercicio IS NOT DISTINCT FROM p.ejercicio
JOIN calls c ON s.ejercicio IS NOT DISTINCT FROM c.ejercicio
GROUP BY s.ejercicio;

-- The published rows: the calls that may be published, then the rest rows
-- that may. A call title shaped like a personal tax ID is blanked; the
-- checks would stop the build otherwise.
CREATE OR REPLACE TABLE publish.concesiones_personas AS
WITH published AS (
    SELECT
        numero_convocatoria,
        CASE WHEN has_personal_id(convocatoria) THEN NULL ELSE convocatoria END AS convocatoria,
        nivel1, nivel2, nivel3, instrumento,
        false AS es_resto, NULL AS ejercicio,
        concesiones, beneficiarios, importe, fechas
    FROM convocatorias_protegidas
    WHERE publishable
    UNION ALL
    SELECT
        NULL, NULL, NULL, NULL, NULL, NULL,
        true, ejercicio,
        concesiones, beneficiarios, importe, fechas
    FROM resto_protegido
    WHERE publishable
)
SELECT
    numero_convocatoria,
    convocatoria,
    nivel1,
    nivel2,
    nivel3,
    instrumento,
    es_resto,
    ejercicio,
    concesiones,
    beneficiarios,
    importe.total                                   AS importe_total,
    importe.media                                   AS importe_media,
    importe.desviacion                              AS importe_desviacion,
    CASE WHEN beneficiarios >= min_beneficiaries_for_tails() THEN importe.p10 END AS importe_p10,
    importe.p25                                     AS importe_p25,
    importe.mediana                                 AS importe_mediana,
    importe.p75                                     AS importe_p75,
    CASE WHEN beneficiarios >= min_beneficiaries_for_tails() THEN importe.p90 END AS importe_p90,
    CASE WHEN beneficiarios >= min_beneficiaries_for_tails() THEN fechas[1] END AS fecha_p10,
    fechas[2]                                       AS fecha_p25,
    fechas[3]                                       AS fecha_mediana,
    fechas[4]                                       AS fecha_p75,
    CASE WHEN beneficiarios >= min_beneficiaries_for_tails() THEN fechas[5] END AS fecha_p90
FROM published;
