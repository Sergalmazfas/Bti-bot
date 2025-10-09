# ✅ BTI-PRICE: Чек-лист деплоя на Google Cloud Run

## 📋 Перед началом (Предварительная подготовка)

### 1. Установка инструментов
- [ ] **Google Cloud SDK** установлен
  ```bash
  gcloud --version
  ```
  Если нет → https://cloud.google.com/sdk/docs/install

- [ ] **Docker** установлен
  ```bash
  docker --version
  ```
  Если нет → https://docs.docker.com/get-docker/

- [ ] **Docker Buildx** доступен
  ```bash
  docker buildx version
  ```

### 2. Авторизация в Google Cloud
- [ ] Выполнен вход в Google Cloud
  ```bash
  gcloud auth login
  ```

- [ ] Настроен Docker для GCR
  ```bash
  gcloud auth configure-docker
  ```

### 3. Создание/Выбор проекта
- [ ] Проект создан или выбран
  ```bash
  # Посмотреть список проектов
  gcloud projects list
  
  # Создать новый проект (если нужно)
  gcloud projects create bti-price-bot-prod --name="BTI Price Bot Production"
  
  # Выбрать проект
  gcloud config set project YOUR_PROJECT_ID
  ```

### 4. Включение необходимых API
- [ ] Cloud Run API включен
  ```bash
  gcloud services enable run.googleapis.com
  ```

- [ ] Container Registry API включен
  ```bash
  gcloud services enable containerregistry.googleapis.com
  ```

## 🔑 Получение API ключей

### OpenAI API Key
- [ ] Создан аккаунт на https://platform.openai.com
- [ ] Создан API ключ на https://platform.openai.com/api-keys
- [ ] API ключ сохранен в безопасном месте
- [ ] Проверен лимит API (платный аккаунт рекомендуется)

### Reestr API Token
- [ ] Получен токен доступа к API Росреестра
- [ ] Токен валиден и активен

## 📦 Проверка файлов проекта

- [ ] `Dockerfile` присутствует и корректен
  ```bash
  cat Dockerfile
  ```

- [ ] `requirements.txt` содержит все зависимости
  ```bash
  cat requirements.txt
  ```

- [ ] `main.py` - основная логика бота
  ```bash
  ls -la main.py
  ```

- [ ] `app.py` - Flask webhook handler
  ```bash
  ls -la app.py
  ```

## 🚀 Деплой

### Вариант A: Автоматический деплой (рекомендуется)

- [ ] Переменные окружения установлены
  ```bash
  export PROJECT_ID="your-project-id"
  export OPENAI_API_KEY="your-openai-key"
  export REESTR_API_TOKEN="your-reestr-token"
  ```

- [ ] Скрипт деплоя исполняемый
  ```bash
  chmod +x deploy.sh
  ```

- [ ] Запущен деплой
  ```bash
  ./deploy.sh
  ```

### Вариант B: Ручной деплой

#### Шаг 1: Сборка образа
- [ ] Docker образ собран
  ```bash
  docker buildx build --platform linux/amd64 \
    -t gcr.io/YOUR_PROJECT_ID/bti-price-bot .
  ```

#### Шаг 2: Отправка в GCR
- [ ] Образ отправлен в Container Registry
  ```bash
  docker push gcr.io/YOUR_PROJECT_ID/bti-price-bot
  ```

#### Шаг 3: Деплой на Cloud Run
- [ ] Сервис развернут на Cloud Run
  ```bash
  gcloud run deploy bti-price-bot \
    --image gcr.io/YOUR_PROJECT_ID/bti-price-bot \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars="BOT_TOKEN=8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o,SERPRIVER_API_KEY=S4CV0-4XX9A-8WVE2-XD7E9-X704Z,OPENAI_API_KEY=YOUR_KEY,REESTR_API_TOKEN=YOUR_TOKEN"
  ```

#### Шаг 4: Настройка Webhook
- [ ] Получен URL сервиса
  ```bash
  SERVICE_URL=$(gcloud run services describe bti-price-bot \
    --region=us-central1 \
    --format="value(status.url)")
  echo "Service URL: $SERVICE_URL"
  ```

- [ ] Webhook установлен для Telegram
  ```bash
  curl -X POST "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/setWebhook?url=$SERVICE_URL/"
  ```

