#!/usr/bin/env python3
"""
Простой тест Forge API через curl
"""

import subprocess
import json
import os

def test_forge_with_curl():
    """Тестирует Forge API через curl"""
    
    print("🔐 Тестирование Forge API через curl")
    print("=" * 50)
    
    try:
        # Получаем секреты
        client_id = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest', 
            '--secret=ForgeClientID', '--project=talkhint'
        ], capture_output=True, text=True).stdout.strip()
        
        client_secret = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest', 
            '--secret=ForgeClientSecret', '--project=talkhint'
        ], capture_output=True, text=True).stdout.strip()
        
        print(f"✅ Client ID: {client_id[:10]}...")
        print(f"✅ Client Secret: {client_secret[:10]}...")
        
        # Тестируем аутентификацию
        print("\n🔑 Тестирование аутентификации...")
        
        curl_cmd = [
            'curl', '-s', '-X', 'POST',
            'https://developer.api.autodesk.com/authentication/v2/token',
            '-d', f'client_id={client_id}',
            '-d', f'client_secret={client_secret}',
            '-d', 'grant_type=client_credentials',
            '-d', 'scope=data:read data:write data:create bucket:create bucket:read'
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        print(f"📊 Статус: {result.returncode}")
        
        if result.returncode == 0:
            try:
                token_data = json.loads(result.stdout)
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in')
                
                print("✅ Аутентификация успешна!")
                print(f"🔑 Token: {access_token[:20]}...")
                print(f"⏰ Срок: {expires_in} сек")
                
                # Тестируем OSS API
                print("\n📦 Тестирование OSS API...")
                
                oss_cmd = [
                    'curl', '-s', '-H', f'Authorization: Bearer {access_token}',
                    'https://developer.api.autodesk.com/oss/v2/buckets'
                ]
                
                oss_result = subprocess.run(oss_cmd, capture_output=True, text=True, timeout=30)
                print(f"📊 OSS статус: {oss_result.returncode}")
                
                if oss_result.returncode == 0:
                    print("✅ OSS API доступен!")
                    try:
                        oss_data = json.loads(oss_result.stdout)
                        items = oss_data.get('items', [])
                        print(f"📦 Buckets: {len(items)}")
                    except:
                        print("📦 OSS ответ получен")
                else:
                    print(f"❌ OSS ошибка: {oss_result.stderr}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка JSON: {e}")
                print(f"📝 Ответ: {result.stdout}")
                return False
        else:
            print(f"❌ Ошибка curl: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_gcs_bucket():
    """Проверяет GCS bucket"""
    
    print("\n🗄️ Проверка GCS bucket")
    print("=" * 30)
    
    try:
        # Проверяем существование bucket
        result = subprocess.run([
            'gsutil', 'ls', 'gs://btibot-processed'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Bucket btibot-processed существует")
            return True
        else:
            print("⚠️ Bucket не существует, создаем...")
            
            create_result = subprocess.run([
                'gsutil', 'mb', '-l', 'europe-west1', 'gs://btibot-processed'
            ], capture_output=True, text=True)
            
            if create_result.returncode == 0:
                print("✅ Bucket создан успешно")
                return True
            else:
                print(f"❌ Ошибка создания bucket: {create_result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка GCS: {e}")
        return False

def main():
    """Основная функция"""
    
    print("🧪 Проверка Forge API и GCS")
    print("=" * 40)
    
    # Тест Forge API
    forge_ok = test_forge_with_curl()
    
    # Тест GCS
    gcs_ok = test_gcs_bucket()
    
    print("\n" + "=" * 40)
    print("📊 РЕЗУЛЬТАТЫ:")
    print(f"🔐 Forge API: {'✅ OK' if forge_ok else '❌ FAIL'}")
    print(f"🗄️ GCS: {'✅ OK' if gcs_ok else '❌ FAIL'}")
    
    if forge_ok and gcs_ok:
        print("\n🎉 ВСЕ ГОТОВО!")
        print("✅ Forge API работает")
        print("✅ GCS настроен")
        print("✅ Можно тестировать конвертацию")
    else:
        print("\n❌ ПРОБЛЕМЫ:")
        if not forge_ok:
            print("• Проверьте Forge credentials")
        if not gcs_ok:
            print("• Настройте GCS bucket")

if __name__ == "__main__":
    main()
