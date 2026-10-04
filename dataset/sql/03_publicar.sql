-- Everything to be published goes in the `publicar` schema, apart from the
-- private tables in `main`. The privacy checks (90_checks.sql) run on the
-- tables in it, and only it is exported.
CREATE SCHEMA IF NOT EXISTS publicar;
