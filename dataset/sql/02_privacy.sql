-- Building blocks for the checks that stop the build before personal data
-- can be published. The checks themselves run at the end, on each table
-- about to be published (90_checks.sql), and they fail instead of cleaning
-- up: a check that quietly dropped what it found would hide the real fault
-- upstream behind a dataset that looks fine.
-- See docs/adr/0002-anonymised-dataset.md.

-- A natural person's tax ID anywhere in a text: masked (***1234**), a DNI,
-- an NIE or a K/L/M one. A legal person's ID (B12345678) matches none.
CREATE OR REPLACE MACRO personal_id_pattern() AS
    '\*{2,}\d{3,5}\*{0,3}|\b\d{8}[A-Za-z]\b|\b[XYZxyz]\d{7}[A-Za-z]\b|\b[KLMklm]\d{7}[A-Za-z0-9]\b';

CREATE OR REPLACE MACRO has_personal_id(text) AS
    regexp_matches(coalesce(text, ''), personal_id_pattern());

-- The rows of a table where any column holds something shaped like a
-- natural person's tax ID. The separator keeps two columns from forming
-- one match between them.
CREATE OR REPLACE MACRO rows_with_personal_ids(tbl) AS TABLE
    SELECT * FROM query_table(tbl)
    WHERE has_personal_id(concat_ws(' | ', *COLUMNS(*)));

-- Columns that identify a beneficiary, or lead back to one: never in a
-- table about natural persons.
CREATE OR REPLACE MACRO identifying_column(name) AS
    lower(name) IN (
        'beneficiario', 'nifcif', 'nif_cif', 'idpersona', 'id_persona',
        'urlbr', 'url_br', 'codconcesion', 'cod_concesion', 'id'
    );

-- The two thresholds of statistical disclosure control, in one place.
-- A published aggregate counts at least this many beneficiaries...
CREATE OR REPLACE MACRO min_beneficiarios() AS 10;
-- ...and no single beneficiary holds more than this share of its amount.
CREATE OR REPLACE MACRO max_cuota_dominante() AS 0.5;

-- Whether an aggregate may be published, given its number of
-- beneficiaries, its total amount and its largest beneficiary's amount.
CREATE OR REPLACE MACRO publicable(beneficiarios, total, mayor) AS
    beneficiarios >= min_beneficiarios()
    AND NOT (coalesce(total, 0) > 0 AND mayor > max_cuota_dominante() * total);
