# Operación programada

`bdns-sync` no sabe qué día es. Una invocación sincroniza un endpoint con
el rango que le pases, y ya. La cadencia vive fuera, en un script de
orquestación.

El repositorio trae uno listo:
[`scripts/delta_load.sh`](https://github.com/cruzlorite/bdns-sync/blob/main/scripts/delta_load.sh).

## Una línea de cron

```crontab
0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://proyecto/dataset /ruta/a/scripts/delta_load.sh
```

Eso es todo. El script decide qué ventana toca hoy.

## Por qué una sola ventana al día

Las ventanas están **anidadas, no son independientes**: todas terminan
ayer, así que en cualquier día dado `annual ⊃ monthly ⊃ weekly ⊃ daily`.
Lanzar la más ancha que aplique hoy ya cubre gratis todas las estrechas.

El calendario del script:

| Cuándo | Ventana | Alcance |
| --- | --- | --- |
| A diario | `weekly` | 7 días de fecha de registro |
| Lunes | `monthly` | 30 días |
| 1 de enero, mayo y septiembre | `annual` | 365 días |

## Por qué la base es semanal y no diaria

Dos motivos, y los dos son de corrección, no de comodidad:

- Un registro puede aparecer con fecha de registro de días atrás. Una
  ventana de un día no lo vería nunca.
- La detección de bajas solo mira dentro de la ventana con la que corre.
  Con una ventana de un día, una baja registrada hace tres días no se
  detecta hasta la siguiente pasada ancha.

Siete días de vuelta atrás cada día atrapan las dos cosas.

## Por qué el script no aborta al primer fallo

Un endpoint que falla no debe cancelar los otros 21. Son sincronizaciones
independientes que no comparten nada salvo el destino, así que abortar el
día entero por una de ellas solo amplía la avería.

Pasó de verdad: el 2 de septiembre de 2026 `sectores` —un catálogo de 24
filas— agotó la cuota diaria de BigQuery y se llevó por delante a las
otras 22 entidades. Ese día quedó 1 ejecución en lugar de 23.

Por eso el script no usa `set -e`. Recoge los fallos, los informa al
final, y aun así sale con código distinto de cero para que el job se
marque como fallido y salte la alerta. `-u` y `pipefail` sí se quedan:
cazan errores del propio script.

## Comprobar que la API no ha cambiado

Antes de la cadencia del día, una vez:

```console
$ bdns-sync check-api
```

Solo sale con error si la API devolvió datos válidos que contradicen un
invariante. Los baches transitorios no bloquean nada. Ver
[`check-api`](../reference/cli.md#check-api).

## Saber si un día fue bien

El estado de una ejecución es su último evento en `_sync_runs`. La regla
de operación es la misma en todos los motores: **si no hay evento
`success`, se vuelve a lanzar.** La herramienta es idempotente.

```python
import sqlite3

db = sqlite3.connect("bdns.db")
for row in db.execute(
    "SELECT table_name, run_type, event, occurred_at"
    " FROM _sync_runs WHERE event != 'started'"
    " ORDER BY occurred_at DESC LIMIT 25"
):
    print(row)
```

El detalle de las garantías por motor está en
[el modelo de datos](../reference/data-model.md).
