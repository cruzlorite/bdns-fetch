# 0018. Un solo paquete con varias herramientas

**Estado:** aceptada · **Fecha:** 2026-10-04

## Contexto

El proyecto lo forman varias herramientas que dependen unas de otras: `bdns-fetch` habla con la API, `bdns-sync` se apoya en él para conservar el histórico y está previsto un generador de un dataset anonimizado a partir de las tablas de `bdns-sync` ([hoja de ruta](../roadmap.md#dataset)).

Cambian a la vez. `bdns-sync` es el principal usuario de `bdns-fetch`, y muchas mejoras de uno nacen de lo que necesita el otro: una rareza de la API se descubre al sincronizar, se resuelve en el cliente y se aprovecha en la sincronización. Si cada herramienta se versiona y se publica por separado, un cambio así obliga a publicar una antes de poder probar la otra, a usar dependencias temporales y a mantener una tabla de qué versiones son compatibles entre sí.

Además, comparten casi todo lo que no es código: la configuración de `ruff`, los scripts que comprueban la documentación, la integración continua y las normas de documentación. Cuando hay varias copias de lo mismo, acaban siendo distintas sin que nadie se dé cuenta. Y la documentación de una herramienta cita constantemente la de la otra, enlaces que solo se pueden comprobar si están en la misma web.

Por otro lado, lo que de verdad usa quien programa con estas herramientas son las rutas de import ([`bdns.fetch`](../fetch/reference/api/index.md), [`bdns.sync`](../sync/reference/api/index.md)) y los comandos; cómo se reparten en paquetes de PyPI es un detalle de empaquetado. La diferencia de dependencias entre herramientas es pequeña, salvo la de BigQuery, que es opcional. Y el proyecto lo mantiene una sola persona, para la que cada versión, cada CHANGELOG y cada configuración de más es trabajo repetido.

## Decisión

Todas las herramientas viven en un solo repositorio y se publican en un solo paquete, `bdns-tools`, con una versión y un CHANGELOG. Cada herramienta es un módulo ([`bdns.fetch`](../fetch/reference/api/index.md), [`bdns.sync`](../sync/reference/api/index.md)) con su propio comando y su sección en la web, y las dependencias pesadas y opcionales van en extras, como `bdns-tools[bigquery]`.

El paquete se llama `bdns-tools` y no `bdns` a secas: BDNS es el nombre de la base de datos oficial, y un paquete o una web que se llamaran exactamente así darían a entender que son la herramienta oficial, justo lo que las condiciones de reutilización de la IGAE piden evitar. El nombre mantiene la palabra que se busca y deja claro que son herramientas de terceros.

Los imports cuelgan de `bdns`, un espacio de nombres sin `__init__.py` propio, de modo que cada módulo se basta a sí mismo. La frontera entre ellos se mantiene: [`bdns.fetch`](../fetch/reference/api/index.md) nunca importa [`bdns.sync`](../sync/reference/api/index.md), y un test lo comprueba.

La numeración continúa la de `bdns-fetch`, cuyas etiquetas `v1.x` ya existen, así que la primera versión de `bdns-tools` es la 2.0.0. Los datos que se generen no se guardan en el repositorio: se publican aparte, con su propia licencia.

## Consecuencias

- Un cambio que afecta a varias herramientas se hace, se prueba y se publica de una vez, sin dependencias temporales ni tabla de compatibilidad entre versiones.
- Un cambio incompatible en cualquier módulo supone una versión mayor para todo el paquete, aunque quien lo use solo necesite otro módulo.
- No todos los módulos son igual de maduros, así que la [política de compatibilidad](../compatibility.md) detalla qué es público en cada uno.
- Quien solo use [`bdns.fetch`](../fetch/reference/api/index.md) instala también SQLAlchemy, unos pocos megas.
- Si algún día un módulo tiene un público propio, se puede publicar como paquete aparte sin cambiar ningún import, gracias al espacio de nombres.
- Quien instalaba `bdns-fetch` o `bdns-sync` tiene que pasar a instalar `bdns-tools`; las versiones ya publicadas con esos nombres siguen en PyPI.
