# What the dataset contains

Each table is published as a Parquet file with the same name (`concesiones_entidades.parquet`, for example) and each column's type, so DuckDB, pandas or R read it directly. Names are in Spanish, like the BDNS data, and text comes as the API returns it, except for the surplus spaces of a few fields. The examples on this page use made-up data.

<a id="entities"></a>
## Companies and public bodies

The first three tables hold, for each award or aid to a legal person or public body ([how they are classified](privacy.md#who)), the last version `bdns-sync` knows. Two things worth knowing before using them:

- **Awards the API has already withdrawn are still there**, with `retirada = true`. They are precisely the ones you cannot get any other way, so filter them out (`WHERE NOT retirada`) only if you want to see what the portal shows today.
- **The same tax ID may appear with its name spelt in several ways**, so to group by beneficiary, group by `nif`, not `nombre`.

### `concesiones_entidades`

Awards to legal persons and public bodies, one row per award. It comes from the awards search (`concesiones_busqueda` in `bdns-sync`).

| Column | Type | API field | What it is |
|---|---|---|---|
| `id` | `BIGINT` | `id` | The award's identifier in the BDNS |
| `cod_concesion` | `VARCHAR` | `codConcesion` | The award's code |
| `fecha_concesion` | `DATE` | `fechaConcesion` | Award date |
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID: the field's first word, upper-cased |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name, what follows the tax ID |
| `tipo_persona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `importe` | `DECIMAL(18,2)` | `importe` | Amount awarded, in euros |
| `ayuda_equivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Gross grant equivalent, in euros |
| `instrumento` | `VARCHAR` | `instrumento` | Aid instrument (`SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN`, `PRÉSTAMO`, `GARANTÍA`...) |
| `numero_convocatoria` | `VARCHAR` | `numeroConvocatoria` | The call's BDNS code |
| `convocatoria` | `VARCHAR` | `convocatoria` | The call's title |
| `nivel1` | `VARCHAR` | `nivel1` | Awarding administration: `ESTADO`, `AUTONOMICA`, `LOCAL` or `OTROS` |
| `nivel2` | `VARCHAR` | `nivel2` | Ministry, region or local authority |
| `nivel3` | `VARCHAR` | `nivel3` | Awarding body |
| `fecha_alta` | `DATE` | `fechaAlta` | Date the award was registered in the BDNS |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it. The row keeps its last version |

### `ayudas_estado_entidades`

State aid to legal persons and public bodies, one row per aid. It comes from the state aid search (`ayudasestado_busqueda`).

| Column | Type | API field | What it is |
|---|---|---|---|
| `id_concesion` | `BIGINT` | `idConcesion` | The award's identifier in the BDNS |
| `cod_concesion` | `VARCHAR` | `codConcesion` | The award's code |
| `fecha_concesion` | `DATE` | `fechaConcesion` | Award date |
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name, without the dash that sometimes separates it from the tax ID |
| `tipo_persona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `tipo_beneficiario` | `VARCHAR` | `tipoBeneficiario` | The BDNS's own category (`GRAN EMPRESA`, `PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA`...) |
| `importe` | `DECIMAL(18,2)` | `importe` | Amount awarded, in euros |
| `ayuda_equivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Gross grant equivalent, in euros |
| `instrumento` | `VARCHAR` | `instrumento` | Aid instrument |
| `numero_convocatoria` | `VARCHAR` | `numeroConvocatoria` | The call's BDNS code |
| `convocatoria` | `VARCHAR` | `convocatoria` | The call's title |
| `convocante` | `VARCHAR` | `convocante` | Calling body, with its administration and department |
| `reglamento` | `VARCHAR` | `reglamento` | The EU regulation the aid is based on |
| `objetivo` | `VARCHAR` | `objetivo` | The aid's objective, with the regulation's article |
| `region` | `VARCHAR` | `region` | Region, with its NUTS code (`ES300 - Madrid`) |
| `sectores` | `VARCHAR` | `sectores` | Sector of activity, with its CNAE code |
| `ayuda_estado` | `VARCHAR` | `ayudaEstado` | The European Commission's case number (`SA.000001`) |
| `url_ayuda_estado` | `VARCHAR` | `urlAyudaEstado` | Link to the European Commission's case, which is about the aid scheme, not the beneficiary |
| `entidad` | `VARCHAR` | `entidad` | Body through which the aid is awarded, if any |
| `intermediario` | `VARCHAR` | `intermediario` | Tax ID of the intermediary body, if any |
| `fecha_alta` | `DATE` | `fechaAlta` | Date the aid was registered in the BDNS |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

### `minimis_entidades`

De minimis aid to legal persons and public bodies, one row per aid. It comes from the de minimis search (`minimis_busqueda`).

| Column | Type | API field | What it is |
|---|---|---|---|
| `id_concesion` | `BIGINT` | `idConcesion` | The award's identifier in the BDNS |
| `codigo_concesion` | `VARCHAR` | `codigoConcesion` | The award's code |
| `fecha_concesion` | `DATE` | `fechaConcesion` | Award date |
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name |
| `tipo_persona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `ayuda_equivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Gross grant equivalent, in euros. It is the amount that counts towards the de minimis ceiling |
| `instrumento` | `VARCHAR` | `instrumento` | Aid instrument |
| `numero_convocatoria` | `VARCHAR` | `numeroConvocatoria` | The call's BDNS code |
| `convocante` | `VARCHAR` | `convocante` | Calling body |
| `reglamento` | `VARCHAR` | `reglamento` | The de minimis regulation applied |
| `sector_actividad` | `VARCHAR` | `sectorActividad` | Sector of activity, with its CNAE code |
| `sector_producto` | `VARCHAR` | `sectorProducto` | Product sector, when given |
| `fecha_registro` | `DATE` | `fechaRegistro` | Date the aid was registered in the BDNS |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

<a id="concesiones-personas"></a>
## Natural persons: `concesiones_personas`

Awards to natural persons, communities of property, civil partnerships, unrecognised beneficiaries and companies whose name carries a person's DNI, as one summary per call and instrument, plus one rest row per year with the calls that cannot be published ([the rules](privacy.md#rules)).

| Column | Type | What it is |
|---|---|---|
| `numero_convocatoria` | `VARCHAR` | The call's BDNS code. Empty in rest rows |
| `convocatoria` | `VARCHAR` | The call's title. Empty in rest rows and when it holds something shaped like a DNI |
| `nivel1`, `nivel2`, `nivel3` | `VARCHAR` | Awarding administration, department and body, as in `concesiones_entidades`. Empty in rest rows |
| `instrumento` | `VARCHAR` | Aid instrument. Empty in rest rows |
| `es_resto` | `BOOLEAN` | `true` in rest rows |
| `ejercicio` | `BIGINT` | A rest row's year, that of the median award date of each call it gathers. Empty in other rows |
| `concesiones` | `BIGINT` | Number of awards |
| `beneficiarios` | `BIGINT` | Number of different people, always 10 or more |
| `importe_total` | `DECIMAL(38,2)` | Sum of the amounts, in euros |
| `importe_media` | `DOUBLE` | Mean amount per award |
| `importe_desviacion` | `DOUBLE` | Standard deviation (sample) of the amounts |
| `importe_p10` | `DECIMAL(18,2)` | 10th percentile of the amount. Only with 20 people or more |
| `importe_p25` | `DECIMAL(18,2)` | First quartile of the amount |
| `importe_mediana` | `DECIMAL(18,2)` | Median amount |
| `importe_p75` | `DECIMAL(18,2)` | Third quartile of the amount |
| `importe_p90` | `DECIMAL(18,2)` | 90th percentile of the amount. Only with 20 people or more |
| `fecha_p10` | `DATE` | 10th percentile of the award date. Only with 20 people or more |
| `fecha_p25` | `DATE` | First quartile of the award date |
| `fecha_mediana` | `DATE` | Median award date |
| `fecha_p75` | `DATE` | Third quartile of the award date |
| `fecha_p90` | `DATE` | 90th percentile of the award date. Only with 20 people or more |

### How to read a row

Amounts and dates are computed over awards, so a person with two awards counts twice in them, though only once in `beneficiarios`. Amount percentiles are interpolated between the two nearest awards, and date percentiles are always a real award date:

```sql
SELECT concesiones, beneficiarios, importe_p10, importe_p25, importe_mediana, importe_p75, importe_p90
FROM 'concesiones_personas.parquet'
WHERE numero_convocatoria = '900101';
```

| concesiones | beneficiarios | importe_p10 | importe_p25 | importe_mediana | importe_p75 | importe_p90 |
|------------:|--------------:|------------:|------------:|----------------:|------------:|------------:|
| 250         | 250           | 1200.00     | 1800.00     | 2400.00         | 2400.00     | 3600.00     |

Half the awards were between 1,800 and 2,400 euros, and 80% between 1,200 and 3,600. In calls with fewer than 20 people, the 10th and 90th percentiles are empty.

<a id="rest"></a>
### Rest rows and totals

Calls that cannot be published are gathered into one rest row per year, with `es_resto = true`, no call number and the year in `ejercicio`, the year of the median award date of each call it holds. Using the same rule for the published calls, you can add everything up per year:

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

Even so, the total falls somewhat short, because awards that reach no publishable row (those of a small call that is the only one in its year, for example) are not in the dataset.

<a id="whole-call"></a>
## A whole call

A call may have beneficiaries of both kinds, and to see it whole you join both parts on `numero_convocatoria`:

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

A call using several instruments (grants and loans, for example) has one summary per instrument, and then you should group by `instrumento` too.
