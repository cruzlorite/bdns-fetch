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
| [`concesiones_personas_juridicas`](contents.md#concesiones_personas_juridicas) | Concesiones a personas jurídicas, entidades públicas incluidas | Una fila por concesión |
| [`concesiones_personas_fisicas`](contents.md#personas-fisicas) | Concesiones a personas físicas | Un resumen por convocatoria |
| [`ayudasestado_personas_juridicas`](contents.md#ayudasestado_personas_juridicas) | Ayudas de Estado a personas jurídicas | Una fila por ayuda |
| [`ayudasestado_personas_fisicas`](contents.md#personas-fisicas) | Ayudas de Estado a personas físicas, casi siempre autónomos | Un resumen por convocatoria |
| [`minimis_personas_juridicas`](contents.md#minimis_personas_juridicas) | Ayudas de minimis a personas jurídicas | Una fila por ayuda |
| [`minimis_personas_fisicas`](contents.md#personas-fisicas) | Ayudas de minimis a personas físicas, casi siempre autónomos | Un resumen por convocatoria |
| [`partidospoliticos`](contents.md#partidospoliticos) | Ayudas a partidos políticos y a sus fundaciones | Una fila por concesión |
| [`grandesbeneficiarios`](contents.md#grandesbeneficiarios) | Los grandes beneficiarios que son personas jurídicas | Una fila por beneficiario y año |
| [`convocatorias`](contents.md#convocatorias) | Convocatorias | Una fila por convocatoria |
| [`planesestrategicos`](contents.md#planesestrategicos) | Planes estratégicos de subvenciones | Una fila por plan |
| [`catalogos`](contents.md#catalogos) | Los catálogos de la BDNS (órganos, regiones, instrumentos…) | Una fila por código |

Las empresas y entidades públicas aparecen registro a registro, con su NIF y su nombre, mientras que de las personas físicas solo se publican resúmenes por convocatoria que no permiten identificar a nadie.

<div class="grid cards" markdown>

- :material-table:{ .lg .middle } **Qué contiene**

    ---

    Las tablas, sus columnas y lo que conviene saber para leerlas bien.

    [:octicons-arrow-right-24: Contenido](contents.md)

- :material-shield-account:{ .lg .middle } **Cómo se protege a las personas**

    ---

    Qué beneficiarios se protegen, qué se publica de ellos y qué se comprueba antes de publicar.

    [:octicons-arrow-right-24: Anonimización](privacy.md)

- :material-cog:{ .lg .middle } **Cómo se genera**

    ---

    Cómo generar el dataset a partir de tu copia de `bdns-sync`, con la línea de comandos de DuckDB.

    [:octicons-arrow-right-24: Generación](build.md)

</div>

## Estado

- [x] La decisión de diseño, como propuesta ([decisión 0020](../adr/0020-anonymised-dataset.md))
- [x] La clasificación de beneficiarios y las piezas de los controles de privacidad, en SQL
- [x] Las concesiones, leídas directamente de `bdns-sync` con la última versión conocida de cada una, incluidas las que la API ya ha retirado, con sus columnas y el tipo de beneficiario
- [x] Las concesiones, ayudas de Estado y minimis a personas jurídicas y entidades públicas, registro a registro, sin el enlace al boletín ni el identificador interno de la BDNS, y los controles que las vigilan
- [x] La exportación a Parquet, que solo se hace si pasan todos los controles
- [x] Las convocatorias, las ayudas a partidos políticos, los grandes beneficiarios que son personas jurídicas, los planes estratégicos y los catálogos
- [x] Las concesiones, ayudas de Estado y minimis a personas físicas, como un resumen por convocatoria: número de concesiones y de beneficiarios, total, media, desviación típica, mediana y cuartiles de cada importe, y los mismos percentiles de la fecha de concesión
- [ ] La ficha del dataset, el esquema y la publicación
- [ ] La evaluación de riesgos y la revisión legal, antes de la primera versión
