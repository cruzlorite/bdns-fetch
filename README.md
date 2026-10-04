# BDNS

[![CI](https://github.com/cruzlorite/bdns/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns.svg)](https://pypi.org/project/bdns/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/cruzlorite/bdns/blob/main/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](https://github.com/cruzlorite/bdns/blob/main/README.en.md)

Herramientas para descargar, conservar y reutilizar los datos de la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api). El paquete trae dos:

- **`bdns-fetch`**, un cliente de Python y una herramienta de línea de comandos que cubren los 29 endpoints de consulta. Se encargan de la paginación, de los reintentos y del límite de peticiones que fija la API.
- **`bdns-sync`**, que mantiene en tu base de datos (SQLite, PostgreSQL, DuckDB o BigQuery) una copia de la BDNS con el histórico de todas sus versiones. Basta con un comando al día.

**Documentación:** <https://cruzlorite.github.io/bdns/>

## Instalación

Necesitas Python 3.11 o posterior (hasta la 3.14).

```bash
pip install bdns                # con SQLite; para otras bases de datos, instala también su driver
pip install "bdns[bigquery]"    # con el driver de BigQuery
```

## Uso

Descargar datos:

```bash
bdns-fetch -o organos.jsonl organos --idAdmon C
bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-31 --num-pages 0 > enero.jsonl
```

```python
from datetime import date

from bdns.fetch import BDNSClient
from bdns.fetch.dates import registration_range

client = BDNSClient()
for concesion in client.fetch_concesiones_busqueda(**registration_range(date(2024, 1, 1), date(2024, 1, 31))):
    print(concesion["beneficiario"], concesion["importe"])
```

Mantener una copia con el histórico, indicando la base de datos con una URL de SQLAlchemy:

```bash
export BDNS_SYNC_TARGET_URL="sqlite:///bdns.db"          # o postgresql://..., bigquery://proyecto/dataset
bdns-sync backfill                                       # una sola vez, para cargar el histórico
bdns-sync delta                                          # todos los días, con la comprobación de la API
```

Para empezar, cada herramienta tiene sus primeros pasos: [bdns-fetch](https://cruzlorite.github.io/bdns/fetch/getting-started/) y [bdns-sync](https://cruzlorite.github.io/bdns/sync/getting-started/).

## Documentación

- **[bdns-fetch](https://cruzlorite.github.io/bdns/fetch/)**: [primeros pasos](https://cruzlorite.github.io/bdns/fetch/getting-started/) · [descargas incrementales](https://cruzlorite.github.io/bdns/fetch/guides/incremental/) · [comportamiento de la API](https://cruzlorite.github.io/bdns/fetch/explanation/api-behavior/) · [línea de comandos](https://cruzlorite.github.io/bdns/fetch/reference/cli/)
- **[bdns-sync](https://cruzlorite.github.io/bdns/sync/)**: [primeros pasos](https://cruzlorite.github.io/bdns/sync/getting-started/) · [sincronización diaria](https://cruzlorite.github.io/bdns/sync/guides/scheduling/) · [carga inicial](https://cruzlorite.github.io/bdns/sync/guides/backfill/) · [despliegue en la nube](https://cruzlorite.github.io/bdns/sync/guides/deployment/) · [modelo de datos](https://cruzlorite.github.io/bdns/sync/reference/data-model/)
- **Proyecto**: [compatibilidad](https://cruzlorite.github.io/bdns/compatibility/) · [hoja de ruta](https://cruzlorite.github.io/bdns/roadmap/) · [decisiones comunes](https://cruzlorite.github.io/bdns/adr/) · [changelog](https://github.com/cruzlorite/bdns/blob/main/CHANGELOG.md)

Hasta la versión 1.3.0 de `bdns-fetch` y la 0.5.0 de `bdns-sync`, cada herramienta se publicaba como un paquete aparte. Los imports y los comandos no han cambiado: basta con instalar `bdns` ([más detalles](https://cruzlorite.github.io/bdns/compatibility/#previous-names)).

## Desarrollo

Necesitas [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/cruzlorite/bdns.git
cd bdns
make install            # el paquete, sus extras y las herramientas de desarrollo
make test               # tests, sin conexión
make check-docs         # enlaces, docstrings y generación de la web
make docs               # sirve la documentación en local
```

Si quieres contribuir, lee [CONTRIBUTING.md](https://github.com/cruzlorite/bdns/blob/main/CONTRIBUTING.md). Para informar de una vulnerabilidad, sigue [SECURITY.md](https://github.com/cruzlorite/bdns/blob/main/SECURITY.md).

## Aviso legal

Es un proyecto personal y no oficial, sin ninguna relación con la Intervención General de la Administración del Estado (IGAE), que es quien gestiona la BDNS. El código se distribuye con licencia MIT, que excluye cualquier garantía.

Si reutilizas los datos, tienes que cumplir las condiciones de reutilización de la IGAE: citar la fuente, no cambiar el sentido de la información, no dar a entender que la IGAE te respalda y reutilizar los datos personales solo para los fines permitidos. Quien guarda datos personales es responsable de tratarlos conforme al RGPD y la LOPDGDD, y ten en cuenta que el histórico de `bdns-sync` **los conserva aunque el portal los retire**.

Todos los detalles, incluido qué datos personales publica la BDNS, están en el [aviso legal](https://cruzlorite.github.io/bdns/legal/).

## Licencia y enlaces

- [Licencia MIT](https://github.com/cruzlorite/bdns/blob/main/LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal de la BDNS](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns/)
