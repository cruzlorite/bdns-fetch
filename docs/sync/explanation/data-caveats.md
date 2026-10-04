# Antes de consultar los datos

Hay algunas cosas que conviene saber antes de sacar conclusiones de las tablas sincronizadas. Todas se deben a cómo se comporta la API de origen (lo explicamos en [cómo sincroniza](sync-behavior.md)), no a un fallo de `bdns-sync`.

## `_reg_date` en el cambio de día

`_reg_date` guarda la fecha de registro que trae el propio registro (`fechaAlta`, `fechaRegistro` o `fechaRecepcion`, según la entidad). Un registro dado de alta justo a medianoche puede acabar asignado al día siguiente.

Para ti, eso significa que si comparas los recuentos de un día con una consulta directa a la API, puede haber una diferencia de un registro arriba o abajo. No falta ni sobra nada: el registro cae en un día o en el otro según cómo trate cada extremo la medianoche. Si comparas periodos de varios días en lugar de días sueltos, la diferencia desaparece.

## Duplicados que pueden quedar tras una carga histórica

La API pagina por posición (offset). Si entran registros nuevos en un rango de fechas **mientras se está recorriendo** (algo que solo pasa con fechas recientes), una fila que quede cerca del final de una página puede aparecer también en la siguiente. `bdns-sync` elimina las copias al insertar, así que las sincronizaciones normales no dejan duplicados, pero una carga histórica muy grande hecha de una sola vez sí puede dejar alguna pareja en casos raros.

Un duplicado de este tipo son **dos filas con `_is_current` y la misma `_natural_key`, idénticas byte a byte** (el mismo `_row_hash` y el mismo contenido). No estropean nada, pero inflan los recuentos y pueden duplicar filas en un `JOIN`.

Para encontrarlos:

```sql
SELECT _natural_key, COUNT(*) AS n
FROM tu_tabla
WHERE _is_current
GROUP BY _natural_key
HAVING COUNT(*) > 1;
```

Para eliminarlos y quedarte con una sola copia de cada clave (como son idénticas, da igual cuál):

```sql
CREATE TABLE _dedup AS
SELECT DISTINCT * FROM tu_tabla
WHERE _natural_key IN ( /* claves encontradas arriba */ ) AND _is_current;

DELETE FROM tu_tabla
WHERE _natural_key IN ( /* las mismas claves */ ) AND _is_current;

INSERT INTO tu_tabla SELECT * FROM _dedup;
DROP TABLE _dedup;
```

Solo puede pasar con fechas que estaban recibiendo altas durante la carga, es decir, con las recientes. Las fechas antiguas ya no reciben registros nuevos, se paginan de forma estable y no pueden tener duplicados.

## Bajas por caducidad y bajas de verdad

`_valid_from` y `_valid_to` indican cuándo **vio** `bdns-sync` cada versión, no cuándo ocurrió el hecho en la realidad. Cuando un registro deja de llegar, se cierra con `_closed_reason = 'removed'` (y cuando cambia, con `superseded`). Pero un registro puede dejar de llegar por dos motivos muy distintos que en la tabla se ven igual:

- **Baja de verdad**: el órgano concedente eliminó el registro o lo volvió a dar de alta de otra forma.
- **Caducidad**: se cumplió el periodo de visualización y la ayuda salió del portal. En `concesiones_busqueda` son los cuatro años naturales siguientes a la concesión, y en `ayudasestado_busqueda` y `minimis_busqueda`, diez años.

Como la caducidad sigue una regla fija, se puede distinguir con una regla y no con una estimación: basta comparar el año de `fechaConcesion` con el de `_valid_to`.

```sql
SELECT
  CASE WHEN EXTRACT(YEAR FROM _valid_to)
            - CAST(SUBSTR(JSON_VALUE(payload,'$.fechaConcesion'),1,4) AS INT64) > 4
       THEN 'caducidad' ELSE 'baja de verdad' END AS motivo,
  COUNT(*)
FROM tu_tabla
WHERE _closed_reason = 'removed'
GROUP BY motivo;
```

Hay dos cosas que **no** sirven para distinguirlas. Que las bajas lleguen en bloque no significa nada, porque las bajas de verdad también llegan a tandas cuando un órgano corrige muchos registros de golpe (en agosto de 2026 vimos bloques de 5.420 y 2.032 bajas en un solo día, de concesiones de cuatro y cinco años distintos). Tampoco sirve lo que ha durado la versión, porque mide el tiempo desde la última modificación y no la antigüedad del registro: una concesión antigua modificada hace poco tiene una versión reciente.

### Cuándo aparecen las caducidades

La sincronización diaria apenas las ve. El periodo anual llega a 365 días de fecha de registro, así que solo revisa filas registradas hace menos de un año; una concesión antigua registrada hace poco sí se cerrará cuando caduque, pero son casos sueltos.

Con una **carga histórica amplia** es distinto, porque compara todo el rango que se le pide y cierra de una vez todo lo que haya caducado, con la fecha del día en que se lanzó. Es justo lo que pasa si vuelves a lanzar `bdns-sync backfill` sobre una base de datos que ya tiene datos. En septiembre de 2026 había guardadas 1,13 millones de concesiones de 2022 a punto de caducar, así que una carga histórica lanzada en 2027 las cerraría todas a la vez.

No es un error, porque el registro ya no está en el origen y la tabla lo refleja, pero ten en cuenta que esa fecha de cierre te dice cuándo te enteraste, no cuándo caducó.

## Plazos que desaparecen y vuelven

En `convocatorias` encontrarás versiones en las que el plazo de solicitud se queda vacío y, en una versión posterior, vuelve con los mismos valores. No ha habido ninguna modificación administrativa: la API pierde el bloque entero (`fechaInicioSolicitud`, `fechaFinSolicitud`, `textInicio` y `textFin`) en algunas llamadas y lo devuelve en la siguiente. Pasa en algo menos del 9% de las parejas de versiones (lo explicamos en [cambios espurios](sync-behavior.md#spurious-changes)).

El registro refleja fielmente lo que devolvió la API, pero si cuentas modificaciones de convocatorias sin filtrar te saldrán más de las reales. Para descartarlas, ignora las versiones en las que un campo pasa de tener valor a `null` y luego recupera el valor anterior:

```sql
SELECT * FROM convocatorias v
WHERE JSON_VALUE(v.payload,'$.fechaFinSolicitud') IS NULL
  AND EXISTS (SELECT 1 FROM convocatorias p
              WHERE p._natural_key = v._natural_key AND p._valid_from < v._valid_from
                AND JSON_VALUE(p.payload,'$.fechaFinSolicitud') IS NOT NULL);
```

Lo mismo ocurre, aunque menos, con `descripcionLeng` en `convocatorias_busqueda` y con `sectorActividad` en `minimis_busqueda`.
