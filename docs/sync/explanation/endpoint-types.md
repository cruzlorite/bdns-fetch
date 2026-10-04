# Tipos de entidad

Las entidades se dividen en dos grupos según cuántos datos tienen: las que se descargan enteras en cada ejecución y las que se descargan por fecha de registro.

## Entidades completas

Son catálogos pequeños, así que sale barato descargarlos enteros cada vez. Como cada descarga trae todo lo que existe en ese momento, lo que deje de aparecer se puede dar por retirado.

Hay tres formas de descargarlas:

- **Con una sola llamada**, porque no necesitan parámetros: `sectores`, `actividades`, `finalidades`, `beneficiarios`, `instrumentos`, `objetivos`, `regiones` y `sanciones_busqueda`.
- **Recorriendo un parámetro**, porque si se omite la API no lo devuelve todo junto: `organos` y `organos_agrupacion` recorren `idAdmon`, y `reglamentos` recorre `ambito`. Cada valor se pide por separado y los resultados se juntan en una sola tabla.
- **Primero el listado y después el detalle**, porque el listado no trae todos los campos: `planesestrategicos_busqueda`, `planesestrategicos` y `planesestrategicos_vigencia`, y también `grandesbeneficiarios_anios` y `grandesbeneficiarios_busqueda`.

## Entidades incrementales

Son las que tienen decenas de millones de filas, donde descargarlo todo cada vez no es viable. Se piden por fecha de registro, con el periodo que toque ese día (`--window daily`, `weekly`, `monthly` o `annual`) o con un rango concreto (`--since` y `--until`).

| Entidad | Clave natural |
|---|---|
| `concesiones_busqueda` | `id` |
| `ayudasestado_busqueda` | `idConcesion` |
| `minimis_busqueda` | `idConcesion` |
| `partidospoliticos_busqueda` | `id` |
| `convocatorias_busqueda` | `numeroConvocatoria` |
| `convocatorias` | `codigoBDNS` |

`convocatorias` se descarga en dos pasos. Primero se consulta el listado de `convocatorias_busqueda` para sacar los códigos registrados en ese periodo, y después se pide el detalle de cada código al endpoint `convocatorias` (por `numConv`). Lo que se guarda en la tabla `convocatorias` es ese detalle; el listado se guarda aparte, en la tabla `convocatorias_busqueda`, igual que el resto de entidades incrementales.

Ojo, porque `convocatorias_busqueda` **no sustituye** a `convocatorias`: el listado solo trae 10 de los cerca de 30 campos del detalle (no incluye el presupuesto, las fechas de solicitud, los documentos ni los instrumentos, por ejemplo), y que su hash no cambie no garantiza que no haya cambiado ningún campo del detalle. Por eso nunca se usa el listado para decidir si hace falta pedir el detalle de un código.

El paso caro es el del detalle, porque hace una llamada por cada código y no se puede paginar. Por defecto las llamadas se hacen de una en una, como piden las buenas prácticas oficiales. Mientras el servidor responde rápido no importa, porque el ritmo lo marca el máximo de peticiones por segundo; si va cargado, `--max-workers` permite hacer varias a la vez y bajar mucho el tiempo (las cifras están en [rendimiento](sync-behavior.md#performance)). Los detalles de `planesestrategicos` y `planesestrategicos_vigencia` funcionan igual ([`bdns.sync.pipeline`](../reference/api/pipeline.md)).

La fecha de registro de un registro no cambia aunque se edite después, así que volver a consultar el mismo periodo no trae altas nuevas, pero sí permite detectar las modificaciones gracias al hash. Las correcciones suelen llegar poco después del registro y cada vez son menos con el tiempo, y por eso se repasan periodos de distinta longitud. Todos terminan ayer ([`window_bounds`][bdns.sync.windows.window_bounds]), de modo que un mismo día el anual incluye al mensual, el mensual al semanal y el semanal al diario. Qué periodo lanza cada día `bdns-sync delta` ([`cadence_window`][bdns.sync.windows.cadence_window]), y por qué basta con uno, lo explicamos en [sincronización diaria](../guides/scheduling.md).
