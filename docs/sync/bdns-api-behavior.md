# Comportamiento del API de la BDNS: ventanas de fecha

[🇬🇧 English version](./api-behavior.en.md)

Este documento recoge el comportamiento real del API de la BDNS respecto a los parámetros de fecha, verificado mediante pruebas en vivo contra el servicio. Se documenta en detalle porque estos comportamientos son sutiles, no figuran en la documentación oficial (o la contradicen), y un error en su manejo provoca pérdida silenciosa de datos.

Cada afirmación indica la comprobación empírica que la respalda.

## 1. Convención interna: rango de días inclusivo

En `bdns-sync`, una ventana es un rango de días **inclusivo por ambos extremos**: la ventana `daily` sobre el día `X` significa "los registros del día `X`". El extremo superior de toda ventana es *ayer* (`date.today() - 1`), porque los datos del día en curso no están cerrados hasta la mañana siguiente.

## 2. Semántica del extremo superior según el endpoint

El API tiene dos familias de parámetros de fecha, y su extremo superior se comporta de forma **opuesta**:

| Familia | Parámetros | Endpoints | Extremo superior | Comprobación en vivo (día `D`) |
|---|---|---|---|---|
| Búsqueda por fecha de registro | `fechaRegInicio` / `fechaRegFin` | `concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `partidospoliticos_busqueda` | **Exclusivo** (no incluye el día `D`) | `fechaRegFin=D` devuelve ~0 filas del día `D`; `fechaRegFin=D+1` devuelve el día `D` completo (en `concesiones`, 1 fila frente a 58.488) |
| Descubrimiento de convocatorias | `fechaDesde` / `fechaHasta` | `convocatorias` (paso de descubrimiento) | **Inclusivo** (incluye el día `D`) | `fechaHasta=D` devuelve todas las convocatorias con `fechaRecepcion == D`; `fechaHasta=D+1` devuelve los días `D` y `D+1` |

La conversión entre la convención interna (inclusiva) y la familia exclusiva está centralizada en una única función, `generic.to_api_upper_bound(fin_inclusivo)`, que suma un día al extremo superior. El endpoint `convocatorias` no la usa: su `fechaHasta` ya es inclusivo, y sumar un día incorporaría convocatorias de fuera de la ventana.

En `convocatorias`, los parámetros de fecha solo intervienen en el paso de descubrimiento (`convocatorias_busqueda`): por cada código descubierto se solicita después el registro completo al endpoint de detalle (por `numConv`), que no tiene parámetros de fecha y es el que se almacena.

El coste de `convocatorias` es por tanto lineal en el número de códigos, no en el ancho de la ventana. Medido en vivo con un mes real (mayo de 2026, 6.186 códigos): el descubrimiento tarda ~1 s, y el paso de detalle domina por completo. La latencia por llamada de detalle varía con la carga del servidor: ~0,22 s/llamada en horario favorable (un mes ≈ 23 minutos), pero una ejecución completa del mismo mes llegó a tardar 3 h 12 min (~1,9 s/llamada) con un único reintento por timeout. La ejecución terminó con éxito en ambos regímenes (6.186 filas, 0 descartes); solo cambia la duración.

El paso de detalle está paralelizado para acercarse al límite de 10 req/s en vez de quedar atado a la latencia de una sola conexión. El servidor rechaza las ráfagas, así que los arranques de petición van espaciados; el detalle medido está en la [sección 7](#7-rendimiento-medido).

Consecuencias de un manejo incorrecto, medidas en vivo:

- Sin la conversión, la ventana `daily` de los cuatro endpoints `fechaReg` no devolvería prácticamente nada, y toda ventana más ancha perdería su día más reciente.
- Con troceo (ver sección 3), el error se multiplica: se pierde un día por cada frontera de trozo. Un rango de 28 días troceado por día devolvió 8 filas en lugar de ~1,2 millones.

## 3. Troceo de ventanas en piezas de 7 días

Toda ventana se divide en piezas de como máximo 7 días antes de consultarse (`generic.iter_date_chunks`). Las ventanas `daily` y `weekly` caben en una sola pieza y no se ven afectadas; `monthly` y `annual` sí se trocean. Los motivos, ambos verificados contra `concesiones_busqueda`:

- **Fiabilidad.** Un rango de 4 años (27,4 millones de filas) devuelve `ERR_MANTENIMIENTO_BBDD` de forma intermitente en cualquier profundidad de página. Una ventana semanal sobre las mismas fechas no falló ni una vez en 6 intentos.
- **Velocidad.** Un rango de 30 días consultado de una sola vez tardó 286,7 s; el mismo rango troceado en semanas tardó 142,5 s, ambos sin errores.

### El resultado no depende del tamaño de trozo

Como la conversión de fechas se aplica a cada pieza, el resultado es invariante al tamaño de trozo: un rango de 14 días de `partidospoliticos_busqueda` devuelve exactamente las mismas 36 filas troceado en piezas de 1, 7 o 14 días (comprobado en vivo).

El tamaño de 7 días tampoco es crítico para la velocidad: sobre un rango fijo de 14 días de `concesiones_busqueda` (~530.000 filas), los tamaños de 1, 3, 7 y 14 días tardaron 51, 41, 47 y 57 s respectivamente, diferencias dentro del ruido de carga del servicio y sin errores en ningún caso. Se mantiene el tamaño de 7 días por equilibrio: rápido, fiable y coincidente con la ventana semanal.

## 4. Verificación de los límites de ventana

Para descartar tanto un solapamiento (traer un día de más) como un hueco (perder un día), se verificó en vivo, en las 5 entidades incrementales, que dos días consecutivos `X` y `X+1` consultados por la ruta real de producción, con la conversión correcta según familia, cumplen dos propiedades:

1. `fetch(X)` y `fetch(X+1)` son **disjuntos** (solapamiento cero).
2. Su unión es exactamente `fetch([X, X+1])` (**aditividad**).

Las cuentas cuadran fila a fila: en `concesiones`, 115.862 + 68.457 = 184.319 filas, sin solapamiento. Un `+1` de más en la familia exclusiva, o un límite mal aplicado en la inclusiva, habría duplicado el día frontera; un día perdido habría roto la unión. El invariante está fijado como test permanente en `tests/test_generic.py`.

## 5. Detección de bajas acotada por ventana

Las entidades `concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `convocatorias_busqueda` y `convocatorias` detectan bajas reales comparando, dentro de la misma ejecución, lo obtenido del API contra las filas de la tabla cuya propia fecha de registro (`fechaAlta`, `fechaRegistro` o `fechaRecepcion`, según la entidad) cae en el mismo rango.

