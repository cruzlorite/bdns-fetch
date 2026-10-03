# Operación programada

Una instalación en producción ejecuta **un comando al día**:

```console
$ bdns-sync delta
```

`delta` comprueba que la API no ha cambiado, sincroniza las 16 entidades
completas y después las 6 de ventana, con la ventana que toca ese día.
Si una entidad falla, sigue con las demás y termina con código 1 para que
salte la alerta.

Antes de programarlo, lanza una sola vez la carga histórica: ver
[cargas iniciales y backfills](backfill.md). Para ver qué haría hoy sin
tocar nada: `bdns-sync delta --dry-run`.

## Una línea de cron

```crontab
0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://proyecto/dataset bdns-sync delta
```

Si prefieres no mantener una máquina propia, la imagen de contenedor
ejecuta `bdns-sync delta` por defecto y hay una receta de job programado
en la nube: ver [despliegue](deployment.md).

## Qué ventana toca cada día

Las ventanas están **anidadas, no son independientes**: todas terminan
ayer, así que en cualquier día `annual ⊃ monthly ⊃ weekly ⊃ daily`.
Lanzar la más ancha que aplique ya cubre todas las estrechas, así que
`delta` lanza exactamente una
([`cadence_window`][bdns.sync.windows.cadence_window]):

| Cuándo | Ventana | Alcance |
| --- | --- | --- |
| A diario | `weekly` | 7 días de fecha de registro |
| Lunes | `monthly` | 30 días |
| 1 de enero, mayo y septiembre | `annual` | 365 días |

`--window` fuerza otra, por ejemplo para recuperar un mes concreto tras
una avería.

## Por qué la base es semanal y no diaria

Dos motivos, y los dos son de corrección, no de comodidad:

- Un registro puede aparecer con fecha de registro de días atrás. Una
  ventana de un día no lo vería nunca.
- La detección de bajas solo mira dentro de la ventana con la que corre.
  Con una ventana de un día, una baja registrada hace tres días no se
  detecta hasta la siguiente pasada ancha.

Siete días de vuelta atrás cada día atrapan las dos cosas.

## Por qué no se aborta al primer fallo

Una entidad que falla no debe cancelar las otras 21. Son sincronizaciones
independientes que no comparten nada salvo el destino, así que abortar el
día entero por una de ellas solo amplía la avería. Pasó de verdad: el 2
de septiembre de 2026 `sectores`, un catálogo de 24 filas, agotó la cuota
diaria de BigQuery y, con un orquestador que abortaba al primer fallo,
se llevó por delante a las otras 22 entidades.

`delta` registra cada fallo en `_sync_runs`, sigue con las demás e
informa al final:

```console
ok      sectores                         fetched=24 new=0 changed=0 unchanged=24 removed=0 skipped=0
FAILED  concesiones_busqueda             BDNSTransientError: HTTP 503: Server error
...
1 of 22 sync(s) failed
```

## La comprobación de la API va incluida

Antes de sincronizar, `delta` ejecuta la comprobación de contrato de
`bdns-fetch`: que `fechaRegFin` sigue siendo exclusivo, `fechaHasta`
inclusivo, y los días consecutivos disjuntos. Si la API devuelve datos
válidos que contradicen algo de eso, **no se sincroniza nada** y sale con
código 1. Un error pasajero o un día vacío no bloquean
([por qué](../explanation/sync-behavior.md#boundary-check)).
`--skip-api-check` la omite.

## Saber si un día fue bien

El estado de una ejecución es su último evento en `_sync_runs`. La regla
de operación es la misma en todos los motores: **si no hay evento
`success`, se vuelve a lanzar.** La herramienta es idempotente.

```sql
SELECT table_name, run_type, event, occurred_at, window_start, window_end,
       rows_inserted, rows_changed, rows_soft_deleted, rows_skipped, error
FROM _sync_runs
WHERE event != 'started'
ORDER BY occurred_at DESC
LIMIT 25;
```

Vigila también `rows_skipped`: una ejecución puede terminar bien
descartando registros malformados, que quedan en `_sync_errors`. Las
garantías por motor están en [el modelo de datos](../reference/data-model.md).
