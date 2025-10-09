# 🚀 BTI-PRICE: Руководство по деплою на Google Cloud Run

## 📋 Предварительная подготовка

### 1. Установите Google Cloud SDK (если еще не установлен)
```bash
# Проверка установки
gcloud --version

# Если не установлен, установите отсюда:
# https://cloud.google.com/sdk/docs/install
```

### 2. Авторизация в Google Cloud
```bash
# Войти в аккаунт Google
gcloud auth login

# Настроить Docker для работы с GCR
gcloud auth configure-docker
```

### 3. Выбор проекта (или создание нового)
```bash
# Посмотреть список проектов
gcloud projects list

# Выбрать существующий проект
gcloud config set project YOUR_PROJECT_ID

# ИЛИ создать новый проект
gcloud projects create bti-price-bot --name="BTI Price Bot"
gcloud config set project bti-price-bot
```

## 🔧 Переменные окружения

### Обязательные переменные:
```bash
BOT_TOKEN="8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o"
OPENAI_API_KEY="your_openai_api_key"              # Нужно получить на https://platform.openai.com/api-keys
REESTR_API_TOKEN="your_reestr_token"              # Токен Росреестра
SERPRIVER_API_KEY="S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
```

## 🐳 Деплой в 3 шага

### Шаг 1: Сборка Docker-образа
```bash
cd /Users/seregaboss/Bti-bot-1

# Сборка образа для Cloud Run (платформа linux/amd64)
docker buildx build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/bti-price-bot .
```

### Шаг 2: Отправка образа в Google Container Registry
```bash
docker push gcr.io/YOUR_PROJECT_ID/bti-price-bot
```

### Шаг 3: Деплой на Cloud Run
```bash
gcloud run deploy bti-price-bot \
  --image gcr.io/YOUR_PROJECT_ID/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="BOT_TOKEN=8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o,SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z" \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest"
```

**Альтернатива без секретов (все через env vars):**
```bash
gcloud run deploy bti-price-bot \
  --image gcr.io/YOUR_PROJECT_ID/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="BOT_TOKEN=8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o,SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z,OPENAI_API_KEY=YOUR_OPENAI_KEY,REESTR_API_TOKEN=YOUR_REESTR_TOKEN"
```

## 🔗 Настройка Telegram Webhook

### Шаг 4: Получить URL сервиса и установить webhook
```bash
# Получить URL развернутого сервиса
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --format="value(status.url)")

echo "Service URL: $SERVICE_URL"

# Установить webhook для Telegram
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"

# Проверить webhook
curl -X GET "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/getWebhookInfo"
```

## ✅ Проверка работоспособности

### 1. Health Check
```bash
curl -s $SERVICE_URL/health
# Ожидается: {"status":"ok"}
```

### 2. Проверка логов
```bash
# Посмотреть последние логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot" --limit=20 --format=json

# Логи с ошибками
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot AND severity>=ERROR" --limit=10
```

### 3. Тестирование бота в Telegram
1. Найти бота: `@your_bot_username`
2. Отправить `/start`
3. Отправить тестовый кадастровый номер: `77:01:0001001:1001`
4. Проверить генерацию коммерческого предложения

## 🔄 Обновление деплоя

Если нужно обновить код:
```bash
cd /Users/seregaboss/Bti-bot-1

# 1. Пересобрать образ
docker buildx build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/bti-price-bot .

# 2. Отправить в GCR
docker push gcr.io/YOUR_PROJECT_ID/bti-price-bot

# 3. Обновить деплой (Cloud Run автоматически подхватит новый образ)
gcloud run deploy bti-price-bot \
  --image gcr.io/YOUR_PROJECT_ID/bti-price-bot \
  --region us-central1
```

## 🚨 Устранение неполадок

### Проблема 1: "Permission denied"
```bash
# Включить необходимые API
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Проблема 2: Бот не отвечает
```bash
# 1. Проверить статус сервиса
gcloud run services describe bti-price-bot --region=us-central1

# 2. Проверить webhook
curl -X GET "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/getWebhookInfo"

# 3. Переустановить webhook
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --format="value(status.url)")
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"
```

### Проблема 3: Ошибки в логах
```bash
# Подробные логи с контекстом
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"
```

### Проблема 4: "Out of memory"
```bash
# Увеличить память до 1GB
gcloud run services update bti-price-bot \
  --region=us-central1 \
  --memory 1Gi
```

## 💰 Оценка стоимости

Cloud Run тарифицируется по факту использования:
- **Бесплатный лимит**: 2 миллиона запросов/месяц
- **CPU**: ~$0.00002400 за vCPU-секунду
- **Память**: ~$0.00000250 за GiB-секунду
- **Запросы**: $0.40 за миллион запросов

Для небольшого бота с 100-1000 пользователей в день: **~$5-10/месяц**

## 📊 Мониторинг

### Метрики в Google Cloud Console:
1. Перейти: Cloud Run → bti-price-bot → Metrics
2. Отслеживать:
   - Request count (количество запросов)
   - Request latency (задержка)
   - Memory utilization (использование памяти)
   - CPU utilization (использование CPU)

### Настройка алертов:
```bash
# Создать политику алертов для ошибок
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="BTI Bot Errors" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=60s
```

## 🎯 Быстрый деплой (одна команда)

```bash
# Полный деплой одной командой (замените YOUR_PROJECT_ID и API ключи)
cd /Users/seregaboss/Bti-bot-1 && \
docker buildx build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/bti-price-bot . && \
docker push gcr.io/YOUR_PROJECT_ID/bti-price-bot && \
gcloud run deploy bti-price-bot \
  --image gcr.io/YOUR_PROJECT_ID/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="BOT_TOKEN=8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o,SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z,OPENAI_API_KEY=YOUR_OPENAI_KEY,REESTR_API_TOKEN=YOUR_REESTR_TOKEN" && \
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --format="value(status.url)") && \
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/" && \
echo "Деплой завершен! Service URL: $SERVICE_URL"
```

## 📝 Чек-лист перед деплоем

- [ ] Google Cloud SDK установлен и настроен
- [ ] Создан/выбран проект в Google Cloud
- [ ] Получен OPENAI_API_KEY
- [ ] Получен REESTR_API_TOKEN
- [ ] Dockerfile проверен и готов
- [ ] requirements.txt содержит все зависимости
- [ ] main.py и app.py на месте
- [ ] Telegram Bot Token активен

## 🎉 Готово!

После успешного деплоя ваш BTI-PRICE бот будет доступен 24/7 на Google Cloud Run с автомасштабированием и высокой доступностью!

**URL мониторинга:** https://console.cloud.google.com/run

---
**Создано для BTI-PRICE Bot 🏠💰**

