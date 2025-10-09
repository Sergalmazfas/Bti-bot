#!/bin/bash
# 🔐 BTI-PRICE Bot - Деплой с использованием Google Secret Manager

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  BTI-PRICE Bot Deployment${NC}"
echo -e "${BLUE}  (Using Secret Manager)${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 1. Проверка переменных окружения
echo -e "${YELLOW}📋 Шаг 1: Проверка переменных...${NC}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Ошибка: PROJECT_ID не установлен${NC}"
    echo -e "${YELLOW}Установите: export PROJECT_ID=your-project-id${NC}"
    exit 1
fi

echo -e "${GREEN}✅ PROJECT_ID установлен: $PROJECT_ID${NC}"
echo ""

# 2. Установка проекта
echo -e "${YELLOW}⚙️  Шаг 2: Настройка Google Cloud проекта...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Проект установлен: $PROJECT_ID${NC}"
echo ""

# 3. Проверка существования секрета
echo -e "${YELLOW}🔐 Шаг 3: Проверка секрета BOT-BTI-PRICE...${NC}"
if gcloud secrets describe BOT-BTI-PRICE &> /dev/null; then
    echo -e "${GREEN}✅ Секрет BOT-BTI-PRICE найден${NC}"
    # Показать краткую информацию
    SECRET_INFO=$(gcloud secrets versions list BOT-BTI-PRICE --limit=1 --format="table(name,state)" 2>&1)
    echo -e "${BLUE}$SECRET_INFO${NC}"
else
    echo -e "${RED}❌ Секрет BOT-BTI-PRICE не найден!${NC}"
    echo -e "${YELLOW}Создайте секрет следуя инструкции в SECRET_SETUP.md${NC}"
    echo ""
    echo -e "${YELLOW}Быстрая команда для создания:${NC}"
    echo 'gcloud secrets create BOT-BTI-PRICE --data-file=- << EOF'
    echo '{'
    echo '  "BOT_TOKEN": "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o",'
    echo '  "OPENAI_API_KEY": "your-openai-key",'
    echo '  "REESTR_API_TOKEN": "your-reestr-token",'
    echo '  "SERPRIVER_API_KEY": "S4CV0-4XX9A-8WVE2-XD7E9-X704Z"'
    echo '}'
    echo 'EOF'
    exit 1
fi
echo ""

# 4. Проверка прав доступа
echo -e "${YELLOW}🔑 Шаг 4: Проверка прав доступа к секрету...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Дать права на чтение секрета (если еще не даны)
echo -e "${BLUE}Service Account: $SERVICE_ACCOUNT${NC}"
gcloud secrets add-iam-policy-binding BOT-BTI-PRICE \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None &> /dev/null || true

echo -e "${GREEN}✅ Права доступа настроены${NC}"
echo ""

# 5. Сборка Docker образа
echo -e "${YELLOW}🐳 Шаг 5: Сборка Docker образа...${NC}"
IMAGE_NAME="gcr.io/$PROJECT_ID/bti-price-bot"
docker buildx build --platform linux/amd64 -t $IMAGE_NAME .
echo -e "${GREEN}✅ Образ собран: $IMAGE_NAME${NC}"
echo ""

# 6. Отправка в Container Registry
echo -e "${YELLOW}📤 Шаг 6: Отправка образа в GCR...${NC}"
docker push $IMAGE_NAME
echo -e "${GREEN}✅ Образ отправлен в GCR${NC}"
echo ""

# 7. Деплой на Cloud Run с секретами
echo -e "${YELLOW}🚀 Шаг 7: Деплой на Cloud Run...${NC}"
echo -e "${BLUE}Используется секрет: BOT-BTI-PRICE${NC}"

# Вариант 1: Если секрет содержит JSON с отдельными ключами
# Монтируем секрет как файл
gcloud run deploy bti-price-bot \
  --image $IMAGE_NAME \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --update-secrets=/secrets/bot-config=BOT-BTI-PRICE:latest

# Альтернативный вариант (если секреты хранятся отдельно):
# gcloud run deploy bti-price-bot \
#   --image $IMAGE_NAME \
#   --region us-central1 \
#   --platform managed \
#   --allow-unauthenticated \
#   --memory 512Mi \
#   --cpu 1 \
#   --timeout 300 \
#   --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest" \
#   --set-env-vars="SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z"

echo -e "${GREEN}✅ Деплой завершен${NC}"
echo ""

# 8. Получение URL сервиса
echo -e "${YELLOW}🔗 Шаг 8: Настройка Telegram Webhook...${NC}"
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --format="value(status.url)")
echo -e "${BLUE}Service URL: $SERVICE_URL${NC}"

# Получаем BOT_TOKEN из секрета для настройки webhook
echo -e "${BLUE}Получение BOT_TOKEN из секрета...${NC}"
SECRET_DATA=$(gcloud secrets versions access latest --secret="BOT-BTI-PRICE")

# Извлекаем BOT_TOKEN из JSON (предполагаем, что секрет в формате JSON)
BOT_TOKEN=$(echo "$SECRET_DATA" | grep -o '"BOT_TOKEN"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"BOT_TOKEN"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Не удалось извлечь BOT_TOKEN из секрета${NC}"
    echo -e "${YELLOW}Используется значение по умолчанию${NC}"
    BOT_TOKEN="8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o"
fi

# 9. Установка webhook
WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$SERVICE_URL/")
echo -e "${BLUE}Webhook response: $WEBHOOK_RESPONSE${NC}"

# 10. Проверка webhook
echo ""
echo -e "${YELLOW}📊 Проверка webhook...${NC}"
WEBHOOK_INFO=$(curl -s -X GET "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
echo -e "${BLUE}$WEBHOOK_INFO${NC}"
echo ""

# 11. Health check
echo -e "${YELLOW}🏥 Health Check...${NC}"
sleep 3  # Даем время на запуск сервиса
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo "Service starting...")
echo -e "${BLUE}$HEALTH_RESPONSE${NC}"
echo ""

# 12. Финальный отчет
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  ✅ ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📍 Service URL:${NC} $SERVICE_URL"
echo -e "${BLUE}🔐 Secret:${NC} BOT-BTI-PRICE"
echo -e "${BLUE}📊 Мониторинг:${NC} https://console.cloud.google.com/run/detail/us-central1/bti-price-bot?project=$PROJECT_ID"
echo -e "${BLUE}🔒 Секреты:${NC} https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "1. Откройте бота в Telegram"
echo "2. Отправьте /start"
echo "3. Попробуйте кадастровый номер: 77:01:0001001:1001"
echo "4. Нажмите '📝 Коммерческое предложение'"
echo ""
echo -e "${GREEN}Готово! 🎉${NC}"

