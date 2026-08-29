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
