#!/usr/bin/env python3
"""
Полный тест конвертации 3D → 2D через Forge API
"""

import requests
import json
import time
import os

def test_forge_conversion():
    """Тестирует полный процесс конвертации IFC → DWG/PDF"""
    
    print("🧪 Полный тест конвертации 3D → 2D")
    print("=" * 50)
    
    # URL сервиса
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    # Проверяем, что тестовый файл существует
    test_file = "test_model.ifc"
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден!")
        print("Сначала создайте его с помощью create_test_ifc.py")
        return False
    
    print(f"📁 Тестовый файл: {test_file}")
    print(f"📏 Размер: {os.path.getsize(test_file)} байт")
    
    # Шаг 1: Health check
    print("\n1️⃣ Проверка сервиса...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Сервис работает")
            print(f"   📊 Ответ: {response.json()}")
        else:
            print(f"   ❌ Ошибка сервиса: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False
    
    # Шаг 2: Status check
    print("\n2️⃣ Проверка статуса...")
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("   ✅ Статус получен")
            print(f"   📊 Поддерживаемые форматы: {status.get('supported_formats', [])}")
            print(f"   📏 Максимальный размер: {status.get('max_file_size_mb', 0)} MB")
        else:
            print(f"   ❌ Ошибка статуса: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка получения статуса: {e}")
    
    # Шаг 3: Загрузка файла
    print("\n3️⃣ Загрузка IFC файла...")
    try:
        with open(test_file, 'rb') as f:
            files = {"file": (test_file, f, "application/octet-stream")}
            print(f"   📤 Отправляем файл {test_file}...")
            
            start_time = time.time()
            response = requests.post(f"{base_url}/upload", files=files, timeout=300)  # 5 минут timeout
            upload_time = time.time() - start_time
            
            print(f"   ⏱️ Время загрузки: {upload_time:.2f} секунд")
            print(f"   📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Файл успешно обработан!")
                print(f"   📊 Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                if result.get('success'):
                    gcs_url = result.get('gcs_url')
                    if gcs_url:
                        print(f"\n🎉 УСПЕХ! Конвертация завершена!")
                        print(f"📁 Результат сохранен: {gcs_url}")
                        print(f"🔗 Ссылка для скачивания: {gcs_url}")
                        
                        # Шаг 4: Проверка результата
                        print("\n4️⃣ Проверка результата...")
                        print(f"   📁 GCS URL: {gcs_url}")
                        print(f"   📏 Формат: {result.get('file_info', {}).get('format', 'Unknown')}")
                        print(f"   📊 Размер исходного файла: {result.get('file_info', {}).get('file_size', 0)} байт")
                        
                        return True
                    else:
                        print("   ❌ GCS URL не получен")
                        return False
                else:
                    print(f"   ❌ Ошибка обработки: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"   ❌ Ошибка загрузки: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📊 Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   📊 Текст ошибки: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Ошибка загрузки файла: {e}")
        return False

def test_api_endpoints():
    """Тестирует все API эндпоинты"""
    
    print("\n🔧 Тестирование API эндпоинтов")
    print("=" * 40)
    
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    endpoints = [
        ("GET", "/health", "Health check"),
        ("GET", "/status", "Service status"),
        ("POST", "/upload", "File upload (requires file)")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"\n📡 {method} {endpoint} - {description}")
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint}", timeout=10)
            
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Успешно")
                try:
                    data = response.json()
                    print(f"   📊 Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   📊 Текст: {response.text[:200]}...")
            else:
                print("   ⚠️ Ошибка (ожидаемо для POST без файла)")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск полного теста конвертации 3D → 2D")
    print("=" * 60)
    
    # Тестируем API эндпоинты
    test_api_endpoints()
    
    # Тестируем полную конвертацию
    success = test_forge_conversion()
    
    print("\n" + "=" * 60)
    if success:
        print("�� ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("✅ IFC файл успешно конвертирован в DWG/PDF")
        print("✅ Результат сохранен в Google Cloud Storage")
        print("✅ Ссылка на результат получена")
        print("\n📋 Следующие шаги:")
        print("1. Откройте ссылку на результат в браузере")
        print("2. Скачайте DWG/PDF файл")
        print("3. Проверьте качество 2D чертежа")
        print("4. Убедитесь, что все элементы модели отображены корректно")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН!")
        print("❌ Ошибка в процессе конвертации")
        print("\n🔧 Возможные причины:")
        print("1. Проблемы с Forge API")
        print("2. Неправильные секреты")
        print("3. Ошибки в GCS")
        print("4. Проблемы с IFC файлом")
    
    print("\n📊 Статистика теста:")
    print(f"   🌐 Сервис: https://btibot-637190449180.europe-west1.run.app")
    print(f"   📁 Тестовый файл: test_model.ifc")
    print(f"   🎯 Ожидаемый результат: DWG/PDF чертеж")

if __name__ == "__main__":
    main()
