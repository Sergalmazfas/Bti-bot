# 🏆 BTI-PRICE Bot - Платиновая рабочая версия

## 🎯 Статус: PRODUCTION READY ✅

Это **платиновая рабочая версия** BTI-PRICE бота с полной интеграцией Росреестра и генерацией коммерческих предложений через GPT.

**Деплой:** Google Cloud Run  
**Проект:** bti-price (637190449180)  
**Статус:** ✅ Работает стабильно

---

## 🚀 Ключевые возможности

### 1. 🔍 Интеграция с Росреестром
- Автоматический запрос данных по кадастровому номеру
- API: `reestr-api.ru`
- Извлечение: адрес, площадь, год постройки, материалы, тип помещения

### 2. 💰 Тройной расчет цен
- **Карточка 1 - БТИ**: Официальные тарифы по регионам
  - Москва (77): 50₽/м² обмеры, 250₽/м² техпаспорт
  - СПБ (78): 45₽/м², 220₽/м²
  - МО (50): 40₽/м², 200₽/м²
  
- **Карточка 2 - Рыночные цены**: Через SERP API (Avito, ЦИАН, Яндекс)
  
- **Карточка 3 - Рекомендация**: Баланс БТИ и рынка

### 3. 🤖 Генерация КП через GPT
- OpenAI GPT-3.5-turbo
- Персонализированные коммерческие предложения
- Профессиональный текст готовый для клиентов

---

## 📋 Архитектура

```
┌─────────────┐
│  Telegram   │
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   Google Cloud Run          │
│                             │
│  ┌──────────────────────┐   │
│  │   Flask App          │   │
│  │   (app.py)           │   │
│  └──────┬───────────────┘   │
│         │                   │
│  ┌──────▼───────────────┐   │
│  │   Main Bot Logic     │   │
│  │   (main.py)          │   │
│  │                      │   │
│  │  ┌─────────────────┐ │   │
│  │  │ Secret Manager  │ │   │
│  │  │ BOT-BTI-PRICE  │ │   │
│  │  └─────────────────┘ │   │
│  └──────┬───────────────┘   │
└─────────┼───────────────────┘
          │
    ┌─────┴──────┐
    │            │
    ▼            ▼
┌─────────┐  ┌─────────┐
│Росреестр│  │OpenAI   │
│  API    │  │GPT API  │
└─────────┘  └─────────┘
```

---

## 🔐 Конфигурация

### Google Secret Manager: `BOT-BTI-PRICE`

```json
{
  "BOT_TOKEN": "8433620621:AAG85NhZ-OPYn9v5NhNZneC3nmuQzuL0eKE",
  "OPENAI_API_KEY": "sk-proj-...",
  "REESTR_API_TOKEN": "189b2d78-...",
  "SERPRIVER_API_KEY": "Y9CN0-..."
}
```

**Монтируется как:** `/secrets/bot-config` (Volume mount в Cloud Run)

---

## 🛠️ Технический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| **Runtime** | Python | 3.12 |
| **Framework** | Flask | 3.0.0 |
| **Telegram** | python-telegram-bot | 20.7 |
| **AI** | OpenAI GPT | 3.5-turbo |
| **HTTP** | httpx | 0.25.2 |
| **Server** | Gunicorn | 23.0.0 |
| **Platform** | Google Cloud Run | - |

---

## 📦 Структура проекта

```
Bti-bot-1/
├── main.py                      # 🏆 Основная логика бота (492 строки)
├── app.py                       # Flask wrapper для Cloud Run
├── Dockerfile                   # Docker конфигурация
├── requirements.txt             # Python зависимости
│
├── deploy-bti-price.sh          # 🚀 Автоматический деплой
├── README.md                    # Эта документация
│
├── BTI_DEPLOY_GUIDE.md         # Полное руководство по деплою
├── DEPLOY_NOW.md               # Готовые команды
├── SECRET_SETUP.md             # Настройка Secret Manager
└── DEPLOY_CHECKLIST.md         # Чек-лист деплоя
```

---

## 🚀 Деплой

### Быстрый деплой (одна команда):

```bash
./deploy-bti-price.sh
```

### Ручной деплой:

```bash
# 1. Сборка через Cloud Build
gcloud builds submit --tag gcr.io/bti-price/bti-price-bot . --project=bti-price

# 2. Деплой на Cloud Run
gcloud run deploy bti-price-bot \
  --image gcr.io/bti-price/bti-price-bot:latest \
  --region us-central1 \
  --project=bti-price

# 3. Настройка webhook
curl -X POST "https://api.telegram.org/bot8433620621:AAG85NhZ-OPYn9v5NhNZneC3nmuQzuL0eKE/setWebhook?url=https://bti-price-bot-956046571821.us-central1.run.app/"
```

