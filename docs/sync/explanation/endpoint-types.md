# Tipos de endpoint

Hay dos familias, según el volumen de datos.

## Reemplazo completo (`bdns-sync sync <entidad>`)

Catálogos pequeños, donde traer el conjunto entero en cada ejecución sale barato.

| Forma | Motivo | Entidades |
|---|---|---|
| Simple | Una sola llamada, sin parámetros | `sectores`, `actividades`, `finalidades`, `beneficiarios`, `instrumentos`, `objetivos`, `regiones` |
| Barrido | La API no devuelve la unión si se omite el parámetro: hay que consultar valor por valor y juntar los resultados en una tabla | `organos`/`organos_agrupacion` (barren `idAdmon`), `reglamentos` (barre `ambito`), `sanciones_busqueda` |
| Descubrimiento y detalle | El listado no trae todos los campos | `planesestrategicos_busqueda`/`planesestrategicos`/`planesestrategicos_vigencia`, `grandesbeneficiarios_anios`/`grandesbeneficiarios_busqueda` |

## Incremental por fecha de registro (`bdns-sync sync <entidad> --window {daily,weekly,monthly,annual}`)

Endpoints con decenas de millones de filas, donde el reemplazo completo no es viable.

| Entidad | Clave natural |
|---|---|
| `concesiones_busqueda` | `id` |
| `ayudasestado_busqueda` | `idConcesion` |
| `minimis_busqueda` | `idConcesion` |
| `partidospoliticos_busqueda` | `id` |
| `convocatorias_busqueda` | `numeroConvocatoria` |
| `convocatorias` | `codigoBDNS` |

`convocatorias` va en dos pasos: el descubrimiento consulta el listado de `convocatorias_busqueda` por rango de fechas para sacar los códigos registrados en la ventana, y de cada código se pide después el registro completo al endpoint de detalle (`convocatorias`, por `numConv`). Lo que se versiona en la tabla `convocatorias` es el registro de detalle; el listado de descubrimiento se sincroniza además por su cuenta, en la tabla `convocatorias_busqueda`, con la misma maquinaria incremental que el resto de entidades de esta sección.

`convocatorias_busqueda` **no sustituye** a `convocatorias`: el listado trae solo 10 de los ~30 campos del detalle (se queda fuera el presupuesto, las fechas de solicitud, los documentos, los instrumentos...), y que su hash no cambie no dice nada sobre si cambió algún campo que solo existe en el detalle. Nunca hay que usar el listado para decidir si se puede ahorrar la llamada de detalle de un código.

El paso de detalle de `convocatorias` es el caro: una llamada real por cada código descubierto, sin paginación posible. Va paralelizado espaciando los arranques de petición (8 hilos, ~9,5 peticiones por segundo, justo por debajo del límite oficial de 10/s), lo que baja un mes real de horas a minutos sin un solo `429`; las cifras están en la [rendimiento medido](bdns-api-behavior.md#performance). Los pasos de detalle de `planesestrategicos` y `planesestrategicos_vigencia` usan esa misma maquinaria ([`bdns.sync.pipeline`](../reference/api/pipeline.md)).

La fecha de registro no cambia cuando el registro se edita más tarde, así que volver a consultar la misma ventana no descubre altas nuevas, pero sí detecta ediciones a través del hash. Las correcciones se concentran cerca de la fecha de registro y se van espaciando con el tiempo; de ahí la cascada de ventanas: cada nivel llega hasta ayer (`window_bounds`), así que el mismo día `annual` contiene a `monthly`, `monthly` a `weekly` y `weekly` a `daily`. Qué ventana se lanza cada día, y por qué nunca varias apiladas, está en [operación programada](../guides/scheduling.md).
