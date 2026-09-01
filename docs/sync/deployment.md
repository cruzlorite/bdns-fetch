# Despliegue en la nube

Cómo mantener un destino sincronizado sin tener una máquina propia. `bdns-sync` es una herramienta de línea de comandos sin estado local —toda la configuración es una variable de entorno y todo lo que persiste está en la base de datos de destino—, así que el patrón es el mismo en cualquier nube:

> **imagen de contenedor + job programado + `BDNS_SYNC_TARGET_URL`**

## La imagen

Cada release publica una imagen en GitHub Container Registry con el extra de BigQuery y los scripts de orquestación dentro:

```bash
docker pull ghcr.io/cruzlorite/bdns-sync:latest    # o :0.1.0
```

- El comando por defecto es `scripts/delta_load.sh` (la carga diaria; la ventana la decide él solo).
- Cualquier otro comando se pasa tal cual: `docker run ... ghcr.io/cruzlorite/bdns-sync bdns-sync sync sectores`.
- El modelo tipo Cloud Function no encaja: sus timeouts (de 15 a 60 min) no dan para las ventanas anchas (una `annual` de `convocatorias` son unas 3 h) ni para la carga inicial (~24 h, ver el README).

## Receta: Google Cloud (Cloud Run Jobs + Cloud Scheduler)

Es la nube con el destino comprobado contra el servicio real (BigQuery). Con una cuenta de servicio asociada al job la autenticación funciona sola (ADC), sin claves ni secretos.

```bash
PROJECT=mi-proyecto REGION=europe-southwest1 DATASET=bdns_sync

# 1. Cuenta de servicio con los permisos mínimos
gcloud iam service-accounts create bdns-sync --project $PROJECT
SA=bdns-sync@$PROJECT.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.jobUser
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.dataEditor
# (dataEditor puede concederse solo sobre el dataset, si se prefiere)

# 2. Cloud Run no descarga imágenes de ghcr.io directamente: un repositorio
#    remoto en Artifact Registry hace de proxy (pull-through) de ghcr
gcloud artifacts repositories create ghcr \
  --project $PROJECT --location $REGION \
  --repository-format docker --mode remote-repository \
  --remote-docker-repo https://ghcr.io

# 3. El job de la carga diaria
gcloud run jobs create bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --image $REGION-docker.pkg.dev/$PROJECT/ghcr/cruzlorite/bdns-sync:latest \
  --service-account $SA \
  --set-env-vars BDNS_SYNC_TARGET_URL=bigquery://$PROJECT/$DATASET \
  --memory 4Gi --task-timeout 6h --max-retries 0
gcloud run jobs add-iam-policy-binding bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --member serviceAccount:$SA --role roles/run.invoker

# 4. El cron (Cloud Scheduler no está en todas las regiones; vale
#    cualquiera, porque solo llama a la API del job)
gcloud scheduler jobs create http bdns-sync-delta-daily \
  --project $PROJECT --location europe-west1 \
  --schedule "0 2 * * *" --time-zone "Europe/Madrid" \
  --uri "https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/bdns-sync-delta:run" \
  --http-method POST \
  --oauth-service-account-email $SA
```

Notas:

- `--memory 4Gi`, no menos. El consumo lo marca la ventana más ancha, la `annual` de `concesiones_busqueda`, que se lanza tres días al año y stagea unos 20 millones de filas: pico medido de **2,33 GB**. Las dos veces que se ha quedado corto se vieron en real, y las dos con la misma firma, un `exit 137` sin evento terminal en `_sync_runs`: con 1 Gi murieron cuatro ejecuciones semanales seguidas en julio de 2026, y con 2 Gi murió la anual del 1 de septiembre. Subir de 2 a 4 Gi cuesta unos 0,18 $ al mes y no obliga a subir de vCPU.
- `--task-timeout 6h` deja holgura para las ventanas `monthly` y `annual`; la semanal, que se lanza a diario, tarda unos 20 min.
- `--max-retries 0`: si una ejecución se cae, la del cron del día siguiente lo arregla, porque el proceso es idempotente; reintentar en caliente solo repite trabajo de descarga.

### Coste y topes de gasto

Con este esquema hay dos servicios de pago en juego, y el gasto esperado son céntimos al mes (el job corre unos 20 min al día con 1 vCPU, los load jobs de BigQuery son gratis y las consultas del diff escanean pocos GB):

- **Presupuestos**: los de Google Cloud **solo avisan, no cortan**. Para poner un tope de gasto de verdad, el único freno nativo es la cuota de BigQuery.
- **Cuota dura de BigQuery** (esta sí corta): límite diario de bytes escaneados por consultas. El consumo tiene dos regímenes muy distintos: un día normal son ~0,2 GiB, pero los tres días al año que corre la ventana `annual` el diff escanea unos 127 GiB, de los cuales 115 son solo `concesiones_busqueda`: correlaciona los 29 millones de filas de la tabla con los ~20 millones del staging, y lo hace varias veces entre los recuentos, el refresco de `_synced_at`, el cierre de versiones y la inserción. El tope hay que ponerlo pensando en esos tres días, no en la media, y con holgura para cualquier consulta manual que caiga el mismo día. 300.000 MiB (293 GiB) dan algo más del doble de lo medido y acotan el peor caso a menos de 2 € al día:

  ```bash
  gcloud alpha services quota update --service bigquery.googleapis.com \
    --consumer projects/$PROJECT \
    --metric bigquery.googleapis.com/quota/query/usage \
    --unit 1/d/{project} --value 300000 --force
  ```

- **Aviso si falla el job** (Cloud Monitoring): una política sobre la métrica `run.googleapis.com/job/completed_execution_count` con `result=failed` hacia un canal de email. Una ejecución fallida no obliga a hacer nada de inmediato, porque el cron del día siguiente la repara, pero conviene enterarse.

## La carga inicial

Es una operación de unas 24 h (ver la tabla del README) que se lanza a mano una sola vez. Dos opciones:

- **Un segundo job** con el comando de la carga completa y el timeout al máximo (24 h en Cloud Run Jobs, justo; si un corte lo interrumpe, basta con volver a lanzarlo, porque los tramos de un año se confirman por separado):

  ```bash
  gcloud run jobs create bdns-sync-full ... --command /app/scripts/full_load.sh --task-timeout 24h
  gcloud run jobs execute bdns-sync-full --project $PROJECT --region $REGION
  ```

- **Cualquier máquina con Docker**: `docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync /app/scripts/full_load.sh`

## Otras nubes

El mismo patrón y los mismos números:

| Nube | Job | Programación |
|---|---|---|
| AWS | Tarea de ECS Fargate (o AWS Batch) | EventBridge Scheduler |
| Azure | Container Apps Job | El cron del propio job |

La única diferencia real está en la autenticación contra el destino: fuera de GCP no hay ADC implícito, así que las credenciales (`GOOGLE_APPLICATION_CREDENTIALS`, o la URL con contraseña de un Postgres) entran como secreto del job.

## Sin nube

Una línea de cron en cualquier máquina, tal como explica el [README](../README.md#operación-programada).
