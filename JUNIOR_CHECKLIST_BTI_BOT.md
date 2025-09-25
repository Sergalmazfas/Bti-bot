# 🔹 Чек-лист для джуна: BTI Bot - Полное восстановление и развертывание

## 🎯 **Задача**
Восстановить рабочую версию BTI Bot на Google Cloud Run с полной функциональностью.

## 📋 **Что сдаём на выходе**
- ✅ Бот отвечает в Telegram
- ✅ Логи чистые без ошибок
- ✅ Webhook настроен и работает
- ✅ Все функции бота работают
- ✅ Деплой на Cloud Run успешен

---

## 🏗️ **Архитектура проекта BTI Bot**

### **Основные компоненты:**
- **main.py** (974 строки) - Основная логика бота
- **app.py** - Flask приложение для Cloud Run
- **EnhancedDatabase** - SQLite база данных
- **Telegram Bot API** - Обработка сообщений
- **SERP API** - Поиск конкурентов
- **OpenAI GPT** - Генерация коммерческих предложений

### **Функциональность:**
1. **Расчет БТИ** - По кадастровому номеру и адресу
2. **Поиск конкурентов** - Через SERP API
3. **Расчет цен** - 3 типа цен (техпаспорт, замеры, техзадание)
4. **GPT интеграция** - Коммерческие предложения
5. **База данных** - Сохранение результатов

---

## 📝 **Детальный чек-лист для джуна**

### **A. Подготовка окружения**

#### **A1. Клонирование репозитория**
```bash
# Создать папку для проекта
mkdir bti-bot-restore
cd bti-bot-restore

# Клонировать репозиторий
git clone https://github.com/Sergalmazfas/Bti-bot.git
cd Bti-bot

# Проверить структуру
ls -la
```

**✅ Критерий успеха:** Видишь файлы main.py, app.py, requirements.txt, Dockerfile

#### **A2. Создание ветки для работы**
```bash
# Создать ветку
git checkout -b feature/restore-bot-<твои_инициалы>

# Проверить статус
git status
```

**✅ Критерий успеха:** Находишься в новой ветке

#### **A3. Настройка Google Cloud**
```bash
# Авторизация
gcloud auth login
gcloud config set project talkhint

# Проверить проект
gcloud config get-value project
```

**✅ Критерий успеха:** Проект = talkhint

---

### **B. Проверка и исправление кода**

#### **B1. Анализ основных файлов**
```bash
# Проверить main.py
head -20 main.py

# Проверить app.py
cat app.py

# Проверить requirements.txt
cat requirements.txt
```

**✅ Критерий успеха:** Все файлы читаются без ошибок

#### **B2. Исправление критических ошибок**
```bash
# Проверить импорты в main.py
grep -n "import" main.py | head -10

# Проверить функции
grep -n "def " main.py | head -10

# Проверить обработчики
grep -n "add_handler" main.py
```

**✅ Критерий успеха:** Нет ошибок импорта, все функции определены

#### **B3. Тестирование локально**
```bash
# Установить зависимости
pip install -r requirements.txt

# Проверить синтаксис
python -m py_compile main.py
python -m py_compile app.py
```

**✅ Критерий успеха:** Нет синтаксических ошибок

---

### **C. Настройка переменных окружения**

#### **C1. Проверка секретов в Google Cloud**
```bash
# Проверить секреты
gcloud secrets list

# Должны быть:
# - BOT_TOKEN
# - OPENAI_API_KEY  
# - REESTR_API_TOKEN
# - SERPRIVER_API_KEY
```

**✅ Критерий успеха:** Все 4 секрета существуют

#### **C2. Проверка значений секретов**
```bash
# Проверить BOT_TOKEN (должен начинаться с цифр)
gcloud secrets versions access latest --secret="BOT_TOKEN" | head -c 20

# Проверить OPENAI_API_KEY (должен начинаться с sk-)
gcloud secrets versions access latest --secret="OPENAI_API_KEY" | head -c 20
```

**✅ Критерий успеха:** Секреты содержат корректные значения

---

### **D. Сборка и деплой**

#### **D1. Сборка Docker образа**
```bash
# Собрать образ
docker buildx build --platform linux/amd64 -t gcr.io/talkhint/btibot .

# Проверить сборку
echo "Сборка завершена успешно"
```

**✅ Критерий успеха:** Образ собран без ошибок

#### **D2. Отправка в реестр**
```bash
# Отправить в GCR
docker push gcr.io/talkhint/btibot

# Проверить отправку
echo "Образ отправлен в реестр"
```

**✅ Критерий успеха:** Образ загружен в gcr.io/talkhint/btibot

#### **D3. Развертывание на Cloud Run**
```bash
# Развернуть сервис
gcloud run deploy btibot-restore \
  --image gcr.io/talkhint/btibot \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest"

# Получить URL
SERVICE_URL=$(gcloud run services describe btibot-restore --region=europe-west1 --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
```

**✅ Критерий успеха:** Деплой завершен, получен URL сервиса

---

### **E. Настройка webhook**

#### **E1. Получение URL сервиса**
```bash
# Получить URL
SERVICE_URL=$(gcloud run services describe btibot-restore --region=europe-west1 --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
```

