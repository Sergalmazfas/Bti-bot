import os
import json
import logging
import asyncio
import threading
import re
import requests
import statistics
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Глобальные переменные для сессий пользователей
user_data = {}

# Глобальные переменные приложения и event loop
application = None
_background_loop = None
_loop_thread = None

# Коэффициенты CRPTI (обновляются раз в полгода)
CRPTI_COEFFICIENTS = {
    'coefficient_measurements': 50,  # руб/м² для обмеров
    'coefficient_tech': 750,  # руб/м² для техпаспорта + техзадания
    'last_updated': '2025-09-24'
}

# Инициализация OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_commercial_proposal(object_data: dict, pricing_cards: dict) -> str:
    """Генерация коммерческого предложения через GPT"""
    try:
        # Формируем промпт для GPT
        prompt = f"""Ты работаешь в компании, предоставляющей услуги БТИ: обмеры помещений, подготовка технического паспорта и технического задания.

Составь коммерческое предложение для клиента по объекту недвижимости.

Данные об объекте:
- Адрес: {object_data.get('address', 'Не указан')}
- Площадь: {object_data.get('area', 'Не указана')} м²
- Год постройки: {object_data.get('build_year', 'Не указан')}
- Материал стен: {object_data.get('materials', 'Не указан')}
- Тип помещения: {object_data.get('room_type', 'Не указан')}

Карточки цен:
- Карточка 1 (БТИ): {pricing_cards.get('bti_total', 0):,.0f} руб.
  • Обмеры: {pricing_cards.get('bti_measurements', 0):,.0f} руб.
  • Техпаспорт + задание: {pricing_cards.get('bti_tech', 0):,.0f} руб.
- Карточка 2 (Конкуренты): {pricing_cards.get('competitor_price', 0):,.0f} руб.
- Карточка 3 (Рекомендованная): {pricing_cards.get('recommended_price', 0):,.0f} руб.

Требования к тексту:
- Стиль: деловой, максимум 6–7 предложений.
- Основная цена: рекомендованная (Карточка 3).
- Используй цены БТИ и конкурентов только как аргументы для подтверждения выгодности предложения.
- Сделай упор на том, что клиент получает полный пакет услуг БТИ (обмеры, паспорт, задание).
- Заверши приглашением к контакту.

Ответь только текстом коммерческого предложения без дополнительных комментариев."""

        # Вызов OpenAI API (новая версия)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты профессиональный менеджер по продажам услуг БТИ."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        if response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Не удалось сгенерировать коммерческое предложение."
            
    except Exception as e:
        logger.error(f"Ошибка генерации коммерческого предложения: {e}")
        return f"🤝 **КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ** по объекту {object_data.get('area', 0)} м²\n\nПредлагаем выполнить полный комплекс услуг БТИ: обмеры помещений, подготовку технического паспорта и технического задания по выгодной цене **{pricing_cards.get('recommended_price', 0):,.0f} руб.**\n\nДанная стоимость учитывает рыночные цены и официальные тарифы БТИ, обеспечивая оптимальное соотношение цена-качество. Полный пакет документов будет готов в сжатые сроки с гарантией качества.\n\n📞 Свяжитесь с нами для оформления заказа!"


def _start_background_loop():
    """Запускает постоянный asyncio event loop в фоновом потоке."""
    global _background_loop
    _background_loop = asyncio.new_event_loop()

    def run_loop_forever():
        asyncio.set_event_loop(_background_loop)
        _background_loop.run_forever()

    global _loop_thread
    _loop_thread = threading.Thread(target=run_loop_forever, name="bot-event-loop", daemon=True)
    _loop_thread.start()
    logger.info("Background asyncio loop started")


def _run_coro(coro):
    """Планирует корутину на постоянном loop и ждет результата синхронно."""
    if _background_loop is None:
        raise RuntimeError("Background loop is not started")
    future = asyncio.run_coroutine_threadsafe(coro, _background_loop)
    return future.result()


