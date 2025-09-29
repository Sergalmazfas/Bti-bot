#!/bin/bash

# Скрипт для деплоя Forge 3D → 2D сервиса в Cloud Run

set -e

echo "🚀 Starting Forge 3D → 2D deployment..."

# Переменные
PROJECT_ID="swiftchair"
SERVICE_NAME="forge-3d-to-2d"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "📦 Building Docker image..."
docker build -f Dockerfile.forge -t ${IMAGE_NAME} .

echo "📤 Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --max-instances 10 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-secrets="ForgeClientID=ForgeClientID:latest,ForgeClientSecret=ForgeClientSecret:latest"

echo "✅ Deployment completed!"
echo "🌐 Service URL: https://${SERVICE_NAME}-${PROJECT_ID}.${REGION}.run.app"
echo "📊 Monitor: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_ID}"
