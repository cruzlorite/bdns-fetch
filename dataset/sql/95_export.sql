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
