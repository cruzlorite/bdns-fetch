# BDNS Sync

[![CI](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Motor de sincronización que mantiene una copia local versionada (SCD2) de la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api).

Se apoya en [`bdns-fetch`](https://github.com/cruzlorite/bdns-fetch), que se encarga de extraer los datos de la API; `bdns-sync` pone encima la capa de almacenamiento: histórico versionado, detección de cambios y de bajas, y registro de ejecuciones.

La herramienta hace una sola cosa: cada invocación sincroniza un endpoint y no hay fichero de configuración. La cadencia de ejecución se define en [`scripts/delta_load.sh`](scripts/delta_load.sh).

**Documentación:** <https://cruzlorite.github.io/bdns-sync/>

## Instalación

Python 3.11 a 3.14.

```bash
pip install bdns-sync                # SQLite; para otros motores, instala además su driver
pip install "bdns-sync[bigquery]"    # con el driver de BigQuery
```

## Uso

El destino es cualquier URL de SQLAlchemy, en `BDNS_SYNC_TARGET_URL`:

```bash
export BDNS_SYNC_TARGET_URL="sqlite:///bdns.db"          # o postgresql://..., bigquery://proyecto/dataset
bdns-sync sync sectores                                  # catálogo: reemplazo completo
bdns-sync sync concesiones_busqueda --window daily       # incremental: el día de ayer
bdns-sync sync concesiones_busqueda --since 2020-01-01   # carga histórica, hasta ayer
```

De cero a una tabla sincronizada en unos diez minutos: [Empezar](https://cruzlorite.github.io/bdns-sync/getting-started/). Todas las opciones: [referencia del CLI](https://cruzlorite.github.io/bdns-sync/reference/cli/).

## Documentación

- **[Empezar](https://cruzlorite.github.io/bdns-sync/getting-started/)**: tutorial, de cero a una tabla consultable.
- **Guías**: [operación programada](https://cruzlorite.github.io/bdns-sync/guides/scheduling/) · [cargas iniciales y backfills](https://cruzlorite.github.io/bdns-sync/guides/backfill/) · [despliegue en la nube](https://cruzlorite.github.io/bdns-sync/guides/deployment/)
- **Explicación**: [tipos de endpoint](https://cruzlorite.github.io/bdns-sync/explanation/endpoint-types/) · [qué cuenta como un cambio](https://cruzlorite.github.io/bdns-sync/explanation/payload-policy/) · [comportamiento de la API](https://cruzlorite.github.io/bdns-sync/explanation/bdns-api-behavior/) · [buenas prácticas oficiales](https://cruzlorite.github.io/bdns-sync/explanation/official-practices/) · [antes de consultar los datos](https://cruzlorite.github.io/bdns-sync/explanation/data-caveats/) · [limitaciones conocidas](https://cruzlorite.github.io/bdns-sync/explanation/limitations/) · [bases de datos de destino](https://cruzlorite.github.io/bdns-sync/explanation/sinks/)
- **Referencia**: [CLI](https://cruzlorite.github.io/bdns-sync/reference/cli/) · [modelo de datos](https://cruzlorite.github.io/bdns-sync/reference/data-model/) · [API Python](https://cruzlorite.github.io/bdns-sync/reference/api/)
- **[Decisiones de arquitectura](https://cruzlorite.github.io/bdns-sync/adr/)**

## Desarrollo

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install -E bigquery
make test         # tests
make check-docs   # referencias a docs/, docstrings y build del sitio
make docs         # sirve la documentación en local
```

Las convenciones de docstrings están en [docs/contributing/docstrings.md](docs/contributing/docstrings.md), y lo pendiente en la [hoja de ruta](docs/roadmap.md).

## Aviso legal

Proyecto no oficial, sin ninguna relación con la Base de Datos Nacional de Subvenciones (BDNS) ni con el Ministerio de Hacienda. Se distribuye bajo licencia GPL v3, que excluye expresamente cualquier garantía: se usa bajo la responsabilidad de quien lo usa, sin garantía de ningún tipo y sin que el autor responda por daños, pérdidas de datos o usos indebidos.

Los datos sincronizados proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) y están sujetos a su propio [aviso legal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) y a las [buenas prácticas de la API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

## Licencia y enlaces

- [GNU GPL v3.0](./LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal BDNS](https://www.infosubvenciones.es) · [Aviso legal BDNS](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal)
- Proyecto hermano: [bdns-fetch](https://github.com/cruzlorite/bdns-fetch) (extracción)
