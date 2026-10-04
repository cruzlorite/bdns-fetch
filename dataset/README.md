# Dataset

El SQL que genera el dataset anonimizado de la BDNS a partir de una base de datos de `bdns-sync`. Es SQL de DuckDB y no forma parte del paquete de Python.

```console
$ duckdb /ruta/privada/dataset.duckdb \
    -cmd "ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY);
          SET VARIABLE output_dir = '/ruta/de/salida'" \
    -f dataset/build.sql
```

- Se lanza desde la raíz del repositorio, con la base de datos de `bdns-sync` conectada como `sync` y en modo solo lectura.
- El fichero de DuckDB tiene que ser privado: hasta el final contiene datos personales.
- `build.sql` ejecuta, en orden, los pasos de `sql/`. Lo que se publica queda en el esquema `publish`, los controles de privacidad paran la ejecución si encuentran algo que pueda identificar a una persona física y, si todo va bien, cada tabla se escribe como un fichero Parquet en la carpeta `output_dir`, que tiene que existir.
- Los datos van en español, como en la BDNS: las tablas, las columnas y también los valores que calcula el propio SQL, como el tipo de beneficiario (`persona_fisica`). El código, en cambio, va en inglés, como el resto del proyecto: macros, variables y comentarios. Los ficheros se llaman como la entidad de la BDNS que tratan (`10_concesiones.sql`) o como lo que hacen (`02_privacy.sql`).

Qué se publica, con qué detalle y por qué está en la [decisión 0020](../docs/adr/0020-anonymised-dataset.md), y el estado del trabajo, en la [página del dataset](https://cruzlorite.github.io/bdns-tools/dataset/).
