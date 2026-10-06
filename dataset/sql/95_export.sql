-- Writes each published table as a Parquet file, the dataset's only
-- format, in the folder named by the `output_dir` variable, which must
-- exist:
--
--   SET VARIABLE output_dir = '/path/to/output';
--
-- Only tables in the publish database are exported, and only after the
-- privacy checks (90_checks.sql) have passed. DuckDB's EXPORT DATABASE would
-- write them all at once, but it takes the folder only as a literal, so
-- each table has its COPY line, and the last check fails if a published
-- table has none.

SELECT CASE WHEN getvariable('output_dir') IS NULL THEN error(
    'No output folder: run SET VARIABLE output_dir = ''/path/to/output'' before the build'
) END;

COPY publish.concesiones_personas_juridicas
    TO (getvariable('output_dir') || '/concesiones_personas_juridicas.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.concesiones_personas_fisicas
    TO (getvariable('output_dir') || '/concesiones_personas_fisicas.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.ayudasestado_personas_juridicas
    TO (getvariable('output_dir') || '/ayudasestado_personas_juridicas.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.ayudasestado_personas_fisicas
    TO (getvariable('output_dir') || '/ayudasestado_personas_fisicas.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.minimis_personas_juridicas
    TO (getvariable('output_dir') || '/minimis_personas_juridicas.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.minimis_personas_fisicas
    TO (getvariable('output_dir') || '/minimis_personas_fisicas.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.partidospoliticos
    TO (getvariable('output_dir') || '/partidospoliticos.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.grandesbeneficiarios
    TO (getvariable('output_dir') || '/grandesbeneficiarios.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.convocatorias
    TO (getvariable('output_dir') || '/convocatorias.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.planesestrategicos
    TO (getvariable('output_dir') || '/planesestrategicos.parquet') (FORMAT parquet, COMPRESSION zstd);

COPY publish.catalogos
    TO (getvariable('output_dir') || '/catalogos.parquet') (FORMAT parquet, COMPRESSION zstd);

SELECT CASE WHEN count(*) > 0 THEN error(
    'Published but not exported, add its COPY line to 95_export.sql: ' || string_agg(table_name, ', ')
) END
FROM duckdb_tables()
WHERE database_name = 'publish'
    AND table_name NOT IN (
        SELECT parse_filename(file, true) FROM glob(getvariable('output_dir') || '/*.parquet')
    );
