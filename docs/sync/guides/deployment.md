# Despliegue en la nube

Esta guía explica cómo mantener la base de datos sincronizada sin tener una máquina propia. `bdns-sync` no guarda nada en local (toda la configuración va en variables de entorno y todo lo que necesita conservar está en la base de datos de destino), así que en cualquier nube se hace igual:

> **imagen de Docker + tarea programada + `BDNS_SYNC_TARGET_URL`**

## La imagen

Con cada versión se publica una imagen en GitHub Container Registry que ya incluye el extra de BigQuery:

```bash
docker pull ghcr.io/cruzlorite/bdns-sync:latest    # o una versión concreta, por ejemplo :0.6.0
```

- Por defecto ejecuta `bdns-sync delta`, la sincronización diaria, que elige sola el periodo y sigue aunque falle alguna entidad ([sincronización diaria](scheduling.md)).
- Si quieres otro comando, pásalo tal cual: `docker run ... ghcr.io/cruzlorite/bdns-sync bdns-sync sync sectores`.
- Las funciones tipo Cloud Functions no sirven, porque su tiempo máximo (entre 15 y 60 minutos) no da para los periodos largos ni para la carga inicial ([carga inicial](backfill.md)).

## Ejemplo con Google Cloud (Cloud Run Jobs y Cloud Scheduler)

Es la nube en la que se ha probado el destino contra el servicio real (BigQuery). Si asocias una cuenta de servicio a la tarea, la autenticación funciona sola, sin claves ni secretos.

```bash
PROJECT=mi-proyecto REGION=europe-southwest1 DATASET=bdns_sync

# 1. Cuenta de servicio con los permisos mínimos
gcloud iam service-accounts create bdns-sync --project $PROJECT
SA=bdns-sync@$PROJECT.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.jobUser
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.dataEditor
# (si lo prefieres, dataEditor se puede conceder solo sobre el dataset)

# 2. Cloud Run no descarga imágenes de ghcr.io directamente, así que un
#    repositorio remoto de Artifact Registry hace de intermediario
gcloud artifacts repositories create ghcr \
  --project $PROJECT --location $REGION \
  --repository-format docker --mode remote-repository \
  --remote-docker-repo https://ghcr.io

# 3. La tarea de la sincronización diaria
gcloud run jobs create bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --image $REGION-docker.pkg.dev/$PROJECT/ghcr/cruzlorite/bdns-sync:latest \
  --service-account $SA \
  --set-env-vars BDNS_SYNC_TARGET_URL=bigquery://$PROJECT/$DATASET \
  --memory 4Gi --task-timeout 24h --max-retries 0
gcloud run jobs add-iam-policy-binding bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --member serviceAccount:$SA --role roles/run.invoker

# 4. La programación (Cloud Scheduler no está en todas las regiones, pero
#    da igual cuál uses, porque solo llama a la API de la tarea)
gcloud scheduler jobs create http bdns-sync-delta-daily \
  --project $PROJECT --location europe-west1 \
  --schedule "0 2 * * *" --time-zone "Europe/Madrid" \
  --uri "https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/bdns-sync-delta:run" \
  --http-method POST \
  --oauth-service-account-email $SA
```

Algunas notas:

- **`--memory 4Gi`, no menos.** Lo que más memoria necesita es el periodo anual de `concesiones_busqueda`, que se lanza tres días al año y carga en el staging unos 20 millones de filas, con un pico medido de **2,33 GB**. Las dos veces que se quedó corta la memoria se vio en producción, y las dos de la misma manera, con un `exit 137` y sin evento final en `_sync_runs`: con 1 GiB fallaron cuatro ejecuciones semanales seguidas en julio de 2026, y con 2 GiB falló la anual del 1 de septiembre. Pasar de 2 a 4 GiB cuesta unos 0,18 dólares al mes y no obliga a añadir más vCPU.
- **`--task-timeout 24h`.** Con una llamada cada vez, como piden las buenas prácticas oficiales, la sincronización diaria con el periodo semanal sigue tardando minutos, y la del lunes (mensual), algo más. El periodo anual es el más largo: solo pedir el detalle de las unas 74.000 convocatorias de un año lleva unas 2 horas al ritmo máximo que permite la API, y más si el servidor va cargado, así que conviene dejar margen. Si necesitas que vaya más rápido, puedes lanzar la tarea con `BDNS_SYNC_MAX_WORKERS`, sabiendo que te apartas de la recomendación oficial.
- **`--max-retries 0`.** Si una ejecución falla, la del día siguiente lo arregla, porque repetir una sincronización no duplica nada; reintentarla en el momento solo volvería a descargar lo mismo.

