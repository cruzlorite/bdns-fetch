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
-- export (95_export.sql) unrun and nothing is written. Each step prints
-- the time it starts and its name, so you can follow a long run, and after
-- 80_schema_drift.sql come its warnings about fields the API stopped sending;
-- query results are not printed.

.bail on
.headers off

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  01_beneficiarios.sql';
.mode trash
.read dataset/sql/01_beneficiarios.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  02_privacy.sql';
.mode trash
.read dataset/sql/02_privacy.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  03_publish.sql';
.mode trash
.read dataset/sql/03_publish.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  04_versions.sql';
.mode trash
.read dataset/sql/04_versions.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  05_schemas.sql';
.mode trash
.read dataset/sql/05_schemas.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  06_summaries.sql';
.mode trash
.read dataset/sql/06_summaries.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  10_concesiones.sql';
.mode trash
.read dataset/sql/10_concesiones.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  11_ayudasestado.sql';
.mode trash
.read dataset/sql/11_ayudasestado.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  12_minimis.sql';
.mode trash
.read dataset/sql/12_minimis.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  13_partidospoliticos.sql';
.mode trash
.read dataset/sql/13_partidospoliticos.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  14_grandesbeneficiarios.sql';
.mode trash
.read dataset/sql/14_grandesbeneficiarios.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  15_convocatorias.sql';
.mode trash
.read dataset/sql/15_convocatorias.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  16_planesestrategicos.sql';
.mode trash
.read dataset/sql/16_planesestrategicos.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  17_catalogos.sql';
.mode trash
.read dataset/sql/17_catalogos.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  80_schema_drift.sql';
.mode trash
.read dataset/sql/80_schema_drift.sql
.mode list
SELECT 'warning: ' || tabla || '.' || campo || ' is empty in every record stored in its last 30 days'
FROM campos_vacios ORDER BY tabla, campo;
.mode trash

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  90_checks.sql';
.mode trash
.read dataset/sql/90_checks.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  95_export.sql';
.mode trash
.read dataset/sql/95_export.sql

.mode list
SELECT strftime(now(), '%H:%M:%S') || '  done';
.mode trash
