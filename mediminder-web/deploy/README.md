# Cloud deployment (GCP)

> **Scope note.** Per the task's `<out of scope>` clause, the actual deploy is
> not executed. The files below are provided so a deployer can follow them
> end-to-end.

## Files

- `cloudbuild.yaml` — Cloud Build pipeline: build → push → deploy backend → deploy frontend.
- `cloud-run-backend.yaml` — Standalone service manifest for the backend Cloud Run service.
- `cloud-run-frontend.yaml` — Same for the frontend.

## One-time setup

```bash
PROJECT=mediminder-app
REGION=asia-south1

gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com \
  secretmanager.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com --project=$PROJECT

# Artifact Registry
gcloud artifacts repositories create mediminder \
  --repository-format=docker --location=$REGION --project=$PROJECT

# Cloud SQL
gcloud sql instances create mediminder \
  --database-version=POSTGRES_17 --region=$REGION \
  --tier=db-f1-micro --project=$PROJECT
gcloud sql databases create mediminder --instance=mediminder --project=$PROJECT

# Secret Manager (the task pins this ID)
gcloud secrets create serviceaccount \
  --replication-policy=automatic --project=645869155931
# Populate a JSON blob with { "database_url": "...", "jwt_secret": "...",
# "admin_password": "...", "admin_username": "admin" } as the latest version.

# Runtime service account
gcloud iam service-accounts create mediminder-runtime --project=$PROJECT
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:mediminder-runtime@$PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
gcloud secrets add-iam-policy-binding serviceaccount \
  --member=serviceAccount:mediminder-runtime@$PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor --project=645869155931
```

## Deploy

```bash
gcloud builds submit --config=deploy/cloudbuild.yaml \
  --substitutions=_PROJECT=$PROJECT,_REGION=$REGION
```

Or, if using the manifest files directly:

```bash
sed -i 's/PLACEHOLDER_SHA/<git-sha>/g' deploy/cloud-run-*.yaml
gcloud run services replace deploy/cloud-run-backend.yaml --region=$REGION
gcloud run services replace deploy/cloud-run-frontend.yaml --region=$REGION
```
