# BTI Bot (Cloud Run)

Telegram-бот: получает данные из Росреестра (PKK) по кадастровому номеру и считает три карточки цен.

## Функции
- Поиск по кадастру (PKK API)
- Карточка 1: БТИ (обмеры, техпаспорт, техзадание)
- Карточка 2: Конкуренты (медиана + НДС 22% + прибыль 10%)
- Карточка 3: Рекомендуемая (среднее между БТИ и итогом конкурентов)

## Переменные окружения (через Secret Manager)
- BOT_TOKEN
- REESTR_API_TOKEN
- SERPRIVER_API_KEY

## Локальный запуск
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN=xxx
export REESTR_API_TOKEN=xxx
export SERPRIVER_API_KEY=xxx
python app.py
```

## Docker (локально)
```bash
docker build -t bti-bot .
docker run -p 8080:8080 \
  -e BOT_TOKEN=$BOT_TOKEN \
  -e REESTR_API_TOKEN=$REESTR_API_TOKEN \
  -e SERPRIVER_API_KEY=$SERPRIVER_API_KEY \
  bti-bot
```

## Деплой в Cloud Run
```bash
PROJECT_ID=talkhint
SERVICE_NAME=btibot
REGION=europe-west1
IMAGE=gcr.io/$PROJECT_ID/$SERVICE_NAME

docker buildx build --platform linux/amd64 -t $IMAGE .
docker push $IMAGE

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=BOT_TOKEN=BOT_TOKEN:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest
```

## Webhook настройка
```bash
BOT_TOKEN=$(gcloud secrets versions access latest --secret=BOT_TOKEN)
SERVICE_URL=$(gcloud run services describe btibot --region=europe-west1 --format='value(status.url)')
curl -s "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$SERVICE_URL"
```

## Тест
```bash
curl -s https://SERVICE_URL/health
```

## Безопасность
- Секреты через Secret Manager
- В репозитории нет токенов и .env

