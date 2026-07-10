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

# 2. Cloud Run no puede tirar de ghcr.io directamente: un repo remoto en
#    Artifact Registry hace de proxy (pull-through) de ghcr
gcloud artifacts repositories create ghcr \
  --project $PROJECT --location $REGION \
  --repository-format docker --mode remote-repository \
  --remote-docker-repo https://ghcr.io

# 3. El job de la delta diaria
gcloud run jobs create bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --image $REGION-docker.pkg.dev/$PROJECT/ghcr/cruzlorite/bdns-sync:latest \
  --service-account $SA \
  --set-env-vars BDNS_SYNC_TARGET_URL=bigquery://$PROJECT/$DATASET \
  --memory 1Gi --task-timeout 6h --max-retries 0
gcloud run jobs add-iam-policy-binding bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --member serviceAccount:$SA --role roles/run.invoker

# 4. El cron (Cloud Scheduler no existe en todas las regiones; vale
#    cualquiera, solo llama a la API del job)
gcloud scheduler jobs create http bdns-sync-delta-daily \
  --project $PROJECT --location europe-west1 \
  --schedule "0 2 * * *" --time-zone "Europe/Madrid" \
  --uri "https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/bdns-sync-delta:run" \
  --http-method POST \
  --oauth-service-account-email $SA
```

Notas:

- `--task-timeout 6h` da holgura a las ventanas `monthly`/`annual`; la weekly diaria tarda ~20 min.
- `--max-retries 0`: si un run muere, el siguiente cron lo repara (idempotente); reintentar en caliente solo duplica trabajo de fetch.

### Coste y candados

Con este esquema los servicios de pago en juego son dos, y el gasto esperado es de céntimos al mes (el job corre ~20 min/día con 1 vCPU; los load jobs de BigQuery son gratis; las queries del diff escanean pocos GB):

- **Presupuesto**: los presupuestos de Google Cloud **solo avisan, no cortan**. Para un tope de gasto real el único candado nativo es la cuota de BigQuery.
- **Cuota dura de BigQuery** (esto sí corta): límite diario de bytes escaneados por queries. 500 GiB/día cubre de sobra las ventanas anuales y acota el peor caso a ~3 €/día:

  ```bash
  gcloud alpha services quota update --service bigquery.googleapis.com \
    --consumer projects/$PROJECT \
    --metric bigquery.googleapis.com/quota/query/usage \
    --unit 1/d/{project} --value 512000 --force
  ```

- **Alerta de fallo del job** (Cloud Monitoring): política sobre la métrica `run.googleapis.com/job/completed_execution_count` con `result=failed` hacia un canal de email. Un run fallido no exige acción inmediata — el cron del día siguiente lo repara — pero conviene enterarse.

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
