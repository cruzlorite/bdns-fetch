# Qué contiene el dataset

Cada tabla se publica como un fichero Parquet con su mismo nombre (`concesiones_personas_juridicas.parquet`, por ejemplo) y con los tipos de cada columna, así que DuckDB, pandas o R la leen directamente. Las tablas se llaman como los endpoints de la API, y las columnas, exactamente como sus campos (`codConcesion`, `fechaConcesion`…); las que calcula el dataset siguen el mismo estilo (`tipoPersona`, `importeMediana`…). Los textos van tal y como los devuelve la API, salvo los espacios sobrantes de algunos campos. Los ejemplos de esta página usan datos inventados.

<a id="entities"></a>
## Personas jurídicas

Las tres primeras tablas tienen, de cada concesión o ayuda a una persona jurídica o a una entidad pública ([cómo se clasifican](privacy.md#who)), la última versión que conoce `bdns-sync`. Dos cosas que conviene saber antes de usarlas:

- **Las concesiones que la API ya ha retirado siguen ahí**, con `retirada = true`. Son justo las que no puedes conseguir de otra forma, así que fíltralas (`WHERE NOT retirada`) solo si quieres ver lo mismo que muestra hoy el portal.
- **Un mismo NIF puede aparecer con el nombre escrito de varias formas**, así que, para agrupar por beneficiario, agrupa por `nif` y no por `nombre`.

### `concesiones_personas_juridicas`

Las concesiones a personas jurídicas y entidades públicas, una fila por concesión. Sale de la búsqueda de concesiones (`concesiones_busqueda` en `bdns-sync`).

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `id` | `BIGINT` | `id` | Identificador de la concesión en la BDNS |
| `codConcesion` | `VARCHAR` | `codConcesion` | Código de la concesión |
| `fechaConcesion` | `DATE` | `fechaConcesion` | Fecha de concesión |
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario: la primera palabra del campo, en mayúsculas |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario, lo que va después del NIF |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `importe` | `DECIMAL(18,2)` | `importe` | Importe concedido, en euros |
| `ayudaEquivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Ayuda equivalente (el equivalente de subvención bruta), en euros |
| `instrumento` | `VARCHAR` | `instrumento` | Instrumento de ayuda (`SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN`, `PRÉSTAMO`, `GARANTÍA`...) |
| `numeroConvocatoria` | `VARCHAR` | `numeroConvocatoria` | Código BDNS de la convocatoria |
| `convocatoria` | `VARCHAR` | `convocatoria` | Título de la convocatoria |
| `nivel1` | `VARCHAR` | `nivel1` | Administración que concede: `ESTADO`, `AUTONOMICA`, `LOCAL` u `OTROS` |
| `nivel2` | `VARCHAR` | `nivel2` | Ministerio, comunidad autónoma o entidad local |
| `nivel3` | `VARCHAR` | `nivel3` | Órgano que concede |
| `fechaAlta` | `DATE` | `fechaAlta` | Fecha en que la concesión se registró en la BDNS |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve. La fila conserva su última versión |

### `ayudasestado_personas_juridicas`

Las ayudas de Estado a personas jurídicas y entidades públicas, una fila por ayuda. Sale de la búsqueda de ayudas de Estado (`ayudasestado_busqueda`).

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `idConcesion` | `BIGINT` | `idConcesion` | Identificador de la concesión en la BDNS |
| `codConcesion` | `VARCHAR` | `codConcesion` | Código de la concesión |
| `fechaConcesion` | `DATE` | `fechaConcesion` | Fecha de concesión |
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario, sin el guion que a veces lo separa del NIF |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `tipoBeneficiario` | `VARCHAR` | `tipoBeneficiario` | Categoría que da la propia BDNS (`GRAN EMPRESA`, `PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA`...) |
| `importe` | `DECIMAL(18,2)` | `importe` | Importe concedido, en euros |
| `ayudaEquivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Ayuda equivalente (el equivalente de subvención bruta), en euros |
| `instrumento` | `VARCHAR` | `instrumento` | Instrumento de ayuda |
| `numeroConvocatoria` | `VARCHAR` | `numeroConvocatoria` | Código BDNS de la convocatoria |
| `convocatoria` | `VARCHAR` | `convocatoria` | Título de la convocatoria |
| `convocante` | `VARCHAR` | `convocante` | Órgano convocante, con su administración y su departamento |
| `reglamento` | `STRUCT(descripcion, orden)` | `reglamento` | Reglamento europeo en el que se basa la ayuda |
| `objetivo` | `VARCHAR` | `objetivo` | Objetivo de la ayuda, con el artículo del reglamento |
| `region` | `VARCHAR` | `region` | Región, con su código NUTS (`ES300 - Madrid`) |
| `sectores` | `VARCHAR` | `sectores` | Sector de actividad, con su código CNAE |
| `ayudaEstado` | `VARCHAR` | `ayudaEstado` | Número del caso en la Comisión Europea (`SA.000001`) |
| `urlAyudaEstado` | `VARCHAR` | `urlAyudaEstado` | Enlace al caso en la Comisión Europea, que trata del régimen de ayudas y no del beneficiario |
| `entidad` | `VARCHAR` | `entidad` | Entidad a través de la que se concede, cuando la hay |
| `intermediario` | `VARCHAR` | `intermediario` | NIF de la entidad intermediaria, cuando la hay |
| `fechaAlta` | `DATE` | `fechaAlta` | Fecha en que la ayuda se registró en la BDNS |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve |

### `minimis_personas_juridicas`

Las ayudas de minimis a personas jurídicas y entidades públicas, una fila por ayuda. Sale de la búsqueda de minimis (`minimis_busqueda`).

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `idConcesion` | `BIGINT` | `idConcesion` | Identificador de la concesión en la BDNS |
| `codigoConcesion` | `VARCHAR` | `codigoConcesion` | Código de la concesión |
| `fechaConcesion` | `DATE` | `fechaConcesion` | Fecha de concesión |
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `ayudaEquivalente` | `DECIMAL(18,2)` | `ayudaEquivalente` | Ayuda equivalente (el equivalente de subvención bruta), en euros. Es el importe que cuenta para el límite de minimis |
| `instrumento` | `VARCHAR` | `instrumento` | Instrumento de ayuda |
| `numeroConvocatoria` | `VARCHAR` | `numeroConvocatoria` | Código BDNS de la convocatoria |
| `convocante` | `VARCHAR` | `convocante` | Órgano convocante |
| `reglamento` | `STRUCT(descripcion, orden)` | `reglamento` | Reglamento de minimis que se aplica |
| `sectorActividad` | `VARCHAR` | `sectorActividad` | Sector de actividad, con su código CNAE |
| `sectorProducto` | `VARCHAR` | `sectorProducto` | Sector del producto, cuando se indica |
| `fechaRegistro` | `DATE` | `fechaRegistro` | Fecha en que la ayuda se registró en la BDNS |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve |

<a id="personas-fisicas"></a>
## Personas físicas

Tres tablas, una por entidad, con un resumen por convocatoria e instrumento de las concesiones a personas físicas y a quien se protege como ellas (comunidades de bienes, sociedades civiles, beneficiarios que no se reconocen y empresas cuyo nombre lleva el DNI de una persona), más una fila de resto por año con las convocatorias que no se pueden publicar ([las reglas](privacy.md#rules)). En ayudas de Estado y minimis, casi todas estas personas son autónomos.

Las tres tienen las mismas columnas, salvo las que identifican la convocatoria y las de importe, que dependen de lo que trae cada entidad:

- **`concesiones_personas_fisicas`**: el número y el título de la convocatoria, los tres niveles del órgano que concede y estadísticas del importe y de la ayuda equivalente.
- **`ayudasestado_personas_fisicas`**: el número y el título de la convocatoria, el órgano convocante y estadísticas del importe y de la ayuda equivalente.
- **`minimis_personas_fisicas`**: el número de la convocatoria, el órgano convocante y estadísticas de la ayuda equivalente, porque los registros de minimis no traen importe.

| Columna | Tipo | Qué es |
|---|---|---|
| `numeroConvocatoria` | `VARCHAR` | Código BDNS de la convocatoria. Vacío en las filas de resto |
| `convocatoria` | `VARCHAR` | Título de la convocatoria. Vacío en las filas de resto y cuando contiene algo con forma de DNI |
| `nivel1`, `nivel2`, `nivel3` | `VARCHAR` | Administración, departamento y órgano que conceden, como en `concesiones_personas_juridicas` |
| `convocante` | `VARCHAR` | Órgano convocante, como en las tablas de personas jurídicas |
| `instrumento` | `VARCHAR` | Instrumento de ayuda. Vacío en las filas de resto |
| `esResto` | `BOOLEAN` | `true` en las filas de resto |
| `ejercicio` | `BIGINT` | Año de una fila de resto, que es el de la fecha mediana de cada convocatoria que junta. Vacío en las demás filas |
| `concesiones` | `BIGINT` | Número de concesiones |
| `beneficiarios` | `BIGINT` | Número de personas distintas, siempre 10 o más |
| `importeTotal` | `DECIMAL(38,2)` | Suma de los importes, en euros |
| `importeMedia` | `DECIMAL(18,2)` | Importe medio por concesión, redondeado al céntimo |
| `importeDesviacion` | `DECIMAL(18,2)` | Desviación típica (muestral) de los importes, redondeada al céntimo |
| `importeP10` | `DECIMAL(18,2)` | Percentil 10 del importe. Solo con 20 personas o más |
| `importeP25` | `DECIMAL(18,2)` | Primer cuartil del importe |
| `importeMediana` | `DECIMAL(18,2)` | Mediana del importe |
| `importeP75` | `DECIMAL(18,2)` | Tercer cuartil del importe |
| `importeP90` | `DECIMAL(18,2)` | Percentil 90 del importe. Solo con 20 personas o más |
| `fechaConcesionP10` | `DATE` | Percentil 10 de la fecha de concesión. Solo con 20 personas o más |
| `fechaConcesionP25` | `DATE` | Primer cuartil de la fecha de concesión |
| `fechaConcesionMediana` | `DATE` | Mediana de la fecha de concesión |
| `fechaConcesionP75` | `DATE` | Tercer cuartil de la fecha de concesión |
| `fechaConcesionP90` | `DATE` | Percentil 90 de la fecha de concesión. Solo con 20 personas o más |

Las columnas `ayudaEquivalenteTotal`, `ayudaEquivalenteMedia` y siguientes son las mismas estadísticas sobre la ayuda equivalente. Si el título o el órgano no son los mismos en todas las concesiones de una convocatoria, se publican los de la mayoría, y en las filas de resto van vacíos.

### Cómo se lee una fila

Los importes y las fechas se calculan sobre las concesiones, de modo que una persona con dos concesiones cuenta dos veces en ellos, aunque en `beneficiarios` cuente una. Los percentiles del importe se interpolan entre las dos concesiones más cercanas, y los de la fecha son siempre una fecha de concesión real:

```sql
SELECT concesiones, beneficiarios, importeP10, importeP25, importeMediana, importeP75, importeP90
FROM 'concesiones_personas_fisicas.parquet'
WHERE numeroConvocatoria = '900101';
```

| concesiones | beneficiarios | importeP10 | importeP25 | importeMediana | importeP75 | importeP90 |
|------------:|--------------:|-----------:|-----------:|---------------:|-----------:|-----------:|
| 250         | 250           | 1200.00    | 1800.00    | 2400.00        | 2400.00    | 3600.00    |

La mitad de las concesiones fue de entre 1.800 y 2.400 euros, y el 80 %, de entre 1.200 y 3.600. En las convocatorias con menos de 20 personas, el percentil 10 y el 90 vienen vacíos.

<a id="rest"></a>
### Las filas de resto y los totales

Las convocatorias que no se pueden publicar se juntan en una fila de resto por año, con `esResto = true`, sin número de convocatoria y con el año en `ejercicio`, que es el de la fecha mediana de cada convocatoria que reúne. Si usas el mismo criterio para las convocatorias publicadas, puedes sumarlo todo por año:

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

Aun así, el total se queda algo corto, porque las concesiones que no llegan a ninguna fila publicable (por ejemplo, las de una convocatoria pequeña que es la única de su año) no están en el dataset.

<a id="whole-call"></a>
## Una convocatoria entera

Una convocatoria puede tener beneficiarios de los dos tipos, y para verla entera hay que juntar las dos partes por `numeroConvocatoria`:

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

Si una convocatoria usa varios instrumentos (por ejemplo, subvenciones y préstamos), tiene un resumen por cada uno, y entonces conviene agrupar también por `instrumento`.

## `convocatorias`

Las convocatorias, una fila por convocatoria, con la última versión de su ficha que conoce `bdns-sync` (la tabla `convocatorias`, con el detalle de cada una). Los campos conservan el nombre y la forma de la API: el órgano es un objeto con sus tres niveles, y las listas (instrumentos, sectores, regiones…) son listas de objetos. Se cruzan con las demás tablas por `codigoBDNS`, que es su `numeroConvocatoria`.

Los textos que escribe a mano el órgano (el título, la descripción de las bases, las fechas en texto) se publican vacíos si contienen algo con forma de DNI, y lo mismo el enlace a las bases cuando tiene esa forma. Quedan fuera los documentos y los anuncios en boletines, porque suelen listar a los beneficiarios, y el aviso legal del portal, que es el mismo en todas.

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `id` | `BIGINT` | `id` | Identificador interno de la convocatoria |
| `codigoBDNS` | `VARCHAR` | `codigoBDNS` | Código BDNS de la convocatoria |
| `fechaRecepcion` | `DATE` | `fechaRecepcion` | Fecha en que la convocatoria llegó a la BDNS |
| `organo` | `STRUCT(nivel1, nivel2, nivel3)` | `organo` | Administración, departamento y órgano que convoca |
| `sedeElectronica` | `VARCHAR` | `sedeElectronica` | Sede electrónica donde se tramita |
| `descripcion` | `VARCHAR` | `descripcion` | Título de la convocatoria |
| `descripcionLeng` | `VARCHAR` | `descripcionLeng` | Título en la lengua cooficial, si lo hay |
| `tipoConvocatoria` | `VARCHAR` | `tipoConvocatoria` | Tipo de procedimiento (concurrencia competitiva, concesión directa…) |
| `presupuestoTotal` | `DECIMAL(18,2)` | `presupuestoTotal` | Presupuesto total, en euros |
| `mrr` | `BOOLEAN` | `mrr` | Si se financia con el Mecanismo de Recuperación y Resiliencia |
| `instrumentos` | `STRUCT(descripcion)[]` | `instrumentos` | Instrumentos de ayuda |
| `tiposBeneficiarios` | `STRUCT(descripcion)[]` | `tiposBeneficiarios` | Tipos de beneficiario a los que se dirige |
| `sectores` | `STRUCT(codigo, descripcion)[]` | `sectores` | Sectores de actividad, con su código CNAE |
| `regiones` | `STRUCT(descripcion)[]` | `regiones` | Regiones, con su código NUTS |
| `descripcionFinalidad` | `VARCHAR` | `descripcionFinalidad` | Finalidad de la convocatoria |
| `descripcionBasesReguladoras` | `VARCHAR` | `descripcionBasesReguladoras` | Norma que aprueba las bases reguladoras |
| `urlBasesReguladoras` | `VARCHAR` | `urlBasesReguladoras` | Enlace a las bases reguladoras |
| `sePublicaDiarioOficial` | `BOOLEAN` | `sePublicaDiarioOficial` | Si se publica en un diario oficial |
| `abierto` | `BOOLEAN` | `abierto` | Si el plazo de solicitud estaba abierto en la última versión conocida |
| `fechaInicioSolicitud`, `fechaFinSolicitud` | `DATE` | `fechaInicioSolicitud`, `fechaFinSolicitud` | Plazo de solicitud, cuando viene como fecha |
| `textInicio`, `textFin` | `VARCHAR` | `textInicio`, `textFin` | El plazo de solicitud tal y como lo escribe el órgano |
| `ayudaEstado`, `urlAyudaEstado` | `VARCHAR` | `ayudaEstado`, `urlAyudaEstado` | Caso de ayuda de Estado en la Comisión Europea y su enlace |
| `fondos` | `STRUCT(descripcion)[]` | `fondos` | Fondos europeos que la financian |
| `reglamento` | `STRUCT(descripcion, orden)` | `reglamento` | Reglamento europeo en el que se basa |
| `objetivos` | `STRUCT(descripcion)[]` | `objetivos` | Objetivos, con el artículo del reglamento |
| `sectoresProductos` | `STRUCT(descripcion)[]` | `sectoresProductos` | Sectores de producto |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve |

## `partidospoliticos`

Las concesiones a partidos políticos y a sus fundaciones, una fila por concesión. Todos los beneficiarios son personas jurídicas; si alguna vez apareciera uno protegido, se quedaría fuera. Tiene las columnas de `concesiones_personas_juridicas`, salvo `fechaAlta`, que esta búsqueda no trae, y dos más:

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `tieneProyecto` | `BOOLEAN` | `tieneProyecto` | Si la concesión tiene un proyecto asociado |
| `idConvocatoria` | `BIGINT` | `idConvocatoria` | Identificador interno de la convocatoria |

## `grandesbeneficiarios`

La lista de grandes beneficiarios que publica la BDNS: la ayuda total que recibió cada uno en un año. Solo se publican las personas jurídicas, entidades públicas incluidas. Las personas físicas y las comunidades de bienes de la lista se quedan fuera, y no tendría sentido resumirlas, porque cada fila ya es el total de un beneficiario.

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `nif` | `VARCHAR` | `beneficiario` | NIF del beneficiario |
| `nombre` | `VARCHAR` | `beneficiario` | Nombre del beneficiario |
| `tipoPersona` | `VARCHAR` | | `persona_juridica` o `entidad_publica` |
| `ejercicio` | `INTEGER` | `ejercicio` | Año |
| `ayudaETotal` | `DECIMAL(18,2)` | `ayudaETotal` | Ayuda equivalente total del año, en euros |
| `retirada` | `BOOLEAN` | | `true` si la API ya no la devuelve |

## `planesestrategicos`

Los planes estratégicos de subvenciones de las administraciones, uno por fila, sin los documentos adjuntos ni el aviso legal del portal.

| Columna | Tipo | Campo de la API | Qué es |
|---|---|---|---|
| `idPES` | `BIGINT` | `idPES` | Identificador del plan |
| `descripcion` | `VARCHAR` | `descripcion` | Título del plan |
| `descripcionCooficial` | `VARCHAR` | `descripcionCooficial` | Título en la lengua cooficial, si lo hay |
| `tipoPlan` | `VARCHAR` | `tipoPlan` | Tipo de plan |
| `vigenciaDesde`, `vigenciaHasta` | `INTEGER` | `vigenciaDesde`, `vigenciaHasta` | Años de vigencia |
| `fechaAprobacion` | `DATE` | `fechaAprobacion` | Fecha de aprobación |
| `ambitos` | `VARCHAR[]` | `ambitos` | Ámbitos que cubre |
| `retirada` | `BOOLEAN` | | `true` si la API ya no lo devuelve |

## `catalogos`

Los catálogos de la BDNS en una sola tabla: los códigos que usan las demás, con su descripción. Los órganos y las regiones son árboles, y cada nodo es una fila con el identificador de su padre y su profundidad.

| Columna | Tipo | Qué es |
|---|---|---|
| `catalogo` | `VARCHAR` | El catálogo, con el nombre de su endpoint |
| `id` | `VARCHAR` | Código dentro del catálogo |
| `descripcion` | `VARCHAR` | Descripción |
| `idPadre` | `VARCHAR` | Código del nodo padre, en `organos` y `regiones` |
| `nivel` | `INTEGER` | Profundidad en el árbol, desde 1 |
| `ambito` | `VARCHAR` | Ámbito del reglamento, solo en `reglamentos` |
| `idAdmon` | `VARCHAR` | Tipo de administración, en `organos` y `organos_agrupacion` |
| `retirada` | `BOOLEAN` | `true` si la API ya no lo devuelve |

Los catálogos son diez: actividades, tipos de beneficiario (`beneficiarios`), finalidades, instrumentos, objetivos, órganos, agrupaciones de órganos (`organos_agrupacion`), regiones, reglamentos y sectores.
