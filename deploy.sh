#!/bin/bash
# 🚀 BTI-PRICE Bot - Скрипт автоматического деплоя на Google Cloud Run

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  BTI-PRICE Bot Deployment${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 1. Проверка переменных окружения
echo -e "${YELLOW}📋 Шаг 1: Проверка переменных...${NC}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Ошибка: PROJECT_ID не установлен${NC}"
    echo -e "${YELLOW}Установите: export PROJECT_ID=your-project-id${NC}"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ Ошибка: OPENAI_API_KEY не установлен${NC}"
    echo -e "${YELLOW}Установите: export OPENAI_API_KEY=your-key${NC}"
    exit 1
fi

if [ -z "$REESTR_API_TOKEN" ]; then
    echo -e "${RED}❌ Ошибка: REESTR_API_TOKEN не установлен${NC}"
    echo -e "${YELLOW}Установите: export REESTR_API_TOKEN=your-token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все переменные установлены${NC}"
echo ""

# 2. Установка проекта
echo -e "${YELLOW}⚙️  Шаг 2: Настройка Google Cloud проекта...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Проект установлен: $PROJECT_ID${NC}"
echo ""

# 3. Сборка Docker образа
echo -e "${YELLOW}🐳 Шаг 3: Сборка Docker образа...${NC}"
IMAGE_NAME="gcr.io/$PROJECT_ID/bti-price-bot"
docker buildx build --platform linux/amd64 -t $IMAGE_NAME .
echo -e "${GREEN}✅ Образ собран: $IMAGE_NAME${NC}"
echo ""

# 4. Отправка в Container Registry
echo -e "${YELLOW}📤 Шаг 4: Отправка образа в GCR...${NC}"
docker push $IMAGE_NAME
echo -e "${GREEN}✅ Образ отправлен в GCR${NC}"
echo ""

# 5. Деплой на Cloud Run
echo -e "${YELLOW}🚀 Шаг 5: Деплой на Cloud Run...${NC}"
gcloud run deploy bti-price-bot \
  --image $IMAGE_NAME \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="BOT_TOKEN=8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o,SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z,OPENAI_API_KEY=$OPENAI_API_KEY,REESTR_API_TOKEN=$REESTR_API_TOKEN"

echo -e "${GREEN}✅ Деплой завершен${NC}"
echo ""

# 6. Получение URL сервиса
echo -e "${YELLOW}🔗 Шаг 6: Настройка Telegram Webhook...${NC}"
SERVICE_URL=$(gcloud run services describe bti-price-bot --region=us-central1 --format="value(status.url)")
echo -e "${BLUE}Service URL: $SERVICE_URL${NC}"

# 7. Установка webhook
BOT_TOKEN="8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o"
WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$SERVICE_URL/")
echo -e "${BLUE}Webhook response: $WEBHOOK_RESPONSE${NC}"

# 8. Проверка webhook
echo ""
echo -e "${YELLOW}📊 Проверка webhook...${NC}"
WEBHOOK_INFO=$(curl -s -X GET "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
echo -e "${BLUE}$WEBHOOK_INFO${NC}"
echo ""

# 9. Health check
echo -e "${YELLOW}🏥 Health Check...${NC}"
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health")
echo -e "${BLUE}$HEALTH_RESPONSE${NC}"
echo ""

# 10. Финальный отчет
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  ✅ ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📍 Service URL:${NC} $SERVICE_URL"
echo -e "${BLUE}🤖 Bot Token:${NC} $BOT_TOKEN"
echo -e "${BLUE}📊 Мониторинг:${NC} https://console.cloud.google.com/run/detail/us-central1/bti-price-bot?project=$PROJECT_ID"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "1. Откройте бота в Telegram"
echo "2. Отправьте /start"
echo "3. Попробуйте кадастровый номер: 77:01:0001001:1001"
echo ""
echo -e "${GREEN}Готово! 🎉${NC}"