## ✅ Проверка работоспособности

### 1. Health Check
- [ ] Сервис отвечает на health endpoint
  ```bash
  curl -s $SERVICE_URL/health
  # Ожидается: {"status":"ok"}
  ```

### 2. Webhook Info
- [ ] Webhook настроен корректно
  ```bash
  curl -s "https://api.telegram.org/bot8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o/getWebhookInfo"
  ```
  
  **Проверьте:**
  - `url` содержит ваш SERVICE_URL
  - `has_custom_certificate` = false
  - `pending_update_count` = 0
  - Нет ошибок в `last_error_message`

### 3. Проверка логов
- [ ] Логи без критических ошибок
  ```bash
  gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot" \
    --limit=20
  ```

- [ ] Логи показывают успешное подключение к MongoDB (если используется)
  ```bash
  gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot AND textPayload:\"Connected\"" \
    --limit=5
  ```

### 4. Тестирование бота в Telegram

- [ ] Бот найден в Telegram (по username или через BotFather)

- [ ] Команда `/start` работает
  - Бот отвечает приветственным сообщением

- [ ] Отправка кадастрового номера работает
  - Тестовый номер: `77:01:0001001:1001`
  - Бот возвращает информацию о объекте
  - Отображаются 3 ценовые карточки (БТИ, Конкуренты, Рекомендуемая)

- [ ] Генерация коммерческого предложения работает
  - Нажата кнопка "📝 Коммерческое предложение"
  - GPT сгенерировал текст (5-10 секунд ожидания)
  - Текст корректный и релевантный

- [ ] Кнопка "📞 Связаться с менеджером" работает

## 📊 Мониторинг

### Cloud Run Metrics
- [ ] Открыта страница метрик
  ```
  https://console.cloud.google.com/run/detail/us-central1/bti-price-bot
  ```

- [ ] Проверены метрики:
  - Request count (количество запросов)
  - Request latency (задержка ответа)
  - Memory utilization (использование памяти)
  - CPU utilization (использование CPU)
  - Error count (количество ошибок)

### Логи в реальном времени
- [ ] Настроен просмотр логов в реальном времени
  ```bash
  gcloud logging tail \
    "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot"
  ```

## 🔒 Безопасность

- [ ] API ключи НЕ закоммичены в Git
- [ ] Используются переменные окружения для секретов
- [ ] (Опционально) Созданы Secret Manager секреты в GCP
  ```bash
  echo -n "your-key" | gcloud secrets create OPENAI_API_KEY --data-file=-
  ```

## 💰 Оптимизация затрат

- [ ] Настроено автомасштабирование
  ```bash
  gcloud run services update bti-price-bot \
    --region=us-central1 \
    --min-instances=0 \
    --max-instances=10
  ```

- [ ] Установлен лимит на одновременные запросы
  ```bash
  gcloud run services update bti-price-bot \
    --region=us-central1 \
    --concurrency=80
  ```

- [ ] Настроены алерты на превышение бюджета (опционально)

## 📝 Документация

- [ ] URL сервиса сохранен
- [ ] Переменные окружения задокументированы
- [ ] Процесс деплоя задокументирован (этот чек-лист!)

## 🎯 Финальная проверка

- [ ] ✅ Сервис работает 24/7
- [ ] ✅ Бот отвечает на команды
- [ ] ✅ GPT генерирует предложения
- [ ] ✅ Логи чистые, без ошибок
- [ ] ✅ Webhook настроен корректно
- [ ] ✅ Health check проходит
- [ ] ✅ Метрики в норме

## 📞 Контакты для поддержки

- **Google Cloud Support**: https://cloud.google.com/support
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **OpenAI Support**: https://help.openai.com

## 🎉 Поздравляем!

Если все пункты отмечены ✅, ваш BTI-PRICE бот успешно развернут на Google Cloud Run!

**Service URL**: `https://bti-price-bot-XXXXXXXXXX-uc.a.run.app`
**Мониторинг**: https://console.cloud.google.com/run
**Логи**: https://console.cloud.google.com/logs

---

**Дата деплоя**: _____________
**Версия**: 1.0.0
**Деплоил**: _____________

