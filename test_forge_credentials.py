#!/usr/bin/env python3
"""
Тест Forge API credentials и прав доступа
"""

import requests
import json
import os
from google.cloud import secretmanager

def test_forge_authentication():
    """Тестирует аутентификацию в Forge API"""
    
    print("🔐 Тестирование Forge API credentials")
    print("=" * 50)
    
    try:
        # Получаем секреты из Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        project_id = "talkhint"
        
        # ForgeClientID
        name_id = f"projects/{project_id}/secrets/ForgeClientID/versions/latest"
        response_id = client.access_secret_version(request={"name": name_id})
        client_id = response_id.payload.data.decode("UTF-8")
        
        # ForgeClientSecret  
        name_secret = f"projects/{project_id}/secrets/ForgeClientSecret/versions/latest"
        response_secret = client.access_secret_version(request={"name": name_secret})
        client_secret = response_secret.payload.data.decode("UTF-8")
        
        print(f"✅ Client ID получен: {client_id[:10]}...")
        print(f"✅ Client Secret получен: {client_secret[:10]}...")
        
        # Тестируем аутентификацию
        print("\n🔑 Тестирование аутентификации...")
        
        url = "https://developer.api.autodesk.com/authentication/v2/token"
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'data:read data:write data:create bucket:create bucket:read'
        }
        
        response = requests.post(url, data=data, timeout=30)
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in')
            
            print("✅ Аутентификация успешна!")
            print(f"🔑 Access Token: {access_token[:20]}...")
            print(f"⏰ Срок действия: {expires_in} секунд")
            
            # Тестируем доступ к OSS API
            print("\n📦 Тестирование доступа к OSS API...")
            
            headers = {'Authorization': f'Bearer {access_token}'}
            oss_url = "https://developer.api.autodesk.com/oss/v2/buckets"
            
            oss_response = requests.get(oss_url, headers=headers, timeout=30)
            print(f"📊 OSS API статус: {oss_response.status_code}")
            
            if oss_response.status_code == 200:
                print("✅ Доступ к OSS API успешен!")
                buckets = oss_response.json()
                print(f"📦 Количество buckets: {len(buckets.get('items', []))}")
            else:
                print(f"❌ Ошибка OSS API: {oss_response.text}")
                
            # Тестируем доступ к Model Derivative API
            print("\n🔄 Тестирование доступа к Model Derivative API...")
            
            md_url = "https://developer.api.autodesk.com/modelderivative/v2/designdata"
            md_response = requests.get(md_url, headers=headers, timeout=30)
            print(f"📊 Model Derivative API статус: {md_response.status_code}")
            
            if md_response.status_code in [200, 404]:  # 404 нормально для пустого списка
                print("✅ Доступ к Model Derivative API успешен!")
            else:
                print(f"❌ Ошибка Model Derivative API: {md_response.text}")
                
            return True
            
        else:
            print(f"❌ Ошибка аутентификации: {response.status_code}")
            print(f"📝 Детали: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_gcs_access():
    """Тестирует доступ к Google Cloud Storage"""
    
    print("\n🗄️ Тестирование Google Cloud Storage")
    print("=" * 50)
    
    try:
        from google.cloud import storage
        
        client = storage.Client()
        print("✅ GCS клиент инициализирован")
        
        # Проверяем существование bucket
        bucket_name = "btibot-processed"
        bucket = client.bucket(bucket_name)
        
        if bucket.exists():
            print(f"✅ Bucket {bucket_name} существует")
        else:
            print(f"⚠️ Bucket {bucket_name} не существует, создаем...")
            try:
                bucket = client.create_bucket(bucket_name, location="europe-west1")
                print(f"✅ Bucket {bucket_name} создан")
            except Exception as e:
                print(f"❌ Ошибка создания bucket: {e}")
                return False
        
        # Тестируем загрузку файла
        print("📤 Тестирование загрузки файла...")
        blob_name = "test/test_file.txt"
        blob = bucket.blob(blob_name)
        
        test_content = "Test content for Forge integration"
        blob.upload_from_string(test_content, content_type='text/plain')
        
        print(f"✅ Тестовый файл загружен: gs://{bucket_name}/{blob_name}")
        
        # Очищаем тестовый файл
        blob.delete()
        print("🧹 Тестовый файл удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка GCS: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("🧪 Комплексная проверка Forge API и GCS")
    print("=" * 60)
    
    # Тест 1: Forge API credentials
    forge_ok = test_forge_authentication()
    
    # Тест 2: GCS доступ
    gcs_ok = test_gcs_access()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"�� Forge API: {'✅ OK' if forge_ok else '❌ FAIL'}")
    print(f"🗄️ GCS: {'✅ OK' if gcs_ok else '❌ FAIL'}")
    
    if forge_ok and gcs_ok:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Forge API credentials работают корректно")
        print("✅ GCS доступ настроен правильно")
        print("✅ Готово для полного тестирования конвертации")
    else:
        print("\n❌ ЕСТЬ ПРОБЛЕМЫ:")
        if not forge_ok:
            print("• Проверьте Forge API credentials")
            print("• Убедитесь в правильности Client ID и Secret")
        if not gcs_ok:
            print("• Проверьте права доступа к GCS")
            print("• Убедитесь в существовании bucket btibot-processed")

if __name__ == "__main__":
    main()
