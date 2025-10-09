#!/bin/bash
# 🚀 BTI-PRICE Bot - Деплой на проект bti-price

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  BTI-PRICE Bot Deployment${NC}"
echo -e "${BLUE}  Project: bti-price (637190449180)${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# Установка проекта
PROJECT_ID="bti-price"
PROJECT_NUMBER="637190449180"
SERVICE_ACCOUNT="bti-price-bot@bti-price.iam.gserviceaccount.com"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
SECRET_NAME="BOT-BTI-PRICE"
SERVICE_NAME="bti-price-bot"
REGION="us-central1"

echo -e "${YELLOW}⚙️  Шаг 1: Настройка проекта...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Проект установлен: $PROJECT_ID${NC}"
echo ""

# Проверка существования секрета
echo -e "${YELLOW}🔐 Шаг 2: Проверка секрета $SECRET_NAME...${NC}"
if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}✅ Секрет $SECRET_NAME найден${NC}"
    
    # Показать версии
    LATEST_VERSION=$(gcloud secrets versions list $SECRET_NAME --project=$PROJECT_ID --limit=1 --format="value(name)")
    echo -e "${BLUE}Последняя версия: $LATEST_VERSION${NC}"
else
    echo -e "${RED}❌ Секрет $SECRET_NAME не найден!${NC}"
    echo -e "${YELLOW}Создайте секрет командой:${NC}"
    echo ""
    echo "gcloud secrets create $SECRET_NAME --project=$PROJECT_ID --data-file=- << 'EOF'"
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

# Настройка прав доступа
echo -e "${YELLOW}🔑 Шаг 3: Настройка прав доступа к секрету...${NC}"
echo -e "${BLUE}Service Account: $SERVICE_ACCOUNT${NC}"
echo -e "${BLUE}Compute SA: $COMPUTE_SA${NC}"

# Дать права custom service account
gcloud secrets add-iam-policy-binding $SECRET_NAME \
  --project=$PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None &> /dev/null || true

# Дать права compute service account
gcloud secrets add-iam-policy-binding $SECRET_NAME \
  --project=$PROJECT_ID \
  --member="serviceAccount:$COMPUTE_SA" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None &> /dev/null || true

echo -e "${GREEN}✅ Права доступа настроены${NC}"
echo ""

# Сборка Docker образа
echo -e "${YELLOW}🐳 Шаг 4: Сборка Docker образа...${NC}"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
echo -e "${BLUE}Image: $IMAGE_NAME${NC}"

docker buildx build --platform linux/amd64 -t $IMAGE_NAME .

echo -e "${GREEN}✅ Образ собран${NC}"
echo ""

# Отправка в Container Registry
echo -e "${YELLOW}📤 Шаг 5: Отправка образа в GCR...${NC}"
docker push $IMAGE_NAME
echo -e "${GREEN}✅ Образ отправлен в GCR${NC}"
echo ""

# Деплой на Cloud Run
echo -e "${YELLOW}🚀 Шаг 6: Деплой на Cloud Run...${NC}"
echo -e "${BLUE}Region: $REGION${NC}"
echo -e "${BLUE}Service: $SERVICE_NAME${NC}"
echo -e "${BLUE}Secret: $SECRET_NAME${NC}"

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --project=$PROJECT_ID \
  --service-account=$SERVICE_ACCOUNT \
  --update-secrets=/secrets/bot-config=$SECRET_NAME:latest

echo -e "${GREEN}✅ Деплой завершен${NC}"
echo ""

# Получение URL сервиса
echo -e "${YELLOW}🔗 Шаг 7: Настройка Telegram Webhook...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)")

echo -e "${BLUE}Service URL: $SERVICE_URL${NC}"

# Получаем BOT_TOKEN из секрета для настройки webhook
echo -e "${BLUE}Получение BOT_TOKEN из секрета...${NC}"
SECRET_DATA=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project=$PROJECT_ID)

# Извлекаем BOT_TOKEN из JSON
BOT_TOKEN=$(echo "$SECRET_DATA" | grep -o '"BOT_TOKEN"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"BOT_TOKEN"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Не удалось извлечь BOT_TOKEN из секрета${NC}"
    echo -e "${YELLOW}Используется значение по умолчанию${NC}"
    BOT_TOKEN="8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o"
fi

# Установка webhook
echo ""
echo -e "${YELLOW}📲 Установка webhook...${NC}"
WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$SERVICE_URL/")
echo -e "${BLUE}$WEBHOOK_RESPONSE${NC}"

# Проверка webhook
echo ""
echo -e "${YELLOW}📊 Проверка webhook...${NC}"
WEBHOOK_INFO=$(curl -s -X GET "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
echo -e "${BLUE}$WEBHOOK_INFO${NC}"
echo ""

# Health check
echo -e "${YELLOW}🏥 Health Check...${NC}"
sleep 3  # Даем время на запуск сервиса
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo '{"status":"starting"}')
echo -e "${BLUE}$HEALTH_RESPONSE${NC}"
echo ""

# Проверка логов
echo -e "${YELLOW}📋 Проверка логов (последние 5 строк)...${NC}"
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --project=$PROJECT_ID \
  --limit=5 \
  --format="table(timestamp,severity,textPayload)" 2>/dev/null || echo "Логи появятся через несколько секунд..."
echo ""

# Финальный отчет
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📍 Service URL:${NC} $SERVICE_URL"
echo -e "${BLUE}🔐 Secret:${NC} $SECRET_NAME"
echo -e "${BLUE}👤 Service Account:${NC} $SERVICE_ACCOUNT"
echo -e "${BLUE}🌍 Region:${NC} $REGION"
echo ""
echo -e "${BLUE}📊 Мониторинг:${NC}"
echo "  Cloud Run: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo "  Секреты: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo "  Логи: https://console.cloud.google.com/logs?project=$PROJECT_ID"
echo ""
echo -e "${YELLOW}🧪 Следующие шаги:${NC}"
echo "1. Откройте бота в Telegram"
echo "2. Отправьте /start"
echo "3. Попробуйте кадастровый номер: 77:01:0001001:1001"
echo "4. Нажмите '📝 Коммерческое предложение'"
echo ""
echo -e "${BLUE}📝 Полезные команды:${NC}"
echo "  # Логи в реальном времени:"
echo "  gcloud logging tail \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --project=$PROJECT_ID"
echo ""
echo "  # Статус сервиса:"
echo "  gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo ""
echo -e "${GREEN}Готово! 🎉${NC}"

