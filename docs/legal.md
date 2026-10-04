# Aviso legal

## Qué es este proyecto

`bdns-tools` es un proyecto personal y no oficial. No tiene ninguna relación con la Intervención General de la Administración del Estado (IGAE), que es el organismo que gestiona la BDNS, ni cuenta con su apoyo.

El código se distribuye con [licencia MIT](https://github.com/cruzlorite/bdns-tools/blob/main/LICENSE), que excluye cualquier garantía: lo usas bajo tu responsabilidad, y el autor no responde de daños, pérdidas de datos ni usos indebidos.

## De dónde vienen los datos y cómo puedes reutilizarlos

Los datos proceden del [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es), y su reutilización está sujeta al [aviso legal del portal](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) y a sus [buenas prácticas para la API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf). En resumen, si reutilizas los datos:

- tienes que citar la fuente (por ejemplo, "Origen de los datos: Intervención General de la Administración del Estado") e indicar la fecha de la última actualización si viene en los datos;
- no puedes cambiar el sentido de la información;
- no puedes dar a entender que la IGAE participa en tu reutilización, la patrocina o la apoya;
- si hay datos personales, solo puedes reutilizarlos para controlar la actuación de los gestores públicos o con fines históricos, estadísticos o científicos, y en este último caso tienes que disociarlos antes e indicar que lo has hecho y quién lo ha hecho.

Este resumen no sustituye al texto oficial ni a la [Ley 37/2007 sobre reutilización de la información del sector público](https://www.boe.es/eli/es/l/2007/11/16/37/con), que prevé sanciones para quien la incumpla. Si tienes dudas, consúltalo con un asesor legal.

<a id="personal-data"></a>
## Datos personales

Varios endpoints y tablas (`concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda` o `terceros`, entre otros) contienen datos de personas físicas: la BDNS publica su nombre completo y oculta solo parte del NIF. `bdns-fetch` y `bdns-sync` los entregan y los guardan tal y como los publica la API, sin transformarlos.

Ten en cuenta que el histórico de `bdns-sync` **los conserva aunque el portal los retire**: las concesiones a personas físicas, por ejemplo, solo se publican durante el año de la concesión y el siguiente. Quien descarga los datos o gestiona la base de datos de destino es responsable de tratarlos conforme al RGPD y a la LOPDGDD (con una finalidad legítima, un plazo de conservación y control de quién accede) y a las condiciones de reutilización anteriores.

El dataset que está previsto publicar irá siempre anonimizado y agregado, precisamente para que no contenga datos personales ([hoja de ruta](roadmap.md#dataset)).

## Contacto

Para dudas o problemas, abre un [issue en GitHub](https://github.com/cruzlorite/bdns-tools/issues). Si se trata de una vulnerabilidad, sigue la [política de seguridad](https://github.com/cruzlorite/bdns-tools/blob/main/SECURITY.md).
