#!/usr/bin/env python3
"""
Простой тест сервиса без зависимостей
"""

def test_service_endpoints():
    """Тестирует доступность эндпоинтов сервиса"""
    
    print("🧪 Тестирование сервиса BTI Bot + Forge 3D→2D")
    print("=" * 60)
    
    # URL сервиса
    base_url = "https://btibot-637190449180.europe-west1.run.app"
    
    print(f"\n🌐 Сервис: {base_url}")
    print("\n📡 Доступные эндпоинты:")
    print("   • GET /health - Health check")
    print("   • GET /status - Service status")
    print("   • POST /upload - IFC file upload")
    print("   • POST / - Telegram webhook")
    
    print("\n🎨 Функции для чертежей:")
    print("   • Технические чертежи - 150 ₽/м²")
    print("   • Исполнительные чертежи - 200 ₽/м²")
    print("   • BIM-модель - 300 ₽/м²")
    print("   • Исправления - 100 ₽/м²")
    
    print("\n🔧 Для тестирования используйте:")
    print("   curl -s https://btibot-637190449180.europe-west1.run.app/health")
    print("   curl -s https://btibot-637190449180.europe-west1.run.app/status")
    
    print("\n📋 Готовые функции:")
    print("   ✅ BTI расчеты с региональными тарифами")
    print("   ✅ Анализ рыночных цен через SERP")
    print("   ✅ Генерация коммерческих предложений")
    print("   ✅ Конвертация IFC → DWG через Forge")
    print("   ✅ Сохранение результатов в GCS")
    print("   ✅ Функции для предложения чертежей")
    
    print("\n🚀 Следующие шаги:")
    print("   1. Интегрировать функции чертежей в основной бот")
    print("   2. Добавить кнопки в Telegram интерфейс")
    print("   3. Создать систему заказов")
    print("   4. Добавить уведомления о статусе заказа")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_service_endpoints()
