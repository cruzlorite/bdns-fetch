# 0013. Un único registro de entidades

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Hay 22 entidades, y de cada una hay que saber lo mismo: cómo se descargan sus filas, qué campos forman la clave natural, si cada ejecución la descarga entera o solo un periodo de fechas, qué reglas se le aplican al calcular el hash y desde cuándo merece la pena cargar su histórico.

Si esa información está repartida en muchos sitios (una función por entidad, un diccionario con las reglas, otro con las entidades completas, otro con las incrementales, listas escritas a mano en los scripts y en la documentación), cada entidad nueva hay que añadirla en cinco lugares. Y una errata en uno de ellos no da ningún error: una regla con el nombre de la entidad mal escrito se ignora sin avisar, y la entidad empieza a crear versiones por cambios que no lo son.

## Decisión

Cada entidad se define **una sola vez**, como un [`Entity`][bdns.sync.entities.Entity] dentro de [`ENTITIES`][bdns.sync.entities.ENTITIES], con su nombre, su tipo (`full` o `windowed`), su clave natural, cómo se descargan sus filas, su campo de fecha de registro, sus reglas y la fecha desde la que empieza su histórico. Las formas de descargar las filas son pocas y se reutilizan (una sola llamada, recorrer un parámetro, por fecha de registro, por periodo, o primero el listado y después el detalle).

Todo lo demás lee de ese registro: [`sync_entity`][bdns.sync.entities.sync_entity], los planes de `delta` y `backfill`, `bdns-sync list`, `--dry-run` y los tests.

## Consecuencias

- Una entidad nueva es una entrada más en una tabla.
- No hay listas que puedan acabar siendo distintas: las reglas que muestra `--dry-run` son las que aplica la ejecución, y las entidades que sincroniza `delta` son las que muestra `list`.
- Las mediciones que justifican cada regla están junto a la entidad a la que se aplican.
- Si una entidad necesita una lógica realmente propia, se puede hacer: basta con escribir otra función que descargue sus filas.
