# Tipos de entidad

Las entidades se dividen en dos grupos según cuántos datos tienen: las que se descargan enteras en cada ejecución y las que se descargan por fecha de registro.

## Entidades completas

Son catálogos pequeños, así que sale barato descargarlos enteros cada vez. Como cada descarga trae todo lo que existe en ese momento, lo que deje de aparecer se puede dar por retirado.

| Cómo se descargan | Por qué | Entidades |
|---|---|---|
| Con una sola llamada | No necesitan parámetros | `sectores`, `actividades`, `finalidades`, `beneficiarios`, `instrumentos`, `objetivos`, `regiones`, `sanciones_busqueda` |
| Recorriendo un parámetro | La API no devuelve todo junto si se omite el parámetro, así que hay que pedir cada valor por separado y juntar los resultados en una sola tabla | `organos` y `organos_agrupacion` (recorren `idAdmon`), `reglamentos` (recorre `ambito`) |
| Primero el listado y después el detalle | El listado no trae todos los campos | `planesestrategicos_busqueda`, `planesestrategicos` y `planesestrategicos_vigencia`; `grandesbeneficiarios_anios` y `grandesbeneficiarios_busqueda` |

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

El paso caro es el del detalle, porque hace una llamada por cada código y no se puede paginar. Por defecto las llamadas se hacen de una en una, como piden las buenas prácticas oficiales; con `--max-workers` puedes hacer varias a la vez y bajar mucho el tiempo, y en [rendimiento](sync-behavior.md#performance) tienes las cifras. Los detalles de `planesestrategicos` y `planesestrategicos_vigencia` funcionan igual ([`bdns.sync.pipeline`](../reference/api/pipeline.md)).

La fecha de registro de un registro no cambia aunque se edite después, así que volver a consultar el mismo periodo no trae altas nuevas, pero sí permite detectar las modificaciones gracias al hash. Las correcciones suelen llegar poco después del registro y cada vez son menos con el tiempo, y por eso se repasan periodos de distinta longitud. Todos terminan ayer ([`window_bounds`][bdns.sync.windows.window_bounds]), de modo que un mismo día el anual incluye al mensual, el mensual al semanal y el semanal al diario. Qué periodo lanza cada día `bdns-sync delta` ([`cadence_window`][bdns.sync.windows.cadence_window]), y por qué basta con uno, lo explicamos en [sincronización diaria](../guides/scheduling.md).
