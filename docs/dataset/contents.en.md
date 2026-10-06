# What the dataset contains

Each table is published as a Parquet file with the same name (`concesiones_personas_juridicas.parquet`, for example) and each column's type, so DuckDB, pandas or R read it directly. Tables are named after the API's endpoints, and columns exactly as its fields (`codConcesion`, `fechaConcesion`…); those the dataset computes follow the same style (`tipoPersona`, `importeMediana`…). Text comes as the API returns it, except for the surplus spaces of a few fields. The examples on this page use made-up data.

<a id="entities"></a>
## Legal persons

The first three tables hold, for each award or aid to a legal person or public body ([how they are classified](privacy.md#who)), the last version `bdns-sync` knows. Two things worth knowing before using them:

- **Awards the API has already withdrawn are still there**, with `retirada = true`. They are precisely the ones you cannot get any other way, so filter them out (`WHERE NOT retirada`) only if you want to see what the portal shows today.
- **The same tax ID may appear with its name spelt in several ways**, so to group by beneficiary, group by `nif`, not `nombre`.

### `concesiones_personas_juridicas`

Awards to legal persons and public bodies, one row per award. It comes from the awards search (`concesiones_busqueda` in `bdns-sync`).

| Column | Type | API field | What it is |
|---|---|---|---|
| `id` | `BIGINT` | `id` | The award's identifier in the BDNS |
| `codConcesion` | `VARCHAR` | `codConcesion` | The award's code |
| `fechaConcesion` | `DATE` | `fechaConcesion` | Award date |
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID: the field's first word, upper-cased |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name, what follows the tax ID |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `importe` | `DECIMAL(18,2)` | `importe` | Amount awarded, in euros |
| `ayudaEquivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Gross grant equivalent, in euros |
| `instrumento` | `VARCHAR` | `instrumento` | Aid instrument (`SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN`, `PRÉSTAMO`, `GARANTÍA`...) |
| `numeroConvocatoria` | `VARCHAR` | `numeroConvocatoria` | The call's BDNS code |
| `convocatoria` | `VARCHAR` | `convocatoria` | The call's title |
| `nivel1` | `VARCHAR` | `nivel1` | Awarding administration: `ESTADO`, `AUTONOMICA`, `LOCAL` or `OTROS` |
| `nivel2` | `VARCHAR` | `nivel2` | Ministry, region or local authority |
| `nivel3` | `VARCHAR` | `nivel3` | Awarding body |
| `fechaAlta` | `DATE` | `fechaAlta` | Date the award was registered in the BDNS |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it. The row keeps its last version |

### `ayudasestado_personas_juridicas`

State aid to legal persons and public bodies, one row per aid. It comes from the state aid search (`ayudasestado_busqueda`).

| Column | Type | API field | What it is |
|---|---|---|---|
| `idConcesion` | `BIGINT` | `idConcesion` | The award's identifier in the BDNS |
| `codConcesion` | `VARCHAR` | `codConcesion` | The award's code |
| `fechaConcesion` | `DATE` | `fechaConcesion` | Award date |
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name, without the dash that sometimes separates it from the tax ID |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `tipoBeneficiario` | `VARCHAR` | `tipoBeneficiario` | The BDNS's own category (`GRAN EMPRESA`, `PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA`...) |
| `importe` | `DECIMAL(18,2)` | `importe` | Amount awarded, in euros |
| `ayudaEquivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Gross grant equivalent, in euros |
| `instrumento` | `VARCHAR` | `instrumento` | Aid instrument |
| `numeroConvocatoria` | `VARCHAR` | `numeroConvocatoria` | The call's BDNS code |
| `convocatoria` | `VARCHAR` | `convocatoria` | The call's title |
| `convocante` | `VARCHAR` | `convocante` | Calling body, with its administration and department |
| `reglamento` | `STRUCT(descripcion, orden)` | `reglamento` | The EU regulation the aid is based on |
| `objetivo` | `VARCHAR` | `objetivo` | The aid's objective, with the regulation's article |
| `region` | `VARCHAR` | `region` | Region, with its NUTS code (`ES300 - Madrid`) |
| `sectores` | `VARCHAR` | `sectores` | Sector of activity, with its CNAE code |
| `ayudaEstado` | `VARCHAR` | `ayudaEstado` | The European Commission's case number (`SA.000001`) |
| `urlAyudaEstado` | `VARCHAR` | `urlAyudaEstado` | Link to the European Commission's case, which is about the aid scheme, not the beneficiary |
| `entidad` | `VARCHAR` | `entidad` | Body through which the aid is awarded, if any |
| `intermediario` | `VARCHAR` | `intermediario` | Tax ID of the intermediary body, if any |
| `fechaAlta` | `DATE` | `fechaAlta` | Date the aid was registered in the BDNS |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

### `minimis_personas_juridicas`

De minimis aid to legal persons and public bodies, one row per aid. It comes from the de minimis search (`minimis_busqueda`).

| Column | Type | API field | What it is |
|---|---|---|---|
| `idConcesion` | `BIGINT` | `idConcesion` | The award's identifier in the BDNS |
| `codigoConcesion` | `VARCHAR` | `codigoConcesion` | The award's code |
| `fechaConcesion` | `DATE` | `fechaConcesion` | Award date |
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `ayudaEquivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Gross grant equivalent, in euros. It is the amount that counts towards the de minimis ceiling |
| `instrumento` | `VARCHAR` | `instrumento` | Aid instrument |
| `numeroConvocatoria` | `VARCHAR` | `numeroConvocatoria` | The call's BDNS code |
| `convocante` | `VARCHAR` | `convocante` | Calling body |
| `reglamento` | `STRUCT(descripcion, orden)` | `reglamento` | The de minimis regulation applied |
| `sectorActividad` | `VARCHAR` | `sectorActividad` | Sector of activity, with its CNAE code |
| `sectorProducto` | `VARCHAR` | `sectorProducto` | Product sector, when given |
| `fechaRegistro` | `DATE` | `fechaRegistro` | Date the aid was registered in the BDNS |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

<a id="personas-fisicas"></a>
## Natural persons

Three tables, one per entity, with one summary per call and instrument of the awards to natural persons and to those protected like them (communities of property, civil partnerships, unrecognised beneficiaries and companies whose name carries a person's DNI), plus one rest row per year with the calls that cannot be published ([the rules](privacy.md#rules)). In state aid and de minimis aid, nearly all these people are self-employed.

The three share their columns, except those that identify the call and the amount ones, which depend on what each entity carries:

- **`concesiones_personas_fisicas`**: the call's number and title, the three levels of the awarding body, and statistics of the amount and of the gross grant equivalent.
- **`ayudasestado_personas_fisicas`**: the call's number and title, the calling body, and statistics of the amount and of the gross grant equivalent.
- **`minimis_personas_fisicas`**: the call's number, the calling body, and statistics of the gross grant equivalent, since de minimis records carry no amount.

| Column | Type | What it is |
|---|---|---|
| `numeroConvocatoria` | `VARCHAR` | The call's BDNS code. Empty in rest rows |
| `convocatoria` | `VARCHAR` | The call's title. Empty in rest rows and when it holds something shaped like a DNI |
| `nivel1`, `nivel2`, `nivel3` | `VARCHAR` | Awarding administration, department and body, as in `concesiones_personas_juridicas` |
| `convocante` | `VARCHAR` | Calling body, as in the legal-person tables |
| `instrumento` | `VARCHAR` | Aid instrument. Empty in rest rows |
| `esResto` | `BOOLEAN` | `true` in rest rows |
| `ejercicio` | `BIGINT` | A rest row's year, that of the median award date of each call it gathers. Empty in other rows |
| `concesiones` | `BIGINT` | Number of awards |
| `beneficiarios` | `BIGINT` | Number of different people, always 10 or more |
| `importeTotal` | `DECIMAL(38,2)` | Sum of the amounts, in euros |
| `importeMedia` | `DECIMAL(18,2)` | Mean amount per award, rounded to the cent |
| `importeDesviacion` | `DECIMAL(18,2)` | Standard deviation (sample) of the amounts, rounded to the cent |
| `importeP10` | `DECIMAL(18,2)` | 10th percentile of the amount. Only with 20 people or more |
| `importeP25` | `DECIMAL(18,2)` | First quartile of the amount |
| `importeMediana` | `DECIMAL(18,2)` | Median amount |
| `importeP75` | `DECIMAL(18,2)` | Third quartile of the amount |
| `importeP90` | `DECIMAL(18,2)` | 90th percentile of the amount. Only with 20 people or more |
| `fechaConcesionP10` | `DATE` | 10th percentile of the award date. Only with 20 people or more |
| `fechaConcesionP25` | `DATE` | First quartile of the award date |
| `fechaConcesionMediana` | `DATE` | Median award date |
| `fechaConcesionP75` | `DATE` | Third quartile of the award date |
| `fechaConcesionP90` | `DATE` | 90th percentile of the award date. Only with 20 people or more |

The columns `ayudaEquivalenteTotal`, `ayudaEquivalenteMedia` and so on are the same statistics for the gross grant equivalent. If the title or the body differ across a call's awards, those of most of them are published, and in rest rows they are empty.

### How to read a row

Amounts and dates are computed over awards, so a person with two awards counts twice in them, though only once in `beneficiarios`. Amount percentiles are interpolated between the two nearest awards, and date percentiles are always a real award date:

```sql
SELECT concesiones, beneficiarios, importeP10, importeP25, importeMediana, importeP75, importeP90
FROM 'concesiones_personas_fisicas.parquet'
WHERE numeroConvocatoria = '900101';
```

| concesiones | beneficiarios | importeP10 | importeP25 | importeMediana | importeP75 | importeP90 |
|------------:|--------------:|-----------:|-----------:|---------------:|-----------:|-----------:|
| 250         | 250           | 1200.00    | 1800.00    | 2400.00        | 2400.00    | 3600.00    |

Half the awards were between 1,800 and 2,400 euros, and 80% between 1,200 and 3,600. In calls with fewer than 20 people, the 10th and 90th percentiles are empty.

<a id="rest"></a>
### Rest rows and totals

Calls that cannot be published are gathered into one rest row per year, with `esResto = true`, no call number and the year in `ejercicio`, the year of the median award date of each call it holds. Using the same rule for the published calls, you can add everything up per year:

```sql
SELECT
    coalesce(ejercicio, year(fechaConcesionMediana)) AS ejercicio,
    sum(concesiones) AS concesiones,
    sum(importeTotal) AS importe
FROM 'concesiones_personas_fisicas.parquet'
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

A call may have beneficiaries of both kinds, and to see it whole you join both parts on `numeroConvocatoria`:

```sql
WITH juridicas AS (
    SELECT numeroConvocatoria, count(*) AS concesiones, sum(importe) AS importe
    FROM 'concesiones_personas_juridicas.parquet'
    GROUP BY numeroConvocatoria
)
SELECT
    f.numeroConvocatoria,
    f.concesiones AS concesiones_fisicas,
    f.importeTotal AS importe_fisicas,
    j.concesiones AS concesiones_juridicas,
    j.importe AS importe_juridicas
FROM 'concesiones_personas_fisicas.parquet' f
LEFT JOIN juridicas j USING (numeroConvocatoria)
WHERE NOT f.esResto
ORDER BY f.numeroConvocatoria;
```

| numeroConvocatoria | concesiones_fisicas | importe_fisicas | concesiones_juridicas | importe_juridicas |
|--------------------|--------------------:|----------------:|----------------------:|------------------:|
| 900101             | 250                 | 588000.00       | NULL                  | NULL              |
| 900102             | 40                  | 8580.00         | NULL                  | NULL              |
| 900103             | 14                  | 51000.00        | 1                     | 90000.00          |

A call using several instruments (grants and loans, for example) has one summary per instrument, and then you should group by `instrumento` too.

## `convocatorias`

Calls for applications, one row per call, with the last version of its detail that `bdns-sync` knows (the `convocatorias` table, with each call's detail). Fields keep the API's names and shape: the body is an object with its three levels, and lists (instruments, sectors, regions…) are lists of objects. They join the other tables on `codigoBDNS`, which is their `numeroConvocatoria`.

Texts the body writes by hand (the title, the description of the regulatory bases, the dates as text) are published empty if they hold something shaped like a DNI, and so is the link to the bases when it has that shape. Left out are the documents and the bulletin announcements, since they often list the beneficiaries, and the portal's legal notice, which is the same in every call.

| Column | Type | API field | What it is |
|---|---|---|---|
| `id` | `BIGINT` | `id` | The call's internal identifier |
| `codigoBDNS` | `VARCHAR` | `codigoBDNS` | The call's BDNS code |
| `fechaRecepcion` | `DATE` | `fechaRecepcion` | Date the call reached the BDNS |
| `organo` | `STRUCT(nivel1, nivel2, nivel3)` | `organo` | Calling administration, department and body |
| `sedeElectronica` | `VARCHAR` | `sedeElectronica` | Online office where it is processed |
| `descripcion` | `VARCHAR` | `descripcion` | The call's title |
| `descripcionLeng` | `VARCHAR` | `descripcionLeng` | Title in the co-official language, if any |
| `tipoConvocatoria` | `VARCHAR` | `tipoConvocatoria` | Kind of procedure (competitive, direct award…) |
| `presupuestoTotal` | `DECIMAL(18,2)` | `presupuestoTotal` | Total budget, in euros |
| `mrr` | `BOOLEAN` | `mrr` | Whether the Recovery and Resilience Facility funds it |
| `instrumentos` | `STRUCT(descripcion)[]` | `instrumentos` | Aid instruments |
| `tiposBeneficiarios` | `STRUCT(descripcion)[]` | `tiposBeneficiarios` | Kinds of beneficiary it targets |
| `sectores` | `STRUCT(codigo, descripcion)[]` | `sectores` | Sectors of activity, with their CNAE code |
| `regiones` | `STRUCT(descripcion)[]` | `regiones` | Regions, with their NUTS code |
| `descripcionFinalidad` | `VARCHAR` | `descripcionFinalidad` | The call's purpose |
| `descripcionBasesReguladoras` | `VARCHAR` | `descripcionBasesReguladoras` | The rule that approves the regulatory bases |
| `urlBasesReguladoras` | `VARCHAR` | `urlBasesReguladoras` | Link to the regulatory bases |
| `sePublicaDiarioOficial` | `BOOLEAN` | `sePublicaDiarioOficial` | Whether it is published in an official journal |
| `abierto` | `BOOLEAN` | `abierto` | Whether the application period was open in the last known version |
| `fechaInicioSolicitud`, `fechaFinSolicitud` | `DATE` | `fechaInicioSolicitud`, `fechaFinSolicitud` | Application period, when given as dates |
| `textInicio`, `textFin` | `VARCHAR` | `textInicio`, `textFin` | The application period as the body writes it |
| `ayudaEstado`, `urlAyudaEstado` | `VARCHAR` | `ayudaEstado`, `urlAyudaEstado` | The European Commission's state aid case and its link |
| `fondos` | `STRUCT(descripcion)[]` | `fondos` | European funds that finance it |
| `reglamento` | `STRUCT(descripcion, orden)` | `reglamento` | The EU regulation it is based on |
| `objetivos` | `STRUCT(descripcion)[]` | `objetivos` | Objectives, with the regulation's article |
| `sectoresProductos` | `STRUCT(descripcion)[]` | `sectoresProductos` | Product sectors |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

## `partidospoliticos`

Awards to political parties and their foundations, one row per award. Every beneficiary is a legal person; should a protected one ever turn up, it would be left out. It has the columns of `concesiones_personas_juridicas`, except `fechaAlta`, which this search does not carry, plus two:

| Column | Type | API field | What it is |
|---|---|---|---|
| `tieneProyecto` | `BOOLEAN` | `tieneProyecto` | Whether the award has a project attached |
| `idConvocatoria` | `BIGINT` | `idConvocatoria` | The call's internal identifier |

## `grandesbeneficiarios`

The BDNS list of large beneficiaries: the total aid each one received in a year. Only legal persons are published, public bodies included. The natural persons and communities of property on the list are left out, and summarising them would make no sense, since each row is already one beneficiary's total.

| Column | Type | API field | What it is |
|---|---|---|---|
| `nif` | `VARCHAR` | `beneficiario` | The beneficiary's tax ID |
| `nombre` | `VARCHAR` | `beneficiario` | The beneficiary's name |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` or `entidad_publica` |
| `ejercicio` | `INTEGER` | `ejercicio` | Year |
| `ayudaETotal` | `DECIMAL(18,2)` | `ayudaETotal` | Total gross grant equivalent of the year, in euros |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

## `planesestrategicos`

The administrations' strategic subsidy plans, one per row, without the attached documents or the portal's legal notice.

| Column | Type | API field | What it is |
|---|---|---|---|
| `idPES` | `BIGINT` | `idPES` | The plan's identifier |
| `descripcion` | `VARCHAR` | `descripcion` | The plan's title |
| `descripcionCooficial` | `VARCHAR` | `descripcionCooficial` | Title in the co-official language, if any |
| `tipoPlan` | `VARCHAR` | `tipoPlan` | Kind of plan |
| `vigenciaDesde`, `vigenciaHasta` | `INTEGER` | `vigenciaDesde`, `vigenciaHasta` | Years in force |
| `fechaAprobacion` | `DATE` | `fechaAprobacion` | Approval date |
| `ambitos` | `VARCHAR[]` | `ambitos` | Areas it covers |
| `retirada` | `BOOLEAN` | | `true` if the API no longer returns it |

## `catalogos`

The BDNS catalogues in one table: the codes the other tables use, with their descriptions. Bodies and regions are trees, and each node is a row with its parent's code and its depth.

| Column | Type | What it is |
|---|---|---|
| `catalogo` | `VARCHAR` | The catalogue, named after its endpoint |
| `id` | `VARCHAR` | Code within the catalogue |
| `descripcion` | `VARCHAR` | Description |
| `idPadre` | `VARCHAR` | The parent node's code, in `organos` and `regiones` |
| `nivel` | `INTEGER` | Depth in the tree, from 1 |
| `ambito` | `VARCHAR` | The regulation's scope, only in `reglamentos` |
| `idAdmon` | `VARCHAR` | Kind of administration, in `organos` and `organos_agrupacion` |
| `retirada` | `BOOLEAN` | `true` if the API no longer returns it |

There are ten catalogues: activities, kinds of beneficiary (`beneficiarios`), purposes, instruments, objectives, bodies, groupings of bodies (`organos_agrupacion`), regions, regulations and sectors.
