# Sincronización diaria

Para tener la base de datos al día basta con ejecutar un comando una vez al día:

```console
$ bdns-sync delta
```

`delta` comprueba primero que la API sigue comportándose como esperamos y, si todo está en orden, sincroniza las 16 entidades completas y después las 6 incrementales, cada una con el periodo que toque ese día. Si alguna falla, sigue con las demás y al terminar devuelve un código de error para que salte la alerta.

Antes de programarlo tienes que hacer una vez la carga del histórico (lo explicamos en [carga inicial](backfill.md)). Y si quieres ver qué haría hoy sin descargar ni escribir nada, ejecuta `bdns-sync delta --dry-run`.

## Programarlo con cron

```crontab
0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://proyecto/dataset bdns-sync delta
```

Si prefieres no mantener una máquina propia, la imagen de Docker ejecuta `bdns-sync delta` por defecto, y en [despliegue en la nube](deployment.md) tienes una receta para programarla como tarea en Google Cloud.

## Qué periodo se descarga cada día

Las entidades incrementales no se descargan enteras: se pide lo registrado en un periodo que siempre termina ayer, y ese periodo depende del día ([`cadence_window`][bdns.sync.windows.cadence_window]):

| Cuándo | Periodo | Días de fecha de registro |
| --- | --- | --- |
| Todos los días | `weekly` | 7 |
| Los lunes | `monthly` | 30 |
| El 1 de enero, el 1 de mayo y el 1 de septiembre | `annual` | 365 |

Como todos los periodos terminan ayer, el anual incluye al mensual y el mensual al semanal, así que basta con lanzar el más largo que toque y no hace falta encadenarlos. Si un día necesitas otro, por ejemplo para recuperar un mes concreto después de una caída, puedes forzarlo con `--window`.

## Por qué se repasa cada día la última semana

Podría parecer suficiente con descargar lo que se registró ayer, pero hay dos motivos para repasar cada día los últimos siete:

- Algunos registros aparecen con una fecha de registro de hace varios días. Si solo miráramos el día anterior, no los veríamos nunca.
- Las bajas solo se detectan dentro del periodo que se sincroniza. Con un solo día, si se retira algo registrado hace tres días no nos enteraríamos hasta el siguiente repaso mensual.

## Si una entidad falla, las demás siguen

Cada entidad se sincroniza por separado y no depende de las otras, así que no tiene sentido dar por perdido el día entero porque falle una. Nos pasó el 2 de septiembre de 2026: `sectores`, un catálogo de 24 filas, agotó la cuota diaria de BigQuery y, como el script de entonces se paraba en el primer error, arrastró con él a las otras 22 entidades.

Ahora `delta` anota el fallo en `_sync_runs`, continúa con el resto y al final muestra un resumen como este:

```console
ok      sectores                         fetched=24 new=0 changed=0 unchanged=24 removed=0 skipped=0
FAILED  concesiones_busqueda             BDNSTransientError: HTTP 503: Server error
...
1 of 22 sync(s) failed
```

## La comprobación de la API va incluida

Antes de sincronizar, `delta` usa la comprobación de `bdns-fetch` para confirmar que la API sigue tratando las fechas como siempre: que `fechaRegFin` no incluye el propio día, que `fechaHasta` sí lo incluye y que dos días seguidos no comparten registros. Si la API devuelve datos válidos que contradicen alguna de estas reglas, no se sincroniza nada y el comando termina con error, porque seguir adelante supondría perder o duplicar registros sin que nadie se diera cuenta. Si el problema es pasajero (un error del servidor, un día sin datos), no se bloquea nada ([más detalle](../explanation/sync-behavior.md#boundary-check)). Si quieres saltarte la comprobación, usa `--skip-api-check`.

## Cómo saber si ha ido bien

Cada ejecución deja su rastro en `_sync_runs`, y su estado es el del último evento anotado. La regla es la misma con cualquier base de datos: **si no hay un evento `success`, vuelve a lanzarla**. Repetir una sincronización no duplica nada.

```sql
SELECT table_name, run_type, event, occurred_at, window_start, window_end,
       rows_inserted, rows_changed, rows_soft_deleted, rows_skipped, error
FROM _sync_runs
WHERE event != 'started'
ORDER BY occurred_at DESC
LIMIT 25;
```

Fíjate también en `rows_skipped`: una ejecución puede terminar bien aunque haya descartado registros mal formados, que se guardan en `_sync_errors`. Qué garantiza cada base de datos cuando algo falla a medias lo tienes en [el modelo de datos](../reference/data-model.md).
