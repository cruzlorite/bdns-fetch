# BDNS Fetch

[![CI](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Cliente de Python y herramienta de línea de comandos para descargar datos de la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api). Cubre los 29 endpoints de consulta, se encarga de la paginación, de los reintentos y del límite de peticiones que fija la API, y documenta cómo se comporta esta de verdad.

Si además quieres guardar los datos con su histórico de versiones, [`bdns-sync`](https://github.com/cruzlorite/bdns-sync) hace justo eso apoyándose en este cliente.

**Documentación:** <https://cruzlorite.github.io/bdns-fetch/>

## Instalación

Necesitas Python 3.11 o posterior (hasta la 3.14).

```bash
pip install bdns-fetch
```

## Uso

```bash
bdns-fetch -o organos.jsonl organos --idAdmon C
bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-31 --num-pages 0 > enero.jsonl
bdns-fetch check-api
```

```python
from datetime import date

from bdns.fetch import BDNSClient
from bdns.fetch.dates import registration_range

client = BDNSClient()
for concesion in client.fetch_concesiones_busqueda(**registration_range(date(2024, 1, 1), date(2024, 1, 31))):
    print(concesion["beneficiario"], concesion["importe"])
```

Para hacer tu primera consulta en cinco minutos, empieza por [primeros pasos](https://cruzlorite.github.io/bdns-fetch/getting-started/).

## Documentación

- **[Primeros pasos](https://cruzlorite.github.io/bdns-fetch/getting-started/)**: tu primera consulta desde la terminal y desde Python.
- **Guías**: [descargas incrementales](https://cruzlorite.github.io/bdns-fetch/guides/incremental/) · [errores y reintentos](https://cruzlorite.github.io/bdns-fetch/guides/errors/) · [endpoints sin método propio](https://cruzlorite.github.io/bdns-fetch/guides/other-endpoints/)
- **Conceptos**: [comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/) · [cómo trabaja el cliente](https://cruzlorite.github.io/bdns-fetch/explanation/policies/)
- **Referencia**: [línea de comandos](https://cruzlorite.github.io/bdns-fetch/reference/cli/) · [Python](https://cruzlorite.github.io/bdns-fetch/reference/api/)
- **[Decisiones de diseño](https://cruzlorite.github.io/bdns-fetch/adr/)** · **[Compatibilidad](https://cruzlorite.github.io/bdns-fetch/compatibility/)** · **[Changelog](CHANGELOG.md)**

## Desarrollo

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install
make test               # tests unitarios, sin conexión
make test-integration   # tests contra la API real
make check-docs         # enlaces, docstrings y generación de la web
make docs               # sirve la documentación en local
```

Si quieres contribuir, lee [CONTRIBUTING.md](CONTRIBUTING.md). Para informar de una vulnerabilidad, sigue [SECURITY.md](SECURITY.md).

## Aviso legal

Este es un proyecto personal y no oficial. No tiene ninguna relación con la Intervención General de la Administración del Estado (IGAE), que es el organismo que gestiona la BDNS, ni cuenta con su apoyo. Se distribuye con licencia MIT, que excluye cualquier garantía: lo usas bajo tu responsabilidad y el autor no responde de daños, pérdidas de datos ni usos indebidos.

Los datos que descargas proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es), y su reutilización está sujeta al [aviso legal del portal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal). En resumen, si los reutilizas:

- tienes que citar la fuente (por ejemplo, "Origen de los datos: Intervención General de la Administración del Estado") e indicar la fecha de la última actualización si viene en los datos;
- no puedes cambiar el sentido de la información;
- no puedes dar a entender que la IGAE participa en tu reutilización, la patrocina o la apoya;
- si hay datos personales, solo puedes reutilizarlos para controlar la actuación de los gestores públicos o con fines históricos, estadísticos o científicos, y en este último caso tienes que disociarlos antes e indicar que lo has hecho y quién lo ha hecho.

Este resumen no sustituye al texto oficial ni a la [Ley 37/2007 sobre reutilización de la información del sector público](https://www.boe.es/eli/es/l/2007/11/16/37/con), que prevé sanciones para quien la incumpla. Si tienes dudas, consúltalo con un asesor legal.

**Datos personales.** Algunos endpoints (`concesiones-busqueda`, `sanciones-busqueda` o `terceros`, entre otros) devuelven nombres y NIF de personas físicas, que la BDNS publica parcialmente anonimizados. `bdns-fetch` los entrega tal y como los publica la API, sin transformarlos, y quien los descarga y los guarda es responsable de tratarlos conforme al RGPD y a las condiciones anteriores.

## Licencia y enlaces

- [Licencia MIT](./LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal de la BDNS](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns-fetch)
- Proyecto relacionado: [bdns-sync](https://github.com/cruzlorite/bdns-sync), para guardar el histórico de versiones
