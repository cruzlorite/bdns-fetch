---
icon: material/chart-box
---

# BDNS Dataset

!!! warning "En preparación"

    Todavía no hay ninguna versión publicada. Esta sección cuenta qué será el dataset y cómo se está construyendo, y su SQL es experimental: puede cambiar en cualquier momento hasta que se publique la primera versión.

Un conjunto de datos listo para usar con **todo el histórico** de la BDNS que conserva `bdns-sync`, y no solo con los años que todavía publica el portal ([por qué importa](../sync/index.md#why-history)). Irá siempre **anonimizado y agregado**: proteger a las personas físicas es la prioridad, y todo el proceso tiene que cumplir las condiciones de reutilización de la IGAE, el RGPD y la LOPDGDD.

Son ficheros Parquet, uno por tabla, que puedes abrir con DuckDB, pandas, R o cualquier otra herramienta de datos:

| Tabla | Qué contiene | Detalle |
|---|---|---|
| `concesiones_entidades` | Concesiones a personas jurídicas y entidades públicas | Una fila por concesión |
| `ayudas_estado_entidades` | Ayudas de Estado a personas jurídicas y entidades públicas | Una fila por ayuda |
| `minimis_entidades` | Ayudas de minimis a personas jurídicas y entidades públicas | Una fila por ayuda |
| `concesiones_personas` | Concesiones a personas físicas | Un resumen por convocatoria |

Por ejemplo, para ver qué órganos han concedido más a empresas y entidades basta con consultar el fichero directamente (los datos son inventados):

```console
$ duckdb -c "
    SELECT nivel3 AS organo, count(*) AS concesiones, sum(importe) AS importe
    FROM 'concesiones_entidades.parquet'
    GROUP BY organo
    ORDER BY importe DESC
    LIMIT 3"
┌─────────────────────────────┬─────────────┬───────────────┐
│           organo            │ concesiones │    importe    │
│           varchar           │    int64    │ decimal(38,2) │
├─────────────────────────────┼─────────────┼───────────────┤
│ CONSEJERÍA DE AGRICULTURA   │           3 │     145000.00 │
│ CONSEJERÍA DE EDUCACIÓN     │           1 │      90000.00 │
│ SERVICIO REGIONAL DE EMPLEO │           3 │      28000.00 │
└─────────────────────────────┴─────────────┴───────────────┘
```

## Por dónde empezar

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **Es la primera vez**

    ---

    Genera el dataset a partir de tu copia de `bdns-sync` y haz tu primera consulta.

    [:octicons-arrow-right-24: Primeros pasos](getting-started.md)

- :material-magnify:{ .lg .middle } **Quiero analizar los datos**

    ---

    Consultas de ejemplo con DuckDB y pandas, y cómo leer los resúmenes de las personas físicas.

    [:octicons-arrow-right-24: Guías](guides/queries.md)

- :material-shield-account:{ .lg .middle } **Quiero saber cómo se protege a las personas**

    ---

    Qué beneficiarios se protegen, qué se publica de ellos y qué se comprueba antes de escribir nada.

    [:octicons-arrow-right-24: Conceptos](explanation/anonymisation.md)

- :material-code-braces:{ .lg .middle } **Busco un detalle concreto**

    ---

    Todas las tablas y sus columnas, y los pasos de la generación.

    [:octicons-arrow-right-24: Referencia](reference/tables.md)

</div>

## Estado

- [x] La decisión de diseño, como propuesta ([decisión 0002](../adr/0002-anonymised-dataset.md))
- [x] La clasificación de beneficiarios y las piezas de los controles de privacidad, en SQL
- [x] Las concesiones, leídas directamente de `bdns-sync` con la última versión conocida de cada una, incluidas las que la API ya ha retirado, con sus columnas y el tipo de beneficiario
- [x] Las concesiones, ayudas de Estado y minimis a personas jurídicas y entidades públicas, registro a registro, sin el enlace al boletín ni el identificador interno de la BDNS, y los controles que las vigilan
- [x] La exportación a Parquet, que solo se hace si pasan todos los controles
- [x] Las concesiones a personas físicas, como un resumen por convocatoria: número de concesiones y de beneficiarios, importe total, media, desviación típica, mediana y cuartiles del importe, y los mismos percentiles de la fecha de concesión
- [ ] Lo mismo para ayudas de Estado y minimis
- [ ] La ficha del dataset, el esquema y la publicación
- [ ] La evaluación de riesgos y la revisión legal, antes de la primera versión
