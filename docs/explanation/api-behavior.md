# Comportamiento de la API

En esta página está recogido cómo se comporta de verdad la API de la BDNS, comprobado contra el servicio real. Nada de esto aparece en la [documentación oficial](https://www.infosubvenciones.es/bdnstrans/api), o aparece de otra manera, y si no se tiene en cuenta se pierden o se duplican datos sin que nadie se entere.

Cada afirmación va acompañada de la prueba en la que se basa. Casi todas se hicieron mientras se desarrollaba [`bdns-sync`](https://cruzlorite.github.io/bdns-sync/), que descarga la API entera todos los días, pero están aquí porque hablan de la API y no de cómo se guardan los datos. Lo que `bdns-sync` hace con cada una lo explica su propia documentación.

<a id="upper-bound"></a>
## Las dos familias de fechas no tratan igual el último día

La API tiene dos familias de parámetros de fecha, y cada una trata el último día del rango justo al revés que la otra:

| Familia | Parámetros | Endpoints | ¿Incluye el último día? | Comprobación (día `D`) |
|---|---|---|---|---|
| Fecha de registro | `fechaRegInicio` / `fechaRegFin` | `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda` | **No** | Con `fechaRegFin=D` apenas llega nada del día `D`; con `fechaRegFin=D+1` llega entero (en `concesiones`, 1 fila frente a 58.488) |
| Periodo | `fechaDesde` / `fechaHasta` | el resto de búsquedas, entre ellas `convocatorias-busqueda` | **Sí** | Con `fechaHasta=D` llegan todas las convocatorias con `fechaRecepcion` igual a `D`; con `fechaHasta=D+1` llegan las de `D` y `D+1` |

Equivocarse sale caro. Si no se suma un día a `fechaRegFin`, una consulta de un solo día no devuelve prácticamente nada y cualquier rango más largo pierde su último día. Y si además el rango se divide en tramos, se pierde un día en cada corte: un rango de 28 días dividido en días sueltos devolvió 8 filas en lugar de cerca de 1,2 millones.

`bdns-fetch` deja los parámetros tal y como los define la API, pero te da [`registration_range`][bdns.fetch.dates.registration_range] y [`period_range`][bdns.fetch.dates.period_range], que reciben un rango con los dos extremos incluidos y devuelven los parámetros correctos para cada familia.

<a id="range-reliability"></a>
## Los rangos largos fallan y los semanales no

Lo comprobamos con `concesiones-busqueda`:

- **Fiabilidad.** Un rango de cuatro años (27,4 millones de filas) devuelve `ERR_MANTENIMIENTO_BBDD` de vez en cuando, en cualquier página. Las mismas fechas pedidas semana a semana no fallaron ni una vez en seis intentos, y un rango de siete días trajo 147.856 filas sin un solo error.
- **Velocidad.** Un rango de 30 días pedido de una vez tardó 286,7 segundos; dividido en semanas, 142,5. Ninguno de los dos dio errores.

El tamaño exacto del tramo no es crítico. Con un rango fijo de 14 días (unas 530.000 filas), los tramos de 1, 3, 7 y 14 días tardaron 51, 41, 47 y 57 segundos, diferencias que entran dentro de lo que varía la carga del servicio. Siete días es un buen término medio y es lo que usa [`split_range`][bdns.fetch.dates.split_range] por defecto ([`MAX_RANGE_DAYS`][bdns.fetch.dates.MAX_RANGE_DAYS]).

El resultado tampoco depende del tamaño del tramo, siempre que en cada uno se trate bien el último día: un rango de 14 días de `partidospoliticos-busqueda` devuelve las mismas 36 filas dividido en tramos de 1, 7 o 14 días.

<a id="boundary-check"></a>
## Dos días seguidos no comparten registros ni dejan huecos

Para descartar tanto que se cuele un día de más como que se pierda uno, comprobamos en las cinco búsquedas incrementales que dos días seguidos `X` y `X+1`, pedidos con el extremo correcto en cada familia, cumplen dos condiciones:

1. no tienen ningún registro en común;
2. juntos dan exactamente lo mismo que la consulta de `[X, X+1]`.

Las cuentas cuadran fila a fila: en `concesiones`, 115.862 + 68.457 = 184.319, sin ningún registro repetido.

Estas dos condiciones, junto con el comportamiento de cada extremo, son lo que comprueba [`check_api_contract`][bdns.fetch.contract.check_api_contract] (`bdns-fetch check-api`) contra el servicio real. Los tests solo pueden comprobar la idea que nosotros tenemos de la API; esta comprobación es la que avisa si la API cambia.

<a id="rate-limit"></a>
## El límite de peticiones no admite ráfagas

El límite oficial es de 10 peticiones por segundo y por IP. Pero además el servidor responde con un `429` cuando varias peticiones **empiezan a la vez**, aunque la media quede por debajo del límite: diez hilos que solo respetaban la media dejaron de funcionar en cuestión de segundos. En cambio, con las peticiones espaciadas (una cada 100 milisegundos), el mismo servidor aguantó 9,8 peticiones por segundo de forma continuada.

Por eso el limitador de `bdns-fetch` ([`RateLimiter`][bdns.fetch.utils.RateLimiter]) espacia las peticiones en lugar de permitir ráfagas y, por defecto, deja algo de margen: 9,5 por segundo, una cada 105 milisegundos aproximadamente. El límite es por IP, así que si lanzas varios procesos desde la misma máquina tendrás que repartirlo entre ellos con `--rate-limit`.

Las buenas prácticas oficiales piden también no hacer llamadas en paralelo, y por eso `bdns-fetch` hace una cada vez salvo que le indiques lo contrario con `--max-workers`.

<a id="latency"></a>
## El tiempo de respuesta depende mucho de la carga

Una llamada sencilla, como pedir el detalle de una convocatoria, tarda unos 0,22 segundos cuando el servidor va bien y alrededor de 1,9 cuando va cargado. Un mismo lote de 6.186 detalles (mayo de 2026) tardó entre 23 minutos y 3 horas y 12 minutos haciendo las llamadas una detrás de otra; con ocho hilos y las peticiones espaciadas tardó 10 minutos y 54 segundos, sin un solo `429`.

<a id="history-depth"></a>
## Cada endpoint guarda un histórico distinto

Hasta dónde llegan los datos depende del periodo de visualización de cada endpoint:

| Endpoint | Datos disponibles | Por qué |
|---|---|---|
| `concesiones-busqueda` | unos 4 años | se publican durante los cuatro años naturales siguientes a la concesión |
| `partidospoliticos-busqueda` | unos 4 años | sigue el mismo criterio que las concesiones |
| `ayudasestado-busqueda` | entre 9 y 10 años | la normativa europea obliga a 10 años |
| `minimis-busqueda` | unos 10 años | la normativa europea obliga a 10 años |
| `convocatorias-busqueda`, `convocatorias` | unos 12 años | el portal empezó a funcionar hacia 2014 |

Pedir fechas anteriores no da error, simplemente devuelve semanas vacías, y cada una cuesta una sola llamada.

<a id="api-issues"></a>
## Problemas conocidos

- **Registros sueltos que llegan mal.** A veces el servidor falla con un registro concreto y devuelve una página de error en HTML en lugar de JSON. No tiene que ver con el límite de peticiones ni con los parámetros, porque las llamadas de justo antes y justo después funcionan. En `planesestrategicos`, entre el 8 de julio y el 30 de agosto de 2026, los mismos 10 `idPES` fallaron en las 57 ejecuciones; el 30 de agosto fallaron 114 de 2.029. Un registro roto suele seguir roto, pero el conjunto va cambiando.
- **Errores dentro de una respuesta 200.** Algunos errores llegan con estado 200 y un cuerpo del tipo `{"codigo": ..., "error": ...}`. `bdns-fetch` los trata como errores.
- **`ERR_MANTENIMIENTO_BBDD` en rangos largos.** Explicado [más arriba](#range-reliability). `bdns-fetch` lo considera un fallo pasajero y lo reintenta.
- **Las fechas no se comportan igual en todos los endpoints.** `fechaRegFin` no incluye el último día y `fechaHasta` sí, y la documentación oficial no lo dice. Explicado [más arriba](#upper-bound).
- **`partidospoliticos-busqueda` no trae fecha de registro.** Su respuesta no incluye ningún campo con la fecha de registro, aunque la documentación oficial diga que funciona igual que `concesiones-busqueda`. Lo comprobamos con más de 70 filas reales de dos rangos de fechas distintos.
- **Listas anidadas que cambian de orden.** `regiones` devuelve el mismo árbol con los `children` en distinto orden de una llamada a otra, sin que haya cambiado ningún dato.
- **Paginación inestable en fechas recientes.** La paginación funciona por posición (offset). Si entran registros nuevos mientras se recorre un rango reciente, una fila cercana al final de una página puede aparecer también en la siguiente. Con fechas ya cerradas la paginación es estable.
- **`terceros` no aporta nada.** Las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) desaconsejan usarlo, porque `concesiones-busqueda` ya trae los datos del beneficiario.

<a id="spurious-changes"></a>
## El mismo dato, escrito de otra manera

De una llamada a otra, la API puede devolver un registro idéntico pero escrito de otra forma. No ha habido ninguna corrección administrativa; solo ha cambiado la manera en que se ha montado la respuesta. Si guardas histórico (como hace `bdns-sync`), cada uno de estos casos genera una versión falsa: en la pasada anual de `bdns-sync` del 1 de septiembre de 2026, el 60% de las versiones nuevas eran de este tipo. Hay tres casos distintos.

<a id="unstable-names"></a>
### Nombres que cambian de grafía

El campo `beneficiario` de `concesiones-busqueda` y de `grandesbeneficiarios-busqueda` llega escrito de distinta forma para el mismo beneficiario, con el mismo importe y el mismo identificador:

```
GONZALEZ                      →  GONZÁLEZ            (con y sin tilde, en los dos sentidos)
REMEDIOS BENITEZ BASILIO .    →  REMEDIOS BENITEZ BASILIO . .
MONTSERRAT LOPEZ REYNOSO MECA →  MONTSERRAT LOPEZ-REYNOSO MECA
LIMMAT M&M, S.L.              →  LIMMAT MM SL        (seis variantes en once días)
```

En `concesiones-busqueda`, los 230.878 cambios de `beneficiario` mantienen **el mismo `idPersona` en el 100% de los casos**, y 213.176 son idénticos una vez quitadas las tildes y los signos de puntuación. Además, el valor **va y vuelve**: recupera grafías que ya había tenido (`ASOCIACIÓN INCLUDD → ASOCIACION INCLUDD → ASOCIACIÓN INCLUDD`). En `grandesbeneficiarios-busqueda`, tres descargas en cuatro minutos devolvieron los 148.170 nombres idénticos, pero entre las 00:03 y las 15:20 del mismo día cambiaron 79.000, lo que apunta a un recálculo periódico en origen y no a algo aleatorio en cada petición. Lo más probable es que el nombre se construya a partir de los registros de concesión, donde cada órgano lo escribió a su manera.

<a id="shuffled-lists"></a>
### Listas que cambian de orden dentro de un texto

`sectorActividad` en `minimis-busqueda` (separado por `;`) y `sectores` en `ayudasestado-busqueda` (separado por `#`) contienen varios valores en un mismo texto, y su orden cambia de una llamada a otra aunque los elementos sean los mismos:

```
'52.3 - Intermediación del transporte; 52.2 - Auxiliares del transporte'
'52.2 - Auxiliares del transporte; 52.3 - Intermediación del transporte'
```

Cuidado al separarlos: en `minimis` hay descripciones de la CNAE que llevan su propio `;` ("Administración Pública y defensa; Seguridad Social obligatoria"), y cortar en cada `;` parte por la mitad 374 de 15.931 elementos. Hay que cortar justo antes de donde empieza cada elemento (un código seguido de un guion). En `ayudasestado` el `#` no da problemas.

<a id="intermittent-fields"></a>
### Campos que desaparecen y vuelven

Un campo que normalmente trae valor llega vacío (`null`) en una llamada y vuelve a tener valor en la siguiente. Lo medimos sobre 3.000 parejas de versiones de `convocatorias` y otras tantas del resto:

| Endpoint | Campo | `null→valor` | `valor→null` | % de parejas |
|---|---|---|---|---|
| `convocatorias` | `fechaInicioSolicitud` | 209 | 55 | 8,8% |
| `convocatorias` | `fechaFinSolicitud` | 123 | 61 | 6,1% |
| `convocatorias` | `textInicio` | 40 | 47 | 2,9% |
| `convocatorias` | `textFin` | 48 | 32 | 2,7% |
| `convocatorias-busqueda` | `descripcionLeng` | 18 | 17 | 6,4% |
| `convocatorias` | `descripcionLeng` | 13 | 14 | 0,9% |
| `convocatorias` | `sedeElectronica` | 6 | 7 | 0,4% |
| `minimis-busqueda` | `sectorActividad` | 23 | 40 | 2,1% |

Que las cifras sean tan parecidas en los dos sentidos indica que no se trata de información que se va completando. Además, los vacíos llegan juntos: en 54 parejas desaparecen a la vez `fechaInicioSolicitud` y `fechaFinSolicitud`, y en 25 lo hacen `textInicio` y `textFin`. Es el bloque entero del plazo de solicitud el que desaparece y vuelve, lo que hace pensar en respuestas incompletas del servidor en el endpoint de detalle. Ten en cuenta, por tanto, que un campo que normalmente viene relleno **puede llegar vacío**.

### Lo que no se ve afectado

`convocatorias` y `convocatorias-busqueda` no tienen este problema con los nombres ni con las listas: sus cambios son administrativos de verdad (presupuestos que suben, plazos que se amplían, documentos que se añaden, órganos que se reorganizan). El problema está en cómo se montan las respuestas de unos endpoints concretos, no en la API en general.

### Cómo lo medimos

Sobre parejas formadas por la versión anterior y la nueva de un mismo registro:

- **Cambios de escritura**: se normalizan los dos registros a NFD, se quitan las tildes y todo lo que no sea letra o número, y se comparan.
- **Cambios de orden**: se separa el campo por su separador, se ordenan los trozos, se vuelven a unir y se comparan.

La primera prueba no detecta la segunda, porque cambiar el orden de una lista cambia la secuencia de caracteres.