**✅ Критерий успеха:** Получен URL вида https://btibot-restore-xxx.run.app

#### **E2. Проверка текущего webhook**
```bash
# Проверить webhook
curl -X GET "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/getWebhookInfo"
```

**✅ Критерий успеха:** Получен JSON с информацией о webhook

#### **E3. Установка webhook**
```bash
# Установить webhook
curl -X POST "https://api.telegram.org/bot$(gcloud secrets versions access latest --secret="BOT_TOKEN")/setWebhook?url=$SERVICE_URL/"
```

**✅ Критерий успеха:** Получен ответ {"ok":true,"result":true}

---

### **F. Тестирование функциональности**

#### **F1. Health Check**
```bash
# Проверить health check
curl -s "$SERVICE_URL/health"
```

**✅ Критерий успеха:** Получен ответ {"status":"ok"}

#### **F2. Тест бота в Telegram**
1. Найти бота в Telegram по токену
2. Отправить команду `/start`
3. Проверить ответ бота

**✅ Критерий успеха:** Бот отвечает на команду /start

#### **F3. Тест расчета БТИ**
1. Отправить кадастровый номер (например: 77:01:0001001:1001)
2. Проверить обработку
3. Проверить расчет цен

**✅ Критерий успеха:** Бот обрабатывает кадастровый номер и показывает расчет

---

### **G. Проверка логов**

#### **G1. Общие логи**
```bash
# Посмотреть последние логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore" --limit=10 --format="value(timestamp,severity,textPayload)"
```

**✅ Критерий успеха:** Логи показывают успешные операции

#### **G2. Проверка ошибок**
```bash
# Проверить ошибки
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND severity>=ERROR" --limit=5 --format="value(timestamp,textPayload)"
```

**✅ Критерий успеха:** Нет критических ошибок или ошибки исправлены

#### **G3. Проверка инициализации**
```bash
# Проверить инициализацию бота
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot-restore AND textPayload:\"Инициализация\"" --limit=3
```

**✅ Критерий успеха:** Видны логи инициализации бота

---

### **H. Финальная проверка**

#### **H1. Полный функциональный тест**
1. **Команда /start** - приветствие и меню
2. **Ввод кадастрового номера** - обработка и расчет
3. **Ввод адреса** - альтернативный поиск
4. **Расчет цен** - все 3 типа цен
5. **Сохранение в БД** - проверка записи

**✅ Критерий успеха:** Все функции работают корректно

#### **H2. Проверка производительности**
```bash
# Измерить время ответа
time curl -s "$SERVICE_URL/health"
```

**✅ Критерий успеха:** Время ответа < 5 секунд

#### **H3. Проверка стабильности**
```bash
# Несколько запросов подряд
for i in {1..5}; do
  curl -s "$SERVICE_URL/health"
  sleep 1
done
```

**✅ Критерий успеха:** Все запросы успешны

---

## 📊 **Отчёт для сдачи**

### **Обязательные скриншоты:**

1. **GitHub коммит/ветка**
   - Скрин истории коммитов
   - Скрин текущей ветки

2. **Google Cloud - секреты**
   - Скрин списка секретов
   - Скрин значений секретов (маскированные)

3. **Docker сборка**
   - Скрин успешной сборки
   - Скрин отправки в реестр

4. **Cloud Run деплой**
   - Скрин успешного деплоя
   - Скрин статуса сервиса

5. **Webhook настройка**
   - Скрин getWebhookInfo
   - Скрин setWebhook

6. **Тест бота**
   - Скрин ответа бота в Telegram
   - Скрин команды /start
   - Скрин обработки кадастрового номера

7. **Логи**
   - Скрин логов без ошибок
   - Скрин health check

### **Дополнительные артефакты:**

8. **Структура проекта**
   - Скрин файлов проекта
   - Скрин содержимого main.py (первые 20 строк)

9. **Переменные окружения**
   - Скрин настроек Cloud Run
   - Скрин секретов в интерфейсе

10. **Мониторинг**
    - Скрин метрик Cloud Run
    - Скрин логов в реальном времени

---

## �� **Частые проблемы и решения**

### **Проблема: "ModuleNotFoundError"**
**Решение:** Проверить импорты в main.py и app.py

### **Проблема: "Service Unavailable"**
**Решение:** Проверить логи на ошибки инициализации

### **Проблема: Webhook не работает**
**Решение:** Проверить URL сервиса и токен бота

### **Проблема: Бот не отвечает**
**Решение:** Проверить логи и webhook настройки

### **Проблема: Ошибки расчета**
**Решение:** Проверить API ключи и доступность внешних сервисов

---

## 🎯 **Критерии успеха**

- ✅ Бот отвечает на команду /start
- ✅ Обрабатывает кадастровые номера
- ✅ Рассчитывает все 3 типа цен
- ✅ Сохраняет данные в БД
- ✅ Логи показывают успешные операции
- ✅ Health check возвращает {"status":"ok"}
- ✅ Webhook настроен правильно
- ✅ Нет критических ошибок

**Готово! BTI Bot полностью восстановлен и работает! 🎉**
