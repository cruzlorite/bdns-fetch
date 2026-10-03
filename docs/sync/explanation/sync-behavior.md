# Cómo sincroniza: ventanas, bajas y cambios

Qué decide `bdns-sync` a partir de cómo se comporta la API. Los hechos sobre la API en sí (la semántica de las fechas, los fallos en rangos largos, la retención, los cambios espurios), con sus mediciones, tienen su sitio en la documentación de `bdns-fetch`: [comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/). Aquí se enlazan, no se repiten.

<a id="inclusive-range"></a>
## Rangos inclusivos que terminan ayer

En `bdns-sync`, un rango de fechas es **cerrado por los dos extremos**: la ventana `daily` sobre el día `X` significa "los registros del día `X`". El extremo superior es siempre *ayer* como muy tarde, porque el día en curso sigue recibiendo registros hasta la mañana siguiente, y una ejecución que lo incluyera dejaría un día a medias que nada vuelve a mirar ([`windows`][bdns.sync.windows]).

<a id="upper-bound"></a>
## Las fechas se traducen en bdns-fetch, nunca a mano

La API usa dos semánticas opuestas para el extremo superior: `fechaRegFin` es exclusivo y `fechaHasta` inclusivo ([medición](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#upper-bound)). `bdns-sync` no construye esos parámetros: cada entidad pasa su rango inclusivo por [`registration_range`](https://cruzlorite.github.io/bdns-fetch/reference/api/dates/) o [`period_range`](https://cruzlorite.github.io/bdns-fetch/reference/api/dates/), según su familia. La regla vive en un solo sitio, y es el de la API.

<a id="window-chunking"></a>
## Tramos de 7 días

Todo rango se parte en tramos de 7 días como máximo antes de consultarse, con [`split_range`](https://cruzlorite.github.io/bdns-fetch/reference/api/dates/): los rangos largos fallan de forma intermitente y los de una semana no ([medición](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#range-reliability)). Las ventanas `daily` y `weekly` caben en un tramo; `monthly`, `annual` y los backfills se parten.

El tramo afecta solo a cómo se descarga. El rango que se entrega al sink, y con el que se acotan las bajas, es el rango entero pedido.

<a id="boundary-check"></a>
## Antes de cada día, se comprueba la API

Todo lo anterior descansa en una semántica medida, no documentada. `bdns-sync delta` empieza ejecutando la comprobación de contrato de `bdns-fetch` ([`check-api`](https://cruzlorite.github.io/bdns-fetch/reference/cli/#check-api)): si la API devuelve datos válidos que contradicen la semántica, no se sincroniza nada ese día, porque sincronizar a través de una frontera cambiada pierde o duplica registros sin avisar. Un día de prueba vacío o un error pasajero no bloquean nada.

Los tests fijan además el mismo invariante (días consecutivos disjuntos y aditivos) contra el cliente simulado, para que una regresión en `bdns-sync` no pase desapercibida.

<a id="windowed-deletions"></a>
## Detección de bajas acotada por ventana

Las entidades por ventana que traen su propia fecha de registro (`concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `convocatorias_busqueda` y `convocatorias`, con `fechaAlta`, `fechaRegistro` o `fechaRecepcion` según la entidad) detectan bajas reales comparando, dentro de la misma ejecución, lo que devuelve la API con las filas de la tabla cuya fecha de registro cae en ese mismo rango. Una fila vigente de ese rango que no ha vuelto se cierra con motivo `removed`.

La comparación nunca se hace contra la ejecución anterior: daría falsos positivos constantes, porque toda fila acaba quedándose fuera de una ventana móvil sin que eso signifique que se ha dado de baja.

`partidospoliticos_busqueda` se queda fuera: su payload no trae ningún campo de fecha de registro ([medición](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#api-issues)), así que no hay con qué acotar la comparación. Es una limitación permanente mientras la API no cambie.

<a id="history-depth"></a>
## Hasta dónde llega el histórico

Cada entidad por ventana declara en el [registro de entidades][bdns.sync.entities] desde qué fecha merece la pena cargarla (`history_start`), y `bdns-sync backfill` la carga año a año desde ahí:

| Entidad | Desde | Por qué |
|---|---|---|
| `concesiones_busqueda`, `partidospoliticos_busqueda` | 2020 | retención de ~4 años |
| `ayudasestado_busqueda`, `minimis_busqueda` | 2015 | retención de ~10 años |
| `convocatorias_busqueda`, `convocatorias` | 2013 | arranque del portal |

Son suelos conservadores, no los primeros registros: consultar fechas anteriores a la retención ([medición](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#history-depth)) solo devuelve semanas vacías, una llamada barata cada una.

<a id="performance"></a>
## Rendimiento

- **Peticiones espaciadas.** `bdns-fetch` espacia las peticiones a 9,5 por segundo y sin ráfagas, porque la API rechaza las ráfagas ([medición](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#rate-limit)). El paso de detalle de `convocatorias` y `planesestrategicos` usa 8 hilos para cubrir la latencia; el espaciado lo pone el cliente. Con un mes real de `convocatorias` (6.186 códigos), en paralelo tardó 10 min 54 s; en serie, entre 23 minutos y 3 h 12 min según la carga del servidor.
- **Solape productor/consumidor.** Al cargar el staging se solapa la descarga del lote siguiente con la escritura del actual ([`pipeline`][bdns.sync.pipeline]): un 40% más rápido en los endpoints donde pesa la descarga. La descarga va en un hilo auxiliar y la escritura en el hilo dueño de la conexión, porque los objetos de SQLite tienen afinidad de hilo; la cola acotada hace de contrapresión.
- **BigQuery.** El staging se carga con *load jobs* en lotes de 50.000 filas, no con `INSERT`: son más rápidos, no consumen cuota de DML y dejan margen bajo el límite de operaciones de actualización por tabla ([`dialects`][bdns.sync.sinks.sql.dialects]).
- **Reintentos.** Por defecto, 5 reintentos con espera inicial de 10 s (10, 20, 40, 60, 60 s): una petición aguanta unos 3-4 minutos de problemas antes de que falle la ejecución. Se ajustan con `--max-retries` y `--wait-time`.

<a id="api-issues"></a>
## Qué hace con cada problema conocido de la API

| Problema ([detalle](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#api-issues)) | Qué hace `bdns-sync` |
|---|---|
| Registros sueltos que llegan como página de error HTML | Los descarta con un aviso, los cuenta en `rows_skipped` y guarda el contenido en `_sync_errors`. Si los descartes superan el umbral, la ejecución falla ([ADR 0005](../adr/0005-per-run-reject-tolerance.md)) |
| `ERR_MANTENIMIENTO_BBDD` en rangos largos | Tramos de 7 días; el cliente lo reintenta como transitorio |
| Semántica de fechas inconsistente | Traducción en `bdns-fetch`, comprobación diaria con `check-api` |
| `partidospoliticos_busqueda` sin fecha de registro | Sin detección de bajas para esa entidad |
| Arrays anidados en orden cambiante | El hash ordena claves y elementos de forma recursiva |
| Paginación inestable en fechas recientes | Deduplica copias idénticas al insertar; una carga histórica masiva puede dejar algún par residual ([cómo detectarlo](data-caveats.md)) |
| Nombres reescritos y listas barajadas | Reglas de hash por entidad; ver abajo |

<a id="spurious-changes"></a>
## Cambios espurios: qué cuenta como cambio

La API devuelve a veces el mismo dato escrito de otra forma ([las tres familias](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#spurious-changes)). Para un histórico SCD2 cada una es una versión que no aporta nada. Medido en la pasada anual del 1 de septiembre de 2026, comparando cada versión nueva con la que cerró:

| Entidad | Versiones | Espurias | Campo culpable |
|---|---|---|---|
| `concesiones_busqueda` | 368.818 | **213.176 (58%)** | `beneficiario` |
| `minimis_busqueda` | 35.995 | **30.033 (83%)** | `sectorActividad` |
| `ayudasestado_busqueda` | 6.758 | **5.046 (75%)** | `sectores` |
| `grandesbeneficiarios_busqueda` | ~65.000 al día | **~100%** | `beneficiario` |
| `convocatorias` | 2.366 | 0 | — |
| `convocatorias_busqueda` | 437 | 13 (3%) | — |
| `partidospoliticos_busqueda` | 21 | 1 | — |

De las 414.395 versiones de aquella pasada, unas 248.000 eran ruido: el 60%.

<a id="hash-exclusion-criterion"></a>
### El criterio para excluir un campo del hash

Un campo sale del hash **solo si su valor oscila**, es decir, si vuelve a valores que ya había tenido. Eso distingue un campo que la API reescribe al azar de uno que recibe correcciones reales, y evita excluir por analogía.

La prueba: para cada clave natural con tres o más versiones, se toma la secuencia de valores del campo, se quitan las repeticiones consecutivas y se mira si algún valor reaparece después de otro distinto.

| Entidad | Campo | Claves que cambian | Oscilan | Veredicto |
|---|---|---|---|---|
| `concesiones_busqueda` | `beneficiario` | 177 | **119 (67%)** | aleatorio, fuera del hash |
| `grandesbeneficiarios_busqueda` | `beneficiario` | — | ciclo de hashes probado | aleatorio, fuera del hash |
| `ayudasestado_busqueda` | `beneficiario` | 2 | 0 | muestra insuficiente, se mantiene |
| `minimis_busqueda` | `beneficiario` | 0 | — | muestra insuficiente, se mantiene |
| `concesiones_busqueda` | `convocatoria` | 1 | 0 | muestra insuficiente, se mantiene |

En las entidades con muestra insuficiente el campo **se mantiene en el hash**: el volumen es bajo y, ante la duda, se prefiere registrar el cambio. Conviene rehacer esta medición cuando el histórico tenga más recorrido.

### Qué reglas se aplican

Cuatro, declaradas en el [registro de entidades][bdns.sync.entities] junto a la clave natural de cada una:

| Entidad | Regla | Motivo |
|---|---|---|
| `concesiones_busqueda` | `hash_exclude=("beneficiario",)` | oscilación probada, 67% |
| `grandesbeneficiarios_busqueda` | `hash_exclude=("beneficiario",)` | oscilación probada por ciclo de hashes |
| `ayudasestado_busqueda` | `delimited_lists={"sectores": "#"}` | 84% de sus cambios eran reordenamiento |
| `minimis_busqueda` | `delimited_lists={"sectorActividad": ...}` | 92% de sus cambios eran reordenamiento |

Las dos familias se tratan distinto a propósito. Una lista barajada se puede canonizar sin perder información, así que se ordena antes de hashear y el campo sigue detectando cambios reales. Un nombre reescrito al azar no se puede canonizar sin decidir cuál de las grafías es la buena, así que el campo sale del hash entero. En los dos casos **solo cambia lo que ve el hash**: el payload se guarda exactamente como lo devolvió la API ([por qué es seguro](payload-policy.md)).

<a id="shuffled-lists"></a>
### Cómo se parte una lista barajada

En `minimis_busqueda` los elementos van unidos por `;`, pero varias descripciones CNAE llevan un `;` propio, así que partir por cada `;` cortaría 374 de 15.931 elementos por la mitad. La regla parte **antes del inicio de un elemento** (un código seguido de guion), lo que deja esas descripciones enteras: cero elementos malformados sobre los mismos datos. En `ayudasestado_busqueda` el `#` es inequívoco.

Un patrón que dejara de reconocer los códigos degrada en la dirección segura: el valor no se parte, no se ordena, y el reordenamiento vuelve a producir versiones. Nunca puede fundir dos listas distintas, porque ordenar conserva los elementos.

<a id="intermittent-fields"></a>
### Campos que dejan de venir y vuelven

La tercera familia, campos que llegan `null` y vuelven con valor ([medición](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#intermittent-fields)), **no se arregla con reglas de hash**. Un `null` no se puede normalizar: o cuenta como cambio, o se excluye el campo y se pierde la detección de cuándo se fija un plazo de verdad, que es información legítima. Esas versiones se aceptan como válidas; son unas 650 de las 4.320 versiones cerradas de `convocatorias`. Lo que conviene saber al consultar los datos está en [antes de consultar los datos](data-caveats.md).
