# Comportamiento de la API

Cómo se comporta de verdad la API de la BDNS, comprobado contra el servicio real. Son comportamientos que la [documentación oficial](https://www.infosubvenciones.es/bdnstrans/api) no recoge, o que contradice, y que hacen perder o duplicar datos en silencio si se manejan mal.

Cada afirmación indica la medición en la que se apoya. La mayoría se hicieron mientras se construía [`bdns-sync`](https://cruzlorite.github.io/bdns-sync/), que es quien descarga la API entera a diario; esta página es su hogar porque hablan de la API, no del almacenamiento. Lo que `bdns-sync` hace con cada una está en su propia documentación.

<a id="upper-bound"></a>
## Los dos filtros de fecha discrepan en el extremo superior

La API tiene dos familias de parámetros de fecha, y el extremo superior se comporta justo **al revés** en cada una:

| Familia | Parámetros | Endpoints | Extremo superior | Comprobado (día `D`) |
|---|---|---|---|---|
| Fecha de registro | `fechaRegInicio` / `fechaRegFin` | `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda` | **Exclusivo** | `fechaRegFin=D` devuelve ~0 filas del día `D`; `fechaRegFin=D+1` lo devuelve entero (en `concesiones`, 1 fila frente a 58.488) |
| Periodo | `fechaDesde` / `fechaHasta` | el resto de búsquedas, entre ellas `convocatorias-busqueda` | **Inclusivo** | `fechaHasta=D` devuelve todas las convocatorias con `fechaRecepcion == D`; `fechaHasta=D+1` devuelve `D` y `D+1` |

Equivocarse cuesta caro. Sin sumar un día a `fechaRegFin`, una consulta de un solo día no devuelve prácticamente nada y cualquier rango más ancho pierde su último día. Al trocear un rango el error se multiplica, un día por cada frontera: un rango de 28 días partido en días devolvió 8 filas en lugar de ~1,2 millones.

`bdns-fetch` deja los parámetros tal cual los define la API, y ofrece [`registration_range`][bdns.fetch.dates.registration_range] y [`period_range`][bdns.fetch.dates.period_range]: reciben un rango inclusivo `[primero, último]` y devuelven los argumentos correctos para cada familia.

<a id="range-reliability"></a>
## Los rangos largos fallan; los de una semana no

Medido contra `concesiones-busqueda`:

- **Fiabilidad.** Un rango de 4 años (27,4 millones de filas) devuelve `ERR_MANTENIMIENTO_BBDD` de forma intermitente, a cualquier profundidad de página. Una ventana semanal sobre esas mismas fechas no falló ni una vez en 6 intentos, y un rango de 7 días trajo 147.856 filas sin errores.
- **Velocidad.** Un rango de 30 días consultado de golpe tardó 286,7 s; partido en semanas, 142,5 s. Ninguno dio errores.

El tamaño exacto del tramo no es crítico. Sobre un rango fijo de 14 días (~530.000 filas), tramos de 1, 3, 7 y 14 días tardaron 51, 41, 47 y 57 s, diferencias dentro del ruido de carga del servicio. Siete días es un buen equilibrio, y es lo que usa [`split_range`][bdns.fetch.dates.split_range] por defecto ([`MAX_RANGE_DAYS`][bdns.fetch.dates.MAX_RANGE_DAYS]).

El resultado tampoco depende del tamaño del tramo, siempre que el extremo superior se trate bien en cada uno: un rango de 14 días de `partidospoliticos-busqueda` devuelve las mismas 36 filas partido en tramos de 1, 7 o 14 días.

<a id="boundary-check"></a>
## Días consecutivos: disjuntos y aditivos

Para descartar tanto un solapamiento (traer un día de más) como un hueco (perder uno), se comprobó en las cinco búsquedas incrementales que dos días consecutivos `X` y `X+1`, consultados con el extremo superior correcto en cada familia, cumplen dos propiedades:

1. son **disjuntos**: ningún registro aparece en los dos;
2. su unión es exactamente la consulta de `[X, X+1]` (**aditividad**).

Las cuentas cuadran fila a fila: en `concesiones`, 115.862 + 68.457 = 184.319, sin solapamiento.

Estas dos propiedades, más la semántica de cada extremo, son lo que comprueba [`check_api_contract`][bdns.fetch.contract.check_api_contract] (`bdns-fetch check-api`) contra el servicio real. Los tests unitarios solo pueden fijar el modelo que tenemos de la API; esta comprobación es la que avisa si la API cambia.

<a id="rate-limit"></a>
## El límite de peticiones rechaza ráfagas

El límite oficial son 10 peticiones por segundo y por IP. El servidor, además, responde `429` cuando varias peticiones **arrancan a la vez**, aunque la media quede por debajo del límite: 10 hilos que solo respetaban la media se cayeron en segundos. El mismo servidor acepta 9,8 peticiones por segundo sostenidas cuando los arranques van espaciados (probado con 100 ms entre arranques).

Por eso el limitador de `bdns-fetch` ([`RateLimiter`][bdns.fetch.utils.RateLimiter]) espacia las peticiones en vez de permitir ráfagas, y por defecto deja margen: 9,5 por segundo, una cada ~105 ms. El límite es por IP: varios procesos desde la misma IP lo comparten y tienen que repartírselo (`--rate-limit`).

<a id="latency"></a>
## Latencia variable según la carga

La latencia de una llamada sencilla, como el detalle de una convocatoria, depende mucho de la carga del servidor: ~0,22 s por llamada en horas buenas, ~1,9 s en malas. Un mismo lote de 6.186 detalles (mayo de 2026) tardó entre 23 minutos y 3 h 12 min en serie; en paralelo, con 8 hilos y los arranques espaciados, 10 min 54 s, sin un solo `429`.

<a id="history-depth"></a>
## Retención distinta en cada endpoint

Hasta dónde llegan los datos lo marca la retención de cada endpoint:

| Endpoint | Datos disponibles | Limitado por |
|---|---|---|
| `concesiones-busqueda` | ~4 años | retención de 4 años naturales |
| `partidospoliticos-busqueda` | ~4 años | va con concesiones |
| `ayudasestado-busqueda` | ~9-10 años | retención de 10 años |
| `minimis-busqueda` | ~10 años | retención de 10 años |
| `convocatorias-busqueda`, `convocatorias` | ~12 años | arranque del portal (~2014) |

Consultar fechas anteriores no da error: devuelve semanas vacías, con una llamada barata cada una.

<a id="api-issues"></a>
## Problemas conocidos

- **Registros sueltos malformados.** El backend rechaza a veces un registro concreto y devuelve una página de error HTML en vez de JSON. No es un límite de peticiones ni un problema de parámetros: las llamadas de justo antes y justo después funcionan. En `planesestrategicos`, entre el 8 de julio y el 30 de agosto de 2026, los mismos 10 `idPES` fallaron en las 57 ejecuciones; el 30 de agosto fueron 114 de 2.029. Un registro roto tiende a seguir roto, pero el conjunto no es fijo.
- **Errores dentro de una respuesta 200.** Algunos errores llegan con estado 200 y un cuerpo `{"codigo": ..., "error": ...}`. `bdns-fetch` los trata como errores.
- **`ERR_MANTENIMIENTO_BBDD` en rangos largos.** Ver [arriba](#range-reliability). `bdns-fetch` lo considera transitorio y lo reintenta.
- **Fechas con semántica inconsistente.** `fechaRegFin` exclusivo, `fechaHasta` inclusivo, sin que la documentación oficial lo diga. Ver [arriba](#upper-bound).
- **`partidospoliticos-busqueda` sin fecha de registro.** Su payload no trae ningún campo de fecha de registro, aunque la documentación oficial afirme que funciona igual que `concesiones-busqueda`. Comprobado con más de 70 filas reales en dos rangos distintos.
- **Arrays anidados en orden cambiante.** `regiones` devuelve el mismo árbol con los `children` en distinto orden entre llamadas, sin que cambie ningún dato.
- **Paginación inestable en fechas que reciben altas.** La paginación es por offset. Si entran registros nuevos mientras se pagina un rango reciente, una fila cercana al borde de una página puede venir en dos páginas seguidas. Los rangos ya cerrados paginan de forma estable.
- **`terceros` es redundante.** Las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) recomiendan no usarlo: `concesiones-busqueda` ya trae los datos del beneficiario.

<a id="spurious-changes"></a>
## El mismo dato, escrito de otra forma

Entre una llamada y otra, la API puede devolver un registro idéntico escrito de otra manera. No hubo corrección administrativa: solo cambió cómo se compuso la respuesta. Para quien guarda histórico (como `bdns-sync`) esto genera versiones falsas; medido en la pasada anual de `bdns-sync` del 1 de septiembre de 2026, el 60% de las versiones nuevas eran de este tipo. Hay tres familias.

<a id="unstable-names"></a>
### Nombres que se reconstruyen de forma inestable

El campo `beneficiario` de `concesiones-busqueda` y `grandesbeneficiarios-busqueda` vuelve escrito de otra forma para el mismo beneficiario, con el mismo importe y el mismo identificador:

```
GONZALEZ                      →  GONZÁLEZ            (acentos, en ambas direcciones)
REMEDIOS BENITEZ BASILIO .    →  REMEDIOS BENITEZ BASILIO . .
MONTSERRAT LOPEZ REYNOSO MECA →  MONTSERRAT LOPEZ-REYNOSO MECA
LIMMAT M&M, S.L.              →  LIMMAT MM SL        (seis variantes en once días)
```

En `concesiones-busqueda`, 230.878 cambios de `beneficiario` conservan **el mismo `idPersona` en el 100% de los casos**, y 213.176 son idénticos tras quitar acentos y puntuación. El valor además **oscila**: vuelve a grafías que ya tuvo (`ASOCIACIÓN INCLUDD → ASOCIACION INCLUDD → ASOCIACIÓN INCLUDD`). En `grandesbeneficiarios-busqueda`, tres descargas en cuatro minutos dieron los 148.170 nombres idénticos, pero entre las 00:03 y las 15:20 del mismo día cambiaron 79.000: apunta a una reagregación periódica en origen, no a azar por petición. El nombre probablemente se compone a partir de los registros subyacentes, donde cada órgano lo tecleó a su modo.

<a id="shuffled-lists"></a>
### Listas barajadas dentro de una cadena

`sectorActividad` en `minimis-busqueda` (separado por `;`) y `sectores` en `ayudasestado-busqueda` (separado por `#`) traen varios valores concatenados en un orden que cambia entre llamadas, con los mismos elementos:

```
'52.3 - Intermediación del transporte; 52.2 - Auxiliares del transporte'
'52.2 - Auxiliares del transporte; 52.3 - Intermediación del transporte'
```

Ojo al partir: en `minimis` varias descripciones CNAE llevan un `;` propio ("Administración Pública y defensa; Seguridad Social obligatoria"), así que partir por cada `;` corta 374 de 15.931 elementos por la mitad. Hay que partir antes del inicio de cada elemento (un código seguido de guion). En `ayudasestado`, el `#` sí es inequívoco.

<a id="intermittent-fields"></a>
### Campos que dejan de venir y vuelven

Un campo que normalmente trae valor vuelve `null` en una llamada y con valor en la siguiente. Medido sobre 3.000 pares de versiones de `convocatorias` y otros tantos del resto:

| Endpoint | Campo | `null→valor` | `valor→null` | % de pares |
|---|---|---|---|---|
| `convocatorias` | `fechaInicioSolicitud` | 209 | 55 | 8,8% |
| `convocatorias` | `fechaFinSolicitud` | 123 | 61 | 6,1% |
| `convocatorias` | `textInicio` | 40 | 47 | 2,9% |
| `convocatorias` | `textFin` | 48 | 32 | 2,7% |
| `convocatorias-busqueda` | `descripcionLeng` | 18 | 17 | 6,4% |
| `convocatorias` | `descripcionLeng` | 13 | 14 | 0,9% |
| `convocatorias` | `sedeElectronica` | 6 | 7 | 0,4% |
| `minimis-busqueda` | `sectorActividad` | 23 | 40 | 2,1% |

Los repartos simétricos delatan que no es información completándose. Y los nulos llegan en bloque: 54 pares pierden a la vez `fechaInicioSolicitud` y `fechaFinSolicitud`, y 25 `textInicio` y `textFin`. Es el bloque entero del plazo de solicitud desapareciendo y volviendo, lo que apunta a respuestas parciales del backend en el endpoint de detalle. Un campo que normalmente viene relleno **puede llegar `null`**.

### Lo que no está afectado

`convocatorias` y `convocatorias-busqueda` no tienen ruido de nombres ni de listas: sus cambios son administrativos de verdad (presupuestos que suben, plazos que se amplían, documentos que se añaden, órganos que se reorganizan). El problema es de cómo se compone la respuesta en unos endpoints concretos, no de la API en general.

### Cómo se midió

Sobre pares (versión anterior, versión nueva) del mismo registro:

- **Formato**: normalizar los dos payloads a NFD, quitar diacríticos y todo lo que no sea alfanumérico, y comparar.
- **Reordenamiento**: partir el campo por su separador, ordenar los trozos, volver a unirlos y comparar.

La primera no detecta la segunda, porque barajar una lista cambia la secuencia de caracteres.
