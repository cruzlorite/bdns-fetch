# Dataset

El SQL que genera el dataset anonimizado de la BDNS a partir de una base de datos de `bdns-sync`. Es SQL de DuckDB y no forma parte del paquete de Python.

```console
$ duckdb -cmd "SET temp_directory = '/ruta/privada/tmp';
               ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY);
               SET VARIABLE output_dir = '/ruta/de/salida'" \
    -f dataset/build.sql
```

- Se lanza desde la raíz del repositorio, con la base de datos de `bdns-sync` conectada como `sync` y en modo solo lectura.
- DuckDB trabaja en memoria y vuelca lo que no le cabe a `temp_directory`, con datos personales incluidos, así que esa carpeta tiene que ser privada; sin ella, la generación no arranca. DuckDB la vacía al terminar.
- `build.sql` ejecuta, en orden, los pasos de `sql/`. Lo que se publica queda en la base `publish`, aparte de la privada, los controles de privacidad paran la ejecución si encuentran algo que pueda identificar a una persona física y, si todo va bien, cada tabla se escribe como un fichero Parquet en la carpeta `output_dir`, que tiene que existir.
- Los datos conservan los nombres de la BDNS: las tablas se llaman como los endpoints de la API y las columnas, exactamente como sus campos (`codConcesion`, `fechaConcesion`…). Las que calcula el SQL siguen el mismo estilo (`tipoPersona`, `importeMediana`), y sus valores van en español (`persona_fisica`). El código, en cambio, va en inglés, como el resto del proyecto: macros, variables y comentarios. Los ficheros se llaman como la entidad de la BDNS que tratan (`11_ayudasestado.sql`) o como lo que hacen (`02_privacy.sql`).

Qué se publica, con qué detalle y por qué está en la [decisión 0020](../docs/adr/0020-anonymised-dataset.md), y el estado del trabajo, en la [página del dataset](https://cruzlorite.github.io/bdns-tools/dataset/).
