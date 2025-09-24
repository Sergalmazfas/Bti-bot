# 🚀 Deployment Guide

## Quick Deploy to Google Cloud Run

### 1. Prerequisites
```bash
# Install Google Cloud SDK
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Build and Deploy
```bash
# Build Docker image
docker buildx build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/bti-bot .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/bti-bot

# Deploy to Cloud Run
gcloud run deploy bti-bot \
  --image gcr.io/YOUR_PROJECT_ID/bti-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="BOT_TOKEN=your_bot_token,OPENAI_API_KEY=your_openai_key,REESTR_API_TOKEN=your_reestr_token,SERPRIVER_API_KEY=your_serpriver_key"
```

### 3. Set Webhook
```bash
# Get your service URL
SERVICE_URL="https://bti-bot-XXXXX.us-central1.run.app"

# Set Telegram webhook
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$SERVICE_URL/\"}"
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram Bot Token | `123456789:ABC...` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
| `REESTR_API_TOKEN` | Russian State Register API | `your_reestr_token` |
| `SERPRIVER_API_KEY` | SERP API Key | `your_serpriver_key` |

## Health Check
```bash
curl https://your-service-url/health
# Expected: {"status":"ok"}
```

## Monitoring
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot" --limit=10

# Check service status
gcloud run services describe bti-bot --region=us-central1
```

## Troubleshooting

### Common Issues
1. **Bot not responding**: Check webhook URL and BOT_TOKEN
2. **GPT not working**: Verify OPENAI_API_KEY
3. **Data not found**: Check REESTR_API_TOKEN
4. **Competitor prices missing**: Verify SERPRIVER_API_KEY

### Logs to Check
- `gcloud logging read "severity>=ERROR" --limit=5`
- `gcloud logging read "textPayload:\"GPT\" OR textPayload:\"OpenAI\"" --limit=5`
