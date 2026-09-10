# Empezar

De cero a una tabla sincronizada y consultable. Unos diez minutos, sin
cuenta en la nube ni base de datos que instalar: se usa SQLite, que es un
fichero.

## 1. Instalar

```console
$ pip install bdns-sync
$ bdns-sync --version
bdns-sync 0.5.0
```

## 2. Elegir un destino

El destino se pasa como URL de SQLAlchemy. Aquí, un fichero local:

```console
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
```

Todos los comandos leen esa variable, así que no hay que repetirla. También
se puede pasar con `--target-url`.

## 3. Sincronizar algo pequeño

`sectores` es un catálogo: unas pocas decenas de filas, una sola llamada.
Buen primer paso porque termina en segundos.

```console
$ bdns-sync sync sectores
```

Ya hay datos. Para mirarlos basta con Python, que ya tienes:

```console
$ python -c "import sqlite3; print(sqlite3.connect('bdns.db').execute('SELECT COUNT(*) FROM sectores').fetchone()[0])"
24
```

## 4. Mirar cómo se han guardado

La tabla no tiene una columna por campo. El registro se guarda entero en
`payload`, y el resto son metadatos de versionado:

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

Por qué es así, y qué se gana, está en
[el modelo de datos](reference/data-model.md).

## 5. Volver a sincronizar

Lanza exactamente el mismo comando otra vez:

```console
$ bdns-sync sync sectores
```

Compara los contadores del log. La primera vez:

```text
fetched=24 inserted=24 updated=0 touched=0 soft_deleted=0 skipped=0
```

La segunda:

```text
fetched=24 inserted=0 updated=0 touched=24 soft_deleted=0 skipped=0
```

Todo cayó en `touched`: los registros se volvieron a ver y no habían
cambiado, así que **no se creó ninguna versión nueva**. Solo se refrescó
la marca de última visita.

Esa es la idea central de la herramienta. Qué cuenta como un cambio, y
qué no, se explica en
[qué se guarda y qué cuenta como un cambio](explanation/payload-policy.md).

## 6. Un endpoint incremental

Los grandes no se sincronizan enteros: se piden por rango de fecha de
registro. Antes de lanzarlo, mira qué haría:

```console
$ bdns-sync sync concesiones_busqueda --window daily --dry-run
target      sqlite:///bdns.db  ->  table concesiones_busqueda
run type    daily
range       2026-09-06 .. 2026-09-06  (1 day(s), 1 chunk(s) of at most 7)
policy      drop=[] hash_exclude=['beneficiario'] delimited_lists=[] canonical_arrays=True
limits      max_ratio=10% max_count=none min_to_enforce_ratio=5
dry run     nothing fetched, nothing written
```

`--dry-run` resuelve el rango, la política y los límites, los imprime y
para. No toca ni la API ni el destino. Quítalo para lanzarlo de verdad:

```console
$ bdns-sync sync concesiones_busqueda --window daily
```

`daily` pide el día de ayer. Hoy no, porque hoy todavía está recibiendo
altas y quedaría un día a medias que nada revisa después.

## 7. Ver el registro de ejecuciones

Cada ejecución queda anotada en el destino, junto a los datos:

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

Dos filas por ejecución: un `started` y un `success`. Si alguna vez
ves un `started` suelto, ese proceso murió a mitad — es exactamente la
información que un campo de estado mutable no podría darte.

## Qué hacer después

- Poner esto en marcha a diario: [operación programada](guides/scheduling.md).
- Cargar el histórico completo: [cargas iniciales y backfills](guides/backfill.md).
- Llevarlo a la nube: [despliegue](guides/deployment.md).
- Antes de consultar en serio: [antes de consultar los datos](explanation/data-caveats.md).
