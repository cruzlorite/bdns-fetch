# Línea de comandos

```console
$ bdns-fetch [OPCIONES GLOBALES] COMANDO [OPCIONES DEL COMANDO]
```

Los registros se escriben en formato [JSON Lines](https://jsonlines.org/), uno por línea, y los documentos tal cual llegan. Si la API devuelve un error, se muestra el mensaje y el comando termina con código 1; si el comando está mal escrito, termina con código 2.

## Opciones globales

Se ponen **antes** del comando.

| Opción | Por defecto | Para qué sirve |
|---|---|---|
| `--output-file`, `-o` | `-` (pantalla) | Fichero donde se escribe el resultado |
| `--max-retries` | `3` | Reintentos ante fallos pasajeros; con 0 no se reintenta |
| `--wait-time` | `2` | Primera espera entre reintentos, en segundos; se duplica en cada uno hasta un máximo de 60 |
| `--max-workers` | `1` | Llamadas en paralelo al paginar (de 1 a 20). Las buenas prácticas oficiales piden no hacer llamadas en paralelo |
| `--rate-limit` | `9.5` | Peticiones por segundo (como mucho 10). Bájalo si varios procesos comparten la misma IP |
| `--progress` / `--no-progress` | automático | Barra de progreso; por defecto solo aparece si la salida de errores es una terminal |
| `--verbose`, `-v` | no | Muestra cada petición HTTP y los detalles de los errores |
| `--version` | | Muestra la versión |

## Comandos de los endpoints

Hay un comando por cada método `fetch_*` del cliente. Se llama como el método sin el `fetch_` y con guiones; también se acepta con guiones bajos (`concesiones_busqueda`), que es como lo llama `bdns-sync`.

Las opciones de cada comando son los parámetros de la API, escritos igual (`--fechaDesde`, `--nifCif`). Las fechas se escriben como `AAAA-MM-DD` o `DD/MM/AAAA`. Con `bdns-fetch COMANDO --help` ves las de cada uno.

| Comando | Tipo |
|---|---|
| `actividades`, `beneficiarios`, `finalidades`, `instrumentos`, `objetivos`, `regiones`, `reglamentos`, `sectores` | catálogo |
| `organos`, `organos-agrupacion`, `organos-codigo`, `organos-codigoadmin` | catálogo |
| `convocatorias`, `convocatorias-ultimas` | consulta |
| `convocatorias-busqueda` | búsqueda paginada |
| `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda` | búsqueda paginada |
| `grandesbeneficiarios-anios` | catálogo |
| `grandesbeneficiarios-busqueda`, `sanciones-busqueda` | búsqueda paginada |
| `planesestrategicos`, `planesestrategicos-vigencia` | consulta |
| `planesestrategicos-busqueda` | búsqueda paginada |
| `terceros` | consulta |
| `convocatorias-pdf`, `convocatorias-documentos`, `planesestrategicos-documentos` | documento |

En las búsquedas paginadas, `--num-pages` (por defecto **1**; con 0 se descargan todas), `--from-page` y `--pageSize` (como mucho 10000) controlan la paginación. Si quedan páginas sin descargar, se avisa por la salida de errores.

!!! warning "`--fechaRegFin` no incluye el último día"
    Las opciones son los parámetros de la API sin ninguna traducción. Si quieres incluir el día 31 con `--fechaRegFin`, tienes que poner el día 1 del mes siguiente. Más detalles en [comportamiento de la API](../explanation/api-behavior.md#upper-bound).

## Herramientas

### `get`

```console
$ bdns-fetch get RUTA [-p CLAVE=VALOR]... [--binary]
```

Pide cualquier ruta de la API con los mismos reintentos y el mismo límite de peticiones. Escribe el documento JSON en una sola línea o, con `--binary`, el contenido tal cual. Lo explica la guía de [endpoints sin método propio](../guides/other-endpoints.md).

### `check-api`

```console
$ bdns-fetch check-api [--day AAAA-MM-DD]
```

Comprueba contra el servicio real que los filtros de fecha se siguen comportando como está documentado. Solo termina con código 1 si la API devuelve datos válidos que lo contradicen; si el día de prueba no tiene datos o hay un error pasajero, lo indica y termina con 0. Lo explica la guía de [descargas incrementales](../guides/incremental.md#comprueba-que-la-api-no-ha-cambiado).
