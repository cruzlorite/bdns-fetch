-- The BDNS catalogues, in one table: the codes the other tables use, with
-- their descriptions. catalogo says which one each row belongs to, named
-- after its endpoint. Bodies (organos) and regions (regiones) are trees:
-- each node is a row, with its parent's id and its depth.

CREATE OR REPLACE TABLE publish.catalogos AS
WITH RECURSIVE flat(catalogo, id, descripcion, ambito, idAdmon, retirada) AS (
    SELECT 'actividades', r->>'id', r->>'descripcion', NULL::VARCHAR, NULL::VARCHAR, NOT is_current FROM latest_versions('sync.actividades')
    UNION ALL
    SELECT 'beneficiarios', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM latest_versions('sync.beneficiarios')
    UNION ALL
    SELECT 'finalidades', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM latest_versions('sync.finalidades')
    UNION ALL
    SELECT 'instrumentos', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM latest_versions('sync.instrumentos')
    UNION ALL
    SELECT 'objetivos', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM latest_versions('sync.objetivos')
    UNION ALL
    SELECT 'reglamentos', r->>'id', r->>'descripcion', r->>'ambito', NULL, NOT is_current FROM latest_versions('sync.reglamentos')
    UNION ALL
    SELECT 'sectores', r->>'id', r->>'descripcion', NULL, NULL, NOT is_current FROM latest_versions('sync.sectores')
    UNION ALL
    SELECT 'organos_agrupacion', r->>'id', r->>'descripcion', NULL, r->>'idAdmon', NOT is_current FROM latest_versions('sync.organos_agrupacion')
),
tree(catalogo, id, descripcion, idPadre, nivel, children, idAdmon, retirada) AS (
    SELECT 'organos', r->>'id', r->>'descripcion', NULL::VARCHAR, 1, r->'children', r->>'idAdmon', NOT is_current
    FROM latest_versions('sync.organos')
    UNION ALL
    SELECT 'regiones', r->>'id', r->>'descripcion', NULL::VARCHAR, 1, r->'children', NULL, NOT is_current
    FROM latest_versions('sync.regiones')
    UNION ALL
    SELECT t.catalogo, c->>'id', c->>'descripcion', t.id, t.nivel + 1, c->'children', t.idAdmon, t.retirada
    FROM tree t, unnest(CAST(t.children AS JSON[])) AS u(c)
    WHERE t.children IS NOT NULL
)
SELECT catalogo, id, descripcion, NULL::VARCHAR AS idPadre, 1 AS nivel, ambito, idAdmon, retirada FROM flat
UNION ALL
SELECT catalogo, id, descripcion, idPadre, nivel, NULL::VARCHAR, idAdmon, retirada FROM tree;