La comparación nunca se hace contra la ejecución anterior: produciría falsos positivos constantes, porque toda fila termina envejeciendo fuera de una ventana móvil sin que eso signifique una baja.

`partidospoliticos_busqueda` queda excluida de la detección de bajas: se confirmó en vivo, con más de 70 filas reales en dos rangos de fechas distintos, que su payload no expone ningún campo de fecha de registro. El documento oficial afirma que este endpoint "funciona igual, con los mismos filtros y resultados" que `concesiones_busqueda`; en la práctica no es así. Es una limitación permanente salvo que el API cambie.

## 6. Profundidad histórica por endpoint

El alcance de una carga histórica completa lo determina la retención de datos del API por endpoint, medida en vivo:

| Entidad | Datos disponibles hasta ~ | Limitado por |
|---|---|---|
| `concesiones_busqueda` | ~4 años | Retención de 4 años naturales |
| `partidospoliticos_busqueda` | ~4 años | (sigue a concesiones) |
| `ayudasestado_busqueda` | ~9-10 años | Retención de 10 años |
| `minimis_busqueda` | ~10 años | Retención de 10 años |
| `convocatorias_busqueda` | ~12 años | (sigue a `convocatorias`, misma fuente de descubrimiento) |
| `convocatorias` | ~12 años | Arranque del portal (~2014) |

Estas fechas no están codificadas en `bdns-sync`: la herramienta es un primitivo puro y no conoce la profundidad histórica de cada endpoint. Igual que `scripts/delta_load.sh` es dueño de la cadencia, `scripts/full_load.sh` es dueño de las fechas de inicio y las pasa mediante `--since`. Consultar fechas anteriores a la retención solo devuelve semanas vacías (una llamada barata cada una), por lo que las fechas del script son suelos conservadores, no primeros registros exactos.

## 7. Rendimiento medido

Cifras medidas en vivo que justifican decisiones de diseño. Los detalles operativos viven junto al código (`bdns/sync/sinks/sql/dialects.py`, `bdns/sync/pipeline.py`); esto es el registro de evidencia.

### Límite de peticiones y paso de detalle paralelo

