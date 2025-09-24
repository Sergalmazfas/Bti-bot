# Telegram PKK Bot (Cloud Run)

- index.py: handler for PKK queries
- app.py: Flask adapter for Cloud Run
- requirements.txt: runtime deps
- Dockerfile: container build for Cloud Run

Deploy:
- gcloud builds submit --tag gcr.io/PROJECT/telegram-pkk-bot
- gcloud run deploy telegram-pkk-bot --image gcr.io/PROJECT/telegram-pkk-bot --region us-central1 --allow-unauthenticated
