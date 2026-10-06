-- The BDNS catalogues, in one table: the codes the other tables use, with
-- their descriptions. catalogo says which one each row belongs to, named
-- after its endpoint. Bodies (organos) and regions (regiones) are trees:
-- each node is a row, with its parent's id and its depth.

-- Each catalogue is read in a statement of its own: DuckDB's BigQuery
-- extension returns the first table for every latest_versions() call when
-- a statement makes several.
CREATE OR REPLACE TEMP TABLE catalogo_actividades AS FROM latest_versions('sync.actividades');
CREATE OR REPLACE TEMP TABLE catalogo_beneficiarios AS FROM latest_versions('sync.beneficiarios');
CREATE OR REPLACE TEMP TABLE catalogo_finalidades AS FROM latest_versions('sync.finalidades');
CREATE OR REPLACE TEMP TABLE catalogo_instrumentos AS FROM latest_versions('sync.instrumentos');
CREATE OR REPLACE TEMP TABLE catalogo_objetivos AS FROM latest_versions('sync.objetivos');
CREATE OR REPLACE TEMP TABLE catalogo_reglamentos AS FROM latest_versions('sync.reglamentos');
CREATE OR REPLACE TEMP TABLE catalogo_sectores AS FROM latest_versions('sync.sectores');
CREATE OR REPLACE TEMP TABLE catalogo_organos_agrupacion AS FROM latest_versions('sync.organos_agrupacion');
CREATE OR REPLACE TEMP TABLE catalogo_organos AS FROM latest_versions('sync.organos');
CREATE OR REPLACE TEMP TABLE catalogo_regiones AS FROM latest_versions('sync.regiones');

CREATE OR REPLACE TABLE publish.catalogos AS
WITH RECURSIVE flat(catalogo, id, descripcion, ambito, idAdmon, retirada) AS (
    SELECT 'actividades', r->>'id', r->>'descripcion', NULL::VARCHAR, NULL::VARCHAR, NOT is_current FROM catalogo_actividades
    UNION ALL
    SELECT 'beneficiarios', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM catalogo_beneficiarios
    UNION ALL
    SELECT 'finalidades', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM catalogo_finalidades
    UNION ALL
    SELECT 'instrumentos', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM catalogo_instrumentos
    UNION ALL
    SELECT 'objetivos', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM catalogo_objetivos
    UNION ALL
    SELECT 'reglamentos', r->>'id', r->>'descripcion', r->>'ambito', NULL, NOT is_current FROM catalogo_reglamentos
    UNION ALL
    SELECT 'sectores', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM catalogo_sectores
    UNION ALL
    SELECT 'organos_agrupacion', r->>'id', r->>'descripcion', NULL, r->>'idAdmon', NOT is_current FROM catalogo_organos_agrupacion
),
tree(catalogo, id, descripcion, idPadre, nivel, children, idAdmon, retirada) AS (
    SELECT 'organos', r->>'id', r->>'descripcion', NULL::VARCHAR, 1, r->'children', r->>'idAdmon', NOT is_current
    FROM catalogo_organos
    UNION ALL
    SELECT 'regiones', r->>'id', r->>'descripcion', NULL::VARCHAR, 1, r->'children', NULL, NOT is_current
    FROM catalogo_regiones
    UNION ALL
    SELECT t.catalogo, c->>'id', c->>'descripcion', t.id, t.nivel + 1, c->'children', t.idAdmon, t.retirada
    FROM tree t, unnest(CAST(t.children AS JSON[])) AS u(c)
    WHERE t.children IS NOT NULL
)
SELECT catalogo, id, descripcion, NULL::VARCHAR AS idPadre, 1 AS nivel, ambito, idAdmon, retirada FROM flat
UNION ALL
SELECT catalogo, id, descripcion, idPadre, nivel, NULL::VARCHAR, idAdmon, retirada FROM tree;