El límite oficial es 10 peticiones/segundo por IP. El *token bucket* del cliente lo respeta como media, pero arranca lleno: un pool de hilos nuevo dispara sus primeras peticiones simultáneamente y el servidor responde `429` a la ráfaga (comprobado en vivo: 10 hilos solo con token bucket murieron en segundos). El mismo servidor acepta 9,8 req/s sostenidas sin ningún `429` cuando los *arranques* de petición van espaciados (comprobado a 100 ms); el espaciado usado es 105 ms.

Con un mes real de `convocatorias` (mayo de 2026, 6.186 códigos): el paso de detalle secuencial tardó entre 23 minutos y 3 h 12 min según la carga del servidor (0,2-1,9 s/llamada); en paralelo (8 hilos, arranques espaciados) tardó 10 min 54 s, sin ningún `429`.

### Solape productor/consumidor

El staging solapa el fetch del lote siguiente con la escritura del actual (`bdns/sync/pipeline.py`): +40% medido en endpoints donde el fetch pesa. El fetch va en el hilo auxiliar y la escritura en el hilo dueño de la conexión porque los objetos DBAPI de SQLite tienen afinidad de hilo; la cola acotada hace de contrapresión.

### Fiabilidad de rangos largos

Un rango de 7 días contra `concesiones_busqueda` trajo 147.856 filas sin errores; un rango de 4 años falló de forma intermitente con `ERR_MANTENIMIENTO_BBDD` a cualquier profundidad de página. De ahí el troceo universal en piezas de 7 días (ver [sección 3](#3-troceo-de-ventanas-en-piezas-de-7-días)).

### Reintentos del cliente

Los valores por defecto de `bdns-fetch` (3 reintentos, espera fija de 2 s) abandonan tras ~1 minuto de problemas del servidor: un backfill real de varias horas murió por una única petición que agotó sus 3 intentos. Con 8 × 15 s se sobrevive a un bache de ~2 minutos; el único coste es más retraso ante un fallo genuinamente permanente.

## 8. Problemas conocidos del API

Lista consolidada de los comportamientos problemáticos del API, todos verificados en vivo. El resto del proyecto (README, comentarios del código) enlaza aquí en lugar de repetir cada explicación.

- **Registros individuales malformados.** El backend rechaza a veces un registro concreto con una página de error HTML en lugar de JSON. No es un límite de tasa ni un problema de parámetros: las llamadas inmediatamente anteriores y posteriores al mismo registro funcionan. `bdns-sync` descarta el registro con un aviso, lo cuenta en `_sync_runs.rows_skipped` y lo guarda en `_sync_errors`.
- **`ERR_MANTENIMIENTO_BBDD` en rangos largos.** Los rangos de fechas de varios años fallan de forma intermitente a cualquier profundidad de página. Por eso toda consulta se trocea en piezas de 7 días; ver [sección 3](#3-troceo-de-ventanas-en-piezas-de-7-días).
- **Semántica de fechas inconsistente entre endpoints.** `fechaRegFin` es exclusivo y `fechaHasta` es inclusivo, sin que la documentación oficial lo indique. Ver [sección 2](#2-semántica-del-extremo-superior-según-el-endpoint).
- **`partidospoliticos_busqueda` sin fecha de registro.** Su payload no expone ningún campo de fecha de registro, aunque la documentación oficial afirma que funciona igual que `concesiones_busqueda`. Sin ese campo no hay detección de bajas posible. Ver [sección 5](#5-detección-de-bajas-acotada-por-ventana).
- **Orden no determinista de arrays anidados.** `regiones` devuelve el mismo árbol con los `children` en orden distinto entre llamadas, sin ningún cambio real. El hash canónico de `bdns-sync` ordena recursivamente claves y elementos de array para no producir versiones espurias.
- **Rechazo de ráfagas aunque el promedio respete el límite.** El servidor responde `429` a un arranque simultáneo de peticiones aunque la media esté bajo 10 req/s. Los arranques se espacian 105 ms; ver [sección 7](#7-rendimiento-medido).
- **Retención limitada por endpoint.** Entre ~4 y ~12 años según la entidad. Ver [sección 6](#6-profundidad-histórica-por-endpoint).
- **Paginación inestable contra fechas que siguen recibiendo altas.** Si el conjunto de resultados cambia (nuevas concesiones registradas) mientras se pagina una ventana amplia, la paginación por offset puede repetir filas cercanas al borde de página en dos páginas consecutivas. `bdns-sync` deduplica al insertar, así que las sincronizaciones normales no dejan duplicados; una carga histórica masiva puede dejar algún par residual. Solo afecta a fechas recientes, nunca a rangos ya cerrados. Cómo detectarlo y limpiarlo: [`data-caveats.md`](data-caveats.md).
