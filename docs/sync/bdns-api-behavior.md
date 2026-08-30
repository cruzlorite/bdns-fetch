# Comportamiento de la API de la BDNS: ventanas de fecha

[🇬🇧 English version](./bdns-api-behavior.en.md)

Este documento recoge cómo se comporta de verdad la API de la BDNS con los parámetros de fecha, comprobado con pruebas contra el servicio real. Se explica al detalle porque son comportamientos sutiles, no aparecen en la documentación oficial (o la contradicen) y equivocarse al manejarlos hace perder datos en silencio.

Cada afirmación indica la comprobación empírica en la que se apoya.

## 1. Convención interna: rango de días inclusivo

En `bdns-sync`, una ventana es un rango de días **cerrado por los dos extremos**: la ventana `daily` sobre el día `X` significa «los registros del día `X`». El extremo superior de cualquier ventana es *ayer* (`date.today() - 1`), porque los datos del día en curso no están cerrados hasta la mañana siguiente.

## 2. Semántica del extremo superior según el endpoint

La API tiene dos familias de parámetros de fecha, y el extremo superior se comporta justo **al revés** en cada una:

| Familia | Parámetros | Endpoints | Extremo superior | Comprobado contra el servicio real (día `D`) |
|---|---|---|---|---|
| Búsqueda por fecha de registro | `fechaRegInicio` / `fechaRegFin` | `concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `partidospoliticos_busqueda` | **Exclusivo** (no incluye el día `D`) | `fechaRegFin=D` devuelve ~0 filas del día `D`; `fechaRegFin=D+1` devuelve el día `D` entero (en `concesiones`, 1 fila frente a 58.488) |
| Descubrimiento de convocatorias | `fechaDesde` / `fechaHasta` | `convocatorias` (paso de descubrimiento) | **Inclusivo** (incluye el día `D`) | `fechaHasta=D` devuelve todas las convocatorias con `fechaRecepcion == D`; `fechaHasta=D+1` devuelve los días `D` y `D+1` |

La conversión entre la convención interna (inclusiva) y la familia exclusiva está en una sola función, `generic.to_api_upper_bound(fin_inclusivo)`, que suma un día al extremo superior. El endpoint `convocatorias` no la usa: su `fechaHasta` ya es inclusivo, y sumarle un día metería convocatorias de fuera de la ventana.

En `convocatorias`, las fechas solo intervienen en el paso de descubrimiento (`convocatorias_busqueda`): por cada código descubierto se pide después el registro completo al endpoint de detalle (por `numConv`), que no tiene parámetros de fecha y es el que se guarda.

El coste de `convocatorias` es, por tanto, lineal en el número de códigos, no en el ancho de la ventana. Medido con un mes real (mayo de 2026, 6.186 códigos): el descubrimiento tarda ~1 s y el paso de detalle se lleva todo lo demás. La latencia de cada llamada de detalle depende de la carga del servidor: ~0,22 s en horas buenas (un mes ≈ 23 minutos), pero una ejecución de ese mismo mes llegó a tardar 3 h 12 min (~1,9 s por llamada), con un único reintento por timeout. En los dos casos terminó bien (6.186 filas, 0 descartes); lo único que cambia es la duración.

El paso de detalle va paralelizado para acercarse al límite de 10 req/s, en vez de quedarse atado a la latencia de una sola conexión. El servidor rechaza las ráfagas, así que los arranques de petición van espaciados; el detalle está en la [sección 7](#7-rendimiento-medido).

Qué pasa si esto se maneja mal, medido contra el servicio real:

- Sin la conversión, la ventana `daily` de los cuatro endpoints `fechaReg` no devolvería prácticamente nada, y cualquier ventana más ancha perdería su día más reciente.
- Con el troceo (ver sección 3) el error se multiplica: se pierde un día por cada frontera de tramo. Un rango de 28 días partido en días devolvió 8 filas en lugar de ~1,2 millones.

## 3. Troceo de ventanas en tramos de 7 días

Toda ventana se parte en tramos de 7 días como máximo antes de consultarse (`generic.iter_date_chunks`). Las ventanas `daily` y `weekly` caben en un solo tramo y no se ven afectadas; `monthly` y `annual` sí se parten. Los dos motivos están comprobados contra `concesiones_busqueda`:

- **Fiabilidad.** Un rango de 4 años (27,4 millones de filas) devuelve `ERR_MANTENIMIENTO_BBDD` de forma intermitente, a cualquier profundidad de página. Una ventana semanal sobre esas mismas fechas no falló ni una vez en 6 intentos.
- **Velocidad.** Un rango de 30 días consultado de golpe tardó 286,7 s; ese mismo rango partido en semanas tardó 142,5 s, y ninguno de los dos dio errores.

### El resultado no depende del tamaño del tramo

Como la conversión de fechas se aplica a cada tramo, el resultado no varía con el tamaño: un rango de 14 días de `partidospoliticos_busqueda` devuelve exactamente las mismas 36 filas partido en tramos de 1, 7 o 14 días (comprobado contra el servicio real).

Los 7 días tampoco son críticos para la velocidad: sobre un rango fijo de 14 días de `concesiones_busqueda` (~530.000 filas), los tamaños de 1, 3, 7 y 14 días tardaron 51, 41, 47 y 57 s, diferencias que caben dentro del ruido de carga del servicio y sin errores en ningún caso. Se mantienen los 7 días por equilibrio: es rápido, es fiable y coincide con la ventana semanal.

## 4. Verificación de los límites de ventana

Para descartar tanto un solapamiento (traer un día de más) como un hueco (perder un día), se comprobó contra el servicio real, en las 5 entidades incrementales, que dos días consecutivos `X` y `X+1` consultados por la ruta real de producción, con la conversión que toca en cada familia, cumplen dos propiedades:

1. `fetch(X)` y `fetch(X+1)` son **disjuntos** (cero solapamiento).
2. Su unión es exactamente `fetch([X, X+1])` (**aditividad**).

Las cuentas cuadran fila a fila: en `concesiones`, 115.862 + 68.457 = 184.319 filas, sin solapamiento. Un `+1` de más en la familia exclusiva, o un límite mal aplicado en la inclusiva, habría duplicado el día de la frontera; un día perdido habría roto la unión. El invariante queda fijado como test permanente en `tests/test_generic.py`.

## 5. Detección de bajas acotada por ventana

Las entidades `concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `convocatorias_busqueda` y `convocatorias` detectan bajas reales comparando, dentro de la misma ejecución, lo que devuelve la API con las filas de la tabla cuya fecha de registro (`fechaAlta`, `fechaRegistro` o `fechaRecepcion`, según la entidad) cae en ese mismo rango.

