# BDNS Fetch

[![CI](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Cliente Python y CLI para la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api). Cubre los 29 endpoints de consulta, con paginación, reintentos y el límite de peticiones de la API aplicados por defecto, y documenta cómo se comporta de verdad la API.

Es la capa de extracción de la familia: [`bdns-sync`](https://github.com/cruzlorite/bdns-sync) se apoya en ella para mantener una copia local versionada de los mismos datos.

**Documentación:** <https://cruzlorite.github.io/bdns-fetch/>

## Instalación

Python 3.11 a 3.14.

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

De cero a la primera consulta en cinco minutos: [Empezar](https://cruzlorite.github.io/bdns-fetch/getting-started/).

## Documentación

- **[Empezar](https://cruzlorite.github.io/bdns-fetch/getting-started/)**: tutorial, terminal y Python.
- **Guías**: [descargas incrementales](https://cruzlorite.github.io/bdns-fetch/guides/incremental/) · [errores y reintentos](https://cruzlorite.github.io/bdns-fetch/guides/errors/) · [endpoints sin método propio](https://cruzlorite.github.io/bdns-fetch/guides/other-endpoints/)
- **Explicación**: [comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/) · [cómo trabaja el cliente](https://cruzlorite.github.io/bdns-fetch/explanation/policies/)
- **Referencia**: [CLI](https://cruzlorite.github.io/bdns-fetch/reference/cli/) · [API Python](https://cruzlorite.github.io/bdns-fetch/reference/api/)
- **[Decisiones de arquitectura](https://cruzlorite.github.io/bdns-fetch/adr/)** · **[Compatibilidad](https://cruzlorite.github.io/bdns-fetch/compatibility/)** · **[Changelog](CHANGELOG.md)**

## Desarrollo

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install
make test               # tests unitarios, sin red
make test-integration   # contra la API real
make check-docs         # referencias, docstrings y build del sitio
make docs               # sirve la documentación en local
```

Cómo contribuir: [CONTRIBUTING.md](CONTRIBUTING.md). Vulnerabilidades: [SECURITY.md](SECURITY.md).

## Aviso legal

Proyecto no oficial, sin ninguna relación con la Base de Datos Nacional de Subvenciones (BDNS) ni con el Ministerio de Hacienda. Se distribuye bajo licencia GPL v3, que excluye expresamente cualquier garantía: se usa bajo la responsabilidad de quien lo usa, sin garantía de ningún tipo y sin que el autor responda por daños, pérdidas de datos o usos indebidos.

Los datos proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) y están sujetos a su propio [aviso legal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) y a las [buenas prácticas de la API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

**Datos personales.** Algunos endpoints (`concesiones-busqueda`, `sanciones-busqueda`, `terceros`, entre otros) devuelven nombres y NIF de personas físicas. `bdns-fetch` los entrega tal como los publica la API, sin transformarlos. Quien los descarga y los almacena es responsable de tratarlos conforme al RGPD y a la finalidad de publicidad para la que se publican.

## Licencia y enlaces

- [GNU GPL v3.0 o posterior](./LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal BDNS](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns-fetch)
- Proyecto hermano: [bdns-sync](https://github.com/cruzlorite/bdns-sync) (histórico versionado)
