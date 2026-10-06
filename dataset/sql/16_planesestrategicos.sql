-- Strategic subsidy plans, from bdns-sync's planesestrategicos table (each
-- plan's detail), with the last known version of each (04_versions.sql).
-- They are the administrations' own documents. The attached documents and
-- the portal's standard legal notice are not read.

-- Private: every plan, with the fields in 05_schemas.sql.
CREATE OR REPLACE TABLE planesestrategicos AS
SELECT
    * EXCLUDE (is_current),
    NOT is_current AS retirada
FROM (
    SELECT unnest(from_json(r, PLANESESTRATEGICOS_SCHEMA())), is_current, _valid_from
    FROM latest_versions('sync.planesestrategicos')
);

CREATE OR REPLACE TABLE publish.planesestrategicos AS
SELECT
    idPES,
    without_personal_id(descripcion)            AS descripcion,
    without_personal_id(descripcionCooficial)   AS descripcionCooficial,
    tipoPlan,
    vigenciaDesde,
    vigenciaHasta,
    fechaAprobacion,
    ambitos,
    retirada
FROM planesestrategicos;
