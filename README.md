# BDNS Fetch

[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇬🇧 English version](./README.en.md)

## Introducción

La **Base de Datos Nacional de Subvenciones (BDNS)** es un repositorio público español que ofrece transparencia sobre todas las subvenciones y ayudas públicas concedidas por las administraciones. Gestionada por la Intervención General de la Administración del Estado (IGAE) bajo el Ministerio de Hacienda, la BDNS centraliza información desde 2014 para el sector público estatal y desde 2016 para el resto de administraciones (ver [datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=La%20Base%20de%20Datos%20Nacional,y%20salvaguardando%20el%20honor%20y), [transparencia.gob.es](https://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/Contratos/Subvenciones.html#:~:text=La%20Base%20de%20Datos%20Nacional,las%20Administraciones%20P%C3%BAblicas%20desde%202016)).
Estos datos incluyen el organismo convocante, el importe, el objeto, los beneficiarios y otra información relevante de cada subvención ([transparencia.gob.es](https://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/Contratos/Subvenciones.html#:~:text=La%20Base%20de%20Datos%20Nacional,las%20Administraciones%20P%C3%BAblicas%20desde%202016)).
La BDNS está regulada por el artículo 20 de la Ley 38/2003, General de Subvenciones, y por el Real Decreto 130/2019 (ver [datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=la%20intimidad%20personal%20o%20familiar,de%20la%20Administraci%C3%B3n%20del%20Estado), [BOE](https://www.boe.es/buscar/act.php?id=BOE-A-2019-4671#:~:text=Real%20Decreto%20130%2F2019%2C%20de%208,subvenciones%20y%20dem%C3%A1s%20ayudas%20p%C3%BAblicas)).
Los datos se publican en línea respetando el honor y la intimidad de las personas físicas ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=en%20el%20Real%20Decreto%20130%2F2019,de%20la%20Administraci%C3%B3n%20del%20Estado)).

Los datos del BDNS son accesibles a través del **Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas (SNPSAP)**. La información puede consultarse en formato HTML desde el portal web oficial del Ministerio de Hacienda, y es exportable a formatos abiertos como CSV, XLSX o PDF. Además, existe una API REST que permite obtener los datos en formato JSON ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=La%20informaci%C3%B3n%20es%20consultable%20en,REST%20en%20formato%20JSON)).
La base de datos se actualiza diariamente, aunque el portal oficial impone limitaciones: por ejemplo, solo admite descargas de hasta 10.000 registros por consulta ([transparencia.gob.es](https://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/Contratos/Subvenciones.html#:~:text=Informaci%C3%B3n%20actualizada%20diariamente%20y%20obtenida,000%20registros)).
También se aplica la retención legal de datos: las concesiones permanecen publicadas 4 años desde su concesión (solo 1 año más en caso de personas físicas) ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=La%20informaci%C3%B3n%20sobre%20concesiones%20permanecer%C3%A1,que%20%C3%A9sta%20se%C3%B1ale%20plazos%20superiores)), tras lo cual se retiran automáticamente.

## Propósito del proyecto

El objetivo del repositorio **bdns-fetch** es facilitar el acceso **programático** a los datos de la BDNS. Se trata de una librería Python y herramienta de línea de comandos (CLI) que implementa la API oficial de la BDNS, con el fin de extraer y analizar subvenciones de forma automatizada. En concreto, bdns-fetch cubre los 29 endpoints de datos disponibles en la API del BDNS, con soporte completo de parámetros y manejo automático de paginación ([GitHub](https://github.com/cruzlorite/bdns-fetch#:~:text=,line%20interface%20for%20quick%20testing)). Ofrece tanto una interfaz de cliente Python limpia y tipada como un comando `bdns-fetch` para pruebas rápidas. Esto supera las limitaciones del portal web oficial (búsqueda básica y a menudo lenta, sin posibilidad de descarga masiva) pues bdns-fetch permite consultas automatizadas y la extracción completa de datos a archivos JSONL.

**Ventajas principales de bdns-fetch:** permite descargar rápidamente subvenciones filtradas por criterios (organismo, fecha, descripción, etc.), aplicar paginación automática sin cargar manualmente cada página, y gestionar errores y reintentos.

## Instalación

```bash
pip install bdns-fetch
```
o

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
pip install .
```

## Uso

### Cliente Python

La librería expone un cliente Python para llamar a los endpoints de la BDNS. Por ejemplo, para obtener la lista de organismos (ministerios, agencias, etc.) registrados:

```python
from bdns.fetch.client import BDNSClient

# Inicializar el cliente
client = BDNSClient()

# Ejecutar la consulta al endpoint "organos"
organos = list(client.fetch_organos())
for org in organos:
    print(org["codigo"], "-", org["descripcion"])

```

Otro ejemplo: buscar [Ayudas de Estado](https://es.wikipedia.org/wiki/Ayudas_de_Estado_en_la_Uni%C3%B3n_Europea) cuyo texto contenga "investigación". Se controla la paginación definiendo el tamaño de página y cuántas páginas queremos:

```python
resultados = client.fetch_ayudasestado_busqueda(
    descripcion="investigación",
    pageSize=1000,   # registros por página (máx. 10000)
    num_pages=5,     # número máximo de páginas a recuperar
    from_page=0      # página de inicio (0 = primera página)
)
for element in resultados:
    print(element["titulo"], "-", element["importe"])

```

También es posible descargar documentos binarios asociados (por ejemplo, convocatorias o planes estratégicos) usando los métodos apropiados que devuelven bytes. Por ejemplo:

```python
# Descargar PDF de convocatoria por ID (id y vpd obtenidos de la BDNS)
pdf_bytes = client.fetch_convocatorias_pdf(id=608268, vpd="A07")
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_bytes)

```

### Interfaz de Línea de Comandos (CLI)

bdns-fetch incluye un CLI sencillo. Tras la instalación, use  
`bdns-fetch --help` para ver opciones.

Obtener y guardar lista de órganos:
```bash
bdns-fetch --output-file organos.jsonl organos
```
Buscar ayudas de Estado con palabra clave y rango de fechas:
```bash
bdns-fetch --verbose --output-file ayudas_busqueda.jsonl ayudasestado-busqueda \
    --descripcion "innovación" --fechaDesde "2023-01-01" --fechaHasta "2024-12-31"
```
Descargar las últimas convocatorias oficiales:
```bash
bdns-fetch --output-file convocatorias.jsonl convocatorias-ultimas
```
Todos los datos extraídos por el CLI se guardan en formato **JSON  
Lines** (`.jsonl`), donde cada línea es un objeto JSON independiente. 

## Limitaciones conocidas y advertencias

-   **Limitaciones de la librería:** bdns-fetch **no implementa** ciertos endpoints que no devuelven JSON de datos. En concreto no maneja los endpoints de _exportación_ (generación de ficheros CSV/XLSX desde la BDNS) ni las rutas de configuración del portal o sistema de suscripciones.

-   **Retención de datos:** La BDNS cumple el régimen legal de publicidad limitada. Los registros de subvenciones se eliminan automáticamente **4 años naturales** después del año de concesión (solo 2 años para ayudas a personas físicas)  ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=La%20informaci%C3%B3n%20sobre%20concesiones%20permanecer%C3%A1,que%20%C3%A9sta%20se%C3%B1ale%20plazos%20superiores)).  Por tanto, no encontrará en la BDNS concesiones muy antiguas.

-   **Uso de datos públicos:** Si bien los datos provienen de fuentes oficiales, es responsabilidad del usuario verificar su idoneidad para cada caso. Esta herramienta no proporciona garantía sobre la precisión de los datos, que pueden depender de la administración que reporta. Además, algunos datos personales están protegidos: la BDNS "publica respetando el honor y la intimidad personal o familiar" ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=en%20el%20Real%20Decreto%20130%2F2019,de%20la%20Administraci%C3%B3n%20del%20Estado)).  Se recomienda uso responsable de la información y cumplimiento de la normativa de protección de datos correspondiente.

-   **Advertencia legal:** bdns-fetch se ofrece bajo la premisa de reutilización de datos abiertos. La **Ley 38/2003** y el **RD 130/2019** establecen las condiciones de publicación de subvenciones ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones#:~:text=la%20intimidad%20personal%20o%20familiar,de%20la%20Administraci%C3%B3n%20del%20Estado),  [BOE](https://www.boe.es/buscar/act.php?id=BOE-A-2019-4671#:~:text=Real%20Decreto%20130%2F2019%2C%20de%208,subvenciones%20y%20dem%C3%A1s%20ayudas%20p%C3%BAblicas)). El uso de esta herramienta para fines distintos a la investigación y transparencia ciudadana debe ceñirse a la legislación vigente. El autor no asume responsabilidad por interpretaciones erróneas o usos indebidos de los datos públicos obtenidos.

## Licencia y enlaces relevantes

-   **Licencia:** bdns-fetch está licenciado bajo la **GNU General Public License v3.0** (GPLv3) ([PyPI](https://pypi.org/project/bdns-fetch/#:~:text=,4.0%2C%20%3E%3D3.11), [GitHub](https://github.com/cruzlorite/bdns-fetch#:~:text=License)). Consulte el archivo [LICENSE](https://chatgpt.com/c/LICENSE) para más detalles.

-   **Portal oficial BDNS:** Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas -- [Ministerio de Hacienda (portal SNPSAP)](https://www.infosubvenciones.es/).

-   **Ley 38/2003 (General de Subvenciones):** texto oficial en BOE ([enlace](https://www.boe.es/eli/es/l/2003/11/17/38)).

-   **Real Decreto 130/2019:** regula la BDNS y publicidad de subvenciones, BOE ([enlace](https://www.boe.es/eli/es/rd/2019/03/08/130)).

-   **Información adicional:** Portal de transparencia del Estado sobre subvenciones -- [transparencia.gob.es](https://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/Contratos/Subvenciones.html).

-   **GPLv3:** texto de la licencia en [gnu.org](https://www.gnu.org/licenses/gpl-3.0.html).

**bdns-fetch** es software libre, desarrollado para facilitar la reutilización de datos públicos y promover la transparencia. ¡Su colaboración y contribuciones son bienvenidas!
