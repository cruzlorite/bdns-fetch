-- Who a beneficiary is, read from the leading tax ID of the BDNS field
-- ("B12345678 EMPRESA SL"), never from the name.
--
-- The BDNS hides part of a natural person's tax ID but keeps the full name
-- ("***1234** NOMBRE APELLIDOS"), so the field identifies them and the
-- dataset may only publish them aggregated. The rule is conservative: any
-- shape it does not recognise is 'unknown', and 'unknown' is protected
-- exactly like a natural person. See docs/adr/0002-anonymised-dataset.md.

-- The identifier: the first word of the field, upper-cased.
CREATE OR REPLACE MACRO beneficiary_id(beneficiario) AS
    upper(split_part(trim(coalesce(beneficiario, '')), ' ', 1));

-- The name: everything after the identifier. State aid writes a dash
-- between them ("B12345678 - EMPRESA SL"); the other tables, a space.
CREATE OR REPLACE MACRO beneficiary_name(beneficiario) AS
    trim(regexp_replace(trim(coalesce(beneficiario, '')), '^\S+\s*(-\s+)?', ''));

CREATE OR REPLACE MACRO beneficiary_kind(beneficiario) AS
    CASE
        -- A person: a masked ID (***1234**), a DNI, an NIE, or a K/L/M ID
        -- (minors without a DNI, Spaniards abroad, foreigners without an NIE).
        WHEN regexp_full_match(beneficiary_id(beneficiario),
            '\*{2,}\d{3,5}\*{0,3}|\d{8}[A-Z]|[XYZ]\d{7}[A-Z]|[KLM]\d{7}[A-Z0-9]')
            THEN 'natural_person'
        -- Entity IDs are a letter, seven digits and a control character;
        -- the letter says what kind of entity it is.
        -- P, Q, S: public administrations and bodies.
        WHEN regexp_full_match(beneficiary_id(beneficiario),
            '[PQS]\d{7}[0-9A-J]')
            THEN 'public_body'
        -- E, J: communities of property and civil partnerships, usually
        -- named after their members.
        WHEN regexp_full_match(beneficiary_id(beneficiario),
            '[EJ]\d{7}[0-9A-J]')
            THEN 'person_based_entity'
        -- Companies, associations, foundations and other entities.
        WHEN regexp_full_match(beneficiary_id(beneficiario),
            '[ABCDFGHNRUVW]\d{7}[0-9A-J]')
            THEN 'legal_person'
        -- Empty, a foreign ID, or anything else.
        ELSE 'unknown'
    END;

-- Whether a beneficiary of this kind may only be published aggregated.
CREATE OR REPLACE MACRO is_protected(kind) AS
    kind IN ('natural_person', 'person_based_entity', 'unknown');
