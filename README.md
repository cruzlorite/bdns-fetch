# BDNS Fetch

[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

Cliente Python y CLI para la [API REST de la BDNS](https://www.infosubvenciones.es/bdnstrans/api). Cubre los 29 endpoints disponibles con soporte completo de parámetros, paginación automática y reintentos configurables.

## Instalación

```bash
pip install bdns-fetch
```

o desde el repositorio:

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
pip install .
```

## Uso

### Cliente Python

```python
from bdns.fetch.client import BDNSClient

client = BDNSClient()

for org in client.fetch_organos(idAdmon="C"):
    print(org["codigo"], "-", org["descripcion"])
```

Búsqueda paginada:

```python
resultados = client.fetch_ayudasestado_busqueda(
    descripcion="investigación",
    pageSize=1000,
    num_pages=5,
    from_page=0,
)
for item in resultados:
    print(item)
```

Descarga de documentos binarios:

```python
pdf_bytes = client.fetch_convocatorias_pdf(id=608268, vpd="A07")
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_bytes)
```

Configuración del cliente:

```python
client = BDNSClient(
    max_retries=5,    # reintentos por petición fallida
    wait_time=2,      # segundos entre reintentos
    max_workers=10,   # hilos concurrentes para paginación
    return_raw=False, # True devuelve objetos de página completos
)
```

### CLI

```bash
# Ver ayuda
bdns-fetch --help
bdns-fetch <comando> --help

# Guardar a fichero
bdns-fetch --output-file organos.jsonl organos --idAdmon C

# Búsqueda con filtros
bdns-fetch --output-file resultado.jsonl ayudasestado-busqueda \
    --descripcion "innovación" --fechaDesde "2023-01-01" --fechaHasta "2024-12-31"

# Paginación
bdns-fetch concesiones-busqueda --num-pages 0 --pageSize 10000

# Salida a stdout (por defecto)
bdns-fetch convocatorias-ultimas | jq .
```

Opciones globales:

| Opción | Alias | Por defecto | Descripción |
|---|---|---|---|
| `--output-file` | `-o` | `-` (stdout) | Fichero de salida en formato JSONL |
| `--max-retries` | `-mr` | `3` | Reintentos por petición fallida |
| `--wait-time` | `-wt` | `2` | Segundos entre reintentos |
| `--max-workers` | `-mw` | `5` | Hilos concurrentes para paginación |
| `--return-raw` | `-rr` | `false` | Devolver objetos de página completos |
| `--verbose` | `-v` | `false` | Log detallado de peticiones HTTP |

### Comandos disponibles

| Comando | Método cliente |
|---|---|
| `actividades` | `fetch_actividades` |
| `sectores` | `fetch_sectores` |
| `regiones` | `fetch_regiones` |
| `finalidades` | `fetch_finalidades` |
| `beneficiarios` | `fetch_beneficiarios` |
| `instrumentos` | `fetch_instrumentos` |
| `reglamentos` | `fetch_reglamentos` |
| `objetivos` | `fetch_objetivos` |
| `organos` | `fetch_organos` |
| `organos-agrupacion` | `fetch_organos_agrupacion` |
| `organos-codigo` | `fetch_organos_codigo` |
| `organos-codigoadmin` | `fetch_organos_codigoadmin` |
| `convocatorias` | `fetch_convocatorias` |
| `convocatorias-busqueda` | `fetch_convocatorias_busqueda` |
| `convocatorias-ultimas` | `fetch_convocatorias_ultimas` |
| `convocatorias-documentos` | `fetch_convocatorias_documentos` |
| `convocatorias-pdf` | `fetch_convocatorias_pdf` |
| `concesiones-busqueda` | `fetch_concesiones_busqueda` |
| `ayudasestado-busqueda` | `fetch_ayudasestado_busqueda` |
| `minimis-busqueda` | `fetch_minimis_busqueda` |
| `grandesbeneficiarios-anios` | `fetch_grandesbeneficiarios_anios` |
| `grandesbeneficiarios-busqueda` | `fetch_grandesbeneficiarios_busqueda` |
| `planesestrategicos` | `fetch_planesestrategicos` |
| `planesestrategicos-busqueda` | `fetch_planesestrategicos_busqueda` |
| `planesestrategicos-documentos` | `fetch_planesestrategicos_documentos` |
| `planesestrategicos-vigencia` | `fetch_planesestrategicos_vigencia` |
| `partidospoliticos-busqueda` | `fetch_partidospoliticos_busqueda` |
| `sanciones-busqueda` | `fetch_sanciones_busqueda` |
| `terceros` | `fetch_terceros` |

## Buenas prácticas (oficiales)

Según el documento oficial ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf):

- **Límite de peticiones**: máximo 10 peticiones GET/segundo por IP. `bdns-fetch` lo aplica internamente con un limitador tipo token-bucket compartido entre todas las peticiones HTTP, independientemente de `--max-workers`.
- **Sincronización incremental**: usa `fechaRegInicio`/`fechaRegFin` (fecha de registro) para detectar altas/cambios, no `fechaConcesion`/`fechaDesde`/`fechaHasta` (fecha de concesión) — son filtros independientes. Disponible en `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda`.
- **`terceros`**: el documento señala este endpoint como redundante — `concesiones-busqueda` ya devuelve toda la información del beneficiario. Usa `concesiones-busqueda` y evita `terceros`.

## Limitaciones

- No implementa los endpoints de exportación (CSV/XLSX) ni los de configuración del portal.
- Los resultados de paginación concurrente no están ordenados por número de página.

## Licencia y enlaces

- **Licencia:** [GNU General Public License v3.0](./LICENSE)
- **API oficial:** [https://www.infosubvenciones.es/bdnstrans/api](https://www.infosubvenciones.es/bdnstrans/api)
- **Portal BDNS:** [https://www.infosubvenciones.es](https://www.infosubvenciones.es)
- **PyPI:** [https://pypi.org/project/bdns-fetch](https://pypi.org/project/bdns-fetch)

Para más información sobre los datos disponibles, consulta el portal oficial.

---

**bdns-fetch** es software libre. ¡Las contribuciones son bienvenidas!
