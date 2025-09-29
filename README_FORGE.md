# Forge 3D → 2D Automation Service

Сервис для автоматической конвертации IFC файлов в DWG/PDF через Autodesk Forge API и сохранения результатов в Google Cloud Storage.

## 🎯 Функциональность

- **POST /upload** - загрузка IFC файлов через multipart/form-data
- **Автоматическая конвертация** IFC → DWG через Forge Model Derivative API
- **Сохранение в GCS** в папку `gs://btibot-processed/processed/<дата>/<имя_файла>.dwg`
- **Валидация файлов** - только .ifc формат, максимум 100MB
- **Логирование ошибок** в Cloud Run

## 🛠 Настройка

### 1. Секреты в Google Secret Manager

Создайте секреты для Forge API:

```bash
# Forge Client ID
gcloud secrets create ForgeClientID --data-file=- <<< "your_forge_client_id"

# Forge Client Secret  
gcloud secrets create ForgeClientSecret --data-file=- <<< "your_forge_client_secret"
```

### 2. Google Cloud Storage Bucket

Создайте bucket для сохранения результатов:

```bash
gsutil mb gs://btibot-processed
```

### 3. IAM Permissions

Настройте права доступа для Cloud Run:

```bash
# Service Account для Cloud Run
gcloud iam service-accounts create forge-service-account

# Права на Secret Manager
gcloud projects add-iam-policy-binding swiftchair \
  --member="serviceAccount:forge-service-account@swiftchair.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Права на Cloud Storage
gcloud projects add-iam-policy-binding swiftchair \
  --member="serviceAccount:forge-service-account@swiftchair.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## 🚀 Деплой

```bash
# Сборка и деплой
./deploy_forge.sh
```

## 📡 API Endpoints

### POST /upload
Загружает IFC файл и конвертирует в DWG.

**Request:**
```bash
curl -X POST \
  -F "file=@example.ifc" \
  https://forge-3d-to-2d-swiftchair.us-central1.run.app/upload
```

**Response:**
```json
{
  "success": true,
  "message": "File processed successfully",
  "gcs_url": "gs://btibot-processed/processed/2024-01-15/converted_1705123456.dwg",
  "file_info": {
    "original_filename": "example.ifc",
    "file_size": 1024000,
    "format": "IFC → DWG"
  }
}
```

### GET /health
Проверка состояния сервиса.

### GET /status
Информация о сервисе и поддерживаемых форматах.

## 🔧 Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export GOOGLE_CLOUD_PROJECT=swiftchair
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Запуск
python forge_app.py
```

## 📊 Мониторинг

- **Cloud Run Logs:** https://console.cloud.google.com/run/detail/us-central1/forge-3d-to-2d/logs
- **Cloud Storage:** https://console.cloud.google.com/storage/browser/btibot-processed
- **Secret Manager:** https://console.cloud.google.com/security/secret-manager

## 🚨 Обработка ошибок

Сервис логирует все ошибки в Cloud Run:
- Ошибки загрузки в Forge
- Ошибки конвертации
- Ошибки сохранения в GCS
- Ошибки валидации файлов

## 📁 Структура проекта

```
├── forge_app.py          # Flask приложение с эндпоинтами
├── forge_service.py      # Сервис для работы с Forge API
├── requirements.txt      # Python зависимости
├── Dockerfile.forge      # Docker конфигурация
├── deploy_forge.sh       # Скрипт деплоя
└── README_FORGE.md       # Документация
```

## 🔄 Workflow

1. **Загрузка файла** → Валидация (.ifc, размер)
2. **Сохранение** → Временный файл на сервере
3. **Forge Upload** → Загрузка в Forge OSS
4. **Конвертация** → IFC → DWG через Model Derivative API
5. **Скачивание** → Получение результата из Forge
6. **GCS Upload** → Сохранение в `gs://btibot-processed/processed/<дата>/`
7. **Очистка** → Удаление временных файлов

## ⚡ Производительность

- **Timeout:** 15 минут на обработку
- **Memory:** 2GB RAM
- **CPU:** 2 vCPU
- **Max instances:** 10
- **File size limit:** 100MB

## 🔐 Безопасность

- Секреты хранятся в Google Secret Manager
- Временные файлы автоматически удаляются
- Валидация типов файлов
- Ограничение размера файлов
