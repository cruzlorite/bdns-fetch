# BDNS Fetch

[![CI](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Cliente Python y CLI para la [API REST de la Base de Datos Nacional de Subvenciones (BDNS)](https://www.infosubvenciones.es/bdnstrans/api). Cubre los 29 endpoints de consulta, con paginación, reintentos y el límite de peticiones de la API aplicados por defecto.

Es la capa de extracción de la familia: [`bdns-sync`](https://github.com/cruzlorite/bdns-sync) se apoya en ella para mantener una copia local versionada de los mismos datos.

## Instalación

Python 3.11 a 3.14.

```bash
pip install bdns-fetch
```

## Cliente Python

```python
from bdns.fetch import BDNSClient, TipoAdministracion

client = BDNSClient()

for organo in client.fetch_organos(idAdmon=TipoAdministracion.C):
    print(organo["id"], organo["descripcion"])
```

Los parámetros de cada método son los de la API, con su misma grafía (`fechaDesde`, `nifCif`...), y se pasan siempre por nombre. Las fechas son objetos `date`; las listas, listas de Python.

Los endpoints de búsqueda están paginados. Por defecto se descargan **todas** las páginas; `num_pages` y `from_page` acotan el rango:

```python
from datetime import date

for concesion in client.fetch_concesiones_busqueda(
    fechaRegInicio=date(2024, 1, 1),
    fechaRegFin=date(2024, 1, 31),
):
    ...

primeras = client.fetch_ayudasestado_busqueda(descripcion="investigación", num_pages=2)
```

Los endpoints de documentos devuelven `bytes`:

```python
pdf = client.fetch_convocatorias_pdf(id=608268, vpd="GE")
```

Configuración:

```python
client = BDNSClient(
    max_retries=3,     # reintentos tras el primer intento, solo para fallos transitorios
    wait_time=2,       # espera inicial entre reintentos (s); se duplica en cada uno, hasta 60
    max_workers=5,     # hilos descargando páginas en paralelo
    return_raw=False,  # True: páginas completas en vez de registros
    progress=None,     # barra de progreso; None = solo si stderr es una terminal
    timeout=30,        # segundos por respuesta HTTP
)
```

### Comportamiento

- **Límite de peticiones.** Como máximo 10 peticiones por segundo por proceso, compartidas entre todas las instancias e hilos. Es el límite por IP que fijan las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).
- **Reintentos.** Se reintentan los errores de red, HTTP 429 y 5xx, y el código `ERR_MANTENIMIENTO_BBDD`, con espera exponencial y aleatoria, respetando `Retry-After`. Cualquier otro error se lanza al momento: repetir una petición incorrecta no la arregla.
- **Paginación.** Las páginas se piden en paralelo pero se entregan en orden, y nunca hay más de `2 × max_workers` en memoria. Si se deja de iterar, no se descargan las restantes.
- **Errores.** Todo fallo es un `BDNSError` (`message`, `suggestion`, `technical_details`). Los transitorios, una vez agotados los reintentos, son su subclase `BDNSTransientError`.

## CLI

```bash
bdns-fetch --help
bdns-fetch <comando> --help

bdns-fetch -o organos.jsonl organos --idAdmon C
bdns-fetch convocatorias-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-12-31 --num-pages 0
bdns-fetch -o convocatoria.pdf convocatorias-pdf --id 608268 --vpd GE
bdns-fetch convocatorias-ultimas | jq .descripcion
```

Los registros se escriben en [JSON Lines](https://jsonlines.org/), uno por línea; los documentos, tal cual. Por defecto el CLI descarga **una** página y avisa si hay más; `--num-pages 0` las descarga todas.

Las opciones de la herramienta van en kebab-case (`--max-retries`) y las que corresponden a un parámetro de la API conservan su grafía (`--fechaDesde`). Las fechas admiten ISO (`2024-01-31`), día primero (`31/01/2024`) o lenguaje natural (`hace 2 semanas`).

Opciones globales:

| Opción | Alias | Por defecto | Descripción |
|---|---|---|---|
| `--output-file` | `-o` | `-` (stdout) | Fichero de salida |
| `--max-retries` | `-mr` | `3` | Reintentos para fallos transitorios; 0 los desactiva |
| `--wait-time` | `-wt` | `2` | Espera inicial entre reintentos (s) |
| `--max-workers` | `-mw` | `5` | Hilos descargando páginas |
| `--return-raw` | `-rr` | no | Páginas completas en vez de registros |
| `--progress/--no-progress` | | automático | Barra de progreso |
| `--verbose` | `-v` | no | Log de cada petición HTTP |

Ante un error de la API, el CLI muestra el mensaje y sale con código 1.

### Comandos

Un comando por endpoint. El nombre es el del método sin `fetch_`, con guiones; la forma con guiones bajos (`concesiones_busqueda`), que es como lo llama `bdns-sync`, también se acepta.

| Comando | Método | Paginado |
|---|---|---|
| `actividades` | `fetch_actividades` | |
| `sectores` | `fetch_sectores` | |
| `regiones` | `fetch_regiones` | |
| `finalidades` | `fetch_finalidades` | |
| `beneficiarios` | `fetch_beneficiarios` | |
| `instrumentos` | `fetch_instrumentos` | |
| `reglamentos` | `fetch_reglamentos` | |
| `objetivos` | `fetch_objetivos` | |
| `organos` | `fetch_organos` | |
| `organos-agrupacion` | `fetch_organos_agrupacion` | |
| `organos-codigo` | `fetch_organos_codigo` | |
| `organos-codigoadmin` | `fetch_organos_codigoadmin` | |
| `convocatorias` | `fetch_convocatorias` | |
| `convocatorias-busqueda` | `fetch_convocatorias_busqueda` | sí |
| `convocatorias-ultimas` | `fetch_convocatorias_ultimas` | |
| `convocatorias-documentos` | `fetch_convocatorias_documentos` | documento |
| `convocatorias-pdf` | `fetch_convocatorias_pdf` | documento |
| `concesiones-busqueda` | `fetch_concesiones_busqueda` | sí |
| `ayudasestado-busqueda` | `fetch_ayudasestado_busqueda` | sí |
| `minimis-busqueda` | `fetch_minimis_busqueda` | sí |
| `partidospoliticos-busqueda` | `fetch_partidospoliticos_busqueda` | sí |
| `grandesbeneficiarios-anios` | `fetch_grandesbeneficiarios_anios` | |
| `grandesbeneficiarios-busqueda` | `fetch_grandesbeneficiarios_busqueda` | sí |
| `sanciones-busqueda` | `fetch_sanciones_busqueda` | sí |
| `planesestrategicos` | `fetch_planesestrategicos` | |
| `planesestrategicos-busqueda` | `fetch_planesestrategicos_busqueda` | sí |
| `planesestrategicos-documentos` | `fetch_planesestrategicos_documentos` | documento |
| `planesestrategicos-vigencia` | `fetch_planesestrategicos_vigencia` | |
| `terceros` | `fetch_terceros` | |

## Buenas prácticas oficiales

Según ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf):

- **Límite de peticiones:** 10 GET por segundo por IP. `bdns-fetch` lo aplica por proceso; varios procesos desde la misma IP lo comparten y deben repartírselo.
- **Sincronización incremental:** usa `fechaRegInicio`/`fechaRegFin` (fecha de registro) para detectar altas y cambios, no `fechaDesde`/`fechaHasta` (fecha de concesión): son filtros independientes. Disponible en `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda` y `partidospoliticos-busqueda`.
- **`terceros`:** el documento lo considera redundante; `concesiones-busqueda` ya trae los datos del beneficiario.

## Limitaciones

- No implementa los endpoints de exportación (CSV/XLSX) ni los de configuración del portal.

## Desarrollo

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install
make test               # tests unitarios, sin red
make test-integration   # contra la API real
make lint
```

Los tests unitarios simulan HTTP y son los que corren en cada push. Los de integración llaman a la API real y corren cada noche en [Integration](.github/workflows/integration.yml). Los cambios se registran en el [CHANGELOG](CHANGELOG.md).

## Aviso legal

Proyecto no oficial, sin ninguna relación con la Base de Datos Nacional de Subvenciones (BDNS) ni con el Ministerio de Hacienda. Se distribuye bajo licencia GPL v3, que excluye expresamente cualquier garantía: se usa bajo la responsabilidad de quien lo usa, sin garantía de ningún tipo y sin que el autor responda por daños, pérdidas de datos o usos indebidos.

Los datos proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) y están sujetos a su propio [aviso legal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) y a las [buenas prácticas de la API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

**Datos personales.** Algunos endpoints (`concesiones-busqueda`, `sanciones-busqueda`, `terceros`, entre otros) devuelven nombres y NIF de personas físicas. `bdns-fetch` los entrega tal como los publica la API, sin transformarlos. Quien los descarga y los almacena es responsable de tratarlos conforme al RGPD y a la finalidad de publicidad para la que se publican.

## Licencia y enlaces

- [GNU GPL v3.0 o posterior](./LICENSE)
- [API oficial](https://www.infosubvenciones.es/bdnstrans/api) · [Portal BDNS](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns-fetch)
- Proyecto hermano: [bdns-sync](https://github.com/cruzlorite/bdns-sync) (histórico versionado)
