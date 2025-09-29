#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Forge 3D → 2D API
"""

import requests
import json
import os
from pathlib import Path

# Конфигурация
BASE_URL = "https://forge-3d-to-2d-swiftchair.us-central1.run.app"
# Для локального тестирования: BASE_URL = "http://localhost:8080"

def test_health():
    """Тест health check"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_status():
    """Тест status endpoint"""
    print("\n📊 Testing status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def test_upload_no_file():
    """Тест загрузки без файла"""
    print("\n🚫 Testing upload without file...")
    try:
        response = requests.post(f"{BASE_URL}/upload", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def test_upload_invalid_file():
    """Тест загрузки неверного файла"""
    print("\n📁 Testing upload with invalid file...")
    try:
        # Создаем временный файл с неверным расширением
        with open("test.txt", "w") as f:
            f.write("This is not an IFC file")
        
        with open("test.txt", "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Удаляем временный файл
        os.remove("test.txt")
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Invalid file test failed: {e}")
        return False

def test_upload_valid_file():
    """Тест загрузки валидного IFC файла (если есть)"""
    print("\n🏗️ Testing upload with valid IFC file...")
    
    # Ищем IFC файл в текущей директории
    ifc_files = list(Path(".").glob("*.ifc"))
    if not ifc_files:
        print("⚠️ No IFC files found for testing")
        return True
    
    ifc_file = ifc_files[0]
    print(f"Using IFC file: {ifc_file}")
    
    try:
        with open(ifc_file, "rb") as f:
            files = {"file": (ifc_file.name, f, "application/octet-stream")}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=300)  # 5 минут timeout
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ File processed successfully!")
                print(f"📁 GCS URL: {result.get('gcs_url')}")
                return True
        
        return False
    except Exception as e:
        print(f"❌ Valid file test failed: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("🧪 Starting Forge 3D → 2D API Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Status Check", test_status),
        ("Upload No File", test_upload_no_file),
        ("Upload Invalid File", test_upload_invalid_file),
        ("Upload Valid File", test_upload_valid_file),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()
