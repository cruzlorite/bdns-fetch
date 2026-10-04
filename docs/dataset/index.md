---
icon: material/chart-box
---

# BDNS Dataset

!!! warning "En preparación"

    Todavía no hay ninguna versión publicada. Esta sección cuenta qué será el dataset y cómo se está construyendo, y el código es experimental: puede cambiar en cualquier versión hasta que se publique la primera.

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

Todas las transformaciones son ficheros SQL que se ejecutan en DuckDB, uno detrás de otro, sobre una copia privada de las tablas de `bdns-sync`. Están en [`src/bdns/dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/src/bdns/dataset/sql), y se pueden leer, revisar y volver a ejecutar tal cual. Este es el que clasifica a los beneficiarios, mostrado directamente desde el código:

```sql
--8<-- "src/bdns/dataset/sql/00_beneficiaries.sql"
```

## Estado

- [x] La decisión de diseño, como propuesta ([decisión 0002](../adr/0002-anonymised-dataset.md))
- [x] La clasificación de beneficiarios ([en SQL](#sql)) y los controles de privacidad ([`privacy`][bdns.dataset.privacy])
- [x] La extracción de la última versión conocida de cada registro, incluidos los que la API ya ha retirado ([`extract`][bdns.dataset.extract])
- [x] Las concesiones con sus columnas y el tipo de beneficiario (`10_concesiones.sql`)
- [ ] Los agregados, con control de revelación estadística
- [ ] La ficha del dataset, el esquema y la publicación
- [ ] La evaluación de riesgos y la revisión legal, antes de la primera versión
