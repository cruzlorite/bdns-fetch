---
hide:
  - toc
---

<div class="bdns-hero" markdown>

# BDNS

<p class="bdns-tagline">Descarga, conserva y reutiliza los datos de la Base de Datos Nacional de Subvenciones a través de su API pública, sin tener que pelearte con ella.</p>

[Empezar con bdns-fetch :octicons-arrow-right-24:](fetch/getting-started.md){ .md-button .md-button--primary }
[Empezar con bdns-sync :octicons-arrow-right-24:](sync/getting-started.md){ .md-button }

</div>

```console
$ pip install bdns                # para BigQuery: pip install "bdns[bigquery]"
```

## Dos herramientas, un paquete

<div class="grid cards" markdown>

- :material-cloud-download:{ .lg .middle } **BDNS Fetch**

    ---

    Cliente de Python y herramienta de línea de comandos para la API. Cubre los 29 endpoints de consulta y se encarga de la paginación, los reintentos y el límite de peticiones.

    [:octicons-arrow-right-24: Ir a bdns-fetch](fetch/index.md)

- :material-database-sync:{ .lg .middle } **BDNS Sync**

    ---

    Mantiene en tu base de datos (SQLite, PostgreSQL, DuckDB o BigQuery) una copia de la BDNS con el histórico de todas sus versiones, con un solo comando al día.

    [:octicons-arrow-right-24: Ir a bdns-sync](sync/index.md)

</div>

## Por qué usarlo

<div class="grid cards" markdown>

- :material-ruler-square:{ .lg .middle } **Comprobado, no supuesto**

    ---

    Todo lo que se documenta sobre la API (las fechas, los límites, los fallos) se ha medido contra el servicio real, y unas pruebas nocturnas avisan si cambia.

- :material-handshake-outline:{ .lg .middle } **Respetuoso con la API**

    ---

    Una llamada cada vez y peticiones espaciadas, como piden las buenas prácticas oficiales de la IGAE.

- :material-history:{ .lg .middle } **Todo el histórico**

    ---

    `bdns-sync` guarda cada versión de cada registro, incluido lo que el portal acaba retirando.

- :material-cog-off-outline:{ .lg .middle } **Sin configuración**

    ---

    Basta con una URL de base de datos y un comando al día.

</div>

!!! note "Proyecto no oficial"

    Es un proyecto personal, sin ninguna relación con la IGAE, que es quien gestiona la BDNS. Si reutilizas los datos, tienes que cumplir sus condiciones de reutilización, que tienes resumidas en el [aviso legal](legal.md).
