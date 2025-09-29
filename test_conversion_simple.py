#!/usr/bin/env python3
"""
Простой тест конвертации 3D → 2D без зависимостей
"""

import os
import subprocess
import json

def test_service_availability():
    """Проверяет доступность сервиса"""
    
    print("🧪 Тест доступности сервиса")
    print("=" * 40)
    
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    # Проверяем health endpoint
    print("\n1️⃣ Health Check:")
    try:
        result = subprocess.run(['curl', '-s', f'{base_url}/health'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Сервис доступен")
            print(f"   📊 Ответ: {result.stdout}")
        else:
            print("   ❌ Сервис недоступен")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Проверяем status endpoint
    print("\n2️⃣ Status Check:")
    try:
        result = subprocess.run(['curl', '-s', f'{base_url}/status'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Статус получен")
            print(f"   📊 Ответ: {result.stdout}")
        else:
            print("   ❌ Ошибка получения статуса")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    return True

def test_file_upload():
    """Тестирует загрузку файла"""
    
    print("\n3️⃣ Тест загрузки файла:")
    
    # Проверяем наличие тестового файла
    test_file = "test_model.ifc"
    if not os.path.exists(test_file):
        print(f"   ❌ Тестовый файл {test_file} не найден!")
        return False
    
    print(f"   📁 Файл найден: {test_file}")
    print(f"   📏 Размер: {os.path.getsize(test_file)} байт")
    
    # Тестируем загрузку через curl
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    print("   📤 Отправляем файл...")
    try:
        cmd = ['curl', '-s', '-X', 'POST', 
               '-F', f'file=@{test_file}',
               f'{base_url}/upload']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        print(f"   📊 Статус: {result.returncode}")
        print(f"   📤 Ответ: {result.stdout}")
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                if response_data.get('success'):
                    print("   ✅ Файл успешно обработан!")
                    print(f"   📁 GCS URL: {response_data.get('gcs_url', 'N/A')}")
                    return True
                else:
                    print(f"   ❌ Ошибка обработки: {response_data.get('message', 'Unknown')}")
                    return False
            except:
                print("   ❌ Не удалось распарсить ответ")
                return False
        else:
            print("   ❌ Ошибка загрузки")
            print(f"   📊 Детали: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

def show_test_instructions():
    """Показывает инструкции по тестированию"""
    
    print("\n📋 Инструкции по тестированию:")
    print("=" * 50)
    
    print("\n🎯 Цель теста:")
    print("   • Загрузить тестовую IFC модель")
    print("   • Конвертировать через Forge API в DWG/PDF")
    print("   • Получить ссылку на результат в GCS")
    print("   • Проверить качество 2D чертежа")
    
    print("\n📁 Тестовая модель:")
    print("   • Файл: test_model.ifc")
    print("   • Параметры: квартира 50 м², 2 комнаты, 1 санузел")
    print("   • Элементы: стены, окна, двери")
    print("   • Размер: 4.5 KB")
    
    print("\n🔄 Процесс конвертации:")
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
    
    print("\n🔧 Для ручного тестирования:")
    print("   curl -X POST -F 'file=@test_model.ifc' \\")
    print("        https://btibot-637190449180.europe-west1.run.app/upload")
    
    print("\n📱 Через Telegram бота:")
    print("   1. Отправьте кадастровый номер")
    print("   2. Дождитесь расчета БТИ")
    print("   3. Нажмите '🔄 Тест 3D→2D конвертации'")
    print("   4. Отправьте IFC файл боту")

def main():
    """Основная функция тестирования"""
    
    print("🚀 Тест конвертации 3D → 2D")
    print("=" * 50)
    
    # Показываем инструкции
    show_test_instructions()
    
    # Проверяем доступность сервиса
    if not test_service_availability():
        print("\n❌ Сервис недоступен, тест прерван")
        return
    
    # Тестируем загрузку файла
    success = test_file_upload()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("✅ IFC файл конвертирован в DWG/PDF")
        print("✅ Результат сохранен в GCS")
        print("✅ Ссылка на результат получена")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН!")
        print("❌ Ошибка в процессе конвертации")
    
    print("\n📊 Информация о тесте:")
    print(f"   🌐 Сервис: https://btibot-637190449180.europe-west1.run.app")
    print(f"   📁 Тестовый файл: test_model.ifc")
    print(f"   🎯 Ожидаемый результат: DWG/PDF чертеж")

if __name__ == "__main__":
    main()