### Coste y límites de gasto

Con esta configuración hay dos servicios de pago, y lo normal es que cuesten unos céntimos al mes: la tarea corre poco tiempo al día con una vCPU, los *load jobs* de BigQuery son gratis y las consultas que comparan los datos leen pocos GB.

- **Presupuestos**: los de Google Cloud **solo avisan, no cortan**. Si quieres un límite de gasto de verdad, el único freno que ofrece la propia plataforma es la cuota de BigQuery.
- **Cuota de BigQuery** (esta sí corta): un límite diario de bytes leídos por las consultas. Aquí hay dos situaciones muy distintas. Un día normal se leen unos 0,2 GiB, pero los tres días al año en que se lanza el periodo anual la comparación lee unos 127 GiB, 115 de ellos solo de `concesiones_busqueda`, porque cruza los 29 millones de filas de la tabla con los cerca de 20 millones del staging, y lo hace varias veces (para los recuentos, para actualizar `_synced_at`, para cerrar versiones y para insertar las nuevas). El límite hay que fijarlo pensando en esos tres días, no en la media, y con margen para cualquier consulta manual que coincida ese día. 300.000 MiB (293 GiB) es algo más del doble de lo medido y deja el peor caso por debajo de 2 euros al día:

  ```bash
  gcloud alpha services quota update --service bigquery.googleapis.com \
    --consumer projects/$PROJECT \
    --metric bigquery.googleapis.com/quota/query/usage \
    --unit 1/d/{project} --value 300000 --force
  ```

- **Aviso si falla la tarea** (Cloud Monitoring): una política sobre la métrica `run.googleapis.com/job/completed_execution_count` con `result=failed` que avise por correo. Una ejecución fallida no exige hacer nada en el momento, porque la del día siguiente lo arregla, pero conviene enterarse.

## La carga inicial

Es una operación larga ([carga inicial](backfill.md)) que se lanza a mano una sola vez. Tienes dos opciones:

- **Una segunda tarea** con el comando de la carga completa y el tiempo máximo al límite (24 horas en Cloud Run Jobs). Si se interrumpe, basta con volver a lanzarla, porque cada año se confirma por separado:

  ```bash
  gcloud run jobs create bdns-sync-full ... --command bdns-sync --args backfill --task-timeout 24h
  gcloud run jobs execute bdns-sync-full --project $PROJECT --region $REGION
  ```

  Como `convocatorias` tarda unas 19 horas y puede tardar más si el servidor va cargado, lo más práctico es lanzar primero todo lo demás y dejar `convocatorias` para otra ejecución, o repartirla por años con `bdns-sync sync convocatorias --since ... --until ...`.

- **Cualquier máquina con Docker**: `docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync bdns-sync backfill`

## Otras nubes

Se hace igual y con los mismos números:

| Nube | Tarea | Programación |
|---|---|---|
| AWS | Tarea de ECS Fargate (o AWS Batch) | EventBridge Scheduler |
| Azure | Container Apps Job | La programación de la propia tarea |

La única diferencia real está en cómo te autenticas contra la base de datos de destino: fuera de Google Cloud no hay credenciales automáticas, así que tienes que pasarlas como secreto de la tarea (`GOOGLE_APPLICATION_CREDENTIALS`, o la URL con contraseña si usas PostgreSQL).

## Sin nube

Basta con una línea de cron en cualquier máquina, como se explica en [sincronización diaria](scheduling.md).
