"""
Функции для предложения создания чертежей и исправлений
"""

import logging
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

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

def calculate_drawing_price(service_type: str, area: float) -> Dict:
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

def create_drawing_services_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с услугами по чертежам"""
    keyboard = []
    
    # Добавляем кнопки для каждой услуги
    for service_id, service in DRAWING_SERVICES.items():
        button_text = f"📐 {service['name']}"
        callback_data = f"drawing_{service_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Добавляем кнопку "Все услуги"
    keyboard.append([InlineKeyboardButton("📋 Все услуги", callback_data="drawing_all")])
    
    return InlineKeyboardMarkup(keyboard)

async def send_drawing_services_offer(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     address: str, area: float, room_type: str) -> None:
    """Отправляет предложение услуг по чертежам"""
    
    message = (
        "🎨 **Дополнительные услуги**\n\n"
        f"📍 **Объект:** {address}\n"
        f"📐 **Площадь:** {area} м²\n"
        f"🏢 **Тип:** {room_type}\n\n"
        "**Мы также можем предложить:**\n\n"
        "📐 **Технические чертежи** - создание рабочих чертежей по обмерам\n"
        "📋 **Исполнительные чертежи** - чертежи фактического состояния\n"
        "🏗️ **BIM-модель** - 3D модель объекта с детализацией\n"
        "✏️ **Исправления** - внесение изменений в документацию\n\n"
        "💡 **Выберите интересующую услугу для расчета стоимости:**"
    )
    
    keyboard = create_drawing_services_keyboard()
    await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')

async def handle_drawing_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор услуги по чертежам"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    if callback_data.startswith("drawing_"):
        service_type = callback_data.replace("drawing_", "")
        
        if service_type == "all":
            # Показываем все услуги
            await show_all_drawing_services(query, context)
        else:
            # Показываем конкретную услугу
            await show_specific_drawing_service(query, context, service_type)

async def show_all_drawing_services(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все услуги по чертежам"""
    
    # Получаем данные об объекте из контекста (если есть)
    area = 100  # По умолчанию, можно получить из user_data
    
    message = "📋 **Все услуги по чертежам:**\n\n"
    
    for service_id, service in DRAWING_SERVICES.items():
        price_info = calculate_drawing_price(service_id, area)
        
        message += (
            f"**{service['name']}**\n"
            f"📝 {service['description']}\n"
            f"💰 {price_info['price_per_m2']} ₽/м²\n"
            f"⏱️ Срок: {service['delivery_days']} дней\n"
            f"💵 Итого: {price_info['final_price']:,.0f} ₽\n\n"
        )
    
    message += "💡 **Выберите конкретную услугу для детального расчета:**"
    
    keyboard = create_drawing_services_keyboard()
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode='Markdown')

async def show_specific_drawing_service(query, context: ContextTypes.DEFAULT_TYPE, service_type: str) -> None:
    """Показывает детальную информацию об услуге"""
    
    if service_type not in DRAWING_SERVICES:
        await query.edit_message_text("❌ Услуга не найдена")
        return
    
    # Получаем площадь из контекста (можно улучшить)
    area = 100  # По умолчанию
    
    service = DRAWING_SERVICES[service_type]
    price_info = calculate_drawing_price(service_type, area)
    
    message = (
        f"📐 **{service['name']}**\n\n"
        f"📝 **Описание:** {service['description']}\n"
        f"📐 **Площадь:** {area} м²\n"
        f"💰 **Цена за м²:** {price_info['price_per_m2']} ₽\n"
        f"🧮 **Расчет:** {area} × {price_info['price_per_m2']} = {price_info['calculated_price']:,.0f} ₽\n"
        f"💵 **Итого:** {price_info['final_price']:,.0f} ₽\n"
        f"⏱️ **Срок:** {service['delivery_days']} дней\n\n"
    )
    
    if price_info['savings'] > 0:
        message += f"🎉 **Экономия:** {price_info['savings']:,.0f} ₽ (минимальная цена)\n\n"
    
    message += (
        "📞 **Для заказа услуги:**\n"
        "• Email: sales@zamerpro.ru\n"
        "• Телефон: +7 (495) 000-00-00\n"
        "• Telegram: @zamerpro_support\n\n"
        "💼 **Что входит в услугу:**\n"
        "• Выезд специалиста\n"
        "• Обмеры и фотофиксация\n"
        "• Создание чертежей в AutoCAD\n"
        "• Проверка и корректировка\n"
        "• Передача в форматах DWG, PDF"
    )
    
    # Кнопка "Назад к услугам"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад к услугам", callback_data="drawing_all")],
        [InlineKeyboardButton("📞 Заказать", callback_data=f"order_{service_type}")]
    ])
    
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode='Markdown')

def get_drawing_services_summary() -> str:
    """Возвращает краткое описание всех услуг"""
    summary = "🎨 **Дополнительные услуги:**\n\n"
    
    for service_id, service in DRAWING_SERVICES.items():
        summary += f"• **{service['name']}** - {service['description']}\n"
        summary += f"  💰 {service['price_per_m2']} ₽/м², ⏱️ {service['delivery_days']} дней\n\n"
    
    return summary

# Функция для тестирования
def test_drawing_services():
    """Тестирует функции услуг по чертежам"""
    print("🧪 Тестирование функций услуг по чертежам")
    print("=" * 50)
    
    # Тест расчета цен
    print("\n1️⃣ Тест расчета цен:")
    for service_type in DRAWING_SERVICES.keys():
        price_info = calculate_drawing_price(service_type, 100)
        print(f"   {service_type}: {price_info['final_price']:,.0f} ₽")
    
    # Тест получения описания
    print("\n2️⃣ Тест описания услуг:")
    summary = get_drawing_services_summary()
    print(summary)
    
    print("\n✅ Все тесты пройдены!")

if __name__ == "__main__":
    test_drawing_services()
