-- Who a beneficiary is (tipoPersona), read from the leading tax ID of the
-- BDNS field ("B12345678 EMPRESA SL"), never from the name. Its values are
-- in Spanish, like all the data: code is in English, data in Spanish.
--
-- The BDNS hides part of a natural person's tax ID but keeps the full name
-- ("***1234** NOMBRE APELLIDOS"), so the field identifies them and the
-- dataset may only publish them aggregated. The rule is conservative: any
-- shape it does not recognise is 'desconocido', and that is protected
-- exactly like a natural person. See docs/adr/0020-anonymised-dataset.md.

-- The identifier: the first word of the field, upper-cased.
CREATE OR REPLACE MACRO beneficiary_id(beneficiary) AS
    upper(split_part(trim(coalesce(beneficiary, '')), ' ', 1));

-- The name: everything after the identifier. State aid writes a dash
-- between them ("B12345678 - EMPRESA SL"); the other tables, a space.
CREATE OR REPLACE MACRO beneficiary_name(beneficiary) AS
    trim(regexp_replace(trim(coalesce(beneficiary, '')), '^\S+\s*(-\s+)?', ''));

CREATE OR REPLACE MACRO beneficiary_kind(beneficiary) AS
    CASE
        -- A person: a masked ID (***1234**), a DNI, an NIE, or a K/L/M ID
        -- (minors without a DNI, Spaniards abroad, foreigners without an NIE).
        WHEN regexp_full_match(beneficiary_id(beneficiary),
            '\*{2,}\d{3,5}\*{0,3}|\d{8}[A-Z]|[XYZ]\d{7}[A-Z]|[KLM]\d{7}[A-Z0-9]')
            THEN 'persona_fisica'
        -- Entity IDs are a letter, seven digits and a control character;
        -- the letter says what kind of entity it is.
        -- P, Q, S: public administrations and bodies.
        WHEN regexp_full_match(beneficiary_id(beneficiary),
            '[PQS]\d{7}[0-9A-J]')
            THEN 'entidad_publica'
        -- E, J: communities of property and civil partnerships, usually
        -- named after their members.
        WHEN regexp_full_match(beneficiary_id(beneficiary),
            '[EJ]\d{7}[0-9A-J]')
            THEN 'comunidad_o_sociedad_civil'
        -- Companies, associations, foundations and other entities.
        WHEN regexp_full_match(beneficiary_id(beneficiary),
            '[ABCDFGHNRUVW]\d{7}[0-9A-J]')
            THEN 'persona_juridica'
        -- Empty, a foreign ID, or anything else.
        ELSE 'desconocido'
    END;

-- Whether a beneficiary of this kind may only be published aggregated.
CREATE OR REPLACE MACRO is_protected(kind) AS
    kind IN ('persona_fisica', 'comunidad_o_sociedad_civil', 'desconocido');
