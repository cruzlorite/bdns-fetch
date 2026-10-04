---
icon: material/chart-box
---

# BDNS Dataset

!!! warning "En preparación"

    Todavía no hay ninguna versión publicada. Esta sección cuenta qué será el dataset y cómo se está construyendo, y su SQL es experimental: puede cambiar en cualquier momento hasta que se publique la primera versión.

Un conjunto de datos listo para usar con **todo el histórico** de la BDNS que conserva `bdns-sync`, y no solo con los años que todavía publica el portal ([por qué importa](../sync/index.md#why-history)). Irá siempre **anonimizado y agregado**: proteger a las personas físicas es la prioridad, y todo el proceso tiene que cumplir las condiciones de reutilización de la IGAE, el RGPD y la LOPDGDD. Qué se publica, con qué detalle y por qué lo recoge la [decisión 0002](../adr/0002-anonymised-dataset.md), que todavía es una propuesta.

## Cómo se protege a las personas físicas

Cada beneficiario se clasifica a partir de su NIF, nunca de su nombre, y lo que no se reconoce se trata como una persona física. Por ejemplo (los nombres y los NIF son inventados):

| Cómo aparece en la BDNS | Se clasifica como | En el dataset |
|---|---|---|
| `***1234** NOMBRE APELLIDOS` | Persona física | Solo agregado |
| `E12345678 APELLIDO Y APELLIDO CB` | Entidad formada por personas | Solo agregado |
| `123456789012 FOREIGN COMPANY LTD` | Dudoso | Solo agregado |
| `B12345678 EMPRESA DE EJEMPLO SL` | Persona jurídica | Registro a registro |
| `P1234567D AYUNTAMIENTO DE EJEMPLO` | Entidad pública | Registro a registro |

Las comunidades de bienes y las sociedades civiles tienen NIF propio, pero suelen llevar el nombre de sus miembros, y por eso se protegen igual que una persona física.

Antes de escribir nada, la generación comprueba lo que va a publicar y **se para** si encuentra un valor con forma de DNI, NIE o NIF enmascarado, una columna que identifica a alguien (`beneficiario`, `idPersona`, `urlBR`...) o una celda agregada con menos de diez beneficiarios. No limpia lo que encuentra: lo señala, porque un fallo así indica un error anterior que hay que corregir.

<a id="sql"></a>
## El SQL

Todo el proceso es SQL de DuckDB, sin una línea de Python. DuckDB se conecta a la base de datos de `bdns-sync` (SQLite, PostgreSQL, DuckDB o BigQuery), lee sus tablas y deja el resultado en un fichero privado, porque hasta el final contiene datos personales. Los pasos son ficheros SQL en [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), que se pueden leer, revisar y volver a ejecutar tal cual, y se lanzan todos desde la raíz del repositorio con la línea de comandos de DuckDB:

```console
$ duckdb /ruta/privada/dataset.duckdb \
    -cmd "ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY);
          SET VARIABLE salida = '/ruta/de/salida'" \
    -f dataset/build.sql
```

Este es el paso que clasifica a los beneficiarios, mostrado directamente desde el código:

```sql
--8<-- "dataset/sql/01_beneficiaries.sql"
```

## Estado

- [x] La decisión de diseño, como propuesta ([decisión 0002](../adr/0002-anonymised-dataset.md))
- [x] La clasificación de beneficiarios y las piezas de los controles de privacidad, en SQL
- [x] Las concesiones, leídas directamente de `bdns-sync` con la última versión conocida de cada una, incluidas las que la API ya ha retirado, con sus columnas y el tipo de beneficiario
- [x] Las concesiones, ayudas de Estado y minimis a personas jurídicas y entidades públicas, registro a registro, sin el enlace al boletín ni el identificador interno de la BDNS, y los controles que las vigilan
- [x] La exportación a Parquet, que solo se hace si pasan todos los controles
- [x] Los agregados de concesiones a personas físicas por convocatoria y año, con supresión de celdas y fila de "resto" (en la muestra real se publica el 98,8 % de los beneficiarios)
- [ ] Los mismos agregados para ayudas de Estado y minimis, y el reparto de importes
- [ ] La ficha del dataset, el esquema y la publicación
- [ ] La evaluación de riesgos y la revisión legal, antes de la primera versión
