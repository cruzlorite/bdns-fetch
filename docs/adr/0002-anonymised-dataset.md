# 0002. Un dataset anonimizado y agregado

**Estado:** propuesta · **Fecha:** 2026-10-04

## Contexto

La API de la BDNS solo devuelve una ventana de tiempo, distinta para cada tipo de dato: unos 12 años de convocatorias, unos 10 de ayudas de Estado y minimis, unos 4 de concesiones, y solo el año de la concesión y el siguiente cuando el beneficiario es una persona física ([cada endpoint guarda un histórico distinto](../fetch/explanation/api-behavior.md#history-depth)). Lo que sale de esa ventana solo lo conserva quien lo guardó a tiempo, y `bdns-sync` lo guarda. Ese histórico es lo que hace valioso un dataset publicado: nadie más puede ofrecerlo, ni siquiera el portal, que permite descargar lo que sigue publicado, pero no lo que ya ha retirado.

Ese mismo histórico contiene datos personales. La BDNS publica el nombre completo de las personas físicas y oculta solo parte de su NIF (`***1234** NOMBRE APELLIDOS`), y en un día cualquiera de 2026 el 94 % de las concesiones fueron a personas físicas, aunque solo sumaron el 12 % del importe. Además, cada registro lleva campos que permiten identificar a la persona aunque se quite el nombre: `idPersona`, un identificador que se repite en todas sus concesiones; `urlBR`, el enlace al boletín oficial que la nombra, y `codConcesion` o `id`, que permiten buscar el registro en el portal mientras siga publicado.

El marco legal limita lo que se puede hacer con esos datos:

- Las condiciones de reutilización de la IGAE solo permiten reutilizar datos personales para controlar la actuación de los gestores públicos o con fines históricos, estadísticos o científicos, y en este caso exigen disociarlos antes.
- El RGPD deja fuera de su ámbito los datos anónimos, pero no los seudonimizados: sustituir un NIF por un código, aunque sea un hash, sigue siendo tratar datos personales, porque el código permite seguir a la persona.
- El límite temporal con el que se publican las concesiones a personas físicas tiene una finalidad, y republicarlas identificables pasado ese plazo iría contra ella.

Las estadísticas oficiales resuelven este mismo problema publicando agregados y suprimiendo las celdas que podrían identificar a alguien, lo que se conoce como control de revelación estadística.

## Decisión

El dataset **no contiene ningún dato personal**. Puede identificar a personas jurídicas y entidades públicas, pero nunca a personas físicas.

1. **Cada beneficiario se clasifica** como persona física, entidad formada por personas (comunidades de bienes y sociedades civiles, que suelen llevar el nombre de sus miembros), persona jurídica, entidad pública o dudoso. La clasificación es conservadora: lo dudoso se trata como persona física ([el SQL](../dataset/index.md#sql)).
2. **Lo que se publica, y con qué detalle:**

    | Datos | Nivel |
    |---|---|
    | Catálogos | Tal cual |
    | Convocatorias | Registro a registro, revisando los títulos que nombran a personas |
    | Concesiones, ayudas de Estado y minimis a personas jurídicas y entidades públicas | Registro a registro |
    | Las mismas, a personas físicas, entidades formadas por personas y beneficiarios dudosos | Solo como un resumen por convocatoria: número de concesiones y de beneficiarios, importe total, media, desviación típica, mediana y cuartiles del importe, y los mismos percentiles de la fecha de concesión |
    | Sanciones a personas físicas | No se publican |

3. **Ningún resumen sobre personas físicas junta a menos de 10 personas**, ni a una que tenga más de la mitad de su importe: un importe que solo aparece una vez aislaría a quien lo recibió, aunque no se diga su nombre, y se podría cruzar con copias antiguas de la BDNS que sí lo dicen. Nunca se publican el mínimo ni el máximo del importe o de la fecha, porque cada uno es el de una persona concreta, y los percentiles 10 y 90, que quedan cerca, solo cuando el resumen junta al menos a 20 personas. Las convocatorias que no cumplen se reúnen, por año, en una fila de "resto", que solo se publica si junta al menos dos (si fuera una, el resto sería esa convocatoria tal cual) y cumple también los umbrales. Cada estadística cubre todas las concesiones de su fila, y no hay otra tabla sobre ellas con la que compararla.
4. **Nunca se publica**, en nada que se refiera a personas físicas, ni el nombre, ni el NIF (completo, parcial o cifrado), ni `idPersona`, `urlBR`, `codConcesion` o `id`.
5. **La generación se para** si lo que va a publicarse contiene un valor con forma de DNI, NIE o NIF enmascarado, un campo prohibido o una celda por debajo del mínimo.
6. **El dataset se genera donde están los datos**, con SQL de DuckDB que lee directamente las tablas de `bdns-sync`, de modo que el método se puede leer y revisar tal cual ([el SQL](../dataset/index.md#sql)). El resultado queda en un sitio privado hasta que una persona lo revisa, y se publica fuera del repositorio (en Zenodo, con un DOI por versión) con la metodología, la cita a la IGAE y la fecha de actualización. El único formato es Parquet, un fichero por tabla: lleva los tipos de cada columna, ocupa poco y lo lee cualquier herramienta de datos.
7. **Antes de la primera publicación** se hacen una evaluación de riesgos y una revisión legal.

Quedan pendientes de decidir: si las comunidades de bienes y las sociedades civiles se protegen como personas físicas (mientras tanto, sí), cada cuánto se publica una versión y la licencia del dataset (las condiciones de la IGAE más, por ejemplo, CC BY 4.0 para el trabajo propio).

## Consecuencias

- Si la anonimización es sólida, lo publicado deja de ser un dato personal, y quien lo reutilice no queda sujeto al RGPD por ello.
- No se puede seguir a una persona física concreta a lo largo del tiempo. Es justo lo que se busca, aunque limite algunos análisis.
- Comparando dos versiones, la diferencia en un resumen del año en curso deja ver lo que recibieron quienes entraron entre una y otra, aunque no quiénes son. Se acepta como riesgo residual: no identifica a nadie, y esos importes los publica la propia BDNS con nombre mientras siguen en su plazo. Se revisará en la evaluación de riesgos, y si hiciera falta bastaría con no publicar más de una versión por trimestre.
- Los resúmenes de personas físicas no suman exactamente el total real, porque falta lo que no llega a ningún resumen publicable.
- El modelo de datos de `bdns-sync` pasa a ser un contrato del generador: un cambio en él puede obligar a cambiar el dataset.
- Cada versión del dataset se puede regenerar a partir de una base de datos de `bdns-sync`, y el método es público, así que se puede revisar.
