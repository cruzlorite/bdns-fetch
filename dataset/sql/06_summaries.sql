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
--   only from MIN_BENEFICIARIES_FOR_TAILS() people.
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
    p10 := CASE WHEN people >= MIN_BENEFICIARIES_FOR_TAILS() THEN s.p10 END,
    p25 := s.p25, mediana := s.mediana, p75 := s.p75,
    p90 := CASE WHEN people >= MIN_BENEFICIARIES_FOR_TAILS() THEN s.p90 END
);

CREATE OR REPLACE MACRO date_with_tails(s, people) AS STRUCT_PACK(
    p10 := CASE WHEN people >= MIN_BENEFICIARIES_FOR_TAILS() THEN s.p10 END,
    p25 := s.p25, mediana := s.mediana, p75 := s.p75,
    p90 := CASE WHEN people >= MIN_BENEFICIARIES_FOR_TAILS() THEN s.p90 END
);

-- The publishable summaries of a table of protected awards, one per call
-- and instrument, then one rest row per year. The table has, per award:
-- numeroConvocatoria, instrumento, persona, fechaConcesion, importe,
-- ayudaEquivalente (either may be NULL throughout, if the entity lacks it)
-- and etiqueta, a struct with the call's title and awarding body as the
-- entity names them.
--
-- Each award first finds its row: its call's, if the call may be published,
-- or else its year's rest row. Then every row, call or rest, is summarised
-- and checked by the same code, so both kinds always follow the same rule.
-- A few calls do not keep their title and body the same across their
-- awards: a call shows those of most of its awards, and on a tie the first
-- in order, so that two builds always agree.
CREATE OR REPLACE MACRO call_summaries(tbl) AS TABLE
WITH awards AS (
    SELECT * FROM query_table(tbl)
),
-- Whether each call may be published, and the year its awards go to if
-- not: that of its median award date.
calls AS (
    SELECT
        numeroConvocatoria,
        instrumento,
        is_publishable(count(*), sum(importe), max(importe))
            AND is_publishable(count(*), sum(equivalente), max(equivalente)) AS publishable
    FROM (
        SELECT numeroConvocatoria, instrumento, persona, sum(importe) AS importe, sum(ayudaEquivalente) AS equivalente
        FROM awards
        GROUP BY ALL
    )
    GROUP BY ALL
),
years AS (
    SELECT numeroConvocatoria, instrumento, year(quantile_disc(fechaConcesion, 0.50)) AS ejercicio
    FROM awards
    GROUP BY ALL
),
grouped AS (
    SELECT
        a.*,
        CASE WHEN c.publishable
            THEN struct_pack(esResto := false, numeroConvocatoria := a.numeroConvocatoria, instrumento := a.instrumento, ejercicio := NULL::BIGINT)
            ELSE struct_pack(esResto := true, numeroConvocatoria := NULL::VARCHAR, instrumento := NULL::VARCHAR, ejercicio := y.ejercicio)
        END AS fila
    FROM awards a
    JOIN calls c
        ON  a.numeroConvocatoria IS NOT DISTINCT FROM c.numeroConvocatoria
        AND a.instrumento IS NOT DISTINCT FROM c.instrumento
    JOIN years y
        ON  a.numeroConvocatoria IS NOT DISTINCT FROM y.numeroConvocatoria
        AND a.instrumento IS NOT DISTINCT FROM y.instrumento
),
-- The same rule again, now for every row: calls (which pass, as before) and
-- rest rows alike.
rows_ AS (
    SELECT
        fila,
        count(*) AS beneficiarios,
        is_publishable(count(*), sum(importe), max(importe))
            AND is_publishable(count(*), sum(equivalente), max(equivalente)) AS publishable
    FROM (
        SELECT fila, persona, sum(importe) AS importe, sum(ayudaEquivalente) AS equivalente
        FROM grouped
        GROUP BY ALL
    )
    GROUP BY ALL
),
-- How many calls each row gathers: one for a call, and at least two for a
-- rest row to be published (with one, it would be that call, plain to see).
gathered AS (
    SELECT fila, count(DISTINCT struct_pack(numeroConvocatoria, instrumento)) AS convocatorias
    FROM grouped
    GROUP BY fila
),
labels AS (
    SELECT fila, first(etiqueta ORDER BY n DESC, etiqueta) AS etiqueta
    FROM (SELECT fila, etiqueta, count(*) AS n FROM grouped GROUP BY ALL)
    GROUP BY ALL
),
summaries AS (
    SELECT
        fila,
        count(*)                                    AS concesiones,
        amount_summary(importe)                     AS importe,
        amount_summary(ayudaEquivalente)            AS ayudaEquivalente,
        date_summary(fechaConcesion)                AS fechaConcesion
    FROM grouped
    GROUP BY fila
)
SELECT
    s.fila.numeroConvocatoria                       AS numeroConvocatoria,
    s.fila.instrumento                              AS instrumento,
    CASE WHEN NOT s.fila.esResto THEN l.etiqueta END AS etiqueta,
    s.fila.esResto                                  AS esResto,
    s.fila.ejercicio                                AS ejercicio,
    s.concesiones                                   AS concesiones,
    r.beneficiarios                                 AS beneficiarios,
    amount_with_tails(s.importe, r.beneficiarios)           AS importe,
    amount_with_tails(s.ayudaEquivalente, r.beneficiarios)  AS ayudaEquivalente,
    date_with_tails(s.fechaConcesion, r.beneficiarios)      AS fechaConcesion
FROM summaries s
JOIN rows_ r ON s.fila IS NOT DISTINCT FROM r.fila
JOIN gathered g ON s.fila IS NOT DISTINCT FROM g.fila
JOIN labels l ON s.fila IS NOT DISTINCT FROM l.fila
WHERE r.publishable AND (NOT s.fila.esResto OR g.convocatorias >= 2);
