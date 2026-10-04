# Dataset

El SQL que genera el dataset anonimizado de la BDNS a partir de una base de datos de `bdns-sync`. Es SQL de DuckDB y nada más: no forma parte del paquete de Python.

```console
$ duckdb /ruta/privada/dataset.duckdb \
    -cmd "ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY)" \
    -f dataset/build.sql
```

- Se lanza desde la raíz del repositorio, con la base de datos de `bdns-sync` conectada como `sync` y en modo solo lectura.
- El fichero de DuckDB tiene que ser privado: hasta el final contiene datos personales.
- `build.sql` ejecuta, en orden, los pasos de `sql/`. Lo que se publica queda en el esquema `publicar`, y los controles de privacidad paran la ejecución si encuentran algo que pueda identificar a una persona física.

Qué se publica, con qué detalle y por qué está en la [decisión 0002](../docs/adr/0002-anonymised-dataset.md), y el estado del trabajo, en la [página del dataset](https://cruzlorite.github.io/bdns-tools/dataset/).
