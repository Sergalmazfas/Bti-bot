# 🚀 Руководство по развертыванию BTI Bot

## 📋 **Быстрый старт для джуна**

### **1. Подготовка (5 минут)**
```bash
# Клонировать проект
git clone https://github.com/Sergalmazfas/Bti-bot.git
cd Bti-bot

# Создать ветку
git checkout -b feature/restore-$(whoami)

# Проверить файлы
ls -la main.py app.py requirements.txt Dockerfile
```

### **2. Настройка Google Cloud (3 минуты)**
```bash
# Авторизация
gcloud auth login
gcloud config set project talkhint

# Проверить секреты
gcloud secrets list
```

### **3. Сборка и деплой (10 минут)**
```bash
# Собрать образ
docker buildx build --platform linux/amd64 -t gcr.io/talkhint/btibot .

# Отправить в реестр
docker push gcr.io/talkhint/btibot

# Развернуть
gcloud run deploy btibot-restore \
  --image gcr.io/talkhint/btibot \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest"
```

### **4. Настройка webhook (2 минуты)**
```bash
# Получить URL
SERVICE_URL=$(gcloud run services describe btibot-restore --region=europe-west1 --format="value(status.url)")

# Установить webhook
curl -X POST "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/setWebhook?url=$SERVICE_URL/"
```

### **5. Тестирование (5 минут)**
```bash
# Health check
curl -s "$SERVICE_URL/health"

# Проверить логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore" --limit=5
```

**Общее время: ~25 минут**

---

## 🔧 **Детальные команды**

### **Проверка структуры проекта**
```bash
# Основные файлы
ls -la main.py app.py requirements.txt Dockerfile

# Размер main.py (должен быть ~40KB)
wc -l main.py

# Проверить импорты
grep -n "import" main.py | head -5
```

### **Проверка зависимостей**
```bash
# Содержимое requirements.txt
cat requirements.txt

# Проверить синтаксис
python -m py_compile main.py
python -m py_compile app.py
```

### **Проверка Dockerfile**
```bash
# Содержимое Dockerfile
cat Dockerfile

# Должно содержать:
# - FROM python:3.12-slim
# - COPY main.py app.py ./
# - CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 30 app:app
```

### **Проверка секретов**
```bash
# Список секретов
gcloud secrets list

# Проверить BOT_TOKEN (должен начинаться с цифр)
gcloud secrets versions access latest --secret="BOT_TOKEN" | head -c 20

# Проверить OPENAI_API_KEY (должен начинаться с sk-)
gcloud secrets versions access latest --secret="OPENAI_API_KEY" | head -c 20
```

### **Сборка Docker образа**
```bash
# Собрать с подробным выводом
docker buildx build --platform linux/amd64 -t gcr.io/talkhint/btibot . --progress=plain

# Проверить образ
docker images | grep btibot
```

### **Отправка в реестр**
```bash
# Отправить образ
docker push gcr.io/talkhint/btibot

# Проверить в реестре
gcloud container images list --repository=gcr.io/talkhint
```

### **Развертывание на Cloud Run**
```bash
# Развернуть с подробным выводом
gcloud run deploy btibot-restore \
  --image gcr.io/talkhint/btibot \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest" \
  --verbose

# Проверить статус
gcloud run services describe btibot-restore --region=europe-west1
```

### **Настройка webhook**
```bash
# Получить URL сервиса
SERVICE_URL=$(gcloud run services describe btibot-restore --region=europe-west1 --format="value(status.url)")
echo "Service URL: $SERVICE_URL"

# Проверить текущий webhook
curl -X GET "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/getWebhookInfo"

# Установить webhook
curl -X POST "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/setWebhook?url=$SERVICE_URL/"

# Проверить установку
curl -X GET "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/getWebhookInfo"
```

### **Тестирование функциональности**
```bash
# Health check
curl -s "$SERVICE_URL/health"

# Тестовый запрос к боту
curl -X POST "$SERVICE_URL/" \
  -H "Content-Type: application/json" \
  -d '{"message":{"chat":{"id":123},"text":"/start"}}'

# Проверить логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore" --limit=10 --format="value(timestamp,severity,textPayload)"
```

---

## 🚨 **Устранение неполадок**

### **Проблема: Docker сборка не удается**
```bash
# Очистить кэш Docker
docker system prune -a

# Пересобрать без кэша
docker buildx build --no-cache --platform linux/amd64 -t gcr.io/talkhint/btibot .
```

### **Проблема: Ошибки импорта в логах**
```bash
# Проверить содержимое app.py
cat app.py

# Должно содержать: import main
# Не должно содержать: import index
```

### **Проблема: Service Unavailable**
```bash
# Проверить логи ошибок
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND severity>=ERROR" --limit=5

# Проверить инициализацию
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND textPayload:\"Инициализация\"" --limit=3
```

### **Проблема: Webhook не работает**
```bash
# Проверить URL сервиса
SERVICE_URL=$(gcloud run services describe btibot-restore --region=europe-west1 --format="value(status.url)")
echo "URL: $SERVICE_URL"

# Проверить доступность
curl -s "$SERVICE_URL/health"

# Переустановить webhook
curl -X POST "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/setWebhook?url=$SERVICE_URL/"
```

### **Проблема: Бот не отвечает**
```bash
# Проверить логи бота
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND textPayload:\"Update processed\"" --limit=5

# Проверить webhook
curl -X GET "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/getWebhookInfo"
```

---

## 📊 **Мониторинг и проверка**

### **Проверка статуса сервиса**
```bash
# Общий статус
gcloud run services list --filter="metadata.name=btibot-restore"

# Детальная информация
gcloud run services describe btibot-restore --region=europe-west1
```

### **Проверка логов**
```bash
# Последние логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore" --limit=10

# Только ошибки
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND severity>=ERROR" --limit=5

# Логи инициализации
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND textPayload:\"Инициализация\"" --limit=3
```

### **Проверка производительности**
```bash
# Время ответа health check
time curl -s "$SERVICE_URL/health"

# Несколько запросов подряд
for i in {1..5}; do
  echo "Request $i:"
  curl -s "$SERVICE_URL/health"
  sleep 1
done
```

---

## ✅ **Критерии успешного развертывания**

1. **✅ Docker образ собран** без ошибок
2. **✅ Образ загружен** в gcr.io/talkhint/btibot
3. **✅ Cloud Run сервис** развернут успешно
4. **✅ Health check** возвращает {"status":"ok"}
5. **✅ Webhook настроен** и работает
6. **✅ Бот отвечает** в Telegram
7. **✅ Логи чистые** без критических ошибок
8. **✅ Все функции** работают корректно

**Готово! BTI Bot успешно развернут! 🎉**
