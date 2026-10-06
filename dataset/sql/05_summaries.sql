-- The summary per call that is all the dataset publishes about awards to
-- natural persons (and to those protected like them), the same for
-- concesiones, ayudas de Estado and minimis: how many awards, to how many
-- people, and how their amounts and dates are distributed. No row says
-- anything about a single person. See docs/adr/0020-anonymised-dataset.md.
--
-- The rules, with their thresholds as macros in 02_privacy.sql:
--
-- * A row is published only if it is_publishable() for every amount it
--   summarises: enough people, none of them holding most of the amount. A
--   person is counted once, by their BDNS identifier, or by the
--   beneficiary field where it is missing.
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

-- An amount's statistics. The mean and the standard deviation are rounded
-- to the cent, like every other amount; unrounded, their last digits change
-- with the order a parallel sum happens to take, and two builds would not
-- agree.
CREATE OR REPLACE MACRO amount_summary(amount) AS STRUCT_PACK(
    total := sum(amount),
    media := CAST(avg(amount) AS DECIMAL(18, 2)),
    desviacion := CAST(stddev_samp(amount) AS DECIMAL(18, 2)),
    p10 := quantile_cont(amount, 0.10),
    p25 := quantile_cont(amount, 0.25),
    mediana := quantile_cont(amount, 0.50),
    p75 := quantile_cont(amount, 0.75),
    p90 := quantile_cont(amount, 0.90)
);

-- The award dates' percentiles, each a real award date.
CREATE OR REPLACE MACRO date_summary(day) AS STRUCT_PACK(
    p10 := quantile_disc(day, 0.10),
    p25 := quantile_disc(day, 0.25),
    mediana := quantile_disc(day, 0.50),
    p75 := quantile_disc(day, 0.75),
    p90 := quantile_disc(day, 0.90)
);

-- The same statistics without the 10th and 90th percentiles when the row
-- gathers too few people for them.
CREATE OR REPLACE MACRO amount_with_tails(s, people) AS STRUCT_PACK(
    total := s.total, media := s.media, desviacion := s.desviacion,
    p10 := CASE WHEN people >= min_beneficiaries_for_tails() THEN s.p10 END,
    p25 := s.p25, mediana := s.mediana, p75 := s.p75,
    p90 := CASE WHEN people >= min_beneficiaries_for_tails() THEN s.p90 END
);

CREATE OR REPLACE MACRO date_with_tails(s, people) AS STRUCT_PACK(
    p10 := CASE WHEN people >= min_beneficiaries_for_tails() THEN s.p10 END,
    p25 := s.p25, mediana := s.mediana, p75 := s.p75,
    p90 := CASE WHEN people >= min_beneficiaries_for_tails() THEN s.p90 END
);

