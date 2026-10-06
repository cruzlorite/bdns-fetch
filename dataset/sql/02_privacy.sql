-- Building blocks for the checks that stop the build before personal data
-- can be published. The checks themselves run at the end, on each table
-- about to be published (90_checks.sql), and they fail instead of cleaning
-- up: a check that quietly dropped what it found would hide the real fault
-- upstream behind a dataset that looks fine.
-- See docs/adr/0020-anonymised-dataset.md.

-- A natural person's tax ID anywhere in a text: masked (***1234**), a DNI,
-- an NIE or a K/L/M one. A legal person's ID (B12345678) matches none, and
-- neither does a local authority's DIR3 code (L01462580), since a K/L/M
-- tax ID always ends in a letter.
CREATE OR REPLACE MACRO PERSONAL_ID_PATTERN() AS
    '\*{2,}\d{3,5}\*{0,3}|\b\d{8}[A-Za-z]\b|\b[XYZxyz]\d{7}[A-Za-z]\b|\b[KLMklm]\d{7}[A-Za-z]\b';

CREATE OR REPLACE MACRO has_personal_id(text) AS
    regexp_matches(coalesce(text, ''), PERSONAL_ID_PATTERN());

-- A published text, or nothing if it holds something shaped like a
-- natural person's tax ID: for titles and descriptions the BDNS writes by
-- hand, where a nominative grant sometimes names its beneficiary.
CREATE OR REPLACE MACRO without_personal_id(text) AS
    CASE WHEN has_personal_id(text) THEN NULL ELSE text END;

-- The rows of a table where any column holds something shaped like a
-- natural person's tax ID. The separator keeps two columns from forming
-- one match between them.
CREATE OR REPLACE MACRO rows_with_personal_ids(tbl) AS TABLE
    SELECT * FROM query_table(tbl)
    WHERE has_personal_id(concat_ws(' | ', *COLUMNS(*)));

-- Whether awards to a beneficiary may only be published aggregated: a
-- protected kind, or a field that carries a natural person's tax ID even
-- though the beneficiary is a company or an association. The BDNS does
-- that for companies named after their partner ("NOMBRE APELLIDOS
-- 12345678Z SL") and for some that add their representative's details;
-- removing only the ID would still leave the person's name.
CREATE OR REPLACE MACRO is_protected_beneficiary(kind, beneficiary) AS
    is_protected(kind) OR has_personal_id(beneficiary);

-- Columns that identify a beneficiary, or lead back to one: never in a
-- table about natural persons. Compared in lower case, since the dataset
-- keeps the API's names (idPersona, urlBR...).
CREATE OR REPLACE MACRO identifying_column(name) AS
    lower(name) IN (
        'beneficiario', 'nifcif', 'idpersona', 'urlbr', 'codconcesion', 'codigoconcesion',
        'id', 'idconcesion', 'nif', 'nombre'
    );

-- The thresholds of statistical disclosure control, in one place.
-- A published summary covers at least this many beneficiaries...
CREATE OR REPLACE MACRO MIN_BENEFICIARIES() AS 10;
-- ...and no single beneficiary holds more than this share of its amount.
CREATE OR REPLACE MACRO MAX_DOMINANT_SHARE() AS 0.5;
-- The 10th and 90th percentiles sit close to the smallest and largest
-- values, each one person's, so they are only published from this many.
CREATE OR REPLACE MACRO MIN_BENEFICIARIES_FOR_TAILS() AS 20;

-- Whether a summary may be published, given its number of beneficiaries,
-- its total amount and its largest beneficiary's amount.
CREATE OR REPLACE MACRO is_publishable(beneficiaries, total, largest) AS
    beneficiaries >= MIN_BENEFICIARIES()
    AND NOT (coalesce(total, 0) > 0 AND largest > MAX_DOMINANT_SHARE() * total);
