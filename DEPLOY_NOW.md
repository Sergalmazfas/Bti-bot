# 🚀 BTI-PRICE: Готовые команды для деплоя

## ✅ Что у вас уже есть:
- Проект: **BTI-PRICE** (637190449180)
- Секрет: **BOT-BTI-PRICE**
- Service Account: `bti-price-bot@bti-price.iam.gserviceaccount.com`

---

## 🎯 Деплой за 3 шага

### Шаг 1: Дать права Service Account на чтение секрета

```bash
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --project=bti-price \
  --member="serviceAccount:bti-price-bot@bti-price.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Также дайте права Compute Engine Service Account:**

```bash
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --project=bti-price \
  --member="serviceAccount:637190449180-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Шаг 2: Установить переменные

```bash
export PROJECT_ID="bti-price"
gcloud config set project bti-price
```

### Шаг 3: Запустить деплой

```bash
cd /Users/seregaboss/Bti-bot-1
./deploy-with-secrets.sh
```

---

## 🔧 Альтернатива: Ручной деплой

Если хотите полный контроль, выполните команды вручную:

### 1. Настроить проект
```bash
gcloud config set project bti-price
export PROJECT_ID="bti-price"
```

### 2. Проверить секрет
```bash
# Посмотреть секрет
gcloud secrets describe BOT-BTI-PRICE --project=bti-price

# Проверить содержимое (для теста)
gcloud secrets versions access latest --secret="BOT-BTI-PRICE" --project=bti-price
```

### 3. Собрать и отправить образ
```bash
# Сборка для Cloud Run
docker buildx build --platform linux/amd64 -t gcr.io/bti-price/bti-price-bot .

# Отправка в GCR
docker push gcr.io/bti-price/bti-price-bot
```

### 4. Деплой на Cloud Run
```bash
gcloud run deploy bti-price-bot \
  --image gcr.io/bti-price/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --project=bti-price \
  --service-account=bti-price-bot@bti-price.iam.gserviceaccount.com \
  --update-secrets=/secrets/bot-config=BOT-BTI-PRICE:latest
```

### 5. Настроить Webhook
```bash
# Получить URL сервиса
SERVICE_URL=$(gcloud run services describe bti-price-bot \
  --region=us-central1 \
  --project=bti-price \
  --format="value(status.url)")

echo "Service URL: $SERVICE_URL"

# Установить webhook
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"
```

---

## ✅ Проверка после деплоя

```bash
# 1. Получить URL
SERVICE_URL=$(gcloud run services describe bti-price-bot \
  --region=us-central1 \
  --project=bti-price \
  --format="value(status.url)")

# 2. Health check
curl -s $SERVICE_URL/health

# 3. Webhook info
curl -s "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/getWebhookInfo"

# 4. Логи (проверить загрузку секретов)
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot" \
  --project=bti-price \
  --limit=20
```

**В логах должно быть:** `✅ Секреты загружены из Google Secret Manager`

---

## 🔐 Проверка прав доступа к секрету

```bash
# Посмотреть, кто имеет доступ к секрету
gcloud secrets get-iam-policy BOT-BTI-PRICE --project=bti-price

# Должны быть:
# - bti-price-bot@bti-price.iam.gserviceaccount.com
# - 637190449180-compute@developer.gserviceaccount.com
```

Если прав нет, добавьте:

```bash
# Service Account бота
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --project=bti-price \
  --member="serviceAccount:bti-price-bot@bti-price.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Compute Engine Service Account
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --project=bti-price \
  --member="serviceAccount:637190449180-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 🔄 Обновление секрета

Если нужно обновить API ключи в секрете:

```bash
# Добавить новую версию секрета
gcloud secrets versions add BOT-BTI-PRICE \
  --project=bti-price \
  --data-file=- << 'EOF'
{
  "BOT_TOKEN": "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o",
  "OPENAI_API_KEY": "новый-ключ",
  "REESTR_API_TOKEN": "новый-токен",
  "SERPRIVER_API_KEY": "S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
}
EOF

# Передеплоить (подхватит новую версию автоматически)
./deploy-with-secrets.sh
```

---

## 📊 Мониторинг

### Cloud Run Console:
```
https://console.cloud.google.com/run/detail/us-central1/bti-price-bot?project=bti-price
```

### Secret Manager:
```
https://console.cloud.google.com/security/secret-manager?project=bti-price
```

### Логи в реальном времени:
```bash
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot" \
  --project=bti-price
```

---

## 🆘 Устранение неполадок

### Проблема: "Permission denied" на секрет

```bash
# Проверить права
gcloud secrets get-iam-policy BOT-BTI-PRICE --project=bti-price

# Добавить права
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --project=bti-price \
  --member="serviceAccount:637190449180-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Проблема: Бот не отвечает

```bash
# Переустановить webhook
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --project=bti-price --format="value(status.url)")
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"
```

### Проблема: Ошибки в логах

```bash
# Логи с ошибками
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot AND severity>=ERROR" \
  --project=bti-price \
  --limit=20
```

---

## 🎯 Полная команда деплоя (одна строка)

```bash
export PROJECT_ID="bti-price" && \
gcloud config set project bti-price && \
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --project=bti-price \
  --member="serviceAccount:637190449180-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" && \
cd /Users/seregaboss/Bti-bot-1 && \
docker buildx build --platform linux/amd64 -t gcr.io/bti-price/bti-price-bot . && \
docker push gcr.io/bti-price/bti-price-bot && \
gcloud run deploy bti-price-bot \
  --image gcr.io/bti-price/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --project=bti-price \
  --service-account=bti-price-bot@bti-price.iam.gserviceaccount.com \
  --update-secrets=/secrets/bot-config=BOT-BTI-PRICE:latest && \
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --project=bti-price --format="value(status.url)") && \
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/" && \
echo "✅ Деплой завершен! URL: $SERVICE_URL"
```

---

## ✅ Чек-лист

- [ ] Выполнен Шаг 1 (права доступа к секрету)
- [ ] Выполнен Шаг 2 (установка переменных)
- [ ] Выполнен Шаг 3 (деплой)
- [ ] Health check прошел
- [ ] Webhook настроен
- [ ] Бот отвечает в Telegram
- [ ] В логах: "✅ Секреты загружены из Google Secret Manager"

---

**Время деплоя: 3-5 минут**  
**Проект: BTI-PRICE**  
**Готово к запуску! 🚀**

