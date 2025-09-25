#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import re
import requests
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8430779813:AAGLaNzplbp9v0ySUi-FxTm1ajEREQYiJ5o"
ADMIN_IDS = [5265534096]
SERPRIVER_API_KEY = "S4CV0-4XX9A-8WVE2-XD7E9-X704Z"

# Хранение состояний пользователей
user_data = {}

class EnhancedDatabase:
    def __init__(self, db_path="zamerprobti.db"):
        self.db_path = db_path
        self.init_db()
        self.init_coefficients()
        self.init_competitors()
    
    def init_db(self):
        """Инициализация базы данных с расширенной схемой"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Основная таблица измерений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                address TEXT,
                room_type TEXT,
                area REAL,
                build_year INTEGER,
                materials TEXT,
                cadastral_number TEXT,
                market_price REAL,
                serp_data TEXT,
                search_type TEXT,
                bti_cost REAL,
                c_base REAL,
                c_base_source TEXT,
                c_base_note TEXT,
                year_source TEXT,
                s_itog REAL,
                k_region REAL,
                k_iznos REAL,
                k_nazn REAL,
                k_dop REAL,
                total_coefficient REAL,
                price_online REAL,
                price_plan REAL,
                price_on_site REAL,
                price_full_package REAL,
                competitor_median REAL,
                competitor_delta_percent REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица коэффициентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coefficients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                c_base REAL,
                k_region REAL,
                k_iznos_min REAL,
                k_iznos_max REAL,
                k_nazn REAL,
                k_dop REAL,
                source TEXT,
                last_updated TIMESTAMP,
                note TEXT
            )
        ''')
        
        # Таблица конкурентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                domains TEXT,
                selectors TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Таблица цен конкурентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor TEXT,
                region TEXT,
                service_type TEXT,
                price REAL,
                currency TEXT,
                url TEXT,
                last_checked TIMESTAMP,
                reliability_score REAL
            )
        ''')
        
        # Таблица стратегий ценообразования
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pricing_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                service_type TEXT,
                target_margin REAL,
                min_price REAL,
                max_price REAL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_coefficients(self):
        """Инициализация коэффициентов для Москвы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже данные
        cursor.execute("SELECT COUNT(*) FROM coefficients WHERE region = 'Moscow'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO coefficients (region, c_base, k_region, k_iznos_min, k_iznos_max, k_nazn, k_dop, source, last_updated, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Moscow', 1500.0, 1.0, 0.5, 1.1, 1.0, 1.0,
                'coefficients_db_v2025-09-22', datetime.now().isoformat(),
                'Default coefficients for Moscow region'
            ))
        
        conn.commit()
        conn.close()
    
    def init_competitors(self):
        """Инициализация списка конкурентов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        competitors = [
            ('BTE', 'bte.ru', '{"online": ".price-online", "plan": ".price-plan", "on_site": ".price-on-site", "full": ".price-full"}', 1),
            ('CompA', 'comp-a.ru', '{"online": ".price", "plan": ".price", "on_site": ".price", "full": ".price"}', 1),
            ('CompB', 'comp-b.ru', '{"online": ".price", "plan": ".price", "on_site": ".price", "full": ".price"}', 1),
            ('CompC', 'comp-c.ru', '{"online": ".price", "plan": ".price", "on_site": ".price", "full": ".price"}', 1)
        ]
        
        for name, domains, selectors, is_active in competitors:
            cursor.execute('''
                INSERT OR IGNORE INTO competitor_list (name, domains, selectors, is_active)
                VALUES (?, ?, ?, ?)
            ''', (name, domains, selectors, is_active))
        
        conn.commit()
        conn.close()
    
    def get_coefficients(self, region="Moscow"):
        """Получение коэффициентов для региона"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c_base, k_region, k_iznos_min, k_iznos_max, k_nazn, k_dop, source, last_updated, note
            FROM coefficients WHERE region = ?
        ''', (region,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'c_base': result[0],
                'k_region': result[1],
                'k_iznos_min': result[2],
                'k_iznos_max': result[3],
                'k_nazn': result[4],
                'k_dop': result[5],
                'source': result[6],
                'last_updated': result[7],
                'note': result[8]
            }
        return None
    
    def add_measurement(self, user_id, address, room_type, area, build_year, materials, 
                       cadastral_number=None, market_price=None, serp_data=None, search_type=None,
                       bti_cost=None, c_base=None, c_base_source=None, c_base_note=None,
                       year_source=None, s_itog=None, k_region=None, k_iznos=None, k_nazn=None,
                       k_dop=None, total_coefficient=None, price_online=None, price_plan=None,
                       price_on_site=None, price_full_package=None, competitor_median=None,
                       competitor_delta_percent=None):
        """Добавление измерения с полной информацией"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO measurements (
                user_id, address, room_type, area, build_year, materials,
                cadastral_number, market_price, serp_data, search_type,
                bti_cost, c_base, c_base_source, c_base_note, year_source,
                s_itog, k_region, k_iznos, k_nazn, k_dop, total_coefficient,
                price_online, price_plan, price_on_site, price_full_package,
                competitor_median, competitor_delta_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, address, room_type, area, build_year, materials,
            cadastral_number, market_price, serp_data, search_type,
            bti_cost, c_base, c_base_source, c_base_note, year_source,
            s_itog, k_region, k_iznos, k_nazn, k_dop, total_coefficient,
            price_online, price_plan, price_on_site, price_full_package,
            competitor_median, competitor_delta_percent
        ))
        
        conn.commit()
        conn.close()

# Инициализация базы данных
db = EnhancedDatabase()

def search_cadastre_data(query, search_type="cadastral"):
    """Поиск кадастровых данных через SerpRiver API"""
    api_url = "https://serpriver.ru/api/search.php"
    
    if search_type == "cadastral":
        search_query = query
    else:
        search_query = f"{query} кадастр"
    
    payload = {
        "api_key": SERPRIVER_API_KEY,
        "system": "yandex",
        "domain": "ru",
        "query": search_query,
        "result_cnt": 3,
        "lr": 213  # Москва
    }
    
    try:
        logger.info(f"🔍 Начинаем поиск: {query} (тип: {search_type})")
        logger.info("🔄 Отправляем запрос к SerpRiver API...")
        
        response = requests.post(api_url, data=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"📊 Получен ответ от API: {data}")
        
        if data.get('search_metadata', {}).get('status') == 'error':
            error_desc = data.get('search_metadata', {}).get('error_description', 'Unknown error')
            logger.warning(f"⚠️ API ошибка: {error_desc}")
            
            if "maximum bid settings" in error_desc:
                logger.info("↪️ Fallback на Google (минимальные результаты)")
                # Fallback на Google с минимальными результатами
                payload_google = payload.copy()
                payload_google["system"] = "google"
                payload_google["result_cnt"] = 2
                
                response_google = requests.post(api_url, data=payload_google, timeout=30)
                response_google.raise_for_status()
                data = response_google.json()
                logger.info(f"📊 Ответ Google: {data}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка API: {e}")
        return None

def extract_cad_info(snippet):
    """Извлечение информации из сниппета"""
    info = {}
    
    # Площадь - сначала ищем числа с пробелами как разделителями тысяч
    area_patterns = [
        r'(\d{1,3}(?:\s\d{3})*(?:,\d+)?)\s*кв\.?м',
        r'(\d+(?:,\d+)?)\s*м²',
        r'(\d+(?:,\d+)?)\s*кв\.?м'
    ]
    
    for pattern in area_patterns:
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            area_str = match.group(1).replace(' ', '').replace(',', '.')
            try:
                info['area'] = float(area_str)
                break
            except ValueError:
                continue
    
    # Год постройки
    year_match = re.search(r'(\d{4})\s*г\.?', snippet)
    if year_match:
        try:
            info['year'] = int(year_match.group(1))
        except ValueError:
            pass
    
    # Цена
    price_patterns = [
        r'(\d{1,3}(?:\s\d{3})*(?:,\d+)?)\s*руб',
        r'(\d+(?:,\d+)?)\s*млн\s*руб'
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(' ', '').replace(',', '.')
            try:
                price = float(price_str)
                if 'млн' in snippet.lower():
                    price *= 1000000
                info['price'] = price
                break
            except ValueError:
                continue
    
    return info

def calculate_s_itog(area, room_type="другое"):
    """Расчет итоговой учетной площади"""
    # Для упрощения используем основную площадь
    # В реальной системе здесь была бы сложная логика с балконами, лоджиями и т.д.
    return area

def calculate_bti_cost(area, build_year, materials, room_type="другое", is_urgent=False):
    """Расчет стоимости БТИ с коэффициентами и источниками"""
    # Получаем коэффициенты из базы
    coeffs = db.get_coefficients("Moscow")
    if not coeffs:
        logger.error("❌ Коэффициенты не найдены в базе данных")
        return None
    
    # Расчет итоговой площади
    s_itog = calculate_s_itog(area, room_type)
    
    # Базовые коэффициенты
    c_base = coeffs['c_base']
    k_region = coeffs['k_region']
    k_nazn = coeffs['k_nazn']
    k_dop = coeffs['k_dop']
    
    # Коэффициент по площади (скидка за объем)
    if s_itog < 500:
        k_area = 1.0
        area_detail = "Стандартная ставка"
    elif s_itog < 2500:
        k_area = 0.95
        area_detail = "Скидка за объем: -5%"
    else:
        k_area = 0.85
        area_detail = "Скидка за объем: -15%"
    
    # Коэффициент по году постройки
    if build_year < 1980:
        k_iznos = 1.1
        year_detail = "Старый фонд: +10%"
    elif build_year < 2000:
        k_iznos = 1.0
        year_detail = "Стандартная ставка"
    else:
        k_iznos = 0.95
        year_detail = "Новый фонд: -5%"
    
    # Коэффициент по материалу
    material_coeffs = {
        'кирпич': 1.05,
        'бетон': 1.05,
        'монолит': 1.0,
        'дерево': 1.15
    }
    k_material = material_coeffs.get(materials.lower(), 1.0)
    material_detail = f"Материал {materials}: {k_material:.0%}"
    
    # Коэффициент срочности
    k_urgent = 1.2 if is_urgent else 1.0
    urgent_detail = "Экспресс: +20%" if is_urgent else "Стандартный срок"
    
    # Общий коэффициент
    total_coeff = k_area * k_iznos * k_material * k_urgent * k_region * k_nazn * k_dop
    
    # Расчет стоимости
    c_bti = s_itog * c_base * total_coeff
    
    return {
        'c_bti': c_bti,
        's_itog': s_itog,
        'c_base': c_base,
        'c_base_source': coeffs['source'],
        'c_base_note': coeffs['note'],
        'k_area': k_area,
        'k_iznos': k_iznos,
        'k_material': k_material,
        'k_urgent': k_urgent,
        'k_region': k_region,
        'k_nazn': k_nazn,
        'k_dop': k_dop,
        'total_coeff': total_coeff,
        'area_detail': area_detail,
        'year_detail': year_detail,
        'material_detail': material_detail,
        'urgent_detail': urgent_detail
    }

def calculate_package_prices(c_bti, region="Moscow"):
    """Расчет цен по пакетам услуг"""
    # Базовые наценки для Москвы
    if region == "Moscow":
        plan_fee = 1500
        on_site_fee = 4500
        notary_fee = 2000
        admin_fee = 1000
    else:
        plan_fee = 1000
        on_site_fee = 3000
        notary_fee = 1500
        admin_fee = 500
    
    prices = {
        'online': max(c_bti * 1.0, 299),  # Минимум 299 руб
        'plan': c_bti + plan_fee,
        'on_site': c_bti + on_site_fee,
        'full_package': c_bti + plan_fee + on_site_fee + notary_fee + admin_fee
    }
    
    return prices

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("📏 БТИ расчёт", callback_data="order_measurement")],
        [InlineKeyboardButton("📞 Контакты", callback_data="show_contacts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏠 Добро пожаловать в бот расчёта стоимости БТИ!\n\n"
        "Я помогу вам рассчитать стоимость технической инвентаризации "
        "с учётом всех коэффициентов и рыночных данных.\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def order_measurement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало заказа измерения"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔢 По кадастровому номеру", callback_data="search_cadastral")],
        [InlineKeyboardButton("📍 По адресу", callback_data="search_address")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 Выберите способ поиска объекта:",
        reply_markup=reply_markup
    )

async def process_search_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа поиска"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data[user_id] = {'step': 'waiting_cadastral' if query.data == 'search_cadastral' else 'waiting_address'}
    
    if query.data == 'search_cadastral':
        await query.edit_message_text(
            "🔢 Введите кадастровый номер объекта:\n\n"
            "Пример: 77:09:0001013:1087"
        )
    else:
        await query.edit_message_text(
            "📍 Введите адрес объекта:\n\n"
            "Пример: ул. Фестивальная, д. 28, стр. 1, Москва"
        )

async def process_cadastral_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода кадастрового номера"""
    user_id = update.effective_user.id
    cadastral_number = update.message.text.strip()
    
    # Проверка формата кадастрового номера
    if not re.match(r'\d{2}:\d{2}:\d{7}:\d{4}', cadastral_number):
        await update.message.reply_text(
            "❌ Неверный формат кадастрового номера.\n\n"
            "Правильный формат: XX:XX:XXXXXXX:XXXX\n"
            "Пример: 77:09:0001013:1087"
        )
        return
    
    user_data[user_id]['cadastral_number'] = cadastral_number
    user_data[user_id]['search_type'] = 'cadastral'
    
    # Поиск данных через API
    await update.message.reply_text("🔍 Ищем данные по кадастровому номеру...")
    
    api_data = search_cadastre_data(cadastral_number, "cadastral")
    
    if api_data and api_data.get('res'):
        # Извлекаем информацию из результатов
        extracted_info = {}
        for result in api_data['res'][:3]:  # Берем первые 3 результата
            snippet = result.get('snippet', '')
            info = extract_cad_info(snippet)
            extracted_info.update(info)
        
        # Сохраняем извлеченные данные
        user_data[user_id].update(extracted_info)
        user_data[user_id]['serp_data'] = json.dumps(api_data)
        
        # Показываем найденные данные
        message = "✅ Найдены данные:\n\n"
        if extracted_info.get('area'):
            message += f"📐 Площадь: {extracted_info['area']} м²\n"
        if extracted_info.get('year'):
            message += f"📅 Год постройки: {extracted_info['year']}\n"
        if extracted_info.get('price'):
            message += f"💰 Рыночная цена: {extracted_info['price']:,.0f} руб.\n"
        
        if not extracted_info:
            message += "⚠️ Не удалось извлечь данные автоматически.\n"
            message += "Продолжаем с ручным вводом...\n"
        
        message += "\n🏠 Выберите тип помещения:"
        
        keyboard = [
            [InlineKeyboardButton("🏠 Жилое", callback_data="room_type_жилое")],
            [InlineKeyboardButton("🏢 Другое", callback_data="room_type_другое")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        user_data[user_id]['step'] = 'waiting_room_type'
        
    else:
        await update.message.reply_text(
            "❌ Не удалось найти данные по кадастровому номеру.\n\n"
            "Попробуйте ввести данные вручную:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🏠 Жилое", callback_data="room_type_жилое")],
            [InlineKeyboardButton("🏢 Другое", callback_data="room_type_другое")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("🏠 Выберите тип помещения:", reply_markup=reply_markup)
        user_data[user_id]['step'] = 'waiting_room_type'

async def process_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода адреса"""
    user_id = update.effective_user.id
    address = update.message.text.strip()
    
    user_data[user_id]['address'] = address
    user_data[user_id]['search_type'] = 'address'
    
    # Поиск данных через API
    await update.message.reply_text("🔍 Ищем данные по адресу...")
    
    api_data = search_cadastre_data(address, "address")
    
    if api_data and api_data.get('res'):
        # Извлекаем информацию из результатов
        extracted_info = {}
        for result in api_data['res'][:3]:  # Берем первые 3 результата
            snippet = result.get('snippet', '')
            info = extract_cad_info(snippet)
            extracted_info.update(info)
        
        # Сохраняем извлеченные данные
        user_data[user_id].update(extracted_info)
        user_data[user_id]['serp_data'] = json.dumps(api_data)
        
        # Показываем найденные данные
        message = "✅ Найдены данные:\n\n"
        if extracted_info.get('area'):
            message += f"📐 Площадь: {extracted_info['area']} м²\n"
        if extracted_info.get('year'):
            message += f"📅 Год постройки: {extracted_info['year']}\n"
        if extracted_info.get('price'):
            message += f"💰 Рыночная цена: {extracted_info['price']:,.0f} руб.\n"
        
        if not extracted_info:
            message += "⚠️ Не удалось извлечь данные автоматически.\n"
            message += "Продолжаем с ручным вводом...\n"
        
        message += "\n🏠 Выберите тип помещения:"
        
        keyboard = [
            [InlineKeyboardButton("🏠 Жилое", callback_data="room_type_жилое")],
            [InlineKeyboardButton("🏢 Другое", callback_data="room_type_другое")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        user_data[user_id]['step'] = 'waiting_room_type'
        
    else:
        await update.message.reply_text(
            "❌ Не удалось найти данные по адресу.\n\n"
            "Попробуйте ввести данные вручную:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🏠 Жилое", callback_data="room_type_жилое")],
            [InlineKeyboardButton("🏢 Другое", callback_data="room_type_другое")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("🏠 Выберите тип помещения:", reply_markup=reply_markup)
        user_data[user_id]['step'] = 'waiting_room_type'

async def process_room_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа помещения"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    room_type = query.data.split('_')[-1]
    user_data[user_id]['room_type'] = room_type
    user_data[user_id]['step'] = 'waiting_area'
    
    await query.edit_message_text(
        "📐 Введите площадь помещения в квадратных метрах:\n\n"
        "Пример: 2000"
    )

async def process_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода площади"""
    user_id = update.effective_user.id
    
    try:
        area = float(update.message.text.replace(',', '.'))
        if area <= 0:
            raise ValueError()
        
        user_data[user_id]['area'] = area
        user_data[user_id]['step'] = 'waiting_build_year'
        
        await update.message.reply_text(
            "📅 Введите год постройки:\n\n"
            "Пример: 1955"
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат площади.\n\n"
            "Введите число больше 0.\n"
            "Пример: 2000"
        )

async def process_build_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода года постройки"""
    user_id = update.effective_user.id
    
    try:
        year = int(update.message.text)
        if year < 1800 or year > 2025:
            raise ValueError()
        
        user_data[user_id]['build_year'] = year
        user_data[user_id]['year_source'] = 'user_input'
        user_data[user_id]['step'] = 'waiting_materials'
        
        await update.message.reply_text(
            "🧱 Выберите материал стен:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🧱 Кирпич", callback_data="material_кирпич")],
            [InlineKeyboardButton("🏗️ Бетон", callback_data="material_бетон")],
            [InlineKeyboardButton("🏢 Монолит", callback_data="material_монолит")],
            [InlineKeyboardButton("🌲 Дерево", callback_data="material_дерево")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("🧱 Выберите материал стен:", reply_markup=reply_markup)
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат года.\n\n"
            "Введите год постройки (например: 1955)"
        )

async def process_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора материала стен"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    materials = query.data.split('_')[-1]
    user_data[user_id]['materials'] = materials
    user_data[user_id]['step'] = 'waiting_urgent'
    
    await query.edit_message_text(
        "⏰ Нужна ли срочная оценка?\n\n"
        "Срочная оценка (+20% к стоимости) выполняется в течение 1-2 дней."
    )
    
    keyboard = [
        [InlineKeyboardButton("⚡ Срочно", callback_data="urgent_yes")],
        [InlineKeyboardButton("📅 Не срочно", callback_data="urgent_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⏰ Нужна ли срочная оценка?\n\n"
        "Срочная оценка (+20% к стоимости) выполняется в течение 1-2 дней.",
        reply_markup=reply_markup
    )

async def process_urgent_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора срочности"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    is_urgent = query.data == 'urgent_yes'
    user_data[user_id]['is_urgent'] = is_urgent
    
    # Получаем данные пользователя
    data = user_data.get(user_id, {})
    
    # Расчет стоимости БТИ
    calculation = calculate_bti_cost(
        data.get('area', 0),
        data.get('build_year', 2000),
        data.get('materials', 'кирпич'),
        data.get('room_type', 'другое'),
        is_urgent
    )
    
    if not calculation:
        await query.edit_message_text("❌ Ошибка при расчете стоимости. Попробуйте позже.")
        return
    
    # Расчет цен по пакетам
    package_prices = calculate_package_prices(calculation['c_bti'])
    
    # Формируем сообщение с результатами
    message = "📊 **РАСЧЕТ СТОИМОСТИ БТИ**\n\n"
    
    # Основные параметры
    message += f"🏠 **Объект:**\n"
    message += f"📍 Адрес: {data.get('address', 'Не указан')}\n"
    message += f"🔢 Кадастр: {data.get('cadastral_number', 'Не указан')}\n"
    message += f"📐 Площадь: {data.get('area', 0):.1f} м²\n"
    message += f"📅 Год: {data.get('build_year', 2000)}\n"
    message += f"🧱 Материал: {data.get('materials', 'кирпич')}\n"
    message += f"🏢 Тип: {data.get('room_type', 'другое')}\n\n"
    
    # Детализация расчета
    message += f"💰 **Базовая ставка:** {calculation['c_base']:,.0f} руб/м²\n"
    message += f"📋 Источник: {calculation['c_base_source']}\n"
    message += f"📝 Примечание: {calculation['c_base_note']}\n\n"
    
    message += f"📊 **Коэффициенты:**\n"
    message += f"• {calculation['area_detail']}\n"
    message += f"• {calculation['year_detail']}\n"
    message += f"• {calculation['material_detail']}\n"
    message += f"• {calculation['urgent_detail']}\n"
    message += f"• Общий коэффициент: {calculation['total_coeff']:.3f}\n\n"
    
    message += f"💵 **Стоимость БТИ:** {calculation['c_bti']:,.0f} руб.\n\n"
    
    # Цены по пакетам
    message += f"📦 **ПАКЕТЫ УСЛУГ:**\n"
    message += f"🌐 Онлайн-оценка: {package_prices['online']:,.0f} руб.\n"
    message += f"📋 План БТИ: {package_prices['plan']:,.0f} руб.\n"
    message += f"🚗 Выезд мастера: {package_prices['on_site']:,.0f} руб.\n"
    message += f"📄 Полный пакет: {package_prices['full_package']:,.0f} руб.\n\n"
    
    message += "⚠️ *Это предварительная оценка. Точная стоимость определяется в БТИ.*"
    
    # Сохраняем в базу данных
    try:
        db.add_measurement(
            user_id=user_id,
            address=data.get('address', ''),
            room_type=data.get('room_type', 'другое'),
            area=data.get('area', 0),
            build_year=data.get('build_year', 2000),
            materials=data.get('materials', 'кирпич'),
            cadastral_number=data.get('cadastral_number'),
            market_price=data.get('price'),
            serp_data=data.get('serp_data'),
            search_type=data.get('search_type'),
            bti_cost=calculation['c_bti'],
            c_base=calculation['c_base'],
            c_base_source=calculation['c_base_source'],
            c_base_note=calculation['c_base_note'],
            year_source=data.get('year_source'),
            s_itog=calculation['s_itog'],
            k_region=calculation['k_region'],
            k_iznos=calculation['k_iznos'],
            k_nazn=calculation['k_nazn'],
            k_dop=calculation['k_dop'],
            total_coefficient=calculation['total_coeff'],
            price_online=package_prices['online'],
            price_plan=package_prices['plan'],
            price_on_site=package_prices['on_site'],
            price_full_package=package_prices['full_package']
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения в БД: {e}")
    
    # Очищаем данные пользователя
    if user_id in user_data:
        del user_data[user_id]
    
    await query.edit_message_text(message, parse_mode='Markdown')

async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ контактной информации"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📞 **КОНТАКТЫ**\n\n"
        "🏢 БТИ Москвы\n"
        "📱 Телефон: +7 (495) 123-45-67\n"
        "🌐 Сайт: www.bti-moscow.ru\n"
        "📍 Адрес: ул. Примерная, д. 1, Москва\n\n"
        "🕒 Режим работы:\n"
        "Пн-Пт: 9:00 - 18:00\n"
        "Сб: 10:00 - 15:00\n"
        "Вс: выходной"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    logger.info(f"msg from {user_id}: '{text}'")
    logger.info(f"current step for {user_id}: {user_data.get(user_id, {}).get('step', 'main_menu')}")
    
    # Проверяем, не является ли сообщение кадастровым номером
    if re.match(r'\d{2}:\d{2}:\d{7}:\d{4}', text):
        logger.info(f"🔢 Обнаружен кадастровый номер: {text}")
        user_data[user_id] = {'step': 'waiting_cadastral', 'cadastral_number': text, 'search_type': 'cadastral'}
        await process_cadastral_number(update, context)
        return
    
    # Обработка по шагам
    if user_id not in user_data:
        user_data[user_id] = {'step': 'main_menu'}
    
    step = user_data[user_id]['step']
    
    if step == 'waiting_area':
        await process_area(update, context)
    elif step == 'waiting_build_year':
        await process_build_year(update, context)
    else:
        # Возвращаемся в главное меню
        keyboard = [
            [InlineKeyboardButton("📏 БТИ расчёт", callback_data="order_measurement")],
            [InlineKeyboardButton("📞 Контакты", callback_data="show_contacts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    """Основная функция"""
    print("🤖 Бот запущен с полной системой БТИ!")
    
    # Создание приложения
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(order_measurement, pattern="^order_measurement$"))
    app.add_handler(CallbackQueryHandler(process_search_type, pattern="^search_"))
    app.add_handler(CallbackQueryHandler(process_room_type, pattern="^room_type_"))
    app.add_handler(CallbackQueryHandler(process_materials, pattern="^material_"))
    app.add_handler(CallbackQueryHandler(process_urgent_option, pattern="^urgent_"))
    app.add_handler(CallbackQueryHandler(show_contacts, pattern="^show_contacts$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    # Запуск бота
    app.run_polling()

if __name__ == '__main__':
    main()


# Flask webhook для Cloud Run
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Глобальная переменная для приложения
application = None

def main():
    """Основная функция запуска бота"""
    global application
    
    # Инициализация бота
    application = Application.builder().token(os.environ.get('BOT_TOKEN')).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(process_search_type))
    
    logger.info('🚀 BTI Bot запущен!')
    
    # НЕ запускаем polling, так как используем webhook

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['POST'])
def webhook():
    """Webhook для Cloud Run"""
    try:
        # Ленивая инициализация бота при первом запросе
        global application
        if application is None:
            logger.info('🚀 Инициализация BTI Bot при первом запросе...')
            main()  # Инициализируем бота только при первом запросе
            
        # Проверяем, что application инициализирован
        if application is None:
            logger.error('Application not initialized')
            return jsonify({"error": "Application not initialized"}), 500
            
        update = Update.de_json(request.get_json(), application.bot)
        application.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f'🚀 Запуск BTI Bot на порту {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
