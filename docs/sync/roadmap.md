# Hoja de ruta

Lo que queda por hacer, en orden aproximado de prioridad. Lo ya hecho está
en el [CHANGELOG](https://github.com/cruzlorite/bdns-sync/blob/main/CHANGELOG.md);
los problemas de la API de origen, en [qué hace con cada problema conocido de la API](explanation/sync-behavior.md#api-issues).

- **Endpoints del grupo H** (`organos_codigo`, `organos_codigoadmin`). Sin sincronizar; el resto del catálogo oficial está cubierto. Con el [registro de entidades][bdns.sync.entities] es una entrada por endpoint, más su clave natural.
- **Supresión o seudonimización de campos del payload.** Un decorador de [`Sink`][bdns.sync.sinks.Sink] (`RedactingSink(inner, drop=[...], anonymize={...})`) que envuelva cualquier sink sin tocarlo. Tiene que actuar **antes** de calcular `_row_hash`: si se suprimiera después, cambiar un campo eliminado generaría versiones nuevas con un payload almacenado idéntico. Debe negarse a tocar los campos clave y la fecha de registro. Estrategias: eliminar el campo, ponerlo a null o seudonimizarlo con HMAC y sal (así se puede agrupar por beneficiario sin exponer el NIF). Cambiar la política más adelante cambia todos los hashes y vuelve a versionar la tabla entera, así que conviene decidirla antes de la carga inicial.
- **Sink de ficheros (Parquet).** Una segunda implementación de [`Sink`][bdns.sync.sinks.Sink], para destinos sin SQL. La interfaz por lotes ya está pensada para admitirla.
- **Vistas de consulta.** Una vista por entidad con solo las versiones vigentes y los campos más usados extraídos del `payload`, para quien consulta sin conocer el modelo SCD2.
