# Cloud deployment

How to keep a target synced without a machine of your own. `bdns-sync` is a CLI with no local state — all configuration is one environment variable, and everything persistent lives in the target database — so the pattern is the same on any cloud:

> **container image + scheduled job + `BDNS_SYNC_TARGET_URL`**

## The image

Every release publishes an image to GitHub Container Registry with the BigQuery extra and the orchestration scripts included:

```bash
docker pull ghcr.io/cruzlorite/bdns-sync:latest    # or :0.1.0
```

- The default command is `scripts/delta_load.sh` (the daily delta; it picks the window by itself).
- Any other command passes through as-is: `docker run ... ghcr.io/cruzlorite/bdns-sync bdns-sync sync sectores`.
- A Cloud Function-style deployment does not fit: timeout limits (15-60 min) cannot cover the wide windows (an `annual` run of `convocatorias` is ~3 h) or the bootstrap (~24 h, see the README).

## Recipe: Google Cloud (Cloud Run Jobs + Cloud Scheduler)

The cloud with a live-verified target (BigQuery). The service account attached to the job makes authentication work by itself (ADC), with no keys and no secrets.

```bash
PROJECT=my-project REGION=europe-southwest1 DATASET=bdns_sync

# 1. Service account with minimum permissions
gcloud iam service-accounts create bdns-sync --project $PROJECT
SA=bdns-sync@$PROJECT.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.jobUser
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.dataEditor
# (dataEditor can be granted on the dataset alone if preferred)

# 2. Cloud Run cannot pull from ghcr.io directly: a remote repository in
#    Artifact Registry acts as a pull-through proxy of ghcr
gcloud artifacts repositories create ghcr \
  --project $PROJECT --location $REGION \
  --repository-format docker --mode remote-repository \
  --remote-docker-repo https://ghcr.io

# 3. The daily delta job
gcloud run jobs create bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --image $REGION-docker.pkg.dev/$PROJECT/ghcr/cruzlorite/bdns-sync:latest \
  --service-account $SA \
  --set-env-vars BDNS_SYNC_TARGET_URL=bigquery://$PROJECT/$DATASET \
  --memory 1Gi --task-timeout 6h --max-retries 0
gcloud run jobs add-iam-policy-binding bdns-sync-delta \
  --project $PROJECT --region $REGION \
  --member serviceAccount:$SA --role roles/run.invoker

# 4. The cron (Cloud Scheduler is not available in every region; any
#    region works, it only calls the job's API)
gcloud scheduler jobs create http bdns-sync-delta-daily \
  --project $PROJECT --location europe-west1 \
  --schedule "0 2 * * *" --time-zone "Europe/Madrid" \
  --uri "https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/bdns-sync-delta:run" \
  --http-method POST \
  --oauth-service-account-email $SA
```

Notes:

- `--task-timeout 6h` leaves slack for the `monthly`/`annual` windows; the daily weekly run takes ~20 min.
- `--max-retries 0`: if a run dies, the next cron heals it (idempotent); hot retries only duplicate fetch work.

### Cost and guardrails

Two paid services are involved, and the expected spend is cents per month (the job runs ~20 min/day on 1 vCPU; BigQuery load jobs are free; the diff queries scan a few GB):

- **Budgets**: Google Cloud budgets **only notify, they never cut off**. For a real spending cap the only native lock is the BigQuery quota.
- **BigQuery hard quota** (this one does cut off): daily limit on bytes scanned by queries. 500 GiB/day comfortably covers the annual windows and bounds the worst case at ~€3/day:

  ```bash
  gcloud alpha services quota update --service bigquery.googleapis.com \
    --consumer projects/$PROJECT \
    --metric bigquery.googleapis.com/quota/query/usage \
    --unit 1/d/{project} --value 512000 --force
  ```

- **Job failure alert** (Cloud Monitoring): a policy on the `run.googleapis.com/job/completed_execution_count` metric with `result=failed` towards an email channel. A failed run needs no immediate action — the next day's cron heals it — but you want to know.

## The initial load (bootstrap)

A one-off ~24 h operation (see the README table), launched by hand. Two options:

- **A second job** with the full-load command and the timeout at its maximum (24 h on Cloud Run Jobs — a tight fit; if an outage cuts it, re-running heals: the one-year slices commit independently):

  ```bash
  gcloud run jobs create bdns-sync-full ... --command /app/scripts/full_load.sh --task-timeout 24h
  gcloud run jobs execute bdns-sync-full --project $PROJECT --region $REGION
  ```

- **Any machine with Docker**: `docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync /app/scripts/full_load.sh`

## Other clouds

Same pattern, same numbers:

| Cloud | Job | Scheduling |
|---|---|---|
| AWS | ECS Fargate task (or AWS Batch) | EventBridge Scheduler |
| Azure | Container Apps Job | the job's built-in cron |

The only real difference is authentication towards the target: outside GCP there is no implicit ADC, so the target's credentials (e.g. `GOOGLE_APPLICATION_CREDENTIALS`, or a Postgres password URL) go in as a job secret.

## No cloud

One cron line on any machine, as documented in the [README](../README.en.md#scheduled-operation).