def fetch_reestr_data(query: str, search_type: str = "cadastral") -> dict:
    """Шаг 1: Получение данных из Госреестра (синхронно)"""
    try:
        reestr_token = os.getenv('REESTR_API_TOKEN')
        if not reestr_token:
            logger.error("REESTR_API_TOKEN not found")
            return {}
        
        if search_type == "cadastral":
            url = f"https://reestr-api.ru/v1/search/cadastrFull?auth_token={reestr_token}"
            data = {"cad_num": query}
        else:
            url = f"https://reestr-api.ru/v1/search/address?auth_token={reestr_token}"
            data = {"address": query}
        
        response = requests.post(url, data=data, timeout=15)
        
        if response.status_code == 404 and search_type == "cadastral":
            # Fallback на краткую версию поиска по кадастру
            fallback_url = f"https://reestr-api.ru/v1/search/cadastr?auth_token={reestr_token}"
            response = requests.post(fallback_url, data={"cad_num": query}, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Reestr fallback HTTP {response.status_code}")
                return {}
        elif response.status_code != 200:
            logger.warning(f"Reestr HTTP {response.status_code}")
            return {}
        
        api_json = response.json()
        
    except Exception as e:
        logger.error(f"Reestr error: {e}")
        return {}

    try:
        items = api_json.get("list") or []
        if not items and isinstance(api_json, dict):
            items = [api_json] if api_json else []
        if not items:
            return {}
        item = items[0]

        # Маппинг данных
        address = item.get("address") or item.get("full_address")
        cad_num = item.get("cad_num") or item.get("cadastral_number") or (query if search_type == "cadastral" else None)
        area_raw = item.get("area")
        unit = item.get("unit")

        # Год постройки
        build_year = None
        for year_key in ("construction_end", "exploitation_start"):
            y = item.get(year_key)
            if isinstance(y, int):
                build_year = y
                break
            if isinstance(y, str):
                y_digits = re.findall(r"(19\d{2}|20\d{2})", y)
                if y_digits:
                    build_year = int(y_digits[0])
                    break
        if build_year is None:
            reg_date = item.get("reg_date") or item.get("update_date")
            if isinstance(reg_date, str):
                parts = re.findall(r"(19\d{2}|20\d{2})", reg_date)
                if parts:
                    build_year = int(parts[-1])

        # Тип помещения
        room_type_raw = item.get("oks_purpose") or item.get("oks_type_more") or item.get("obj_type") or item.get("oks_type")
        room_type = None
        if isinstance(room_type_raw, str):
            lt = room_type_raw.lower()
            if any(k in lt for k in ["нежил", "торгов", "офис", "склад"]):
                room_type = "Нежилое"
            elif any(k in lt for k in ["жил", "квартир", "дом"]):
                room_type = "Жилое"
        room_type = room_type or room_type_raw or "Другое"

        # Материал стен
        materials = item.get("walls_material") or item.get("walls")
        if isinstance(materials, str):
            materials = materials.strip()

        # Парсим площадь
        area = None
        if isinstance(area_raw, (int, float)):
            area = float(area_raw)
        elif isinstance(area_raw, str):
            normalized = area_raw.replace(" ", "").replace(",", ".")
            try:
                area = float(normalized)
            except Exception:
                area = None
        if unit and isinstance(unit, str) and "м" not in unit and "кв" not in unit:
            area = area if area and area > 0 else None

        return {
            "address": address,
            "cadastral_number": cad_num,
            "area": area,
            "build_year": build_year,
            "materials": materials,
            "room_type": room_type
        }
    except Exception as e:
        logger.error(f"Reestr parse error: {e}")
        return {}

def search_competitor_prices(address: str, area: float) -> list:
    """Шаг 3: Поиск цен конкурентов через SERP API (улучшенный)"""
    try:
        serpriver_key = os.getenv('SERPRIVER_API_KEY')
        if not serpriver_key:
            logger.warning("SERPRIVER_API_KEY not found, using default prices")
            return [120, 150, 180, 200, 250]  # Дефолтные цены
        
        # Улучшенные запросы для поиска цен
        queries = [
            f"БТИ услуги обмеры {address} цена за м²",
            f"техпаспорт БТИ {address} стоимость",
            f"обмеры недвижимости {address} цена",
            f"БТИ замеры {int(area)} м² цена",
            f"обмеры помещений {address} стоимость",
            f"технический паспорт БТИ {address} цена",
            f"замеры недвижимости {address} стоимость м²"
        ]
        
        all_prices = []
        
        for query in queries:
            try:
                base_url = "https://serpriver.ru/api/search.php"
                params = {
                    "api_key": serpriver_key,
                    "system": "google",
                    "domain": "ru",
                    "query": query,
                    "result_cnt": 15,  # Увеличиваем количество результатов
                    "lr": 213  # Москва
                }
                
                response = requests.get(base_url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('json', {}).get('res'):
                        results = data['json']['res']
                        prices = parse_competitor_prices(results)
                        all_prices.extend(prices)
                        logger.info(f"Found {len(prices)} prices for query: {query}")
            except Exception as e:
                logger.warning(f"Error searching competitors for query '{query}': {e}")
                continue
        
        # Если не нашли цены, используем дефолтные
        if not all_prices:
            logger.warning("No competitor prices found, using defaults")
            all_prices = [120, 150, 180, 200, 250]
        
        logger.info(f"Total competitor prices found: {len(all_prices)} - {all_prices}")
        return all_prices
        
    except Exception as e:
        logger.error(f"Error in search_competitor_prices: {e}")
        return [120, 150, 180, 200, 250]  # Дефолтные цены

def parse_competitor_prices(results: list) -> list:
    """Улучшенный парсинг цен из результатов поиска"""
    prices = []
    
    for result in results:
        snippet = result.get('snippet', '').lower()
        title = result.get('title', '').lower()
        full_text = f"{title} {snippet}"
        
        # Расширенные паттерны для поиска цен
        price_patterns = [
            r'(\d+)\s*руб[./]?\s*м[²2]',
            r'(\d+)\s*руб[./]?\s*кв[./]?м',
            r'(\d+)\s*руб[./]?\s*за\s*м[²2]',
            r'от\s*(\d+)\s*руб',
            r'(\d+)\s*руб[./]?\s*м²',
            r'(\d+)\s*руб[./]?\s*за\s*кв[./]?м',
            r'стоимость[:\s]*(\d+)\s*руб',
            r'цена[:\s]*(\d+)\s*руб',
            r'(\d+)\s*руб[./]?\s*за\s*м²',
            r'от\s*(\d+)\s*руб[./]?\s*м²'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                try:
                    price = int(match)
                    # Расширенный диапазон для БТИ услуг
                    if 50 <= price <= 800:  # Разумный диапазон для БТИ
                        prices.append(price)
                        logger.debug(f"Found price: {price} in text: {full_text[:100]}...")
                except ValueError:
                    continue
    
    # Убираем дубликаты и сортируем
    unique_prices = list(set(prices))
    unique_prices.sort()
    
    logger.info(f"Parsed prices: {unique_prices}")
    return unique_prices

def calculate_bti_prices(area: float) -> dict:
    """Шаг 2: Расчет карточки БТИ"""
    measurements_price = area * CRPTI_COEFFICIENTS['coefficient_measurements']
    tech_price = area * CRPTI_COEFFICIENTS['coefficient_tech']
    total_price = measurements_price + tech_price
    
    return {
        "measurements": round(measurements_price, 2),
        "techpassport_task": round(tech_price, 2),
        "total": round(total_price, 2)
    }

def calculate_competitor_prices(competitor_prices: list) -> dict:
    """Шаг 3: Расчет карточки конкурентов (улучшенный)"""
    if not competitor_prices:
        logger.warning("No competitor prices, using default")
        median_price = 150  # Дефолтная цена
    else:
        median_price = statistics.median(competitor_prices)
        logger.info(f"Competitor prices: {competitor_prices}, median: {median_price}")
    
    # Применяем НДС (22%) и прибыль (10%) = 1.22 * 1.10 = 1.342
    final_price = median_price * 1.342
    
    return {
        "median_price": round(median_price, 2),
        "price": round(final_price, 2),
        "raw_prices": competitor_prices
    }

def calculate_recommended_price(bti_total: float, competitor_price: float) -> dict:
    """Шаг 4: Расчет рекомендованной цены"""
    # Рекомендуемая цена между БТИ и конкурентами
    recommended = (bti_total + competitor_price) / 2
    
    # Убеждаемся, что она немного выше БТИ, но не выше конкурентов
    recommended = max(bti_total * 1.05, min(recommended, competitor_price * 0.95))
    
    return {
        "price": round(recommended, 2)
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    user_data[user_id] = {
        'step': 'waiting_cadastral',
        'cadastral_number': None,
        'address': None,
        'area': None,
        'build_year': None,
        'materials': None,
        'room_type': None,
        'message_id': None,
        'pricing_data': None  # Добавляем для хранения данных о ценах
    }
    
    await update.message.reply_text(
        "🏠 Привет! Я бот для расчёта стоимости БТИ с тремя карточками цен.\n\n"
        "Введите кадастровый номер (например, 77:09:0001013:1087)."
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    logger.info(f"Message from {user_id}: '{text}'")
    
    if user_id not in user_data:
        user_data[user_id] = {
            'step': 'waiting_cadastral',
            'cadastral_number': None,
            'address': None,
            'area': None,
            'build_year': None,
            'materials': None,
            'room_type': None,
            'message_id': None,
            'pricing_data': None
        }
    
    current_step = user_data[user_id].get('step', 'waiting_cadastral')
    
    if current_step == 'waiting_cadastral':
        if re.match(r'^\d{1,3}:\d{1,3}:\d{1,10}:\d{1,6}$', text):
            logger.info(f"🔢 Обнаружен кадастровый номер: {text}")
            await update.message.reply_text(f"🔍 Ищу данные по кадастру {text} в Росреестре...")
            
            try:
                # Шаг 1: Получаем данные из Госреестра (синхронно)
                reestr_data = fetch_reestr_data(text, "cadastral")
                logger.info(f"📊 Данные из Росреестра: {reestr_data}")
                
                if not reestr_data or not reestr_data.get('address'):
                    await update.message.reply_text("❌ Объект не найден в Росреестре. Проверьте кадастровый номер.")
                    return
                
                if not reestr_data.get('area'):
                    await update.message.reply_text("❌ Не удалось определить площадь объекта.")
                    return
                
                # Сохраняем данные
                user_data[user_id].update({
                    'cadastral_number': text,
                    'address': reestr_data.get('address'),
                    'area': reestr_data.get('area'),
                    'build_year': reestr_data.get('build_year'),
                    'materials': reestr_data.get('materials'),
                    'room_type': reestr_data.get('room_type')
                })
                
                # Показываем найденные данные
                message = f"""✅ **Найдены данные из Росреестра:**

📍 **Адрес:** {reestr_data.get('address', 'Не указан')}
📐 **Площадь:** {reestr_data.get('area', 'Не указана')} м²
📅 **Год постройки:** {reestr_data.get('build_year', 'Не указан')}
🧱 **Материал стен:** {reestr_data.get('materials', 'Не указан')}
🏢 **Тип помещения:** {reestr_data.get('room_type', 'Не указан')}

**Данные верны?**"""
                
                keyboard = [
                    [InlineKeyboardButton("✅ Да, верно", callback_data="verify_yes")],
                    [InlineKeyboardButton("❌ Нет, исправить", callback_data="verify_no")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                sent_message = await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
                user_data[user_id]['message_id'] = sent_message.message_id
                
            except Exception as e:
                logger.error(f"Ошибка получения данных: {e}")
                await update.message.reply_text("❌ Произошла ошибка при получении данных. Попробуйте позже.")
        else:
            await update.message.reply_text("❓ Введите кадастровый номер или используйте /start")
    else:
        await update.message.reply_text("❓ Введите кадастровый номер или используйте /start")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "verify_yes":
        await query.edit_message_text("✅ Данные приняты. Рассчитываем три карточки цен...")
        
        try:
            # Получаем данные пользователя
            area = user_data[user_id].get('area')
            address = user_data[user_id].get('address')
            build_year = user_data[user_id].get('build_year')
            materials = user_data[user_id].get('materials')
            room_type = user_data[user_id].get('room_type')
            
            if not area:
                await query.edit_message_text("❌ Не удалось определить площадь объекта.")
                return
            
            # Шаг 2: Расчет карточки БТИ
            bti_prices = calculate_bti_prices(area)
            
            # Шаг 3: Поиск цен конкурентов
            competitor_prices_list = search_competitor_prices(address or "Москва", area)
            competitor_prices = calculate_competitor_prices(competitor_prices_list)
            
            # Шаг 4: Расчет рекомендованной цены
            recommended_prices = calculate_recommended_price(
                bti_prices['total'], 
                competitor_prices['price']
            )
            
            # Сохраняем данные о ценах для использования в коммерческом предложении
            user_data[user_id]['pricing_data'] = {
                'bti_total': bti_prices['total'],
                'bti_measurements': bti_prices['measurements'],
                'bti_tech': bti_prices['techpassport_task'],
                'competitor_price': competitor_prices['price'],
                'recommended_price': recommended_prices['price'],
                'area': area
            }
            
            # Шаг 5: Формируем три карточки
            message = f"""📊 **ТРИ КАРТОЧКИ ЦЕН** для {area} м² ({room_type}, {materials}, {build_year} г.):

��️ **КАРТОЧКА 1: БТИ (официальные тарифы)**
• Обмеры: {bti_prices['measurements']:,.0f} руб.
• Техпаспорт + задание: {bti_prices['techpassport_task']:,.0f} руб.
• **Итого БТИ: {bti_prices['total']:,.0f} руб.**

🏢 **КАРТОЧКА 2: Конкуренты (рыночные цены)**
• Медиана конкурентов: {statistics.median(competitor_prices_list) if competitor_prices_list else 150:,.0f} руб/м²
• С НДС и прибылью: **{competitor_prices['price']:,.0f} руб.**

⭐ **КАРТОЧКА 3: Рекомендуемая цена**
• Оптимальная цена: **{recommended_prices['price']:,.0f} руб.**

**Коэффициенты CRPTI (обновлены {CRPTI_COEFFICIENTS['last_updated']}):**
• Обмеры: {CRPTI_COEFFICIENTS['coefficient_measurements']} руб/м²
• Техпаспорт: {CRPTI_COEFFICIENTS['coefficient_tech']} руб/м²"""
            
            keyboard = [
                [InlineKeyboardButton("📄 Скачать PDF", callback_data="download_pdf")],
                [InlineKeyboardButton("📝 Коммерческое предложение", callback_data="generate_proposal")],
                [InlineKeyboardButton("📞 Заказать услугу", callback_data="order_service")],
                [InlineKeyboardButton("🔄 Новый расчёт", callback_data="new_calculation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Ошибка расчета цен: {e}")
            await query.edit_message_text("❌ Произошла ошибка при расчете цен. Попробуйте позже.")
        
    elif data == "verify_no":
        await query.edit_message_text("❌ Данные отклонены. Введите кадастровый номер заново.")
        user_data[user_id]['step'] = 'waiting_cadastral'
    
    elif data == "download_pdf":
        await query.edit_message_text("📄 PDF будет сгенерирован и отправлен в ближайшее время.")
    
    elif data == "generate_proposal":
        await query.edit_message_text("�� Генерирую коммерческое предложение...")
        
        try:
            # Получаем данные об объекте
            object_data = {
                'address': user_data[user_id].get('address'),
                'area': user_data[user_id].get('area'),
                'build_year': user_data[user_id].get('build_year'),
                'materials': user_data[user_id].get('materials'),
                'room_type': user_data[user_id].get('room_type')
            }
            
            # Получаем данные о ценах
            pricing_cards = user_data[user_id].get('pricing_data', {})
            
            if not pricing_cards:
                await query.edit_message_text("❌ Данные о ценах не найдены. Сначала выполните расчет.")
                return
            
            # Генерируем коммерческое предложение через GPT
            proposal = generate_commercial_proposal(object_data, pricing_cards)
            
            # Отправляем коммерческое предложение
            keyboard = [
                [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_manager")],
                [InlineKeyboardButton("🔄 Новый расчёт", callback_data="new_calculation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📝 **КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ**\n\n{proposal}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации коммерческого предложения: {e}")
            await query.edit_message_text("❌ Произошла ошибка при генерации предложения. Попробуйте позже.")
    
    elif data == "order_service" or data == "contact_manager":
        await query.edit_message_text("📞 Спасибо за заказ! Менеджер свяжется с вами в течение 15 минут.")
    
    elif data == "new_calculation":
        await query.edit_message_text("🔄 Начинаем новый расчёт. Введите кадастровый номер:")
        user_data[user_id]['step'] = 'waiting_cadastral'


def initialize_bot():
    """Инициализация бота и постоянного event loop."""
    global application
    if _background_loop is None:
        _start_background_loop()
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return False
    
    try:
        application = Application.builder().token(bot_token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        application.add_error_handler(error_handler)
        
        # Инициализируем и запускаем PTB приложение на фоне loop'а
        if not getattr(application, "_initialized", False):
            _run_coro(application.initialize())
        if not getattr(application, "_running", False):
            _run_coro(application.start())
        logger.info("Bot initialized and started on background loop")
        return True
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'message': 'Bot is running'})

@app.route('/', methods=['POST'])
def webhook():
    """Webhook endpoint для Telegram"""
    try:
        if application is None or _background_loop is None:
            if not initialize_bot():
                return jsonify({'error': 'Failed to initialize bot'}), 500
        
        update_data = request.get_json()
        if not update_data:
            return jsonify({'error': 'No JSON data'}), 400
        
        if 'update_id' not in update_data:
            logger.warning("No update_id in webhook data")
            return jsonify({'status': 'OK'})
        
        try:
            update = Update.de_json(update_data, application.bot)
            if update:
                # Планируем обработку в постоянном loop
                _run_coro(application.process_update(update))
                logger.info("Update processed successfully")
            return jsonify({'status': 'OK'})
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return jsonify({'error': f'Error processing webhook: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Локальный запуск Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)


def handler(event, context):
    """
    Yandex Cloud Function compatible handler for app.py compatibility
    """
    try:
        # Parse the event body
        body = event.get('body', '')
        if not body:
            return {'statusCode': 400, 'body': 'No body provided'}
        
        # Parse JSON from body
        try:
            update_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {'statusCode': 400, 'body': 'Invalid JSON'}
        
        # Process the update using our existing webhook logic
        if application is None or _background_loop is None:
            if not initialize_bot():
                return {'statusCode': 500, 'body': 'Failed to initialize bot'}
        
        if 'update_id' not in update_data:
            logger.warning("No update_id in webhook data")
            return {'statusCode': 200, 'body': 'OK'}
        
        try:
            update = Update.de_json(update_data, application.bot)
            if update:
                # Планируем обработку в постоянном loop
                _run_coro(application.process_update(update))
                logger.info("Update processed successfully")
            return {'statusCode': 200, 'body': 'OK'}
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {'statusCode': 500, 'body': f'Error processing webhook: {str(e)}'}
            
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        return {'statusCode': 500, 'body': str(e)}
