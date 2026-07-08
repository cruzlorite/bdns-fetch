# Notas para consumir los datos

Cosas que conviene tener en cuenta al leer las tablas sincronizadas. Todas derivan del comportamiento del API de origen (ver [`bdns-api-behavior.md`](bdns-api-behavior.md)), no de un fallo de `bdns-sync`.

## `_reg_date` en el borde del día

`_reg_date` guarda la fecha de registro propia del payload (`fechaAlta`, `fechaRegistro` o `fechaRecepcion`, según la entidad). Un registro cuya fecha de alta cae a medianoche exacta puede quedar asignado al día natural siguiente.

Impacto para el consumidor: si comparas recuentos por día contra una consulta directa al API, espera diferencias de ±1 registro en los bordes de día. El dato no falta ni está duplicado; solo cae en un día u otro según cómo cada extremo trate la medianoche. Para evitarlo, compara por rangos de varios días en lugar de día a día.

## Duplicados residuales en cargas históricas

El API pagina por offset. Si una ventana de fechas **recibe altas nuevas mientras se está paginando** (algo que solo ocurre en fechas recientes), una fila cercana al borde de una página puede devolverse en dos páginas consecutivas. `bdns-sync` deduplica en el momento de insertar, así que las sincronizaciones incrementales normales no dejan duplicados. Una carga histórica masiva en una sola pasada larga puede, en casos raros, dejar algún par duplicado.

Un duplicado residual son **dos filas `_is_current` con la misma `_natural_key` e idénticas byte a byte** (mismo `_row_hash`, mismo payload). No corrompe nada, pero infla recuentos y puede duplicar filas en un `JOIN`.

Detectarlos:

```sql
SELECT _natural_key, COUNT(*) AS n
FROM tu_tabla
WHERE _is_current
GROUP BY _natural_key
HAVING COUNT(*) > 1;
```

Eliminarlos (quedándose con una copia de cada clave; el payload es idéntico entre copias, así que no hay ambigüedad):

```sql
CREATE TABLE _dedup AS
SELECT DISTINCT * FROM tu_tabla
WHERE _natural_key IN ( /* claves detectadas arriba */ ) AND _is_current;

DELETE FROM tu_tabla
WHERE _natural_key IN ( /* las mismas claves */ ) AND _is_current;

INSERT INTO tu_tabla SELECT * FROM _dedup;
DROP TABLE _dedup;
```

Solo puede afectar a fechas que recibían altas nuevas durante la carga (recientes). Las fechas históricas ya cerradas no reciben escrituras concurrentes, su paginación es estable, y no pueden contener duplicados.
