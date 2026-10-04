-- Writes each published table as a Parquet file, the dataset's only
-- format, in the folder named by the `output_dir` variable, which must
-- exist:
--
--   SET VARIABLE output_dir = '/path/to/output';
--
-- Only tables in the `publish` schema are exported, and only after the
-- privacy checks (90_checks.sql) have passed. A table added to `publish`
-- needs its line here.

SELECT CASE WHEN getvariable('output_dir') IS NULL THEN error(
    'No output folder: run SET VARIABLE output_dir = ''/path/to/output'' before the build'
) END;

COPY publish.concesiones_entidades
    TO (getvariable('output_dir') || '/concesiones_entidades.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.ayudas_estado_entidades
    TO (getvariable('output_dir') || '/ayudas_estado_entidades.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.minimis_entidades
    TO (getvariable('output_dir') || '/minimis_entidades.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.concesiones_personas
    TO (getvariable('output_dir') || '/concesiones_personas.parquet') (FORMAT parquet, COMPRESSION zstd);
