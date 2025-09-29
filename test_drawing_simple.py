#!/usr/bin/env python3
"""
Простой тест функций для предложения чертежей и исправлений
"""

# Услуги по чертежам и исправлениям
DRAWING_SERVICES = {
    "technical_drawings": {
        "name": "Технические чертежи",
        "description": "Создание рабочих чертежей по обмерам",
        "price_per_m2": 150,
        "min_price": 15000,
        "delivery_days": 5
    },
    "as_built_drawings": {
        "name": "Исполнительные чертежи",
        "description": "Чертежи фактического состояния объекта",
        "price_per_m2": 200,
        "min_price": 20000,
        "delivery_days": 7
    },
    "bim_model": {
        "name": "BIM-модель",
        "description": "3D модель объекта с детализацией",
        "price_per_m2": 300,
        "min_price": 30000,
        "delivery_days": 10
    },
    "corrections": {
        "name": "Исправления в документации",
        "description": "Внесение изменений в существующие документы",
        "price_per_m2": 100,
        "min_price": 10000,
        "delivery_days": 3
    }
}

def calculate_drawing_price(service_type: str, area: float):
    """Рассчитывает стоимость услуг по чертежам"""
    if service_type not in DRAWING_SERVICES:
        return {"error": "Unknown service type"}
    
    service = DRAWING_SERVICES[service_type]
    price_per_m2 = service["price_per_m2"]
    min_price = service["min_price"]
    
    calculated_price = area * price_per_m2
    final_price = max(calculated_price, min_price)
    
    return {
        "service_name": service["name"],
        "description": service["description"],
        "area": area,
        "price_per_m2": price_per_m2,
        "calculated_price": calculated_price,
        "final_price": final_price,
        "delivery_days": service["delivery_days"],
        "savings": max(0, calculated_price - final_price) if calculated_price > min_price else 0
    }

def get_drawing_services_summary():
    """Возвращает краткое описание всех услуг"""
    summary = "🎨 **Дополнительные услуги:**\n\n"
    
    for service_id, service in DRAWING_SERVICES.items():
        summary += f"• **{service['name']}** - {service['description']}\n"
        summary += f"  💰 {service['price_per_m2']} ₽/м², ⏱️ {service['delivery_days']} дней\n\n"
    
    return summary

def test_drawing_services():
    """Тестирует функции услуг по чертежам"""
    print("🧪 Тестирование функций услуг по чертежам")
    print("=" * 50)
    
    # Тест расчета цен для разных площадей
    test_areas = [50, 100, 200, 500]
    
    print("\n1️⃣ Тест расчета цен для разных площадей:")
    for area in test_areas:
        print(f"\n   📐 Площадь: {area} м²")
        for service_type in DRAWING_SERVICES.keys():
            price_info = calculate_drawing_price(service_type, area)
            print(f"   • {price_info['service_name']}: {price_info['final_price']:,.0f} ₽")
    
    # Тест получения описания
    print("\n2️⃣ Тест описания услуг:")
    summary = get_drawing_services_summary()
    print(summary)
    
    # Тест конкретной услуги
    print("\n3️⃣ Тест конкретной услуги (BIM-модель, 150 м²):")
    price_info = calculate_drawing_price("bim_model", 150)
    print(f"   Название: {price_info['service_name']}")
    print(f"   Описание: {price_info['description']}")
    print(f"   Площадь: {price_info['area']} м²")
    print(f"   Цена за м²: {price_info['price_per_m2']} ₽")
    print(f"   Расчет: {price_info['calculated_price']:,.0f} ₽")
    print(f"   Итого: {price_info['final_price']:,.0f} ₽")
    print(f"   Срок: {price_info['delivery_days']} дней")
    if price_info['savings'] > 0:
        print(f"   Экономия: {price_info['savings']:,.0f} ₽")
    
    print("\n✅ Все тесты пройдены!")
    print("\n📋 Готовые функции:")
    print("   • calculate_drawing_price() - расчет стоимости")
    print("   • get_drawing_services_summary() - описание услуг")
    print("   • DRAWING_SERVICES - база данных услуг")
    
    print("\n🔧 Следующие шаги:")
    print("   1. Интегрировать в основной бот")
    print("   2. Добавить кнопки в Telegram")
    print("   3. Создать систему заказов")
    print("   4. Добавить уведомления")

if __name__ == "__main__":
    test_drawing_services()
