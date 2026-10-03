# BDNS Sync

Motor de sincronización que mantiene bases de datos de destino en forma
**SCD2** a partir de la API de la [Base de Datos Nacional de
Subvenciones](https://www.infosubvenciones.es/).

Un comando al día mantiene el destino al día: comprueba que la API no ha
cambiado, sincroniza las 22 entidades con la ventana que toca y registra
cada ejecución. Sin fichero de configuración.

```console
$ pip install bdns-sync
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
$ bdns-sync backfill        # una vez: el histórico
$ bdns-sync delta           # a diario
```

Se apoya en [`bdns-fetch`](https://cruzlorite.github.io/bdns-fetch/), que
sabe todo lo que hay que saber de la API; `bdns-sync` pone el histórico
versionado, la detección de bajas y el registro de ejecuciones.

## Por dónde empezar

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **Nunca lo has usado**

    ---

    De cero a una tabla sincronizada y consultable, en unos diez minutos
    y sin salir de tu máquina.

    [:octicons-arrow-right-24: Empezar](getting-started.md)

- :material-calendar-clock:{ .lg .middle } **Ponerlo en producción**

    ---

    Cadencia diaria, cargas iniciales y despliegue en la nube.

    [:octicons-arrow-right-24: Guías](guides/scheduling.md)

- :material-lightbulb-on:{ .lg .middle } **Entender por qué**

    ---

    Qué cuenta como un cambio, cómo se comporta la API de origen, y qué
    saber antes de consultar las tablas.

    [:octicons-arrow-right-24: Explicación](explanation/payload-policy.md)

- :material-code-braces:{ .lg .middle } **Consultar un dato**

    ---

    El CLI, el esquema de tablas y la API Python generada desde los
    docstrings.

    [:octicons-arrow-right-24: Referencia](reference/cli.md)

</div>

## El modelo de datos en una frase

Cada endpoint tiene una tabla con un esquema fijo: el registro se guarda
entero en `payload`, y el resto de columnas son metadatos de versionado.
Las versiones cerradas no se borran nunca — el histórico es
*append-only*.

| Columna | Qué es |
| --- | --- |
| `_natural_key` | Identidad del registro, serializada desde sus campos clave |
| `_row_hash` | Hash del contenido; un hash distinto es una versión nueva |
| `_valid_from` / `_valid_to` | Vigencia de esta versión. `_valid_to` nulo = actual |
| `_is_current` | Si esta es la versión vigente |
| `_synced_at` | Última vez que se vio el registro |
| `_reg_date` | Fecha de registro propia, cuando la entidad la expone |
| `payload` | El registro tal como lo devolvió la API |
| `_created_run_id` / `_closed_run_id` | Ejecución que escribió la versión y la que la cerró |
| `_closed_reason` | Por qué se cerró: `superseded` o `removed` |
