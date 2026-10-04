# Hoja de ruta

Esto es lo que queda por hacer, más o menos por orden de prioridad dentro de cada apartado. Lo que ya está hecho lo tienes en el [CHANGELOG](https://github.com/cruzlorite/bdns-tools/blob/main/CHANGELOG.md), y los problemas de la propia API, en [qué hace bdns-sync con cada problema conocido de la API](sync/explanation/sync-behavior.md#api-issues).

<a id="dataset"></a>
## Un dataset anonimizado con todo el histórico

Un módulo nuevo que genere, a partir de las tablas de `bdns-sync`, un conjunto de datos listo para usar con todo el histórico, y no solo con los años que todavía publica el portal. Lo que se publique irá siempre anonimizado y agregado: proteger a las personas físicas es la prioridad, y todo el proceso tiene que cumplir las condiciones de reutilización de la IGAE, el RGPD y la LOPDGDD. Antes de escribir código se recogerá en una decisión de diseño qué se publica, con qué nivel de detalle y por qué, y la primera versión no se publicará sin una revisión legal.

## bdns-sync

- **Los endpoints que faltan** (`organos_codigo` y `organos_codigoadmin`). Son los únicos del catálogo oficial que todavía no se sincronizan, y con el [registro de entidades][bdns.sync.entities] basta con añadir una entrada por endpoint con su clave natural.
- **Quitar o seudonimizar campos del registro.** Se haría con un envoltorio de [`Sink`][bdns.sync.sinks.Sink] (`RedactingSink(inner, drop=[...], anonymize={...})`) que se pondría alrededor de cualquier sink sin modificarlo. Tendría que actuar **antes** de calcular `_row_hash`, porque si se quitara un campo después, un cambio en ese campo crearía versiones nuevas con un contenido guardado idéntico. Además, tendría que negarse a tocar los campos de la clave y la fecha de registro. Se podría eliminar el campo, dejarlo vacío o seudonimizarlo con un HMAC con sal (así se podría agrupar por beneficiario sin exponer su NIF). Cambiar esta configuración más adelante cambiaría todos los hashes y obligaría a volver a versionar la tabla entera, así que convendría decidirla antes de la carga inicial.
- **Un sink de ficheros (Parquet).** Sería otra implementación de [`Sink`][bdns.sync.sinks.Sink] para destinos sin SQL; la interfaz por lotes ya está pensada para admitirla.
- **Vistas para consultar más fácilmente.** Una vista por entidad con solo las versiones vigentes y los campos más usados ya extraídos de `payload`, para quien quiera consultar los datos sin conocer el modelo SCD2.