-- The publishable summaries of a table of protected awards, one per call
-- and instrument, then one rest row per year. The table has, per award:
-- numero_convocatoria, instrumento, persona, fecha_concesion, importe,
-- ayuda_equivalente (either may be NULL throughout, if the entity lacks
-- it) and etiqueta, a struct with the call's title and awarding body as
-- the entity names them. A few calls do not keep those the same across
-- their awards: a call shows those of most of its awards, and on a tie
-- the first in order, so that two builds always agree.
CREATE OR REPLACE MACRO call_summaries(tbl) AS TABLE
WITH awards AS (
    SELECT * FROM query_table(tbl)
),
per_person AS (
    SELECT
        numero_convocatoria, instrumento, persona,
        sum(importe) AS importe, sum(ayuda_equivalente) AS equivalente
    FROM awards
    GROUP BY ALL
),
people AS (
    SELECT
        numero_convocatoria,
        instrumento,
        count(*) AS beneficiarios,
        is_publishable(count(*), sum(importe), max(importe))
            AND is_publishable(count(*), sum(equivalente), max(equivalente)) AS publishable
    FROM per_person
    GROUP BY ALL
),
labels AS (
    SELECT numero_convocatoria, instrumento, first(etiqueta ORDER BY n DESC, etiqueta) AS etiqueta
    FROM (
        SELECT numero_convocatoria, instrumento, etiqueta, count(*) AS n
        FROM awards
        GROUP BY ALL
    )
    GROUP BY ALL
),
calls AS (
    SELECT
        a.numero_convocatoria,
        a.instrumento,
        any_value(l.etiqueta)                       AS etiqueta,
        count(*)                                    AS concesiones,
        any_value(p.beneficiarios)                  AS beneficiarios,
        any_value(p.publishable)                    AS publishable,
        amount_summary(a.importe)                   AS importe,
        amount_summary(a.ayuda_equivalente)         AS ayuda_equivalente,
        date_summary(a.fecha_concesion)             AS fecha,
        year(quantile_disc(a.fecha_concesion, 0.50)) AS ejercicio
    FROM awards a
    JOIN people p
        ON  a.numero_convocatoria IS NOT DISTINCT FROM p.numero_convocatoria
        AND a.instrumento IS NOT DISTINCT FROM p.instrumento
    JOIN labels l
        ON  a.numero_convocatoria IS NOT DISTINCT FROM l.numero_convocatoria
        AND a.instrumento IS NOT DISTINCT FROM l.instrumento
    GROUP BY a.numero_convocatoria, a.instrumento
),
suppressed AS (
    SELECT a.*, c.ejercicio
    FROM awards a
    JOIN calls c
        ON  a.numero_convocatoria IS NOT DISTINCT FROM c.numero_convocatoria
        AND a.instrumento IS NOT DISTINCT FROM c.instrumento
    WHERE NOT c.publishable
),
rest_per_person AS (
    SELECT ejercicio, persona, sum(importe) AS importe, sum(ayuda_equivalente) AS equivalente
    FROM suppressed
    GROUP BY ALL
),
rest_people AS (
    SELECT
        ejercicio,
        count(*) AS beneficiarios,
        is_publishable(count(*), sum(importe), max(importe))
            AND is_publishable(count(*), sum(equivalente), max(equivalente)) AS publishable
    FROM rest_per_person
    GROUP BY ALL
),
rest_calls AS (
    SELECT ejercicio, count(*) AS suppressed_calls FROM calls WHERE NOT publishable GROUP BY ALL
),
rest AS (
    SELECT
        s.ejercicio,
        count(*)                                    AS concesiones,
        any_value(p.beneficiarios)                  AS beneficiarios,
        any_value(p.publishable) AND any_value(c.suppressed_calls) >= 2 AS publishable,
        amount_summary(s.importe)                   AS importe,
        amount_summary(s.ayuda_equivalente)         AS ayuda_equivalente,
        date_summary(s.fecha_concesion)             AS fecha
    FROM suppressed s
    JOIN rest_people p ON s.ejercicio IS NOT DISTINCT FROM p.ejercicio
    JOIN rest_calls c ON s.ejercicio IS NOT DISTINCT FROM c.ejercicio
    GROUP BY s.ejercicio
),
published AS (
    SELECT numero_convocatoria, instrumento, etiqueta, false AS es_resto, NULL::BIGINT AS ejercicio,
           concesiones, beneficiarios, importe, ayuda_equivalente, fecha
    FROM calls
    WHERE publishable
    UNION ALL BY NAME
    SELECT true AS es_resto, ejercicio, concesiones, beneficiarios, importe, ayuda_equivalente, fecha
    FROM rest
    WHERE publishable
)
SELECT
    numero_convocatoria,
    instrumento,
    etiqueta,
    es_resto,
    ejercicio,
    concesiones,
    beneficiarios,
    amount_with_tails(importe, beneficiarios)           AS importe,
    amount_with_tails(ayuda_equivalente, beneficiarios) AS ayuda_equivalente,
    date_with_tails(fecha, beneficiarios)               AS fecha
FROM published;
