#!/usr/bin/env python3
"""
Тестовая функция для предложения создания чертежей и исправлений
"""

import requests
import json

def test_drawing_services():
    """Тестирует функциональность предложения чертежей и исправлений"""
    
    # URL сервиса
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    print("🧪 Тестирование сервиса предложения чертежей и исправлений")
    print("=" * 60)
    
    # Тест 1: Health check
    print("\n1️⃣ Тест Health Check:")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Тест 2: Status check
    print("\n2️⃣ Тест Status:")
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        if response.status_code == 200:
            print("   ✅ Status check passed")
        else:
            print("   ❌ Status check failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Тест 3: Upload endpoint (без файла)
    print("\n3️⃣ Тест Upload без файла:")
    try:
        response = requests.post(f"{base_url}/upload", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 400:
            print("   ✅ Upload validation working (expected 400)")
        else:
            print("   ⚠️ Unexpected response")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Тест 4: Upload с неверным файлом
    print("\n4️⃣ Тест Upload с неверным файлом:")
    try:
        # Создаем временный файл с неверным расширением
        with open("test.txt", "w") as f:
            f.write("This is not an IFC file")
        
        with open("test.txt", "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(f"{base_url}/upload", files=files, timeout=30)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Удаляем временный файл
        import os
        os.remove("test.txt")
        
        if response.status_code == 400:
            print("   ✅ File validation working (expected 400)")
        else:
            print("   ⚠️ Unexpected response")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Тестирование завершено!")
    print("\n📋 Доступные функции:")
    print("   • BTI расчеты с региональными тарифами")
    print("   • Анализ рыночных цен через SERP")
    print("   • Генерация коммерческих предложений")
    print("   • Конвертация IFC → DWG через Forge")
    print("   • Сохранение результатов в GCS")
    
    print("\n🔧 Следующие шаги для добавления чертежей:")
    print("   1. Добавить кнопки в Telegram бота")
    print("   2. Создать эндпоинт для заказа чертежей")
    print("   3. Интегрировать с Forge для создания DWG")
    print("   4. Добавить систему заказов и уведомлений")

if __name__ == "__main__":
    test_drawing_services()
