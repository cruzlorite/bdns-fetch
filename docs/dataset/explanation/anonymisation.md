# Cómo se protege a las personas físicas

El dataset no contiene ningún dato personal. Puede identificar a empresas y entidades públicas, pero nunca a una persona física, y en esta página se explica cómo se consigue, con ejemplos. El porqué, con el marco legal y las alternativas que se descartaron, está en la [decisión de diseño](../../adr/0020-anonymised-dataset.md).

<a id="who"></a>
## Qué beneficiarios se protegen

Cada beneficiario se clasifica a partir del NIF que va al principio del campo `beneficiario`, nunca a partir de su nombre, porque una empresa puede llamarse como una persona y al revés. Lo que no se reconoce se trata como una persona física. Por ejemplo (los nombres y los NIF son inventados):

| Cómo aparece en la BDNS | `tipo_persona` | En el dataset |
|---|---|---|
| `***1234** NOMBRE APELLIDOS` | `persona_fisica` | Solo en el resumen |
| `12345678Z NOMBRE APELLIDOS` | `persona_fisica` | Solo en el resumen |
| `E12345678 APELLIDO Y APELLIDO CB` | `comunidad_o_sociedad_civil` | Solo en el resumen |
| `123456789012 FOREIGN COMPANY LTD` | `desconocido` | Solo en el resumen |
| `B12345678 EMPRESA DE EJEMPLO SL` | `persona_juridica` | Registro a registro |
| `P1234567D AYUNTAMIENTO DE EJEMPLO` | `entidad_publica` | Registro a registro |

Las comunidades de bienes y las sociedades civiles tienen NIF propio, pero suelen llevar el nombre de sus miembros, y por eso se protegen igual que una persona física.

Las empresas y entidades públicas se publican registro a registro, con su NIF y su nombre, porque no son datos personales. Aun así, de sus concesiones se quitan dos campos: `urlBR`, porque el boletín al que enlaza suele nombrar también a personas físicas, e `idPersona`, que no añade nada que no diga ya el NIF.

<a id="summary"></a>
## Qué se publica de una convocatoria

De las concesiones a beneficiarios protegidos solo se publica un resumen por convocatoria (y por instrumento, si la convocatoria usa varios). Imagina una convocatoria con estas 12 concesiones, que son de 11 personas porque una de ellas recibió dos:

| Importe | Concesiones | Fecha de concesión |
|---:|---:|---|
| 300 € | 4 | 12/03/2026 |
| 450 € | 3 | 20/04/2026 |
| 600 € | 3 | dos el 20/04/2026 y una el 05/06/2026 |
| 900 € | 1 | 05/06/2026 |
| 1.200 € | 1 | 05/06/2026 |

Su fila en `concesiones_personas` sería esta:

| Columna | Valor |
|---|---|
| `concesiones` | 12 |
| `beneficiarios` | 11 |
| `importe_total` | 6.450,00 |
| `importe_media` | 537,50 |
| `importe_desviacion` | 274,79 |
| `importe_p25`, `importe_mediana`, `importe_p75` | 300,00, 450,00 y 600,00 |
| `fecha_p25`, `fecha_mediana`, `fecha_p75` | 2026-03-12, 2026-04-20 y 2026-04-20 |
| `importe_p10`, `importe_p90`, `fecha_p10`, `fecha_p90` | Vacíos, porque son menos de 20 personas |

Con ella puedes saber cuánto repartió la convocatoria, cuánto fue una concesión típica y cuándo se concedieron, pero no quién recibió qué. Tampoco aparecen los 1.200 euros de la concesión más alta, que son de una persona concreta.

<a id="rules"></a>
## Las reglas

**Cada fila junta al menos a 10 personas.** Con pocas personas, un resumen deja adivinar lo que recibió cada una. Con dos, por ejemplo, quien sepa lo que recibió una conoce lo de la otra restándolo del total.

**Ninguna persona tiene más de la mitad del importe de su fila.** Si una persona se lleva casi todo, el total es prácticamente su importe, aunque la fila junte a muchas más. Con 14 concesiones de 100 euros y una de 10.000, el total (11.400 euros) le dice a cualquiera que conozca la convocatoria cuánto recibió esa persona.

**El mínimo y el máximo no se publican nunca, y los percentiles 10 y 90, solo desde 20 personas.** El importe más alto es el de una persona concreta, y lo mismo pasa con el más bajo y con las fechas de los extremos. Los percentiles 10 y 90 quedan muy cerca de ellos: en el ejemplo de arriba, el percentil 90 serían 870 euros, muy cerca de la segunda concesión más alta (900 euros). Con al menos 20 personas, el percentil 10 ya no queda por debajo de la segunda concesión más pequeña, ni el 90 por encima de la segunda más grande.

**Las fechas son fechas reales.** Los percentiles de la fecha se eligen entre las fechas de concesión que existen, sin interpolar, porque un día a medio camino entre dos fechas no significa nada.

**Lo que no cumple va a la fila de resto de su año.** Las concesiones de las convocatorias que no se pueden publicar se juntan en una fila con `es_resto = true`, que no dice qué convocatorias reúne, y en `ejercicio` lleva el año de la fecha mediana de cada una de ellas. Esa fila tiene que cumplir las mismas reglas y, además, juntar al menos dos convocatorias, porque si fuera una sola, el resto sería esa convocatoria con otro nombre.

**Cada persona cuenta una vez.** Se reconoce por su identificador en la BDNS o, si falta, por el campo `beneficiario` completo, y ninguno de los dos sale del fichero privado.

Cada estadística cubre todas las concesiones de su fila, y ninguna otra tabla resume las mismas concesiones, así que no se puede averiguar nada restando una cosa de otra. Los umbrales están definidos una sola vez, en el SQL, y en la [referencia](../reference/build.md#thresholds) tienes sus valores.

<a id="checks"></a>
## Lo que se comprueba antes de publicar

Antes de escribir ningún fichero, la generación revisa lo que va a publicar y **se para** si encuentra:

- un beneficiario protegido en una tabla registro a registro;
- algo con forma de DNI, NIE o NIF enmascarado, en cualquier columna de cualquier tabla;
- una columna que identifica a alguien en el resumen, como `beneficiario`, `id_persona`, `url_br` o `cod_concesion`;
- una fila del resumen con menos de 10 personas, o con los percentiles 10 o 90 y menos de 20.

Lo que encuentra lo señala sin limpiarlo, porque un hallazgo así indica un error en un paso anterior, y limpiarlo sin avisar lo dejaría escondido detrás de un dataset que parece correcto. Los mensajes de cada control están en la [referencia](../reference/build.md#checks).

## Lo que el dataset no permite

- Seguir a una persona física a lo largo del tiempo, ni saber qué recibió una persona concreta. Es justo lo que se busca, aunque limite algunos análisis.
- Cuadrar al céntimo los totales de las personas físicas, porque falta lo que no llega a ninguna fila publicable.
- Leer el título de una convocatoria del resumen cuando contiene algo con forma de DNI, porque se publica vacío.
