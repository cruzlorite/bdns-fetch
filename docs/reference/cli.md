# CLI

```console
$ bdns-fetch [OPCIONES GLOBALES] COMANDO [OPCIONES DEL COMANDO]
```

Los registros se escriben en [JSON Lines](https://jsonlines.org/), uno por línea; los documentos, tal cual. Ante un error de la API el CLI muestra el mensaje y sale con código 1; un uso incorrecto sale con 2.

## Opciones globales

Van **antes** del comando.

| Opción | Por defecto | Descripción |
|---|---|---|
| `--output-file`, `-o` | `-` (stdout) | Fichero de salida |
| `--max-retries` | `3` | Reintentos para fallos transitorios; 0 los desactiva |
| `--wait-time` | `2` | Espera inicial entre reintentos (s); se duplica, hasta 60 |
| `--max-workers` | `5` | Hilos descargando páginas (1-20) |
| `--rate-limit` | `9.5` | Peticiones por segundo (máximo 10). Bájalo si varios procesos comparten IP |
| `--progress` / `--no-progress` | automático | Barra de progreso; por defecto solo si stderr es una terminal |
| `--verbose`, `-v` | no | Log de cada petición HTTP y detalles de los errores |
| `--version` | | Muestra la versión |

## Comandos de endpoint

Uno por método `fetch_*` del cliente, con el nombre del método sin `fetch_` y con guiones. La forma con guiones bajos (`concesiones_busqueda`), la que usa `bdns-sync`, también vale.

Las opciones de cada comando son los parámetros de la API, con su misma grafía (`--fechaDesde`, `--nifCif`). Las fechas se escriben `AAAA-MM-DD` o `DD/MM/AAAA`. `bdns-fetch COMANDO --help` lista las de cada uno.

| Comando | Paginado |
|---|---|
| `actividades`, `beneficiarios`, `finalidades`, `instrumentos`, `objetivos`, `regiones`, `reglamentos`, `sectores` | |
| `organos`, `organos-agrupacion`, `organos-codigo`, `organos-codigoadmin` | |
| `convocatorias`, `convocatorias-ultimas` | |
| `convocatorias-busqueda` | sí |
| `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda` | sí |
| `grandesbeneficiarios-anios` | |
| `grandesbeneficiarios-busqueda`, `sanciones-busqueda` | sí |
| `planesestrategicos`, `planesestrategicos-vigencia` | |
| `planesestrategicos-busqueda` | sí |
| `terceros` | |
| `convocatorias-pdf`, `convocatorias-documentos`, `planesestrategicos-documentos` | documento |

En los paginados, `--num-pages` (por defecto **1**; 0 = todas), `--from-page` y `--pageSize` (máximo 10000) controlan la paginación. Si quedan páginas sin descargar, se avisa por stderr.

!!! warning "`--fechaRegFin` es exclusivo"
    Las opciones son los parámetros de la API sin traducir. Para incluir el día 31 en `--fechaRegFin`, pasa el 1 del mes siguiente. Ver [comportamiento de la API](../explanation/api-behavior.md#upper-bound).

## Herramientas

### `get`

```console
$ bdns-fetch get RUTA [-p CLAVE=VALOR]... [--binary]
```

Pide cualquier ruta de la API, con los mismos reintentos y límite. Escribe el documento JSON en una línea, o el cuerpo tal cual con `--binary`. Ver [endpoints sin método propio](../guides/other-endpoints.md).

### `check-api`

```console
$ bdns-fetch check-api [--day AAAA-MM-DD]
```

Comprueba contra el servicio real que la semántica de los filtros de fecha sigue siendo la documentada. Sale con 1 solo si la API devolvió datos válidos que la contradicen; un día vacío o un error pasajero se informan y salen con 0. Ver [descargas incrementales](../guides/incremental.md#comprueba-que-la-api-no-ha-cambiado).
