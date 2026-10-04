# BDNS Sync

[![CI](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Mantiene en tu base de datos una copia de la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api) con el histórico de todas sus versiones (SCD2).

Para hablar con la API se apoya en [`bdns-fetch`](https://github.com/cruzlorite/bdns-fetch), y por encima añade lo necesario para guardar los datos: el histórico de versiones, la detección de cambios y de bajas, y el registro de cada ejecución.

Basta con un comando al día: comprueba que la API no ha cambiado, sincroniza las 22 entidades con el periodo que toque y deja anotada cada ejecución. No necesita fichero de configuración.

**Documentación:** <https://cruzlorite.github.io/bdns-sync/>

## Instalación

Necesitas Python 3.11 o posterior (hasta la 3.14).

```bash
pip install bdns-sync                # SQLite; para otras bases de datos, instala también su driver
pip install "bdns-sync[bigquery]"    # con el driver de BigQuery
```

## Uso

La base de datos de destino se indica con una URL de SQLAlchemy en `BDNS_SYNC_TARGET_URL`:

```bash
export BDNS_SYNC_TARGET_URL="sqlite:///bdns.db"          # o postgresql://..., bigquery://proyecto/dataset
bdns-sync backfill                                       # una sola vez, para cargar el histórico
bdns-sync delta                                          # todos los días, con la comprobación de la API
bdns-sync sync concesiones_busqueda --window weekly      # una sola entidad
bdns-sync delta --dry-run                                # qué haría hoy, sin tocar nada
```

Para tener una tabla sincronizada en unos diez minutos, empieza por [primeros pasos](https://cruzlorite.github.io/bdns-sync/getting-started/). Todas las opciones están en la [referencia de la línea de comandos](https://cruzlorite.github.io/bdns-sync/reference/cli/).

## Documentación

- **[Primeros pasos](https://cruzlorite.github.io/bdns-sync/getting-started/)**: de cero a una tabla que puedes consultar.
- **Guías**: [sincronización diaria](https://cruzlorite.github.io/bdns-sync/guides/scheduling/) · [carga inicial](https://cruzlorite.github.io/bdns-sync/guides/backfill/) · [despliegue en la nube](https://cruzlorite.github.io/bdns-sync/guides/deployment/)
- **Conceptos**: [tipos de entidad](https://cruzlorite.github.io/bdns-sync/explanation/endpoint-types/) · [qué cuenta como un cambio](https://cruzlorite.github.io/bdns-sync/explanation/payload-policy/) · [cómo sincroniza](https://cruzlorite.github.io/bdns-sync/explanation/sync-behavior/) · [buenas prácticas oficiales](https://cruzlorite.github.io/bdns-sync/explanation/official-practices/) · [antes de consultar los datos](https://cruzlorite.github.io/bdns-sync/explanation/data-caveats/) · [limitaciones conocidas](https://cruzlorite.github.io/bdns-sync/explanation/limitations/) · [bases de datos de destino](https://cruzlorite.github.io/bdns-sync/explanation/sinks/)
- **Referencia**: [línea de comandos](https://cruzlorite.github.io/bdns-sync/reference/cli/) · [modelo de datos](https://cruzlorite.github.io/bdns-sync/reference/data-model/) · [Python](https://cruzlorite.github.io/bdns-sync/reference/api/)
- **[Decisiones de diseño](https://cruzlorite.github.io/bdns-sync/adr/)** · **[Compatibilidad](https://cruzlorite.github.io/bdns-sync/compatibility/)** · **[Changelog](CHANGELOG.md)**

## Desarrollo

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install -E bigquery
make test         # tests
make check-docs   # enlaces, docstrings y generación de la web
make docs         # sirve la documentación en local
```

Si quieres contribuir, lee [CONTRIBUTING.md](CONTRIBUTING.md); para informar de una vulnerabilidad, sigue [SECURITY.md](SECURITY.md). Lo que queda por hacer está en la [hoja de ruta](docs/roadmap.md).

## Aviso legal

Este es un proyecto personal y no oficial. No tiene ninguna relación con la Intervención General de la Administración del Estado (IGAE), que es el organismo que gestiona la BDNS, ni cuenta con su apoyo. Se distribuye con licencia MIT, que excluye cualquier garantía: lo usas bajo tu responsabilidad y el autor no responde de daños, pérdidas de datos ni usos indebidos.

Los datos que se sincronizan proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es), y su reutilización está sujeta al [aviso legal del portal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) y a sus [buenas prácticas para la API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf). En resumen, si reutilizas los datos:

- tienes que citar la fuente (por ejemplo, "Origen de los datos: Intervención General de la Administración del Estado") e indicar la fecha de la última actualización si viene en los datos;
- no puedes cambiar el sentido de la información;
- no puedes dar a entender que la IGAE participa en tu reutilización, la patrocina o la apoya;
- si hay datos personales, solo puedes reutilizarlos para controlar la actuación de los gestores públicos o con fines históricos, estadísticos o científicos, y en este último caso tienes que disociarlos antes e indicar que lo has hecho y quién lo ha hecho.

Este resumen no sustituye al texto oficial ni a la [Ley 37/2007 sobre reutilización de la información del sector público](https://www.boe.es/eli/es/l/2007/11/16/37/con), que prevé sanciones para quien la incumpla. Si tienes dudas, consúltalo con un asesor legal.

**Datos personales.** Varias tablas (`concesiones_busqueda` o `sanciones_busqueda`, entre otras) guardan nombres y NIF de personas físicas, que la BDNS publica parcialmente anonimizados. Ten en cuenta que el histórico **los conserva aunque el portal los retire**: las concesiones a personas físicas, por ejemplo, solo se publican durante el año de la concesión y el siguiente. Quien gestiona la base de datos de destino es responsable de tratar esos datos conforme al RGPD (con una finalidad legítima, un plazo de conservación y control de quién accede) y a las condiciones anteriores.

## Licencia y enlaces

- [Licencia MIT](./LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal de la BDNS](https://www.infosubvenciones.es) · [Aviso legal del portal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal)
- Proyecto relacionado: [bdns-fetch](https://github.com/cruzlorite/bdns-fetch), que se encarga de descargar los datos de la API