La comparación nunca se hace contra la ejecución anterior: daría falsos positivos constantes, porque toda fila acaba quedándose fuera de una ventana móvil sin que eso signifique que se ha dado de baja.

`partidospoliticos_busqueda` se queda fuera de la detección de bajas: se comprobó contra el servicio real, con más de 70 filas reales en dos rangos de fechas distintos, que su payload no trae ningún campo de fecha de registro. El documento oficial dice que este endpoint «funciona igual, con los mismos filtros y resultados» que `concesiones_busqueda`; en la práctica no es así. Es una limitación permanente mientras la API no cambie.

## 6. Profundidad histórica por endpoint

Hasta dónde llega una carga histórica completa lo marca la retención de datos de la API en cada endpoint, medida contra el servicio real:

| Entidad | Datos disponibles hasta ~ | Limitado por |
|---|---|---|
| `concesiones_busqueda` | ~4 años | Retención de 4 años naturales |
| `partidospoliticos_busqueda` | ~4 años | (va con concesiones) |
| `ayudasestado_busqueda` | ~9-10 años | Retención de 10 años |
| `minimis_busqueda` | ~10 años | Retención de 10 años |
| `convocatorias_busqueda` | ~12 años | (va con `convocatorias`, misma fuente de descubrimiento) |
| `convocatorias` | ~12 años | Arranque del portal (~2014) |

Estas fechas no están escritas en `bdns-sync`: la herramienta es una pieza básica y no sabe hasta dónde llega cada endpoint. Igual que `scripts/delta_load.sh` se encarga de la cadencia, `scripts/full_load.sh` se encarga de las fechas de inicio y las pasa con `--since`. Consultar fechas anteriores a la retención solo devuelve semanas vacías, con una llamada barata cada una, así que las fechas del script son suelos conservadores, no los primeros registros exactos.

## 7. Rendimiento medido

Cifras medidas contra el servicio real que justifican decisiones de diseño. Los detalles de funcionamiento están junto al código (`bdns/sync/sinks/sql/dialects.py`, `bdns/sync/pipeline.py`); esto es el registro de las pruebas.

### Límite de peticiones y paso de detalle paralelo

El límite oficial son 10 peticiones por segundo y por IP. El *token bucket* del cliente lo respeta de media, pero arranca lleno: un pool de hilos recién creado lanza sus primeras peticiones a la vez y el servidor responde `429` a la ráfaga (comprobado: 10 hilos con solo el token bucket se cayeron en segundos). Ese mismo servidor acepta 9,8 req/s sostenidas sin un solo `429` cuando los *arranques* de petición van espaciados (probado con 100 ms); el espaciado que se usa es de 105 ms.

Con un mes real de `convocatorias` (mayo de 2026, 6.186 códigos): el paso de detalle en serie tardó entre 23 minutos y 3 h 12 min según la carga del servidor (de 0,2 a 1,9 s por llamada); en paralelo (8 hilos, arranques espaciados) tardó 10 min 54 s, sin ningún `429`.

### Solape productor/consumidor

Al cargar el staging se solapa la descarga del lote siguiente con la escritura del actual (`bdns/sync/pipeline.py`): un 40% más rápido, medido en los endpoints donde pesa la descarga. La descarga va en el hilo auxiliar y la escritura en el hilo dueño de la conexión, porque los objetos DBAPI de SQLite tienen afinidad de hilo; la cola acotada hace de contrapresión.

