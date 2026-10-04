# Tablas y columnas

Cada tabla se publica como un fichero Parquet con su mismo nombre (`concesiones_entidades.parquet`, por ejemplo), con los tipos de cada columna. Los textos van tal y como los devuelve la API, salvo los espacios sobrantes de algunos campos, y cada columna dice de qué campo de la API sale.

Las tres tablas de entidades tienen, de cada concesión o ayuda, la última versión que conoce `bdns-sync`, incluidas las que la API ya ha retirado. Solo contienen personas jurídicas y entidades públicas ([cómo se clasifican](../explanation/anonymisation.md#who)).

## `concesiones_entidades`

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

## `ayudas_estado_entidades`

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

## `minimis_entidades`

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
## `concesiones_personas`

Las concesiones a personas físicas, comunidades de bienes, sociedades civiles y beneficiarios que no se reconocen, como un resumen por convocatoria e instrumento, más una fila de resto por año con las convocatorias que no se pueden publicar ([las reglas](../explanation/anonymisation.md#rules)). Los importes y las fechas se calculan sobre las concesiones, y `beneficiarios` cuenta personas.

| Columna | Tipo | Qué es |
|---|---|---|
| `numero_convocatoria` | `VARCHAR` | Código BDNS de la convocatoria. Vacío en las filas de resto |
| `convocatoria` | `VARCHAR` | Título de la convocatoria. Vacío en las filas de resto y cuando contiene algo con forma de DNI |
| `nivel1`, `nivel2`, `nivel3` | `VARCHAR` | Administración, departamento y órgano que conceden, como en `concesiones_entidades`. Vacíos en las filas de resto |
| `instrumento` | `VARCHAR` | Instrumento de ayuda. Vacío en las filas de resto |
| `es_resto` | `BOOLEAN` | `true` en las filas de resto |
| `ejercicio` | `BIGINT` | Año de una fila de resto, que es el de la fecha mediana de cada convocatoria que junta. Vacío en las demás filas |
| `concesiones` | `BIGINT` | Número de concesiones |
| `beneficiarios` | `BIGINT` | Número de personas distintas, siempre 10 o más |
| `importe_total` | `DECIMAL(38,2)` | Suma de los importes, en euros |
| `importe_media` | `DOUBLE` | Importe medio por concesión |
| `importe_desviacion` | `DOUBLE` | Desviación típica (muestral) de los importes |
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

Los percentiles del importe se interpolan entre las dos concesiones más cercanas, mientras que los de la fecha son siempre una fecha de concesión real.
