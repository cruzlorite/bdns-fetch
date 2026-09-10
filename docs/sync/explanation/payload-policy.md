# Qué se guarda y qué cuenta como un cambio

Cada registro que llega de la API pasa por dos preguntas antes de
almacenarse, y son preguntas distintas:

1. **¿Qué se guarda?** El payload que acabará en la tabla.
2. **¿Qué cuenta como un cambio?** Lo que decide si se abre una versión
   nueva o si solo se refresca la marca de última visita.

Una `PayloadPolicy` es la respuesta a las dos para una entidad concreta.
Toda la dificultad del módulo está en que las dos respuestas no son
simétricas: se pueden desacoplar en un sentido y no en el otro.

## El invariante

> Un hash distinto implica siempre un payload almacenado distinto.
> Nunca al revés.

Leído de izquierda a derecha: si el motor abrió una versión nueva, hay
algo visible en la tabla que cambió. Quien consulte el histórico puede
ver qué fue.

Leído de derecha a izquierda, la implicación **no** se sostiene, y es
deliberado: dos payloads almacenados distintos pueden compartir hash.
Eso es exactamente lo que hacen las reglas de solo-hash, y es la parte
segura.

## Por qué el orden importa

Las reglas se aplican en un orden fijo, y `prepare` es la única forma de
usarlas. No es comodidad de API: es lo que impide emparejarlas mal.

Supón que se hace al revés — descartar un campo del payload almacenado,
pero calcular el hash sobre el registro **tal como llegó**. Entonces un
cambio en el campo descartado abre una versión nueva cuyo payload
almacenado es idéntico byte a byte al de la versión que acaba de cerrar.

El histórico afirma que hubo un cambio que nadie podrá ver nunca, porque
la prueba se descartó a propósito. No es un fallo recuperable: la
información que justificaba la versión no existe en ninguna parte.

Por eso `prepare` devuelve el payload y su hash juntos, en una sola
llamada. Exponer los dos pasos por separado dejaría al alcance de quien
llama la única combinación que produce un histórico ilegible.

## Por qué las reglas de solo-hash sí son seguras

`hash_exclude`, `delimited_lists` y `canonical_arrays` van en el sentido
contrario: hacen el hash **más grueso** que lo almacenado.

Declaran que dos payloads que solo difieren en el orden de un array, o
en una lista barajada dentro de una cadena, o en un campo que se midió
como inestable, son el mismo registro. Se niegan a reportar una
diferencia que se sabe que es ruido. Nunca inventan una.

El payload se guarda entero, tal cual llegó. Si mañana resulta que la
regla estaba mal, el dato sigue ahí: se cambia la regla y se vuelve a
versionar desde el siguiente run. Lo que se pierde es granularidad de
histórico durante el periodo en que la regla estuvo activa, no el dato.

Ese es el criterio para aceptar una regla de solo-hash: **su coste, si
resulta equivocada, es recuperable**. El de una regla de almacenamiento
no lo es.

Qué reglas están declaradas hoy, para qué entidad, y qué se midió para
justificar cada una, está en
[el comportamiento de la API](bdns-api-behavior.md#spurious-changes).
Ninguna es una preferencia; todas son un hallazgo.

## La identidad no es política

Dos cosas quedan fuera del alcance de cualquier política: los campos que
forman la clave natural, y el campo de fecha de registro.

Deciden qué **es** un registro y qué enlaza sus versiones a lo largo del
tiempo. `check_identity` rechaza una política que intente descartarlos.

La asimetría de coste lo explica:

- Cambiar una regla de hash cuesta almacenamiento y ruido. Molesto,
  reversible.
- Cambiar la identidad corta el pasado de un registro de su futuro. Las
  versiones viejas quedan colgando de una clave que ya no existe, y las
  nuevas empiezan de cero. Nada lo recupera.

Sin la clave natural un registro no se puede versionar en absoluto. Sin
su fecha de registro, un run por ventana no puede distinguir una baja
real de una fila que simplemente salió de la ventana — la distinción
está en
[la detección de bajas](bdns-api-behavior.md#windowed-deletions).

## Dónde vive esto en el código

- `bdns.sync.policy` — `PayloadPolicy`, `prepare`, `check_identity`.
- `bdns.sync.hashing` — el JSON canónico y las normalizaciones.
- `bdns.sync.syncers` — el mapa `POLICIES`, una entrada por entidad.