### Fiabilidad de rangos largos

Un rango de 7 días contra `concesiones_busqueda` trajo 147.856 filas sin errores; uno de 4 años falló de forma intermitente con `ERR_MANTENIMIENTO_BBDD` a cualquier profundidad de página. De ahí que se trocee siempre en tramos de 7 días (ver [sección 3](#3-troceo-de-ventanas-en-tramos-de-7-días)).

### Reintentos del cliente

Los valores por defecto de `bdns-fetch` (3 reintentos, espera fija de 2 s) se rinden al minuto escaso de problemas del servidor: una carga histórica real de varias horas se cayó por una sola petición que agotó sus 3 intentos. Con 8 reintentos y 15 s de espera se aguanta un bache de unos 2 minutos; lo único que cuesta es tardar más en darse por vencido ante un fallo realmente permanente.

## 8. Problemas conocidos de la API

Lista de los comportamientos problemáticos de la API, todos comprobados contra el servicio real. El resto del proyecto (README, comentarios del código) enlaza aquí en vez de repetir cada explicación.

- **Registros sueltos malformados.** El backend rechaza a veces un registro concreto y devuelve una página de error HTML en vez de JSON. No es un límite de peticiones ni un problema de parámetros: las llamadas de justo antes y justo después del mismo registro funcionan. `bdns-sync` descarta el registro con un aviso, lo cuenta en `_sync_runs.rows_skipped` y lo guarda en `_sync_errors`. No son fallos pasajeros: en dos meses de operación continua, los mismos 10 `idPES` de `planesestrategicos` fallaron en las 57 ejecuciones, siempre con la misma página HTML (570 descartes, un único contenido distinto). Un registro que falla, falla siempre.
- **`ERR_MANTENIMIENTO_BBDD` en rangos largos.** Los rangos de varios años fallan de forma intermitente a cualquier profundidad de página. Por eso toda consulta se parte en tramos de 7 días; ver [sección 3](#3-troceo-de-ventanas-en-tramos-de-7-días).
- **Fechas con semántica inconsistente entre endpoints.** `fechaRegFin` es exclusivo y `fechaHasta` es inclusivo, sin que la documentación oficial lo diga. Ver [sección 2](#2-semántica-del-extremo-superior-según-el-endpoint).
- **`partidospoliticos_busqueda` sin fecha de registro.** Su payload no trae ningún campo de fecha de registro, aunque la documentación oficial afirme que funciona igual que `concesiones_busqueda`. Sin ese campo no hay forma de detectar bajas. Ver [sección 5](#5-detección-de-bajas-acotada-por-ventana).
- **Nombre de beneficiario inestable en `grandesbeneficiarios_busqueda`.** Para un mismo `idPersona`, la API devuelve una grafía distinta del nombre en casi cada llamada, con el resto del registro idéntico. Observadas seis variantes de la misma razón social en once días (`M&M, S.L.`, `M M S.L.`, `MM SL`, `M&M S.L.`, `M&M SOCIEDAD LIMITADA`, con y sin punto final), siempre con el mismo importe. Probablemente el nombre se compone a partir de los registros de concesión subyacentes, donde cada órgano lo tecleó a su manera. Meter ese campo en el hash versionaba entre el 30% y el 60% de la tabla cada día: 3,7 millones de filas de historial para 148.000 registros vigentes, 25 versiones por clave en 53 días. El campo se excluye del hash (`exclude_from_hash` en el syncer); se sigue guardando entero en el payload, pero deja de contar como cambio. Ninguna otra entidad se comporta así: en `concesiones_busqueda` el versionado alto es real (importes que se van acumulando).
- **Arrays anidados en orden que cambia.** `regiones` devuelve el mismo árbol con los `children` en distinto orden entre llamadas, sin que haya cambiado nada. El hash canónico de `bdns-sync` ordena de forma recursiva las claves y los elementos de los arrays para no generar versiones falsas.
- **Rechazo de ráfagas aunque la media respete el límite.** El servidor responde `429` si varias peticiones arrancan a la vez, aunque la media esté por debajo de 10 req/s. Por eso los arranques se espacian 105 ms; ver [sección 7](#7-rendimiento-medido).
- **Retención limitada y distinta en cada endpoint.** Entre ~4 y ~12 años según la entidad. Ver [sección 6](#6-profundidad-histórica-por-endpoint).
- **Paginación inestable en fechas que siguen recibiendo altas.** Si el conjunto de resultados cambia (nuevas concesiones registradas) mientras se pagina una ventana amplia, la paginación por offset puede repetir en dos páginas seguidas las filas cercanas al borde. `bdns-sync` deduplica al insertar, así que las sincronizaciones normales no dejan duplicados; una carga histórica masiva sí puede dejar algún par residual. Solo afecta a fechas recientes, nunca a rangos ya cerrados. Cómo detectarlo y limpiarlo: [`data-caveats.md`](data-caveats.md).