---

## 🔄 Workflow пользователя

### Шаг 1: Старт
```
Пользователь: /start
Бот: 🏠 Привет! Введите кадастровый номер (пример: 77:09:0001013:1087)
```

### Шаг 2: Ввод кадастрового номера
```
Пользователь: 77:01:0001001:1001
Бот: 🔎 Поиск в Росреестре…
```

### Шаг 3: Данные из Росреестра
```
✅ Получены данные:
📍 Адрес: г. Москва, ул. Ленина, д. 10
📐 Площадь: 85 м²
🏢 Тип: Жилое (Кирпич)
📅 Год: 1985
```

### Шаг 4: Карточка 1 - БТИ (официальные тарифы)
```
🏛️ Карточка 1 — БТИ (официальные тарифы)

💰 Тарифы региона 77:
• Обмеры: 50 ₽/м²
• Техпаспорт: 250 ₽/м²
• Техзадание: 250 ₽/м²

Суммы:
• Обмеры: 4,250 ₽
• Техпаспорт: 21,250 ₽
• Техзадание: 21,250 ₽
• Итого БТИ: 46,750 ₽

Источник: Росреестр (API), поиск 1.23 c, расчет 0.01 c
```

### Шаг 5: Карточка 2 - Рыночные цены
```
🏢 Карточка 2 — Рыночные цены

• Цена за м² (медиана): 850 ₽/м²
• С НДС и прибылью: 1,020 ₽/м²
• Итоговая оценка: 86,700 ₽

Источник: SERP (Avito, ЦИАН и др.), поиск 2.45 c
```

### Шаг 6: Карточка 3 - Рекомендация
```
⭐ Карточка 3 — Рекомендованная цена

• Итог: 66,725 ₽
• За м²: 785 ₽/м²

Обоснование: БТИ = официальные тарифы; Рынок = ориентиры конкурентов; 
Рекомендация = баланс двух источников.
```

### Шаг 7: Коммерческое предложение (GPT)
```
🤝 КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ

Уважаемый клиент!

Предлагаем профессиональные услуги БТИ для вашего объекта по адресу 
г. Москва, ул. Ленина, д. 10, общей площадью 85 м² (жилое помещение, 
кирпич, 1985 год постройки).

Наша рекомендованная стоимость составляет 66,725 рублей и включает 
полный комплекс работ: обмеры помещений (4,250 руб.), подготовку 
технического паспорта и технического задания (62,475 руб.).

Данная цена выгодно отличается от официальных тарифов БТИ (46,750 руб.) 
и предложений рыночных конкурентов (86,700 руб.), обеспечивая 
оптимальное соотношение цены и качества.

Гарантируем профессиональное выполнение всех работ в установленные сроки.

📞 Свяжитесь с нами для оформления заказа!

С уважением,
Архитектурное бюро ZamerPro
```

---

## 🎯 Ключевые функции

### `fetch_reestr_data(query, search_type="cadastral")`
Получает данные из Росреестра по кадастровому номеру или адресу.

**Возвращает:**
```python
{
    "address": "г. Москва, ул. Ленина, 10",
    "cadastral_number": "77:01:0001001:1001",
    "area": 85.0,
    "build_year": 1985,
    "materials": "Кирпич",
    "room_type": "Жилое"
}
```

### `calc_bti(area, region_code)`
Рассчитывает стоимость по официальным тарифам БТИ для региона.

### `search_competitor_prices(address, area)`
Ищет рыночные цены конкурентов через SERP API.

### `generate_commercial_proposal(...)`
Генерирует персонализированное коммерческое предложение через GPT.

---

## 📊 Мониторинг

### Cloud Run Console:
```
https://console.cloud.google.com/run/detail/us-central1/bti-price-bot?project=bti-price
```

### Логи в реальном времени:
```bash
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot" \
  --project=bti-price
```

### Метрики:
- Request count
- Request latency
- Memory utilization
- CPU utilization
- Error rate

---

## 🔄 Обновление

### Обновить код:
```bash
# После изменения main.py или app.py
./deploy-bti-price.sh
```

### Обновить секреты:
```bash
# Добавить новую версию секрета
gcloud secrets versions add BOT-BTI-PRICE \
  --project=bti-price \
  --data-file=- << 'EOF'
{
  "BOT_TOKEN": "8433620621:AAG85NhZ-OPYn9v5NhNZneC3nmuQzuL0eKE",
  "OPENAI_API_KEY": "новый-ключ",
  "REESTR_API_TOKEN": "новый-токен",
  "SERPRIVER_API_KEY": "новый-ключ"
}
EOF

# Обновить сервис
gcloud run services update bti-price-bot \
  --region us-central1 \
  --project=bti-price \
  --update-secrets=/secrets/bot-config=BOT-BTI-PRICE:latest
```

