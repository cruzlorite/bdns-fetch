-- Builds the anonymised BDNS dataset from a bdns-sync database, in DuckDB
-- SQL and nothing else. What may be published, and why, is in
-- docs/adr/0002-anonymised-dataset.md.
--
-- Run it from the repository root, in a private DuckDB file (it holds
-- personal data until the published tables are written), with the
-- bdns-sync database attached as `sync`, read-only, and the folder for the
-- Parquet files in the `salida` variable. For example:
--
--   duckdb /private/dataset.duckdb \
--     -cmd "ATTACH 'postgresql://user@host/bdns' AS sync (TYPE postgres, READ_ONLY);
--           SET VARIABLE salida = '/path/to/output'" \
--     -f dataset/build.sql
--
-- Each step is a file in dataset/sql/, run in this order.

.read dataset/sql/01_beneficiaries.sql
.read dataset/sql/02_privacy.sql
.read dataset/sql/03_publicar.sql
.read dataset/sql/10_concesiones.sql
.read dataset/sql/20_entidades.sql
.read dataset/sql/90_checks.sql
.read dataset/sql/95_export.sql
