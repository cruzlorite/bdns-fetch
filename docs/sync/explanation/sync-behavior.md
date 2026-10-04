# Cómo sincroniza

En esta página se explica qué decide `bdns-sync` a partir de cómo se comporta la API. Lo que se sabe de la propia API (cómo tratan las fechas los parámetros, por qué fallan los rangos largos, cuánto histórico guarda cada endpoint o qué datos cambian de forma sin cambiar de verdad), junto con las pruebas, está en la documentación de `bdns-fetch`: [comportamiento de la API](../../fetch/explanation/api-behavior.md). Aquí lo enlazamos en lugar de repetirlo.

<a id="inclusive-range"></a>
## Los periodos incluyen los dos extremos y terminan ayer

En `bdns-sync`, un periodo de fechas incluye siempre el primer día y el último: el periodo `daily` del día `X` son los registros del día `X`. Como mucho termina ayer, porque el día en curso sigue recibiendo registros hasta la mañana siguiente y, si se incluyera, quedaría un día a medias que nadie volvería a revisar ([`windows`][bdns.sync.windows]).

<a id="upper-bound"></a>
## Las fechas las traduce bdns-fetch

La API trata el último día de dos formas opuestas: `fechaRegFin` no lo incluye y `fechaHasta` sí ([las pruebas](../../fetch/explanation/api-behavior.md#upper-bound)). `bdns-sync` no monta esos parámetros a mano, sino que pasa el periodo de cada entidad por [`registration_range`](../../fetch/reference/api/dates.md) o por [`period_range`](../../fetch/reference/api/dates.md), según la familia de fechas que use. Así la regla está en un solo sitio, que es el que corresponde a la API.

<a id="window-chunking"></a>
## Las consultas se dividen en semanas

Antes de pedir un periodo a la API, se divide en tramos de siete días como máximo con [`split_range`](../../fetch/reference/api/dates.md), porque los rangos largos fallan de vez en cuando y los semanales no ([las pruebas](../../fetch/explanation/api-behavior.md#range-reliability)). Esto es lo que permite descargar años de datos. Los periodos `daily` y `weekly` caben en un solo tramo; el `monthly`, el `annual` y las cargas históricas se dividen.

Los tramos solo afectan a cómo se descarga. El periodo que recibe el sink, y con el que se acotan las bajas, es el periodo completo que se pidió.

<a id="boundary-check"></a>
## Cada día se comprueba primero la API

Todo lo anterior se apoya en un comportamiento que se ha medido, pero que la API no documenta. Por eso `bdns-sync delta` empieza ejecutando la comprobación de `bdns-fetch` ([`check-api`](../../fetch/reference/cli.md#check-api)): si la API devuelve datos válidos que contradicen ese comportamiento, ese día no se sincroniza nada, porque seguir adelante supondría perder o duplicar registros sin que nadie se diera cuenta. Si el día de prueba no tiene datos o hay un error pasajero, no se bloquea nada.

Además, los tests comprueban lo mismo (que dos días seguidos no comparten registros y que juntos dan el total) con un cliente simulado, para que un error en `bdns-sync` no pase desapercibido.

<a id="windowed-deletions"></a>
## Las bajas se detectan dentro del periodo

Las entidades incrementales que traen su propia fecha de registro (`concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `convocatorias_busqueda` y `convocatorias`, con `fechaAlta`, `fechaRegistro` o `fechaRecepcion` según la entidad) detectan las bajas comparando, dentro de la misma ejecución, lo que devuelve la API con las filas guardadas cuya fecha de registro cae en ese mismo periodo. Si una fila vigente de ese periodo no ha vuelto a llegar, se cierra con el motivo `removed`.

Nunca se compara con la ejecución anterior, porque daría falsos positivos todo el tiempo: tarde o temprano todas las filas se quedan fuera de un periodo que avanza cada día, sin que eso signifique que se hayan dado de baja.

`partidospoliticos_busqueda` se queda fuera, porque su respuesta no trae ningún campo con la fecha de registro ([las pruebas](../../fetch/explanation/api-behavior.md#api-issues)) y no hay forma de acotar la comparación. Seguirá así mientras la API no cambie.

<a id="history-depth"></a>
## Hasta dónde llega el histórico

Cada entidad incremental indica en el [registro de entidades][bdns.sync.entities] desde qué fecha merece la pena cargarla (`history_start`), y `bdns-sync backfill` la carga año a año desde ahí:

| Entidad | Desde | Por qué |
|---|---|---|
| `concesiones_busqueda`, `partidospoliticos_busqueda` | 2020 | se publican durante unos cuatro años |
| `ayudasestado_busqueda`, `minimis_busqueda` | 2015 | se publican durante unos diez años |
| `convocatorias_busqueda`, `convocatorias` | 2013 | el portal empezó a funcionar entonces |

Son fechas prudentes, no la del primer registro: pedir fechas anteriores al periodo de visualización ([las pruebas](../../fetch/explanation/api-behavior.md#history-depth)) solo devuelve semanas vacías, y cada una cuesta una sola llamada.

<a id="performance"></a>
## Rendimiento

- **Una llamada cada vez.** `bdns-fetch` espacia las peticiones a 9,5 por segundo y no deja pasar ráfagas, porque la API las rechaza ([las pruebas](../../fetch/explanation/api-behavior.md#rate-limit)), y por defecto hace una sola llamada cada vez, como piden las buenas prácticas oficiales. Lo que más se nota es la paginación: sincronizar una semana de concesiones (236.113 filas) con SQLite como destino tardó 63 segundos con una llamada cada vez y 27 con `--max-workers 5`. Los detalles de `convocatorias` y `planesestrategicos` apenas cambian mientras el servidor responde rápido, porque ya los limita el máximo de peticiones por segundo; si el servidor va cargado, sí se nota: un mes de `convocatorias` (6.186 códigos) llegó a tardar 3 horas y 12 minutos llamada a llamada y 10 minutos y 54 segundos con 8 a la vez ([cuánto se gana con varias llamadas](../../fetch/explanation/api-behavior.md#concurrency)). Dentro de la recomendación no hay más margen en nuestro lado, porque cada página tarda lo que tarda el servidor en prepararla y enviarla.
- **Descarga y escritura a la vez.** Mientras se escribe un lote en el staging se va descargando el siguiente ([`pipeline`][bdns.sync.pipeline]), lo que es un 40% más rápido en los endpoints donde pesa más la descarga. La descarga va en un hilo aparte y la escritura en el hilo dueño de la conexión, porque los objetos de SQLite no se pueden usar desde otro hilo; una cola de tamaño limitado hace que la descarga espere si la escritura va más lenta.
- **BigQuery.** El staging se carga con *load jobs* en lotes de 50.000 filas en lugar de con `INSERT`, porque son más rápidos, no gastan cuota de DML y dejan margen frente al límite de operaciones de actualización por tabla ([`dialects`][bdns.sync.sinks.sql.dialects]).
- **Reintentos.** Por defecto son 5 reintentos, empezando por 10 segundos de espera (10, 20, 40, 60 y 60), de modo que cada petición aguanta unos tres o cuatro minutos de problemas antes de que falle la ejecución. Se ajustan con `--max-retries` y `--wait-time`.

<a id="api-issues"></a>
## Qué hace con cada problema conocido de la API

| Problema ([detalle](../../fetch/explanation/api-behavior.md#api-issues)) | Qué hace `bdns-sync` |
|---|---|
| Registros sueltos que llegan como una página de error en HTML | Los descarta con un aviso, los cuenta en `rows_skipped` y guarda su contenido en `_sync_errors`. Si se descartan demasiados, la ejecución falla ([decisión 0005](../../adr/0005-per-run-reject-tolerance.md)) |
| `ERR_MANTENIMIENTO_BBDD` en rangos largos | Divide las consultas en semanas, y el cliente lo reintenta como fallo pasajero |
| Las fechas no se comportan igual en todos los endpoints | Las traduce `bdns-fetch`, y `check-api` lo comprueba cada día |
| `partidospoliticos_busqueda` no trae fecha de registro | Esa entidad no detecta bajas |
| Listas anidadas que cambian de orden | El hash ordena las claves y los elementos de forma recursiva |
| Paginación inestable en fechas recientes | Elimina las copias idénticas al insertar; una carga histórica muy grande hecha de una vez puede dejar alguna pareja ([cómo encontrarlas](data-caveats.md)) |
| Nombres que cambian de grafía y listas desordenadas dentro de un texto | Reglas de hash para cada entidad, explicadas a continuación |

<a id="spurious-changes"></a>
## Cambios espurios: qué cuenta como cambio

A veces la API devuelve el mismo dato escrito de otra manera ([los tres casos](../../fetch/explanation/api-behavior.md#spurious-changes)), y en un histórico SCD2 cada uno de esos casos es una versión que no aporta nada. En la pasada anual del 1 de septiembre de 2026, comparando cada versión nueva con la que cerraba:

| Entidad | Versiones | Espurias | Campo responsable |
|---|---|---|---|
| `concesiones_busqueda` | 368.818 | **213.176 (58%)** | `beneficiario` |
| `minimis_busqueda` | 35.995 | **30.033 (83%)** | `sectorActividad` |
| `ayudasestado_busqueda` | 6.758 | **5.046 (75%)** | `sectores` |
| `grandesbeneficiarios_busqueda` | unas 65.000 al día | **casi el 100%** | `beneficiario` |
| `convocatorias` | 2.366 | 0 | — |
| `convocatorias_busqueda` | 437 | 13 (3%) | — |
| `partidospoliticos_busqueda` | 21 | 1 | — |

De las 414.395 versiones de aquella pasada, unas 248.000 eran ruido, es decir, el 60%.

<a id="hash-exclusion-criterion"></a>
### Cuándo se saca un campo del hash

Un campo solo sale del hash **si su valor va y vuelve**, es decir, si recupera valores que ya había tenido. Así se distingue un campo que la API reescribe sin motivo de otro que recibe correcciones de verdad, y no se excluye nada solo por parecerse a otro caso.

La prueba es esta: para cada clave natural con tres o más versiones se toma la secuencia de valores del campo, se quitan las repeticiones seguidas y se mira si algún valor reaparece después de otro distinto.

| Entidad | Campo | Claves que cambian | Vuelven a un valor anterior | Resultado |
|---|---|---|---|---|
| `concesiones_busqueda` | `beneficiario` | 177 | **119 (67%)** | cambia sin motivo, sale del hash |
| `grandesbeneficiarios_busqueda` | `beneficiario` | — | comprobado con hashes que se repiten | cambia sin motivo, sale del hash |
| `ayudasestado_busqueda` | `beneficiario` | 2 | 0 | muestra insuficiente, se mantiene |
| `minimis_busqueda` | `beneficiario` | 0 | — | muestra insuficiente, se mantiene |
| `concesiones_busqueda` | `convocatoria` | 1 | 0 | muestra insuficiente, se mantiene |

Cuando la muestra es insuficiente, el campo **se mantiene en el hash**: el volumen es pequeño y, ante la duda, preferimos registrar el cambio. Conviene repetir la medición cuando el histórico sea más largo.

### Qué reglas se aplican

Hay cuatro, definidas en el [registro de entidades][bdns.sync.entities] junto a la clave natural de cada entidad:

| Entidad | Regla | Por qué |
|---|---|---|
| `concesiones_busqueda` | `hash_exclude=("beneficiario",)` | el valor va y vuelve en el 67% de los casos |
| `grandesbeneficiarios_busqueda` | `hash_exclude=("beneficiario",)` | el valor va y vuelve, comprobado con hashes que se repiten |
| `ayudasestado_busqueda` | `delimited_lists={"sectores": "#"}` | el 84% de sus cambios eran solo de orden |
| `minimis_busqueda` | `delimited_lists={"sectorActividad": ...}` | el 92% de sus cambios eran solo de orden |

Los dos casos se tratan de forma distinta a propósito. Una lista desordenada se puede ordenar sin perder información, así que se ordena antes de calcular el hash y el campo sigue detectando los cambios reales. En cambio, un nombre que cambia de grafía sin motivo no se puede normalizar sin decidir cuál de las grafías es la buena, así que el campo sale del hash entero. En los dos casos **solo cambia lo que ve el hash**: el registro se guarda exactamente como lo devolvió la API ([por qué no entraña riesgo](payload-policy.md)).

<a id="shuffled-lists"></a>
### Cómo se separa una lista desordenada

En `minimis_busqueda` los elementos van separados por `;`, pero algunas descripciones de la CNAE llevan su propio `;`, así que cortar en cada `;` partiría por la mitad 374 de 15.931 elementos. La regla corta **justo antes de donde empieza cada elemento** (un código seguido de un guion), lo que deja esas descripciones enteras: con los mismos datos, ningún elemento queda mal separado. En `ayudasestado_busqueda` el `#` no da problemas.

Si algún día el patrón dejara de reconocer los códigos, el fallo sería inofensivo: el valor no se separaría ni se ordenaría, y los cambios de orden volverían a crear versiones. Nunca podría mezclar dos listas distintas, porque ordenar no quita ni añade elementos.

<a id="intermittent-fields"></a>
### Campos que desaparecen y vuelven

El tercer caso, campos que llegan vacíos y luego vuelven a tener valor ([las pruebas](../../fetch/explanation/api-behavior.md#intermittent-fields)), **no se puede resolver con reglas de hash**. Un `null` no se puede normalizar: o cuenta como cambio, o se saca el campo del hash y se pierde la posibilidad de saber cuándo se fija de verdad un plazo, que es información útil. Por eso esas versiones se dan por buenas; son unas 650 de las 4.320 versiones cerradas de `convocatorias`. Qué tener en cuenta al consultar los datos lo explicamos en [antes de consultar los datos](data-caveats.md).
