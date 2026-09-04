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

Cada punto sigue el mismo orden: qué hace la API, qué observamos, y qué hace `bdns-sync` al respecto. El resto del proyecto (README, comentarios del código) enlaza aquí en vez de repetir la explicación.

- **Registros sueltos malformados.** El backend rechaza a veces un registro concreto y devuelve una página de error HTML en vez de JSON. No es un límite de peticiones ni un problema de parámetros: las llamadas de justo antes y justo después del mismo registro funcionan. En `planesestrategicos`, entre el 8 de julio y el 30 de agosto de 2026, los mismos 10 `idPES` fallaron en las 57 ejecuciones, siempre con la misma página HTML; el 30 de agosto fueron 114 sobre 2.029 claves, así que un registro roto tiende a seguir roto pero el conjunto no es fijo. `bdns-sync` descarta el registro con un aviso, lo cuenta en `_sync_runs.rows_skipped` y guarda el contenido en `_sync_errors`, enlazado a la ejecución.
- **`ERR_MANTENIMIENTO_BBDD` en rangos largos.** Los rangos de varios años fallan de forma intermitente, a cualquier profundidad de página. Un rango de 4 años sobre `concesiones_busqueda` (27,4 millones de filas) falló repetidamente, mientras que una ventana semanal sobre esas mismas fechas no falló ni una vez en 6 intentos. `bdns-sync` parte toda consulta en tramos de 7 días; ver [sección 3](#3-troceo-de-ventanas-en-tramos-de-7-días).
- **Fechas con semántica inconsistente entre endpoints.** `fechaRegFin` es exclusivo y `fechaHasta` es inclusivo, sin que la documentación oficial lo diga. Consultando el mismo día `D`, `fechaRegFin=D` devuelve ~0 filas y `fechaRegFin=D+1` devuelve el día entero, mientras que `fechaHasta=D` sí devuelve el día `D` completo. `bdns-sync` centraliza la conversión en `generic.to_api_upper_bound` y la aplica solo a la familia exclusiva; ver [sección 2](#2-semántica-del-extremo-superior-según-el-endpoint).
- **`partidospoliticos_busqueda` sin fecha de registro.** Su payload no trae ningún campo de fecha de registro, aunque la documentación oficial afirme que este endpoint funciona igual que `concesiones_busqueda`. Comprobado con más de 70 filas reales en dos rangos de fechas distintos. Sin ese campo no hay forma de detectar bajas, así que `bdns-sync` deja esta entidad fuera de la detección de bajas; ver [sección 5](#5-detección-de-bajas-acotada-por-ventana).
- **Nombre de beneficiario inestable en `grandesbeneficiarios_busqueda`.** Para un mismo `idPersona`, la API cambia la grafía del nombre de unas horas a otras, con el resto del registro idéntico. Medido el 30 de agosto de 2026: tres descargas consecutivas en cuatro minutos devolvieron los 148.170 nombres idénticos, pero entre la ejecución de las 00:03 y la de las 15:20 cambiaron 79.000 filas, lo que apunta a una caché o una reagregación periódica en el origen y no a azar por petición. Para `idPersona=7818535` se observaron seis variantes de la misma razón social en once días (`M&M, S.L.`, `M M S.L.`, `MM SL`, `M&M S.L.`, `M&M SOCIEDAD LIMITADA`, con y sin punto final), siempre con el mismo importe; el nombre probablemente se compone a partir de los registros de concesión subyacentes, donde cada órgano lo tecleó a su manera. Con ese campo dentro del hash se versionaba entre el 30% y el 60% de la tabla cada día: 3,7 millones de filas de historial para 148.000 registros vigentes, 25 versiones por clave en 53 días. `bdns-sync` excluye el campo del hash (`exclude_from_hash` en el syncer): se sigue guardando entero en el payload, pero deja de contar como cambio. No es el único caso ni la única forma que toma: `concesiones_busqueda` sufre lo mismo con su propio campo `beneficiario`, y `minimis_busqueda` y `ayudasestado_busqueda` una variante distinta. El detalle, con la medición por entidad, está en la [sección 9](#9-cambios-espurios-el-mismo-dato-escrito-de-otra-forma).
- **Arrays anidados en orden que cambia.** `regiones` devuelve el mismo árbol con los `children` en distinto orden entre llamadas, sin que haya cambiado ningún dato. `bdns-sync` ordena de forma recursiva las claves y los elementos de los arrays antes de calcular el hash, para no generar versiones falsas. El mismo desorden aparece dentro de cadenas con separadores, donde la canonicalización no llega; ver [sección 9](#9-cambios-espurios-el-mismo-dato-escrito-de-otra-forma).
- **Rechazo de ráfagas aunque la media respete el límite.** El servidor responde `429` cuando varias peticiones arrancan a la vez, aunque la media esté por debajo del límite oficial de 10 req/s. Un pool de 10 hilos que solo respetaba la media murió en segundos, mientras que el mismo servidor aceptó 9,8 req/s sostenidas con los arranques espaciados. `bdns-sync` espacia los arranques 105 ms; ver [sección 7](#7-rendimiento-medido).
- **Retención limitada y distinta en cada endpoint.** Los datos disponibles van de ~4 años (`concesiones_busqueda`) a ~12 (`convocatorias`), según la entidad. `bdns-sync` no codifica esas fechas —consultar más atrás solo devuelve semanas vacías, que son llamadas baratas—, las decide el script del operador con `--since`; ver [sección 6](#6-profundidad-histórica-por-endpoint).
- **Paginación inestable en fechas que siguen recibiendo altas.** Si el conjunto de resultados cambia mientras se pagina una ventana amplia, porque entran concesiones nuevas, la paginación por offset puede repetir en dos páginas seguidas las filas cercanas al borde. Solo afecta a fechas recientes, nunca a rangos ya cerrados, cuya paginación es estable. `bdns-sync` deduplica al insertar, así que las sincronizaciones normales no dejan duplicados; una carga histórica masiva en una sola pasada sí puede dejar algún par residual. Cómo detectarlo y limpiarlo: [`data-caveats.md`](data-caveats.md).

## 9. Cambios espurios: el mismo dato escrito de otra forma

Un versionado SCD2 crea una versión nueva cada vez que cambia el hash del payload. Si la API devuelve el mismo dato escrito de otra manera entre una llamada y otra, se genera una versión que no aporta nada: ni el registro cambió ni hubo corrección administrativa, solo cambió cómo se compuso la respuesta.

Medido sobre la pasada anual del 1 de septiembre de 2026, comparando cada versión nueva con la que cerró:

| Entidad | Versiones | Espurias | Campo culpable |
|---|---|---|---|
| `concesiones_busqueda` | 368.818 | **213.176 (58%)** | `beneficiario` |
| `minimis_busqueda` | 35.995 | **30.033 (83%)** | `sectorActividad` |
| `ayudasestado_busqueda` | 6.758 | **5.046 (75%)** | `sectores` |
| `grandesbeneficiarios_busqueda` | ~65.000 al día | **~100%** | `beneficiario` |
| `convocatorias` | 2.366 | 0 | — |
| `convocatorias_busqueda` | 437 | 13 (3%) | — |
| `partidospoliticos_busqueda` | 21 | 1 | — |

De las 414.395 versiones que produjo la pasada anual, unas 248.000 son ruido: el 60%. Las correcciones reales rondan las 166.000.

### Familia 1: el nombre se reconstruye de forma inestable

Se mide en las cinco entidades que traen el campo `beneficiario` —`concesiones_busqueda`, `grandesbeneficiarios_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda` y `partidospoliticos_busqueda`— aunque solo en las dos primeras alcanza volumen y oscilación probada. Para el mismo beneficiario, con el mismo importe y el mismo identificador, el campo de nombre vuelve escrito de otra forma:

```
GONZALEZ                      →  GONZÁLEZ            (acentos, en ambas direcciones)
REMEDIOS BENITEZ BASILIO .    →  REMEDIOS BENITEZ BASILIO . .
MONTSERRAT LOPEZ REYNOSO MECA →  MONTSERRAT LOPEZ-REYNOSO MECA
LIMMAT M&M, S.L.              →  LIMMAT MM SL        (seis variantes en once días)
```

En `concesiones_busqueda`, los 230.878 cambios de `beneficiario` conservan **el mismo `idPersona` en el 100% de los casos**, y 213.176 son idénticos tras quitar acentos y puntuación. Nunca es otra persona: es la misma escrita de otra manera. El nombre probablemente se compone a partir de los registros subyacentes, donde cada órgano lo tecleó a su modo.

### El criterio para excluir un campo del hash

Un campo sale del hash **solo si su valor oscila**, es decir, si vuelve a valores que ya había tenido. Eso distingue un campo que la API reescribe al azar de uno que recibe correcciones reales, y evita excluir por analogía.

La prueba: para cada clave natural con tres o más versiones, se toma la secuencia de valores del campo, se quitan las repeticiones consecutivas y se mira si algún valor reaparece después de otro distinto.

Medido sobre el histórico:

| Entidad | Campo | Claves que cambian | Oscilan | Veredicto |
|---|---|---|---|---|
| `concesiones_busqueda` | `beneficiario` | 177 | **119 (67%)** | aleatorio, fuera del hash |
| `grandesbeneficiarios_busqueda` | `beneficiario` | — | ciclo de hashes probado | aleatorio, fuera del hash |
| `ayudasestado_busqueda` | `beneficiario` | 2 | 0 | muestra insuficiente, se mantiene |
| `minimis_busqueda` | `beneficiario` | 0 | — | muestra insuficiente, se mantiene |
| `concesiones_busqueda` | `convocatoria` | 1 | 0 | muestra insuficiente, se mantiene |

Un ejemplo de oscilación en `concesiones_busqueda`, con el mismo `idPersona` en las tres versiones:

```
ASOCIACIÓN INCLUDD  →  ASOCIACION INCLUDD  →  ASOCIACIÓN INCLUDD
```

En las entidades con muestra insuficiente el campo **se mantiene en el hash**, aunque una parte de sus cambios sea de formato. El volumen es bajo —del orden de centenares de versiones frente a las ~240.000 de `concesiones`— y ante la duda se prefiere registrar el cambio. La muestra es corta porque el histórico solo tiene dos meses y la mayoría de registros aún va por su primera o segunda versión; conviene rehacer esta medición cuando haya más recorrido.

### Familia 2: listas barajadas dentro de una cadena

Afecta a `minimis_busqueda` y `ayudasestado_busqueda`. El campo trae varios valores concatenados y el orden cambia entre llamadas, con los mismos elementos:

```
minimis_busqueda      sectorActividad, separador ";"
  '52.3 - Intermediación del transporte; 52.2 - Auxiliares del transporte'
  '52.2 - Auxiliares del transporte; 52.3 - Intermediación del transporte'

ayudasestado_busqueda sectores, separador "#"
```

Es la misma raíz que el orden no determinista de los arrays de `regiones` (ver [sección 8](#8-problemas-conocidos-de-la-api)), pero la canonicalización del hash no puede corregirla: ordena claves de objetos y elementos de arrays JSON, y aquí la lista viaja dentro de un único valor de texto, así que la ve como una cadena cualquiera.

### Qué reglas aplica `bdns-sync`

Cuatro, declaradas en el syncer de cada entidad junto a su clave natural:

| Entidad | Regla | Motivo |
|---|---|---|
| `concesiones_busqueda` | `exclude_from_hash=("beneficiario",)` | oscilación probada, 67% |
| `grandesbeneficiarios_busqueda` | `exclude_from_hash=("beneficiario",)` | oscilación probada por ciclo de hashes |
| `ayudasestado_busqueda` | `delimited_lists={"sectores": "#"}` | 84% de sus cambios eran reordenamiento |
| `minimis_busqueda` | `delimited_lists={"sectorActividad": ";"}` | 92% de sus cambios eran reordenamiento |

Ninguna otra entidad lleva regla alguna. Las dos familias se tratan distinto a propósito: una lista barajada se puede canonizar sin perder información, así que se ordena antes de hashear y el campo sigue detectando cambios reales de sector. Un nombre reescrito al azar no se puede canonizar sin decidir cuál de las grafías es la buena, así que el campo sale del hash entero.

En los dos casos **solo cambia lo que el hash ve**: el payload se almacena exactamente como lo devolvió la API.

### Familia 3: campos que dejan de venir y vuelven

Un campo que normalmente trae valor vuelve `null` en una llamada y con valor en la siguiente. Medido sobre 3.000 pares de `convocatorias` y otros tantos del resto:

| Entidad | Campo | `null→valor` | `valor→null` | % de pares |
|---|---|---|---|---|
| `convocatorias` | `fechaInicioSolicitud` | 209 | 55 | 8,8% |
| `convocatorias` | `fechaFinSolicitud` | 123 | 61 | 6,1% |
| `convocatorias` | `textInicio` | 40 | 47 | 2,9% |
| `convocatorias` | `textFin` | 48 | 32 | 2,7% |
| `convocatorias_busqueda` | `descripcionLeng` | 18 | 17 | 6,4% |
| `convocatorias` | `descripcionLeng` | 13 | 14 | 0,9% |
| `convocatorias` | `sedeElectronica` | 6 | 7 | 0,4% |
| `minimis_busqueda` | `sectorActividad` | 23 | 40 | 2,1% |

Los repartos simétricos (`textInicio` 40 contra 47, `descripcionLeng` 18 contra 17) delatan que no es información completándose. Los unidireccionales sí lo son: `reglamento` (8 y 0), `urlAyudaEstado` (3 y 0) y `ayudaEstado` (3 y 0) son campos que se rellenan y ya no vuelven atrás.

**Los nulos llegan en bloque, no sueltos.** De los pares de `convocatorias` en los que algún campo pasa a `null`, 81 pierden dos campos a la vez y solo 51 pierden uno. Y los que caen juntos van emparejados:

```
54 pares:  fechaInicioSolicitud + fechaFinSolicitud
25 pares:  textInicio + textFin
```

Es el bloque del plazo de solicitud entero, fechas y textos, desapareciendo y volviendo. Eso apunta a respuestas parciales del backend en el endpoint de detalle, no a campos que parpadeen por su cuenta.

**Esta familia no se arregla con reglas de hash**, a diferencia de las dos anteriores. Un `null` no se puede normalizar: o cuenta como cambio, o se excluye el campo y entonces se pierde la detección de cuándo se fija un plazo de verdad, que es información legítima. Las versiones que genera se aceptan como válidas; el volumen es pequeño, unas 650 sobre las 4.320 versiones cerradas de `convocatorias`.

Lo que sí conviene saber al consumir los datos es que **el registro es veraz pero se presta a una lectura falsa**: parece que a una convocatoria le quitaron el plazo de solicitud un día y se lo devolvieron otro, cuando no hubo ninguna modificación administrativa. Ver [`data-caveats.md`](data-caveats.md).

Y deja una lección para el motor: la API **puede devolver `null` en campos que normalmente vienen rellenos**. Hoy no toca ninguno crítico —`fechaRecepcion`, la fecha de registro de `convocatorias`, no aparece en la lista— pero si algún día el bloque que cae incluye uno, la ejecución se rompe; ver la entrada sobre validación de registros en la [hoja de ruta](roadmap.md).

### Lo que no está afectado

`convocatorias` y `convocatorias_busqueda` no tienen ruido apreciable, y conviene decirlo porque comparten origen con el resto. Sus cambios son administrativos de verdad: presupuestos que suben (25.000 → 40.000 €), plazos de solicitud que se amplían, documentos que se añaden, y reorganizaciones de órganos (336 de sus 437 versiones cambian `nivel3`, repartidas entre 80 órganos distintos: una secretaría general que pasa a dirección general arrastra a todas sus convocatorias). Eso es exactamente lo que un histórico debe registrar.

Que la familia de concesiones esté afectada y la de convocatorias no sugiere que el problema no es de la API en general, sino de cómo se compone la respuesta en unos endpoints concretos.

### Cómo se midió

Dos comprobaciones distintas, ambas sobre pares (versión cerrada, versión nueva) de la misma ejecución:

- **Formato**: normalizar ambos payloads a NFD, quitar los diacríticos y todo lo que no sea alfanumérico, y comparar. Si coinciden, el cambio era de escritura.
- **Reordenamiento**: partir el campo por su separador, ordenar los trozos alfabéticamente, volver a unirlos y comparar. Si coinciden, la lista solo estaba barajada.

La primera no detecta la segunda, porque barajar una lista cambia la secuencia de caracteres. Por eso hicieron falta las dos.
