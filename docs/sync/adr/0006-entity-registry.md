# 0006. Un registro único de entidades

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Hay 22 entidades. De cada una hay que saber lo mismo: cómo se descargan
sus filas, qué campos forman la clave natural, si cada ejecución cubre la
entidad entera o una ventana de fechas, qué reglas de payload le
aplican y desde cuándo merece la pena cargar su histórico.

Si ese conocimiento se reparte (una función por entidad, un diccionario
de políticas, otro de entidades completas, otro de entidades por ventana,
listas escritas a mano en los scripts y en la documentación), cada nueva
entidad hay que añadirla en cinco sitios, y una errata en uno de ellos no
falla: una política con el nombre mal escrito se ignora en silencio y la
entidad empieza a versionar ruido.

## Decisión

Cada entidad se declara **una vez**, como un
[`Entity`][bdns.sync.entities.Entity] en
[`ENTITIES`][bdns.sync.entities.ENTITIES]: nombre, tipo (`full` o
`windowed`), clave natural, origen de filas, campo de fecha de registro,
política e inicio del histórico. Los orígenes de filas son pocos y
reutilizables (catálogo, barrido de un parámetro, ventana por fecha de
registro, ventana por periodo, descubrimiento y detalle).

Todo lo demás lee ese registro: [`sync_entity`][bdns.sync.entities.sync_entity],
los planes `delta` y `backfill`, `bdns-sync list`, `--dry-run` y los
tests.

## Consecuencias

- Una entidad nueva es una entrada en una tabla.
- No hay listas que puedan divergir: la política que imprime `--dry-run`
  es la que aplica la ejecución, y las entidades que sincroniza `delta`
  son las que muestra `list`.
- Las mediciones que justifican cada regla quedan junto a la entrada a la
  que aplican.
- Una entidad con lógica propia de verdad sigue siendo posible: su origen
  de filas es una función más.
