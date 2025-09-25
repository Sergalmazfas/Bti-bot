# 🚀 Руководство по деплою BTI Bot

## 📋 Быстрый старт

### 1. Подготовка файлов
```bash
# Скопировать файлы
cp index_clean.py index.py
cp requirements_clean.txt requirements.txt
cp Dockerfile_clean Dockerfile
```

### 2. Сборка и деплой
```bash
# Собрать Docker образ
docker buildx build --platform linux/amd64 -t gcr.io/talkhint/btibot-clean .

# Отправить в реестр
docker push gcr.io/talkhint/btibot-clean

# Развернуть на Cloud Run
gcloud run deploy btibot-clean \
  --image gcr.io/talkhint/btibot-clean \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="BOT_TOKEN=8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o"
```

### 3. Настройка webhook
```bash
# Получить URL сервиса
SERVICE_URL=$(gcloud run services describe btibot-clean --region=europe-west1 --format="value(status.url)")

# Установить webhook
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"
```

### 4. Проверка
```bash
# Health check
curl -s $SERVICE_URL/health

# Проверить webhook
curl -X GET "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/getWebhookInfo"
```

## 🔧 Настройка переменных окружения

### В Google Console:
1. Перейти в Cloud Run
2. Выбрать сервис btibot-clean
3. Edit & Deploy New Revision
4. Variables & Secrets → Add Variable
5. Добавить:
   - `BOT_TOKEN` = `8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o`

## 📱 Тестирование

### 1. Найти бота в Telegram
- Поиск: @your_bot_username
- Или по токену: 8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o

### 2. Отправить команды
- `/start` - приветствие
- `77:01:0001001:1001` - тестовый кадастровый номер

### 3. Проверить логи
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-clean" --limit=10
```

## 🚨 Устранение неполадок

### Проблема: "Service Unavailable"
```bash
# Проверить логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-clean AND severity>=ERROR" --limit=5
```

### Проблема: Бот не отвечает
```bash
# Проверить webhook
curl -X GET "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/getWebhookInfo"

# Переустановить webhook
curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"
```

### Проблема: Ошибки импорта
```bash
# Проверить Dockerfile
cat Dockerfile
# Должно быть: COPY index_clean.py index.py
```

## ✅ Критерии успеха

- ✅ Health check: `{"status":"ok"}`
- ✅ Webhook настроен
- ✅ Бот отвечает на `/start`
- ✅ Логи без ошибок
- ✅ Обработка кадастровых номеров

## 📊 Отчёт

### Обязательные скриншоты:
1. GitHub коммит
2. Google Console - переменные
3. Деплой (gcloud)
4. getWebhookInfo
5. Ответ бота в Telegram
6. Логи без ошибок

**Готово! 🎉**
