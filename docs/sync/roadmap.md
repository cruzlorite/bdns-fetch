# Hoja de ruta

Funcionalidad pendiente, en orden aproximado de prioridad. Los problemas del API de origen no van aquí; están en la [sección 8 de bdns-api-behavior.md](bdns-api-behavior.md#8-problemas-conocidos-del-api).

- **Endpoints del grupo H** (`organos_codigo`, `organos_codigoadmin`). No implementados; el resto del catálogo oficial está cubierto.
- **Verificación en vivo de PostgreSQL y MySQL.** Son compatibles por diseño (SQL portable), pero el ciclo SCD2 completo solo está verificado contra SQLite (tests) y BigQuery (en vivo). Añadir un job de CI con un Postgres de servicio cerraría el hueco.
- **Reanudación de backfills.** Un backfill interrumpido se re-ejecuta desde el principio; es idempotente pero lento. La marca de agua de `_sync_state` permitiría continuar desde el último trozo confirmado.
- **Sink de ficheros (Parquet).** Segunda implementación de la interfaz `Sink`, para destinos sin SQL. La interfaz ya está diseñada para admitirla.
- **Publicación en PyPI.** Instalación con `pip install bdns-sync` sin clonar el repositorio.