---

## 🧪 Тестирование

### Локально (с переменными окружения):
```bash
export BOT_TOKEN="8433620621:AAG85NhZ-OPYn9v5NhNZneC3nmuQzuL0eKE"
export OPENAI_API_KEY="your-key"
export REESTR_API_TOKEN="your-token"
export SERPRIVER_API_KEY="your-key"

python main.py
```

### В продакшене:
1. Откройте бота в Telegram
2. Отправьте `/start`
3. Введите кадастровый номер: `77:01:0001001:1001`
4. Проверьте все 3 карточки и КП

---

## 🔐 Безопасность

### Secret Manager
- Все ключи хранятся в Google Secret Manager
- Секрет: `BOT-BTI-PRICE` (текущая версия: 4)
- Монтируется как Volume: `/secrets/bot-config`
- Автоматический fallback на переменные окружения

### Service Account
- `bti-price-bot@bti-price.iam.gserviceaccount.com`
- Права: Secret Accessor, Cloud Run Admin

---

## 📈 Производительность

### Время отклика:
- Росреестр API: ~1-2 секунды
- SERP поиск: ~2-3 секунды
- GPT генерация: ~5-10 секунд
- **Общее время:** ~8-15 секунд на полный ответ

### Ресурсы:
- Memory: 512 MiB
- CPU: 1 vCPU
- Timeout: 300 seconds
- Concurrency: 80 requests

---

## 💰 Стоимость (оценка)

### Cloud Run:
- Бесплатно: первые 2 млн запросов/месяц
- Платно: ~$5-10/месяц при 100-1000 пользователей/день

### OpenAI API:
- GPT-3.5-turbo: ~$0.002 за запрос
- ~$10-50/месяц в зависимости от использования

### Росреестр API:
- По тарифам reestr-api.ru

**Итого:** ~$15-70/месяц

---

## 🆘 Устранение неполадок

### Бот не отвечает
```bash
# Проверить webhook
curl "https://api.telegram.org/bot8433620621:AAG85NhZ-OPYn9v5NhNZneC3nmuQzuL0eKE/getWebhookInfo"

# Переустановить webhook
curl -X POST "https://api.telegram.org/bot8433620621:AAG85NhZ-OPYn9v5NhNZneC3nmuQzuL0eKE/setWebhook?url=https://bti-price-bot-956046571821.us-central1.run.app/"
```

### Ошибки в логах
```bash
# Последние ошибки
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=bti-price-bot AND severity>=ERROR" \
  --project=bti-price \
  --limit=20
```

### Росреестр не отвечает
```bash
# Проверить токен
gcloud secrets versions access latest --secret="BOT-BTI-PRICE" --project=bti-price | grep REESTR
```

---

## 📝 История версий

### v1.0.0 - Платиновая версия (2025-10-09)
✅ Полная интеграция с Росреестром  
✅ Тройной расчет цен (БТИ + Рынок + Рекомендация)  
✅ Генерация КП через GPT  
✅ Google Secret Manager  
✅ Cloud Run деплой  
✅ Стабильно работает в продакшене  

**Деплой:**
- Проект: bti-price (637190449180)
- Ревизия: bti-price-bot-00013-sz8
- Service URL: https://bti-price-bot-956046571821.us-central1.run.app

---

## 🎓 Документация

| Файл | Описание |
|------|----------|
| `README.md` | Главная документация (этот файл) |
| `BTI_DEPLOY_GUIDE.md` | Полное руководство по деплою |
| `DEPLOY_NOW.md` | Готовые команды для деплоя |
| `SECRET_SETUP.md` | Настройка Secret Manager |
| `DEPLOY_CHECKLIST.md` | Чек-лист деплоя |
| `README_FINAL.md` | Финальная инструкция |

---

## 🔗 Полезные ссылки

- **Cloud Run Console**: https://console.cloud.google.com/run?project=bti-price
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager?project=bti-price
- **Логи**: https://console.cloud.google.com/logs?project=bti-price
- **GitHub**: https://github.com/Sergalmazfas/Bti-bot
- **OpenAI Platform**: https://platform.openai.com
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

## 📞 Поддержка

Для технической поддержки или вопросов:
- GitHub Issues: https://github.com/Sergalmazfas/Bti-bot/issues
- Email: sergalmazfas@gmail.com

---

## 🏆 Статус

**✅ Платиновая рабочая версия**  
**✅ Production Ready**  
**✅ Деплоена на Google Cloud Run**  
**✅ Стабильно работает**  

---

<div align="center">

### 🎉 BTI-PRICE Bot v1.0.0

**Автоматизация БТИ услуг с AI**

Made with ❤️ by Serg Almazfas

**2025**

</div>
