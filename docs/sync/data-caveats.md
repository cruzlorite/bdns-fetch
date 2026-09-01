# Notas para consumir los datos

Cosas que conviene tener en cuenta al leer las tablas sincronizadas. Todas vienen del comportamiento de la API de origen (ver [`bdns-api-behavior.md`](bdns-api-behavior.md)), no de un fallo de `bdns-sync`.

## `_reg_date` en el borde del día

`_reg_date` guarda la fecha de registro que trae el propio payload (`fechaAlta`, `fechaRegistro` o `fechaRecepcion`, según la entidad). Un registro cuya fecha de alta cae justo a medianoche puede acabar asignado al día siguiente.

Qué implica para quien consulta los datos: si comparas recuentos diarios contra una consulta directa a la API, cuenta con diferencias de ±1 registro en los bordes del día. El dato ni falta ni está duplicado; simplemente cae en un día o en otro según cómo trate cada extremo la medianoche. Para evitarlo, compara por rangos de varios días en lugar de día a día.

## Duplicados residuales en cargas históricas

La API pagina por offset. Si a una ventana de fechas le entran altas nuevas **mientras se está paginando** (algo que solo pasa en fechas recientes), una fila que quede cerca del borde de una página puede venir en dos páginas seguidas. `bdns-sync` deduplica al insertar, así que las sincronizaciones incrementales normales no dejan duplicados. Una carga histórica masiva, hecha de una sola pasada larga, sí puede dejar algún par duplicado en casos raros.

Un duplicado residual son **dos filas `_is_current` con la misma `_natural_key` e idénticas byte a byte** (mismo `_row_hash` y mismo payload). No corrompe nada, pero infla los recuentos y puede duplicar filas en un `JOIN`.

Para detectarlos:

```sql
SELECT _natural_key, COUNT(*) AS n
FROM tu_tabla
WHERE _is_current
GROUP BY _natural_key
HAVING COUNT(*) > 1;
```

Para eliminarlos, quedándote con una copia de cada clave (el payload es idéntico entre copias, así que da igual cuál):

```sql
CREATE TABLE _dedup AS
SELECT DISTINCT * FROM tu_tabla
WHERE _natural_key IN ( /* claves detectadas arriba */ ) AND _is_current;

DELETE FROM tu_tabla
WHERE _natural_key IN ( /* las mismas claves */ ) AND _is_current;

INSERT INTO tu_tabla SELECT * FROM _dedup;
DROP TABLE _dedup;
```

Esto solo puede afectar a fechas que estaban recibiendo altas durante la carga, es decir, a las recientes. Las fechas históricas ya cerradas no reciben escrituras a la vez, su paginación es estable y no pueden contener duplicados.

## Bajas por caducidad frente a retiradas reales

`_valid_from` y `_valid_to` registran cuándo **observó** `bdns-sync` una versión, no cuándo ocurrió el hecho en el mundo real. Una fila se cierra cuando deja de venir del origen, y eso pasa por dos motivos muy distintos que en la tabla se ven idénticos:

- **Retirada real**: el órgano concedente eliminó o rehizo el registro.
- **Caducidad**: la ayuda cumplió el plazo de publicación y salió de la BDNS. En `concesiones_busqueda` son los 4 años naturales siguientes a la concesión; en `ayudasestado_busqueda` y `minimis_busqueda`, 10 años.

La caducidad es determinista, así que se distinguen con una regla, no con una estimación: compara el año de `fechaConcesion` con el de `_valid_to`.

```sql
SELECT
  CASE WHEN EXTRACT(YEAR FROM _valid_to)
            - CAST(SUBSTR(JSON_VALUE(payload,'$.fechaConcesion'),1,4) AS INT64) > 4
       THEN 'caducidad' ELSE 'retirada real' END AS motivo,
  COUNT(*)
FROM tu_tabla
WHERE _valid_to IS NOT NULL AND NOT _is_current
GROUP BY motivo;
```

Dos cosas que **no** sirven para distinguirlas. Que la baja llegue en bloque no dice nada: las retiradas reales también vienen a tandas, porque un órgano corrige muchos registros de golpe (medido en agosto de 2026: bloques de 5.420 y 2.032 bajas en un solo día, mezclando cuatro y cinco años de concesión distintos). Y la duración de la versión tampoco: mide el tiempo desde la última edición, no la antigüedad del registro, así que una concesión vieja editada hace poco tiene una versión joven.

### Cuándo aparecen las caducidades

La cadencia normal apenas las ve. La ventana anual alcanza 365 días de fecha de registro, así que solo entran en su ámbito las filas registradas hace menos de un año; una concesión antigua registrada hace poco sí se cerrará al caducar, pero es un goteo.

Un **backfill ancho es otra cosa**: su ámbito de comparación es todo el rango pedido, así que cierra de una vez todo lo caducado, con la fecha del día en que se lanzó. Volver a lanzar [`scripts/full_load.sh`](../scripts/full_load.sh) sobre un destino ya poblado produce exactamente eso. En septiembre de 2026, con 1,13 millones de concesiones de 2022 almacenadas y a punto de cumplir plazo, un backfill lanzado en 2027 las cerraría todas juntas.

No es un fallo: el registro ya no está en el origen y la tabla lo refleja. Pero conviene saber que esa fecha de cierre dice cuándo te enteraste, no cuándo caducó.
