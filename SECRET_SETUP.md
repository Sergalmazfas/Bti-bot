# 🔐 Настройка Secret Manager для BTI-PRICE Bot

## 📋 Что такое Secret Manager?

Google Secret Manager - это сервис для безопасного хранения API ключей, паролей и других конфиденциальных данных. Это **рекомендуемый способ** для продакшена вместо передачи секретов через переменные окружения.

## 🎯 Быстрая настройка секрета "BOT-BTI-PRICE"

### Шаг 1: Включить Secret Manager API
```bash
gcloud services enable secretmanager.googleapis.com
```

### Шаг 2: Создать секрет с данными бота

#### Вариант A: Создать JSON файл с данными
```bash
# Создайте файл bot-secrets.json
cat > bot-secrets.json << 'EOF'
{
  "BOT_TOKEN": "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o",
  "OPENAI_API_KEY": "your-openai-api-key-here",
  "REESTR_API_TOKEN": "your-reestr-api-token-here",
  "SERPRIVER_API_KEY": "S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
}
EOF

# Создать секрет из файла
gcloud secrets create BOT-BTI-PRICE --data-file=bot-secrets.json

# Удалить временный файл (безопасность!)
rm bot-secrets.json
```

#### Вариант B: Создать секрет напрямую
```bash
# Отредактируйте значения ниже и выполните:
gcloud secrets create BOT-BTI-PRICE --data-file=- << 'EOF'
{
  "BOT_TOKEN": "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o",
  "OPENAI_API_KEY": "sk-ваш-openai-ключ",
  "REESTR_API_TOKEN": "ваш-reestr-токен",
  "SERPRIVER_API_KEY": "S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
}
EOF
```

### Шаг 3: Проверить секрет
```bash
# Посмотреть список секретов
gcloud secrets list

# Посмотреть версии секрета
gcloud secrets versions list BOT-BTI-PRICE

# Прочитать секрет (для проверки)
gcloud secrets versions access latest --secret="BOT-BTI-PRICE"
```

### Шаг 4: Дать права Cloud Run на доступ к секрету
```bash
# Получить service account Cloud Run
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Дать права на чтение секрета
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

## 🚀 Деплой с использованием секрета

### Автоматический деплой
```bash
cd /Users/seregaboss/Bti-bot-1

# Установите только PROJECT_ID
export PROJECT_ID="your-project-id"

# Запустите специальный скрипт для деплоя с секретами
./deploy-with-secrets.sh
```

### Ручной деплой
```bash
# Сборка и push образа
docker buildx build --platform linux/amd64 -t gcr.io/$PROJECT_ID/bti-price-bot .
docker push gcr.io/$PROJECT_ID/bti-price-bot

# Деплой на Cloud Run с монтированием секрета
gcloud run deploy bti-price-bot \
  --image gcr.io/$PROJECT_ID/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-secrets="/secrets/bot-config=BOT-BTI-PRICE:latest"
```

**Важно!** В этом случае секрет монтируется как файл `/secrets/bot-config`. Нужно обновить код для чтения из файла.

### Альтернатива: Секреты как переменные окружения
```bash
# Если вы храните каждый ключ отдельно
gcloud run deploy bti-price-bot \
  --image gcr.io/$PROJECT_ID/bti-price-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 300 \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest" \
  --set-env-vars="SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
```

## 🔄 Обновление секрета

Если нужно обновить API ключи:

```bash
# Создать новую версию секрета
cat > bot-secrets-new.json << 'EOF'
{
  "BOT_TOKEN": "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o",
  "OPENAI_API_KEY": "новый-openai-ключ",
  "REESTR_API_TOKEN": "новый-reestr-токен",
  "SERPRIVER_API_KEY": "S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
}
EOF

# Добавить новую версию
gcloud secrets versions add BOT-BTI-PRICE --data-file=bot-secrets-new.json

# Удалить временный файл
rm bot-secrets-new.json

# Cloud Run автоматически подхватит новую версию при следующем деплое
```

## 📊 Рекомендуемая структура секретов

### Вариант 1: Один секрет для всего (текущий)
```
BOT-BTI-PRICE → JSON с всеми ключами
```
**Плюсы**: Просто управлять  
**Минусы**: При изменении одного ключа нужно обновлять всё

### Вариант 2: Раздельные секреты (рекомендуется)
```
BOT_TOKEN → 8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o
OPENAI_API_KEY → sk-...
REESTR_API_TOKEN → token...
```
**Плюсы**: Гибкость, изолированное обновление  
**Минусы**: Больше секретов для управления

### Создание раздельных секретов:
```bash
# Создать отдельный секрет для каждого ключа
echo -n "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o" | gcloud secrets create BOT_TOKEN --data-file=-
echo -n "your-openai-key" | gcloud secrets create OPENAI_API_KEY --data-file=-
echo -n "your-reestr-token" | gcloud secrets create REESTR_API_TOKEN --data-file=-

# Деплой с раздельными секретами
gcloud run deploy bti-price-bot \
  --image gcr.io/$PROJECT_ID/bti-price-bot \
  --region us-central1 \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest" \
  --set-env-vars="SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z"
```

## 🛡️ Безопасность

### Управление доступом
```bash
# Посмотреть, кто имеет доступ к секрету
gcloud secrets get-iam-policy BOT-BTI-PRICE

# Удалить доступ (если нужно)
gcloud secrets remove-iam-policy-binding BOT-BTI-PRICE \
  --member="serviceAccount:some-account@project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Аудит
```bash
# Посмотреть историю изменений секрета
gcloud secrets versions list BOT-BTI-PRICE

# Посмотреть логи доступа
gcloud logging read "protoPayload.resourceName=~\"secrets/BOT-BTI-PRICE\"" --limit=50
```

## ✅ Проверка настройки

```bash
# 1. Секрет существует
gcloud secrets describe BOT-BTI-PRICE

# 2. Есть актуальная версия
gcloud secrets versions access latest --secret="BOT-BTI-PRICE"

# 3. Cloud Run имеет доступ
gcloud secrets get-iam-policy BOT-BTI-PRICE | grep compute@developer

# 4. Деплой с секретом работает
gcloud run services describe bti-price-bot --region=us-central1 | grep -A5 secrets
```

## 💰 Стоимость Secret Manager

- **Бесплатно**: До 6 активных версий секрета
- **$0.06** за активную версию секрета в месяц (от 7-й версии)
- **$0.03** за 10,000 операций доступа

Для нашего бота: **~$0-1/месяц**

## 📝 Рекомендации

1. ✅ **Используйте Secret Manager** для всех чувствительных данных
2. ✅ **Не коммитьте** секреты в Git
3. ✅ **Регулярно ротируйте** API ключи (каждые 90 дней)
4. ✅ **Используйте разные ключи** для dev/staging/production
5. ✅ **Настройте алерты** на доступ к секретам

---

**Готово!** Теперь ваши секреты хранятся безопасно в Google Secret Manager 🔐

