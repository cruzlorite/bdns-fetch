# Primeros pasos

En unos diez minutos vas a tener una tabla sincronizada que puedes consultar, sin cuenta en la nube y sin instalar ninguna base de datos, porque usaremos SQLite, que es un simple fichero.

## 1. Instalación

Necesitas Python 3.11 o posterior (hasta la 3.14).

```console
$ pip install bdns
$ bdns-sync --version
bdns-sync 2.0.0
```

## 2. Elegir dónde se guardan los datos

La base de datos de destino se indica con una URL de SQLAlchemy. Para empezar, un fichero local:

```console
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
```

Todos los comandos leen esa variable, así que no tienes que repetirla en cada uno. Si lo prefieres, también puedes pasarla con `--target-url`.

## 3. Sincronizar algo pequeño

`sectores` es un catálogo de unas pocas decenas de filas que se descarga con una sola llamada, así que tarda unos segundos y es un buen punto de partida.

```console
$ bdns-sync sync sectores
```

Ya tienes datos. Para verlos te basta con Python:

```console
$ python -c "import sqlite3; print(sqlite3.connect('bdns.db').execute('SELECT COUNT(*) FROM sectores').fetchone()[0])"
24
```

## 4. Ver cómo se han guardado

La tabla no tiene una columna por cada campo: el registro se guarda entero en `payload`, y el resto de columnas sirven para llevar el control de las versiones.

```python
import sqlite3

db = sqlite3.connect("bdns.db")
for key, current, payload in db.execute(
    "SELECT _natural_key, _is_current, payload FROM sectores LIMIT 2"
):
    print(key, current, payload)
```

```text
[10] 1 {"descripcion": "Productos transformados a base de frutas y hortalizas (parte X)", "id": 10}
[11] 1 {"descripcion": "Plátanos (parte XI)", "id": 11}
```

Por qué se guarda así y qué se gana con ello lo explicamos en [el modelo de datos](reference/data-model.md).

## 5. Volver a sincronizar

Lanza otra vez exactamente el mismo comando:

```console
$ bdns-sync sync sectores
```

Y compara lo que muestra cada vez. La primera:

```text
ok  sectores  fetched=24 new=24 changed=0 unchanged=0 removed=0 skipped=0
```

La segunda:

```text
ok  sectores  fetched=24 new=0 changed=0 unchanged=24 removed=0 skipped=0
```

Todo ha caído en `unchanged`: los registros se han vuelto a ver y no habían cambiado, así que **no se ha creado ninguna versión nueva**; solo se ha actualizado la fecha en que se vieron por última vez.

Esa es la idea central de la herramienta. Qué cuenta como un cambio y qué no lo explicamos en [qué se guarda y qué cuenta como un cambio](explanation/payload-policy.md).

## 6. Una entidad incremental

Las entidades grandes no se descargan enteras, sino por fecha de registro. Antes de lanzar una, mira qué haría:

```console
$ bdns-sync sync concesiones_busqueda --window daily --dry-run
target      sqlite:///bdns.db  ->  table concesiones_busqueda
run type    daily
range       2026-09-06 .. 2026-09-06  (1 day(s), 1 chunk(s) of at most 7)
policy      drop=[] hash_exclude=['beneficiario'] delimited_lists=[] canonical_arrays=True
limits      max_ratio=10% max_count=none min_to_enforce_ratio=5
dry run     nothing fetched, nothing written
```

Con `--dry-run` calcula el periodo, las reglas y los límites, te los muestra y se detiene sin tocar la API ni la base de datos. Quítalo para lanzarlo de verdad:

```console
$ bdns-sync sync concesiones_busqueda --window daily
```

`daily` pide el día de ayer. El de hoy no, porque todavía está recibiendo altas y quedaría un día a medias que nadie volvería a revisar.

## 7. Ver el registro de ejecuciones

Cada ejecución queda anotada en la propia base de datos, junto a los datos:

```python
for row in db.execute(
    "SELECT run_id, table_name, run_type, event, rows_fetched"
    " FROM _sync_runs ORDER BY occurred_at DESC LIMIT 4"
):
    print(row)
```

```text
(1788734182609786, 'sectores', 'full', 'success', 24)
(1788734182609786, 'sectores', 'full', 'started', None)
(1788734171434519, 'sectores', 'full', 'success', 24)
(1788734171434519, 'sectores', 'full', 'started', None)
```

Cada ejecución deja dos filas, una `started` y una `success`. Si alguna vez ves un `started` sin su `success`, ese proceso se quedó a medias, y eso es algo que no podrías saber si cada ejecución tuviera un único estado que se va actualizando.

## 8. Todo de una vez

En producción no se sincroniza entidad a entidad, sino con un solo comando que se encarga de las 22, cada día con el periodo que toque. Mira qué haría hoy:

```console
$ bdns-sync delta --dry-run
target      sqlite:///bdns.db
limits      max_ratio=10% max_count=none min_to_enforce_ratio=5
  sectores: complete state
  actividades: complete state
  ...
  concesiones_busqueda: weekly [2026-09-26 .. 2026-10-02]
  ...
dry run     22 sync(s) planned; nothing fetched, nothing written
```

## Y ahora qué

- Para ponerlo en marcha todos los días: [sincronización diaria](guides/scheduling.md).
- Para cargar el histórico completo: [carga inicial](guides/backfill.md).
- Para llevarlo a la nube: [despliegue en la nube](guides/deployment.md).
- Antes de ponerte a consultar en serio: [antes de consultar los datos](explanation/data-caveats.md).
