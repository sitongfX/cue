#!/usr/bin/env bash
# Deploy the Cue server to Google Cloud Run in YOUR OWN Google Cloud project.
# Easiest place to run this: Google Cloud Shell (https://shell.cloud.google.com) signed in with your
# personal Google account. Usage:
#   ./deploy.sh <project-id> [region]
# The script asks for your Gemini API key once and stores it in Secret Manager (never in the image).
set -euo pipefail
PROJECT="${1:?usage: ./deploy.sh <project-id> [region]}"
REGION="${2:-us-central1}"
SERVICE="cue-server"

gcloud config set project "$PROJECT" >/dev/null
gcloud services enable run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

if ! gcloud secrets describe gemini-api-key >/dev/null 2>&1; then
  read -rsp "Gemini API key (input hidden): " KEY; echo
  printf '%s' "$KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy=automatic
  unset KEY
fi
if ! gcloud secrets describe cue-invites >/dev/null 2>&1; then
  CODE="cue_$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
  printf 'me:%s' "$CODE" | gcloud secrets create cue-invites --data-file=- --replication-policy=automatic
  echo "Created your first invite code (keep it private): $CODE"
fi

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
for S in gemini-api-key cue-invites; do
  gcloud secrets add-iam-policy-binding "$S" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role=roles/secretmanager.secretAccessor >/dev/null
done

gcloud run deploy "$SERVICE" --source . --region "$REGION" --allow-unauthenticated \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,CUE_INVITES=cue-invites:latest" \
  --set-env-vars "ALLOWED_ORIGINS=https://sitongfx.github.io,app://cue,RATE_PER_MIN=60,DAILY_CAP=3000" \
  --min-instances 0 --max-instances 3 --memory 256Mi --cpu 1 --concurrency 40 --timeout 300

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo
echo "Deployed: $URL"
echo "In Cue, paste:  <your invite code>@${URL#https://}"
