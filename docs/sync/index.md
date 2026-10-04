# BDNS Sync

Mantiene en tu base de datos una copia de la [Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/) (BDNS) con el histórico de todas sus versiones (lo que se conoce como **SCD2**).

Basta con un comando al día: comprueba que la API no ha cambiado, sincroniza las 22 entidades con el periodo que toque y deja anotada cada ejecución. No necesita fichero de configuración.

```console
$ pip install bdns
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
$ bdns-sync backfill        # una sola vez, para cargar el histórico
$ bdns-sync delta           # todos los días
```

Para hablar con la API se apoya en [`bdns-fetch`](../fetch/index.md), que sabe todo lo necesario sobre ella; `bdns-sync` se encarga de guardar el histórico de versiones, detectar las bajas y llevar el registro de ejecuciones.

## Por dónde empezar

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **Es la primera vez**

    ---

    En unos diez minutos, y sin salir de tu ordenador, tendrás una tabla sincronizada que puedes consultar.

    [:octicons-arrow-right-24: Primeros pasos](getting-started.md)

- :material-calendar-clock:{ .lg .middle } **Quiero ponerlo en producción**

    ---

    La sincronización diaria, la carga inicial y el despliegue en la nube.

    [:octicons-arrow-right-24: Guías](guides/scheduling.md)

- :material-lightbulb-on:{ .lg .middle } **Quiero entender por qué funciona así**

    ---

    Qué cuenta como un cambio, cómo se detectan las bajas y qué tener en cuenta antes de consultar las tablas.

    [:octicons-arrow-right-24: Conceptos](explanation/payload-policy.md)

- :material-code-braces:{ .lg .middle } **Busco un detalle concreto**

    ---

    Los comandos, el esquema de las tablas y la referencia de Python generada a partir del código.

    [:octicons-arrow-right-24: Referencia](reference/cli.md)

</div>

## Cómo se guardan los datos

Cada entidad tiene su tabla, y todas tienen las mismas columnas: el registro se guarda entero en `payload` y el resto son datos para llevar el control de las versiones. Las versiones cerradas no se borran nunca, así que el histórico solo crece.

| Columna | Qué guarda |
| --- | --- |
| `_natural_key` | Lo que identifica al registro, a partir de sus campos clave |
| `_row_hash` | El hash del contenido; si cambia, es una versión nueva |
| `_valid_from` / `_valid_to` | Desde cuándo y hasta cuándo es válida esta versión. Si `_valid_to` está vacío, es la vigente |
| `_is_current` | Si esta es la versión vigente |
| `_synced_at` | La última vez que se vio el registro |
| `_reg_date` | La fecha de registro del propio registro, cuando la entidad la tiene |
| `payload` | El registro tal y como lo devolvió la API |
| `_created_run_id` / `_closed_run_id` | La ejecución que escribió la versión y la que la cerró |
| `_closed_reason` | Por qué se cerró: `superseded` (cambió) o `removed` (desapareció) |

Todos los detalles están en el [modelo de datos](reference/data-model.md).

## Aviso

Es un proyecto personal y no oficial, sin ninguna relación con la Intervención General de la Administración del Estado (IGAE), que es quien gestiona la BDNS. Varias tablas guardan nombres y NIF de personas físicas, y su reutilización está limitada por las condiciones de la IGAE; las tienes resumidas en el [aviso legal del README](https://github.com/cruzlorite/bdns#aviso-legal).
