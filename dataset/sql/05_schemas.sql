-- The BDNS data model, as far as the dataset reads it: for each entity,
-- the fields of its records, named and nested as the API names them, and
-- the type each one is read as. It is the only place that lists them; the
-- read steps take each record apart with from_json() and these schemas.
--
-- Macros without parameters are constants, and are named in capitals, like
-- the thresholds in 02_privacy.sql; those with parameters are functions,
-- in lower case.
--
-- from_json() is lenient on purpose: a field the API adds is ignored until
-- it is listed here (so nothing new is published by accident), and a field
-- missing from a record, or a value that does not fit its type, is read as
-- NULL. 80_schema_drift.sql warns when a listed field stops coming.

CREATE OR REPLACE MACRO DESCRIPCIONES_SCHEMA() AS json_array(json_object('descripcion', 'VARCHAR'));

CREATE OR REPLACE MACRO CONCESIONES_SCHEMA() AS json_object(
    'id',                   'BIGINT',
    'codConcesion',         'VARCHAR',
    'fechaConcesion',       'DATE',
    'beneficiario',         'VARCHAR',
    'idPersona',            'BIGINT',
    'importe',              'DECIMAL(18,2)',
    'ayudaEquivalente',     'DECIMAL(18,2)',
    'instrumento',          'VARCHAR',
    'numeroConvocatoria',   'VARCHAR',
    'convocatoria',         'VARCHAR',
    'nivel1',               'VARCHAR',
    'nivel2',               'VARCHAR',
    'nivel3',               'VARCHAR',
    'urlBR',                'VARCHAR',
    'fechaAlta',            'DATE'
);

CREATE OR REPLACE MACRO AYUDASESTADO_SCHEMA() AS json_object(
    'idConcesion',          'BIGINT',
    'codConcesion',         'VARCHAR',
    'fechaConcesion',       'DATE',
    'beneficiario',         'VARCHAR',
    'idPersona',            'BIGINT',
    'importe',              'DECIMAL(18,2)',
    'ayudaEquivalente',     'DECIMAL(18,2)',
    'instrumento',          'VARCHAR',
    'numeroConvocatoria',   'VARCHAR',
    'convocatoria',         'VARCHAR',
    'convocante',           'VARCHAR',
    'reglamento',           'VARCHAR',
    'objetivo',             'VARCHAR',
    'tipoBeneficiario',     'VARCHAR',
    'region',               'VARCHAR',
    'sectores',             'VARCHAR',
    'ayudaEstado',          'VARCHAR',
    'urlAyudaEstado',       'VARCHAR',
    'entidad',              'VARCHAR',
    'intermediario',        'VARCHAR',
    'fechaAlta',            'DATE'
);

CREATE OR REPLACE MACRO MINIMIS_SCHEMA() AS json_object(
    'idConcesion',          'BIGINT',
    'codigoConcesion',      'VARCHAR',
    'fechaConcesion',       'DATE',
    'beneficiario',         'VARCHAR',
    'idPersona',            'BIGINT',
    'ayudaEquivalente',     'DECIMAL(18,2)',
    'instrumento',          'VARCHAR',
    'numeroConvocatoria',   'VARCHAR',
    'convocante',           'VARCHAR',
    'reglamento',           'VARCHAR',
    'sectorActividad',      'VARCHAR',
    'sectorProducto',       'VARCHAR',
    'fechaRegistro',        'DATE'
);

CREATE OR REPLACE MACRO PARTIDOSPOLITICOS_SCHEMA() AS json_object(
    'id',                   'BIGINT',
    'codConcesion',         'VARCHAR',
    'fechaConcesion',       'DATE',
    'beneficiario',         'VARCHAR',
    'importe',              'DECIMAL(18,2)',
    'ayudaEquivalente',     'DECIMAL(18,2)',
    'instrumento',          'VARCHAR',
    'tieneProyecto',        'BOOLEAN',
    'numeroConvocatoria',   'VARCHAR',
    'idConvocatoria',       'BIGINT',
    'convocatoria',         'VARCHAR',
    'nivel1',               'VARCHAR',
    'nivel2',               'VARCHAR',
    'nivel3',               'VARCHAR',
    'urlBR',                'VARCHAR'
);

CREATE OR REPLACE MACRO GRANDESBENEFICIARIOS_SCHEMA() AS json_object(
    'beneficiario',         'VARCHAR',
    'idPersona',            'BIGINT',
    'ejercicio',            'INTEGER',
    'ayudaETotal',          'DECIMAL(18,2)'
);

CREATE OR REPLACE MACRO CONVOCATORIAS_SCHEMA() AS json_object(
    'id',                           'BIGINT',
    'codigoBDNS',                   'VARCHAR',
    'fechaRecepcion',               'DATE',
    'organo',                       json_object('nivel1', 'VARCHAR', 'nivel2', 'VARCHAR', 'nivel3', 'VARCHAR'),
    'sedeElectronica',              'VARCHAR',
    'descripcion',                  'VARCHAR',
    'descripcionLeng',              'VARCHAR',
    'tipoConvocatoria',             'VARCHAR',
    'presupuestoTotal',             'DECIMAL(18,2)',
    'mrr',                          'BOOLEAN',
    'instrumentos',                 DESCRIPCIONES_SCHEMA(),
    'tiposBeneficiarios',           DESCRIPCIONES_SCHEMA(),
    'sectores',                     json_array(json_object('codigo', 'VARCHAR', 'descripcion', 'VARCHAR')),
    'regiones',                     DESCRIPCIONES_SCHEMA(),
    'descripcionFinalidad',         'VARCHAR',
    'descripcionBasesReguladoras',  'VARCHAR',
    'urlBasesReguladoras',          'VARCHAR',
    'sePublicaDiarioOficial',       'BOOLEAN',
    'abierto',                      'BOOLEAN',
    'fechaInicioSolicitud',         'DATE',
    'fechaFinSolicitud',            'DATE',
    'textInicio',                   'VARCHAR',
    'textFin',                      'VARCHAR',
    'ayudaEstado',                  'VARCHAR',
    'urlAyudaEstado',               'VARCHAR',
    'fondos',                       DESCRIPCIONES_SCHEMA(),
    'reglamento',                   json_object('descripcion', 'VARCHAR', 'orden', 'VARCHAR'),
    'objetivos',                    DESCRIPCIONES_SCHEMA(),
    'sectoresProductos',            DESCRIPCIONES_SCHEMA()
);

CREATE OR REPLACE MACRO PLANESESTRATEGICOS_SCHEMA() AS json_object(
    'idPES',                'BIGINT',
    'descripcion',          'VARCHAR',
    'descripcionCooficial', 'VARCHAR',
    'tipoPlan',             'VARCHAR',
    'vigenciaDesde',        'INTEGER',
    'vigenciaHasta',        'INTEGER',
    'fechaAprobacion',      'DATE',
    'ambitos',              json_array('VARCHAR')
);
