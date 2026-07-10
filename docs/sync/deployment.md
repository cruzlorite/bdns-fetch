# Despliegue en la nube

Cómo mantener un destino sincronizado sin una máquina propia. `bdns-sync` es un CLI sin estado local — toda la configuración es una variable de entorno y todo lo persistente vive en la base de datos de destino — así que el patrón es el mismo en cualquier nube:

> **imagen de contenedor + job programado + `BDNS_SYNC_TARGET_URL`**

## La imagen

Cada release publica una imagen en GitHub Container Registry con el extra de BigQuery y los scripts de orquestación incluidos:

```bash
docker pull ghcr.io/cruzlorite/bdns-sync:latest    # o :0.1.0
```

- El comando por defecto es `scripts/delta_load.sh` (la delta diaria; decide sola la ventana).
- Cualquier otro comando se pasa tal cual: `docker run ... ghcr.io/cruzlorite/bdns-sync bdns-sync sync sectores`.
- Un funcionamiento tipo Cloud Function no encaja: los límites de timeout (15-60 min) no cubren las ventanas anchas (una `annual` de `convocatorias` son ~3 h) ni el bootstrap (~24 h, ver README).

## Receta: Google Cloud (Cloud Run Jobs + Cloud Scheduler)

La nube con destino verificado en vivo (BigQuery). La service account adjunta al job hace que la autenticación funcione sola (ADC), sin claves ni secretos.

```bash
PROJECT=mi-proyecto REGION=europe-southwest1 DATASET=bdns_sync

# 1. Service account con permisos mínimos
gcloud iam service-accounts create bdns-sync --project $PROJECT
SA=bdns-sync@$PROJECT.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.jobUser
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.dataEditor
# (dataEditor puede concederse solo sobre el dataset si se prefiere)

# 2. El job de la delta diaria
gcloud run jobs create bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --image ghcr.io/cruzlorite/bdns-sync:latest \
  --service-account $SA \
  --set-env-vars BDNS_SYNC_TARGET_URL=bigquery://$PROJECT/$DATASET \
  --memory 1Gi --task-timeout 6h --max-retries 0

# 3. El cron
gcloud scheduler jobs create http bdns-sync-delta-daily \
  --project $PROJECT --location $REGION \
  --schedule "0 2 * * *" \
  --uri "https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/bdns-sync-delta:run" \
  --http-method POST \
  --oauth-service-account-email $SA
```

Notas:

- `--task-timeout 6h` da holgura a las ventanas `monthly`/`annual`; la weekly diaria tarda ~20 min.
- `--max-retries 0`: si un run muere, el siguiente cron lo repara (idempotente); reintentar en caliente solo duplica trabajo de fetch.
- El scheduler necesita, la primera vez, conceder a la SA `roles/run.invoker` sobre el job (o usar una SA aparte para invocar).

## La carga inicial (bootstrap)

Operación única de ~24 h (ver la tabla del README) que se lanza a mano. Dos opciones:

- **Un segundo job** con el comando del full load y el timeout al máximo (24 h en Cloud Run Jobs — justo; si un corte lo interrumpe, re-ejecutar repara: las rodajas de un año confirman de forma independiente):

  ```bash
  gcloud run jobs create bdns-sync-full ... --command /app/scripts/full_load.sh --task-timeout 24h
  gcloud run jobs execute bdns-sync-full --project $PROJECT --region $REGION
  ```

- **Cualquier máquina con Docker**: `docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync /app/scripts/full_load.sh`

## Otras nubes

Mismo patrón, mismos números:

| Nube | Job | Programación |
|---|---|---|
| AWS | ECS Fargate task (o AWS Batch) | EventBridge Scheduler |
| Azure | Container Apps Job | cron integrado del propio job |

La única diferencia real es la autenticación hacia el destino: fuera de GCP no hay ADC implícito, así que las credenciales del destino (p. ej. `GOOGLE_APPLICATION_CREDENTIALS`, o la URL con contraseña de un Postgres) entran como secreto del job.

## Sin nube

Una línea de cron en cualquier máquina, como documenta el [README](../README.md#operación-programada).
