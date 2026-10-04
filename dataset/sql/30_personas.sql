-- Awards to natural persons, entities made of persons and unrecognised
-- beneficiaries, only as aggregates by call and award year (and
-- instrument, should a call mix several). No row says anything about a
-- single person. See docs/adr/0002-anonymised-dataset.md.
--
-- A person is counted once per cell, by their BDNS identifier, or by the
-- beneficiary field where it is missing. A cell is published only if it is
-- publicable() (02_privacy.sql): enough beneficiaries, none dominant. What
-- is suppressed goes, per year, into one "rest" row, published only if it
-- gathers at least two suppressed cells (otherwise it would be the one
-- suppressed cell, plain to see) and is publicable() itself.

-- Each protected person's total in each cell. Private.
CREATE OR REPLACE TABLE personas_por_celda AS
SELECT
    anio,
    numero_convocatoria,
    instrumento,
    coalesce(CAST(id_persona AS VARCHAR), beneficiario) AS persona,
    count(*)                                            AS concesiones,
    sum(importe)                                        AS importe,
    -- Constant within a call; any value will do.
    any_value(convocatoria)                             AS convocatoria,
    any_value(nivel1)                                   AS nivel1,
    any_value(nivel2)                                   AS nivel2,
    any_value(nivel3)                                   AS nivel3
FROM concesiones
WHERE is_protected(tipo_beneficiario)
GROUP BY anio, numero_convocatoria, instrumento, persona;

-- The cells, and whether each may be published. Private.
CREATE OR REPLACE TABLE celdas_personas AS
SELECT
    anio,
    numero_convocatoria,
    instrumento,
    any_value(convocatoria)          AS convocatoria,
    any_value(nivel1)                AS nivel1,
    any_value(nivel2)                AS nivel2,
    any_value(nivel3)                AS nivel3,
    sum(concesiones)                 AS concesiones,
    count(*)                         AS beneficiarios,
    sum(importe)                     AS importe_total,
    publicable(count(*), sum(importe), max(importe)) AS publicable
FROM personas_por_celda
GROUP BY anio, numero_convocatoria, instrumento;

CREATE OR REPLACE TABLE publicar.concesiones_personas AS
-- The cells that may be published as they are. A call title shaped like a
-- personal tax ID is blanked here; the checks would stop the build otherwise.
SELECT
    anio,
    numero_convocatoria,
    CASE WHEN has_personal_id(convocatoria) THEN NULL ELSE convocatoria END AS convocatoria,
    nivel1,
    nivel2,
    nivel3,
    instrumento,
    concesiones,
    beneficiarios,
    importe_total,
    false AS resto
FROM celdas_personas
WHERE publicable

UNION ALL

-- One rest row per year with everything suppressed, counting each person
-- once across all the cells it gathers.
SELECT
    resto.anio,
    NULL, NULL, NULL, NULL, NULL, NULL,
    resto.concesiones,
    resto.beneficiarios,
    resto.importe_total,
    true
FROM (
    SELECT
        anio,
        sum(concesiones) AS concesiones,
        count(*)         AS beneficiarios,
        sum(importe)     AS importe_total,
        max(importe)     AS mayor
    FROM (
        SELECT p.anio, p.persona, sum(p.concesiones) AS concesiones, sum(p.importe) AS importe
        FROM personas_por_celda p
        JOIN celdas_personas c
            ON  p.anio IS NOT DISTINCT FROM c.anio
            AND p.numero_convocatoria IS NOT DISTINCT FROM c.numero_convocatoria
            AND p.instrumento IS NOT DISTINCT FROM c.instrumento
        WHERE NOT c.publicable
        GROUP BY p.anio, p.persona
    )
    GROUP BY anio
) resto
JOIN (
    SELECT anio, count(*) AS celdas FROM celdas_personas WHERE NOT publicable GROUP BY anio
) suprimidas ON resto.anio IS NOT DISTINCT FROM suprimidas.anio
WHERE suprimidas.celdas >= 2
    AND publicable(resto.beneficiarios, resto.importe_total, resto.mayor);
