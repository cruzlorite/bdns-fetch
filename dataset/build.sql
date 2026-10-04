-- Builds the anonymised BDNS dataset from a bdns-sync database, in DuckDB
-- SQL. What may be published, and why, is in
-- docs/adr/0020-anonymised-dataset.md.
--
-- Run it from the repository root, in a private DuckDB file (it holds
-- personal data until the published tables are written), with the
-- bdns-sync database attached as `sync`, read-only, and the folder for the
-- Parquet files in the `output_dir` variable. For example:
--
--   duckdb /private/dataset.duckdb \
--     -cmd "ATTACH 'postgresql://user@host/bdns' AS sync (TYPE postgres, READ_ONLY);
--           SET VARIABLE output_dir = '/path/to/output'" \
--     -f dataset/build.sql
--
-- Each step is a file in dataset/sql/, run in this order. The run stops at
-- the first error, so a failed privacy check (90_checks.sql) leaves the
-- export (95_export.sql) unrun and nothing is written; results are not
-- printed, only errors are.

.bail on
.mode trash

.read dataset/sql/01_beneficiarios.sql
.read dataset/sql/02_privacy.sql
.read dataset/sql/03_publish.sql
.read dataset/sql/10_concesiones.sql
.read dataset/sql/11_ayudas_estado.sql
.read dataset/sql/12_minimis.sql
.read dataset/sql/20_entidades.sql
.read dataset/sql/30_personas.sql
.read dataset/sql/90_checks.sql
.read dataset/sql/95_export.sql
