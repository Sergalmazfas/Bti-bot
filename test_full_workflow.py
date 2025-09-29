#!/usr/bin/env python3
"""
Полный тест workflow конвертации 3D → 2D
"""

import os
import sys
import time
import json

def test_with_curl():
    """Тестирует с помощью curl (без зависимостей)"""
    
    print("🧪 Полный тест workflow конвертации 3D → 2D")
    print("=" * 60)
    
    # Проверяем наличие тестового файла
    test_file = "test_model.ifc"
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден!")
        print("Создайте его с помощью: python3 create_test_ifc.py")
        return False
    
    print(f"�� Тестовый файл: {test_file}")
    print(f"📏 Размер: {os.path.getsize(test_file)} байт")
    
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    # Шаг 1: Health check
    print("\n1️⃣ Проверка сервиса...")
    try:
        import subprocess
        result = subprocess.run(['curl', '-s', f'{base_url}/health'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Сервис работает")
            health_data = json.loads(result.stdout)
            print(f"   📊 Статус: {health_data.get('status', 'Unknown')}")
            print(f"   📝 Сообщение: {health_data.get('message', 'Unknown')}")
        else:
            print("   ❌ Ошибка сервиса")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Шаг 2: Status check
    print("\n2️⃣ Проверка статуса...")
    try:
        result = subprocess.run(['curl', '-s', f'{base_url}/status'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Статус получен")
            status_data = json.loads(result.stdout)
            print(f"   📊 Сервис: {status_data.get('service', 'Unknown')}")
            print(f"   📁 Поддерживаемые форматы: {status_data.get('supported_formats', [])}")
            print(f"   📏 Максимальный размер: {status_data.get('max_file_size_mb', 0)} MB")
        else:
            print("   ❌ Ошибка получения статуса")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 3: Загрузка и конвертация файла
    print("\n3️⃣ Загрузка IFC файла и конвертация...")
    try:
        print(f"   📤 Отправляем файл {test_file}...")
        start_time = time.time()
        
        cmd = ['curl', '-s', '-X', 'POST', 
               '-F', f'file=@{test_file}',
               f'{base_url}/upload']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        upload_time = time.time() - start_time
        
        print(f"   ⏱️ Время обработки: {upload_time:.2f} секунд")
        print(f"   📊 Статус: {result.returncode}")
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                print(f"   📤 Ответ сервера: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                
                if response_data.get('success'):
                    print("\n🎉 УСПЕХ! Конвертация завершена!")
                    gcs_url = response_data.get('gcs_url')
                    if gcs_url:
                        print(f"📁 Результат сохранен: {gcs_url}")
                        print(f"🔗 Ссылка для скачивания: {gcs_url}")
                        
                        # Информация о файле
                        file_info = response_data.get('file_info', {})
                        print(f"\n📊 Информация о результате:")
                        print(f"   📁 Исходный файл: {file_info.get('original_filename', 'Unknown')}")
                        print(f"   📏 Размер исходного файла: {file_info.get('file_size', 0)} байт")
                        print(f"   🔄 Формат конвертации: {file_info.get('format', 'Unknown')}")
                        
                        return True
                    else:
                        print("   ❌ GCS URL не получен")
                        return False
                else:
                    print(f"   ❌ Ошибка обработки: {response_data.get('message', 'Unknown error')}")
                    return False
            except json.JSONDecodeError as e:
                print(f"   ❌ Ошибка парсинга JSON: {e}")
                print(f"   📤 Сырой ответ: {result.stdout}")
                return False
        else:
            print(f"   ❌ Ошибка загрузки (код: {result.returncode})")
            print(f"   📊 Детали ошибки: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

def show_test_summary():
    """Показывает сводку теста"""
    
    print("\n📋 Сводка теста:")
    print("=" * 40)
    
    print("🎯 Цель теста:")
    print("   • Загрузить тестовую IFC модель")
    print("   • Конвертировать через Forge API в DWG/PDF")
    print("   • Получить ссылку на результат в GCS")
    print("   • Проверить качество 2D чертежа")
    
    print("\n📁 Тестовая модель:")
    print("   • Файл: test_model.ifc")
    print("   • Параметры: квартира 50 м², 2 комнаты, 1 санузел")
    print("   • Элементы: стены, окна, двери")
    print("   • Размер: 4.5 KB")
    
    print("\n🔄 Workflow конвертации:")
    print("   1. Загрузка IFC файла на Cloud Run")
    print("   2. Валидация файла (.ifc, <100MB)")
    print("   3. Загрузка в Forge OSS bucket")
    print("   4. Конвертация IFC → DWG через Model Derivative API")
    print("   5. Скачивание результата из Forge")
    print("   6. Сохранение в GCS: gs://btibot-processed/processed/<дата>/")
    print("   7. Возврат ссылки на результат")
    
    print("\n✅ Ожидаемый результат:")
    print("   • DWG/PDF файл с 2D чертежом")
    print("   • План квартиры с размерами")
    print("   • Отображение стен, окон, дверей")
    print("   • Аннотации и размеры")

def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск полного теста workflow конвертации 3D → 2D")
    print("=" * 70)
    
    # Показываем сводку
    show_test_summary()
    
    # Запускаем тест
    success = test_with_curl()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
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
        print("\n📞 Для решения проблем:")
        print("1. Проверьте логи Cloud Run")
        print("2. Убедитесь, что секреты Forge настроены")
        print("3. Проверьте права доступа к GCS")
    
    print("\n📊 Информация о тесте:")
    print(f"   🌐 Сервис: https://btibot-637190449180.europe-west1.run.app")
    print(f"   📁 Тестовый файл: test_model.ifc")
    print(f"   🎯 Ожидаемый результат: DWG/PDF чертеж")

if __name__ == "__main__":
    main()
