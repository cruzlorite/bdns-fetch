# BDNS

Herramientas para descargar, conservar y reutilizar los datos de la [Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/) (BDNS) a través de su API pública.

```console
$ pip install bdns                # para BigQuery: pip install "bdns[bigquery]"
```

El paquete trae dos herramientas, cada una con su comando y su módulo de Python:

<div class="grid cards" markdown>

- :material-cloud-download:{ .lg .middle } **BDNS Fetch**

    ---

    Cliente de Python y herramienta de línea de comandos para la API. Cubre los 29 endpoints de consulta y se encarga de la paginación, los reintentos y el límite de peticiones. Sirve para hacer consultas o descargar datos a ficheros.

    [:octicons-arrow-right-24: Ir a bdns-fetch](fetch/index.md)

- :material-database-sync:{ .lg .middle } **BDNS Sync**

    ---

    Mantiene en tu base de datos (SQLite, PostgreSQL, DuckDB o BigQuery) una copia de la BDNS con el histórico de todas sus versiones, con un solo comando al día. Usa `bdns-fetch` por debajo.

    [:octicons-arrow-right-24: Ir a bdns-sync](sync/index.md)

</div>

Más adelante habrá también un dataset anonimizado y agregado con todo el histórico, listo para usar ([hoja de ruta](roadmap.md#dataset)).

## Aviso

Es un proyecto personal y no oficial, sin ninguna relación con la Intervención General de la Administración del Estado (IGAE), que es quien gestiona la BDNS. Si reutilizas los datos, tienes que cumplir sus condiciones de reutilización, que tienes resumidas en el [aviso legal del README](https://github.com/cruzlorite/bdns#aviso-legal).
