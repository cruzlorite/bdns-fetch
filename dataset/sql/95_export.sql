-- Writes each published table as a Parquet file, the dataset's only
-- format, in the folder named by the `salida` variable, which must exist:
--
--   SET VARIABLE salida = '/path/to/output';
--
-- Only tables in the `publicar` schema are exported, and only after the
-- privacy checks (90_checks.sql) have passed. A table added to `publicar`
-- needs its line here.

SELECT CASE WHEN getvariable('salida') IS NULL THEN error(
    'No output folder: run SET VARIABLE salida = ''/path/to/output'' before the build'
) END;

COPY publicar.concesiones_entidades
    TO (getvariable('salida') || '/concesiones_entidades.parquet') (FORMAT parquet, COMPRESSION zstd);
