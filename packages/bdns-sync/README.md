# BDNS Sync

[![CI](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Motor de sincronización que mantiene una copia local versionada (SCD2) de la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api).

Se apoya en [`bdns-fetch`](https://github.com/cruzlorite/bdns-fetch), que se encarga de extraer los datos de la API; `bdns-sync` pone encima la capa de almacenamiento: histórico versionado, detección de cambios y de bajas, y registro de ejecuciones.

Un comando al día mantiene el destino al día: comprueba que la API no ha cambiado, sincroniza las 22 entidades con la ventana que toca y registra cada ejecución. Sin fichero de configuración.

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
bdns-sync backfill                                       # una vez: el histórico completo
bdns-sync delta                                          # a diario: la cadencia, con comprobación de la API
bdns-sync sync concesiones_busqueda --window weekly      # una entidad suelta
bdns-sync delta --dry-run                                # qué haría hoy, sin tocar nada
```

De cero a una tabla sincronizada en unos diez minutos: [Empezar](https://cruzlorite.github.io/bdns-sync/getting-started/). Todas las opciones: [referencia del CLI](https://cruzlorite.github.io/bdns-sync/reference/cli/).

## Documentación

- **[Empezar](https://cruzlorite.github.io/bdns-sync/getting-started/)**: tutorial, de cero a una tabla consultable.
- **Guías**: [operación programada](https://cruzlorite.github.io/bdns-sync/guides/scheduling/) · [cargas iniciales y backfills](https://cruzlorite.github.io/bdns-sync/guides/backfill/) · [despliegue en la nube](https://cruzlorite.github.io/bdns-sync/guides/deployment/)
- **Explicación**: [tipos de endpoint](https://cruzlorite.github.io/bdns-sync/explanation/endpoint-types/) · [qué cuenta como un cambio](https://cruzlorite.github.io/bdns-sync/explanation/payload-policy/) · [cómo sincroniza](https://cruzlorite.github.io/bdns-sync/explanation/sync-behavior/) · [buenas prácticas oficiales](https://cruzlorite.github.io/bdns-sync/explanation/official-practices/) · [antes de consultar los datos](https://cruzlorite.github.io/bdns-sync/explanation/data-caveats/) · [limitaciones conocidas](https://cruzlorite.github.io/bdns-sync/explanation/limitations/) · [bases de datos de destino](https://cruzlorite.github.io/bdns-sync/explanation/sinks/)
- **Referencia**: [CLI](https://cruzlorite.github.io/bdns-sync/reference/cli/) · [modelo de datos](https://cruzlorite.github.io/bdns-sync/reference/data-model/) · [API Python](https://cruzlorite.github.io/bdns-sync/reference/api/)
- **[Decisiones de arquitectura](https://cruzlorite.github.io/bdns-sync/adr/)** · **[Compatibilidad](https://cruzlorite.github.io/bdns-sync/compatibility/)** · **[Changelog](CHANGELOG.md)**

## Desarrollo

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install -E bigquery
make test         # tests
make check-docs   # referencias a docs/, docstrings y build del sitio
make docs         # sirve la documentación en local
```

Cómo contribuir: [CONTRIBUTING.md](CONTRIBUTING.md). Vulnerabilidades: [SECURITY.md](SECURITY.md). Lo pendiente, en la [hoja de ruta](docs/roadmap.md).

## Aviso legal

Proyecto no oficial, sin ninguna relación con la Base de Datos Nacional de Subvenciones (BDNS) ni con el Ministerio de Hacienda. Se distribuye bajo licencia MIT, que excluye expresamente cualquier garantía: se usa bajo la responsabilidad de quien lo usa, sin garantía de ningún tipo y sin que el autor responda por daños, pérdidas de datos o usos indebidos.

Los datos sincronizados proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) y están sujetos a su propio [aviso legal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) y a las [buenas prácticas de la API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

**Datos personales.** Varias tablas (`concesiones_busqueda`, `sanciones_busqueda`, entre otras) contienen nombres y NIF de personas físicas, y el histórico SCD2 los conserva aunque la fuente los retire. `bdns-sync` los guarda tal como los publica la API. Quien opera la base de datos de destino es responsable de tratarlos conforme al RGPD: finalidad, plazo de conservación y control de acceso.

## Licencia y enlaces

- [Licencia MIT](./LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal BDNS](https://www.infosubvenciones.es) · [Aviso legal BDNS](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal)
- Proyecto hermano: [bdns-fetch](https://github.com/cruzlorite/bdns-fetch) (extracción)
