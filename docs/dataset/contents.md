# Qué contiene el dataset

Cada tabla se publica como un fichero Parquet con su mismo nombre (`concesiones_entidades.parquet`, por ejemplo) y con los tipos de cada columna, así que DuckDB, pandas o R la leen directamente. Los nombres van en español, como en la BDNS, y los textos, tal y como los devuelve la API, salvo los espacios sobrantes de algunos campos. Los ejemplos de esta página usan datos inventados.

<a id="entities"></a>
## Empresas y entidades públicas

Las tres primeras tablas tienen, de cada concesión o ayuda a una persona jurídica o a una entidad pública ([cómo se clasifican](privacy.md#who)), la última versión que conoce `bdns-sync`. Dos cosas que conviene saber antes de usarlas:

- **Las concesiones que la API ya ha retirado siguen ahí**, con `retirada = true`. Son justo las que no puedes conseguir de otra forma, así que fíltralas (`WHERE NOT retirada`) solo si quieres ver lo mismo que muestra hoy el portal.
- **Un mismo NIF puede aparecer con el nombre escrito de varias formas**, así que, para agrupar por beneficiario, agrupa por `nif` y no por `nombre`.

### `concesiones_entidades`

Las concesiones a personas jurídicas y entidades públicas, una fila por concesión. Sale de la búsqueda de concesiones (`concesiones_busqueda` en `bdns-sync`).

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `id` | `BIGINT` | `id` | Identificador de la concesión en la BDNS |
| `cod_concesion` | `VARCHAR` | `codConcesion` | Código de la concesión |
| `fecha_concesion` | `DATE` | `fechaConcesion` | Fecha de concesión |
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario: la primera palabra del campo, en mayúsculas |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario, lo que va después del NIF |
| `tipo_persona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `importe` | `DECIMAL(18,2)` | `importe` | Importe concedido, en euros |
| `ayuda_equivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Ayuda equivalente (el equivalente de subvención bruta), en euros |
| `instrumento` | `VARCHAR` | `instrumento` | Instrumento de ayuda (`SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN`, `PRÉSTAMO`, `GARANTÍA`...) |
| `numero_convocatoria` | `VARCHAR` | `numeroConvocatoria` | Código BDNS de la convocatoria |
| `convocatoria` | `VARCHAR` | `convocatoria` | Título de la convocatoria |
| `nivel1` | `VARCHAR` | `nivel1` | Administración que concede: `ESTADO`, `AUTONOMICA`, `LOCAL` u `OTROS` |
| `nivel2` | `VARCHAR` | `nivel2` | Ministerio, comunidad autónoma o entidad local |
| `nivel3` | `VARCHAR` | `nivel3` | Órgano que concede |
| `fecha_alta` | `DATE` | `fechaAlta` | Fecha en que la concesión se registró en la BDNS |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve. La fila conserva su última versión |

### `ayudas_estado_entidades`

Las ayudas de Estado a personas jurídicas y entidades públicas, una fila por ayuda. Sale de la búsqueda de ayudas de Estado (`ayudasestado_busqueda`).

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `id_concesion` | `BIGINT` | `idConcesion` | Identificador de la concesión en la BDNS |
| `cod_concesion` | `VARCHAR` | `codConcesion` | Código de la concesión |
| `fecha_concesion` | `DATE` | `fechaConcesion` | Fecha de concesión |
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario, sin el guion que a veces lo separa del NIF |
| `tipo_persona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `tipo_beneficiario` | `VARCHAR` | `tipoBeneficiario` | Categoría que da la propia BDNS (`GRAN EMPRESA`, `PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA`...) |
| `importe` | `DECIMAL(18,2)` | `importe` | Importe concedido, en euros |
| `ayuda_equivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Ayuda equivalente (el equivalente de subvención bruta), en euros |
| `instrumento` | `VARCHAR` | `instrumento` | Instrumento de ayuda |
| `numero_convocatoria` | `VARCHAR` | `numeroConvocatoria` | Código BDNS de la convocatoria |
| `convocatoria` | `VARCHAR` | `convocatoria` | Título de la convocatoria |
| `convocante` | `VARCHAR` | `convocante` | Órgano convocante, con su administración y su departamento |
| `reglamento` | `VARCHAR` | `reglamento` | Reglamento europeo en el que se basa la ayuda |
| `objetivo` | `VARCHAR` | `objetivo` | Objetivo de la ayuda, con el artículo del reglamento |
| `region` | `VARCHAR` | `region` | Región, con su código NUTS (`ES300 - Madrid`) |
| `sectores` | `VARCHAR` | `sectores` | Sector de actividad, con su código CNAE |
| `ayuda_estado` | `VARCHAR` | `ayudaEstado` | Número del caso en la Comisión Europea (`SA.000001`) |
| `url_ayuda_estado` | `VARCHAR` | `urlAyudaEstado` | Enlace al caso en la Comisión Europea, que trata del régimen de ayudas y no del beneficiario |
| `entidad` | `VARCHAR` | `entidad` | Entidad a través de la que se concede, cuando la hay |
| `intermediario` | `VARCHAR` | `intermediario` | NIF de la entidad intermediaria, cuando la hay |
| `fecha_alta` | `DATE` | `fechaAlta` | Fecha en que la ayuda se registró en la BDNS |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve |

### `minimis_entidades`

Las ayudas de minimis a personas jurídicas y entidades públicas, una fila por ayuda. Sale de la búsqueda de minimis (`minimis_busqueda`).

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `id_concesion` | `BIGINT` | `idConcesion` | Identificador de la concesión en la BDNS |
| `codigo_concesion` | `VARCHAR` | `codigoConcesion` | Código de la concesión |
| `fecha_concesion` | `DATE` | `fechaConcesion` | Fecha de concesión |
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario |
| `tipo_persona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `ayuda_equivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Ayuda equivalente (el equivalente de subvención bruta), en euros. Es el importe que cuenta para el límite de minimis |
| `instrumento` | `VARCHAR` | `instrumento` | Instrumento de ayuda |
| `numero_convocatoria` | `VARCHAR` | `numeroConvocatoria` | Código BDNS de la convocatoria |
| `convocante` | `VARCHAR` | `convocante` | Órgano convocante |
| `reglamento` | `VARCHAR` | `reglamento` | Reglamento de minimis que se aplica |
| `sector_actividad` | `VARCHAR` | `sectorActividad` | Sector de actividad, con su código CNAE |
| `sector_producto` | `VARCHAR` | `sectorProducto` | Sector del producto, cuando se indica |
| `fecha_registro` | `DATE` | `fechaRegistro` | Fecha en que la ayuda se registró en la BDNS |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve |

<a id="concesiones-personas"></a>
## Personas físicas: `concesiones_personas`

Las concesiones a personas físicas, comunidades de bienes, sociedades civiles, beneficiarios que no se reconocen y empresas cuyo nombre lleva el DNI de una persona, como un resumen por convocatoria e instrumento, más una fila de resto por año con las convocatorias que no se pueden publicar ([las reglas](privacy.md#rules)).

| Columna | Tipo | Qué es |
|---|---|---|
| `numero_convocatoria` | `VARCHAR` | Código BDNS de la convocatoria. Vacío en las filas de resto |
| `convocatoria` | `VARCHAR` | Título de la convocatoria. Vacío en las filas de resto y cuando contiene algo con forma de DNI |
| `nivel1`, `nivel2`, `nivel3` | `VARCHAR` | Administración, departamento y órgano que conceden, como en `concesiones_entidades`. Si no son los mismos en todas las concesiones de la convocatoria, los de la mayoría. Vacíos en las filas de resto |
| `instrumento` | `VARCHAR` | Instrumento de ayuda. Vacío en las filas de resto |
| `es_resto` | `BOOLEAN` | `true` en las filas de resto |
| `ejercicio` | `BIGINT` | Año de una fila de resto, que es el de la fecha mediana de cada convocatoria que junta. Vacío en las demás filas |
| `concesiones` | `BIGINT` | Número de concesiones |
| `beneficiarios` | `BIGINT` | Número de personas distintas, siempre 10 o más |
| `importe_total` | `DECIMAL(38,2)` | Suma de los importes, en euros |
| `importe_media` | `DECIMAL(18,2)` | Importe medio por concesión, redondeado al céntimo |
| `importe_desviacion` | `DECIMAL(18,2)` | Desviación típica (muestral) de los importes, redondeada al céntimo |
| `importe_p10` | `DECIMAL(18,2)` | Percentil 10 del importe. Solo con 20 personas o más |
| `importe_p25` | `DECIMAL(18,2)` | Primer cuartil del importe |
| `importe_mediana` | `DECIMAL(18,2)` | Mediana del importe |
| `importe_p75` | `DECIMAL(18,2)` | Tercer cuartil del importe |
| `importe_p90` | `DECIMAL(18,2)` | Percentil 90 del importe. Solo con 20 personas o más |
| `fecha_p10` | `DATE` | Percentil 10 de la fecha de concesión. Solo con 20 personas o más |
| `fecha_p25` | `DATE` | Primer cuartil de la fecha de concesión |
| `fecha_mediana` | `DATE` | Mediana de la fecha de concesión |
| `fecha_p75` | `DATE` | Tercer cuartil de la fecha de concesión |
| `fecha_p90` | `DATE` | Percentil 90 de la fecha de concesión. Solo con 20 personas o más |

### Cómo se lee una fila

Los importes y las fechas se calculan sobre las concesiones, de modo que una persona con dos concesiones cuenta dos veces en ellos, aunque en `beneficiarios` cuente una. Los percentiles del importe se interpolan entre las dos concesiones más cercanas, y los de la fecha son siempre una fecha de concesión real:

```sql
SELECT concesiones, beneficiarios, importe_p10, importe_p25, importe_mediana, importe_p75, importe_p90
FROM 'concesiones_personas.parquet'
WHERE numero_convocatoria = '900101';
```

| concesiones | beneficiarios | importe_p10 | importe_p25 | importe_mediana | importe_p75 | importe_p90 |
|------------:|--------------:|------------:|------------:|----------------:|------------:|------------:|
| 250         | 250           | 1200.00     | 1800.00     | 2400.00         | 2400.00     | 3600.00     |

La mitad de las concesiones fue de entre 1.800 y 2.400 euros, y el 80 %, de entre 1.200 y 3.600. En las convocatorias con menos de 20 personas, el percentil 10 y el 90 vienen vacíos.

<a id="rest"></a>
### Las filas de resto y los totales

Las convocatorias que no se pueden publicar se juntan en una fila de resto por año, con `es_resto = true`, sin número de convocatoria y con el año en `ejercicio`, que es el de la fecha mediana de cada convocatoria que reúne. Si usas el mismo criterio para las convocatorias publicadas, puedes sumarlo todo por año:

```sql
SELECT
    coalesce(ejercicio, year(fecha_mediana)) AS ejercicio,
    sum(concesiones) AS concesiones,
    sum(importe_total) AS importe
FROM 'concesiones_personas.parquet'
GROUP BY ALL
ORDER BY ejercicio;
```

| ejercicio | concesiones |  importe  |
|----------:|------------:|----------:|
| 2025      | 40          | 8580.00   |
| 2026      | 277         | 734000.00 |

Aun así, el total se queda algo corto, porque las concesiones que no llegan a ninguna fila publicable (por ejemplo, las de una convocatoria pequeña que es la única de su año) no están en el dataset.

<a id="whole-call"></a>
## Una convocatoria entera

Una convocatoria puede tener beneficiarios de los dos tipos, y para verla entera hay que juntar las dos partes por `numero_convocatoria`:

```sql
WITH entidades AS (
    SELECT numero_convocatoria, count(*) AS concesiones, sum(importe) AS importe
    FROM 'concesiones_entidades.parquet'
    GROUP BY numero_convocatoria
)
SELECT
    p.numero_convocatoria,
    p.concesiones AS concesiones_personas,
    p.importe_total AS importe_personas,
    e.concesiones AS concesiones_entidades,
    e.importe AS importe_entidades
FROM 'concesiones_personas.parquet' p
LEFT JOIN entidades e USING (numero_convocatoria)
WHERE NOT p.es_resto
ORDER BY p.numero_convocatoria;
```

| numero_convocatoria | concesiones_personas | importe_personas | concesiones_entidades | importe_entidades |
|---------------------|---------------------:|-----------------:|----------------------:|------------------:|
| 900101              | 250                  | 588000.00        | NULL                  | NULL              |
| 900102              | 40                   | 8580.00          | NULL                  | NULL              |
| 900103              | 14                   | 51000.00         | 1                     | 90000.00          |

Si una convocatoria usa varios instrumentos (por ejemplo, subvenciones y préstamos), tiene un resumen por cada uno, y entonces conviene agrupar también por `instrumento`.
