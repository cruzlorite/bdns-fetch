# Qué se guarda y qué cuenta como un cambio

Antes de guardar un registro que llega de la API hay que responder a dos preguntas distintas:

1. **¿Qué se guarda?** Es decir, el contenido que acabará en la tabla.
2. **¿Qué cuenta como un cambio?** Es decir, qué hace que se cree una versión nueva en lugar de limitarse a anotar que el registro se ha vuelto a ver.

Una [`PayloadPolicy`][bdns.sync.policy.PayloadPolicy] responde a las dos preguntas para cada entidad. Lo difícil es que las dos respuestas no se pueden separar de cualquier manera: en un sentido sí, pero en el otro no.

## La regla que no se puede romper

> Si el hash es distinto, lo guardado también tiene que ser distinto.
> Al revés no hace falta.

Leída en un sentido, la regla garantiza que si el motor crea una versión nueva, en la tabla hay algo visible que ha cambiado, y quien consulte el histórico puede ver qué fue.

En el otro sentido no se cumple, y es intencionado: dos registros guardados distintos pueden tener el mismo hash. Eso es justo lo que hacen las reglas que solo afectan al hash, y es la parte que no entraña riesgo.

## Por qué importa el orden

Las reglas se aplican siempre en el mismo orden, y [`prepare`][bdns.sync.policy.PayloadPolicy.prepare] es la única forma de usarlas. No es por comodidad: es lo que impide combinarlas mal.

Imagina que se hiciera al revés, es decir, que se quitara un campo de lo que se guarda pero el hash se calculara sobre el registro **tal y como llegó**. Entonces un cambio en ese campo crearía una versión nueva con un contenido guardado idéntico, byte a byte, al de la versión que acaba de cerrarse.

El histórico diría que hubo un cambio que nadie podrá ver nunca, porque la prueba se descartó a propósito. Y no tendría arreglo, porque la información que justificaba esa versión ya no existe en ninguna parte.

Por eso [`prepare`][bdns.sync.policy.PayloadPolicy.prepare] devuelve el contenido y su hash a la vez, en una sola llamada. Si los dos pasos se pudieran hacer por separado, quien los usara tendría a mano justo la combinación que produce un histórico imposible de leer.

## Por qué las reglas que solo afectan al hash no entrañan riesgo

`hash_exclude`, `delimited_lists` y `canonical_arrays` funcionan en el sentido contrario: hacen que el hash sea **menos estricto** que lo que se guarda.

Lo que dicen es que dos registros que solo se diferencian en el orden de una lista, en el orden de los elementos dentro de un texto o en un campo que se ha comprobado que cambia sin motivo, son el mismo registro. Se niegan a dar por cambio algo que se sabe que es ruido, pero nunca se inventan un cambio.

El registro se guarda entero, tal y como llegó. Si mañana resulta que una regla estaba mal, el dato sigue ahí: se cambia la regla y se vuelve a versionar a partir de la siguiente ejecución. Lo que se pierde es detalle en el histórico durante el tiempo en que la regla estuvo activa, no el dato en sí.

Ese es el criterio para aceptar una regla que solo afecta al hash: **si resulta equivocada, el daño tiene arreglo**. El de una regla que cambia lo que se guarda no lo tiene.

Qué reglas hay declaradas hoy, para qué entidades y qué mediciones las justifican lo tienes en [cambios espurios](sync-behavior.md#spurious-changes). Ninguna responde a una preferencia; todas salen de algo que se ha medido.

## La identidad no forma parte de la política

Hay dos cosas que ninguna política puede tocar: los campos que forman la clave natural y el campo con la fecha de registro.

Son los que deciden qué **es** un registro y los que enlazan sus versiones a lo largo del tiempo, y [`check_identity`][bdns.sync.policy.PayloadPolicy.check_identity] rechaza cualquier política que intente quitarlos.

La diferencia de coste lo explica:

- Cambiar una regla de hash cuesta espacio y algo de ruido. Es molesto, pero tiene vuelta atrás.
- Cambiar la identidad separa el pasado de un registro de su futuro. Las versiones antiguas se quedan colgando de una clave que ya no existe y las nuevas empiezan de cero, y no hay forma de recuperarlo.

Sin clave natural, un registro no se puede versionar. Y sin su fecha de registro, una ejecución incremental no puede distinguir una baja de verdad de una fila que simplemente ha quedado fuera del periodo; lo explicamos en [detección de bajas por periodo](sync-behavior.md#windowed-deletions).

## Dónde está en el código

- [`bdns.sync.policy`][bdns.sync.policy]: [`PayloadPolicy`][bdns.sync.policy.PayloadPolicy], [`prepare`][bdns.sync.policy.PayloadPolicy.prepare] y [`check_identity`][bdns.sync.policy.PayloadPolicy.check_identity].
- [`bdns.sync.hashing`][bdns.sync.hashing]: el JSON canónico y las normalizaciones.
- [`bdns.sync.entities`][bdns.sync.entities]: la política de cada entidad, junto a su definición en el registro.
