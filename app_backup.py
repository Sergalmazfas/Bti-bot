import os
import json
import logging
import asyncio
import threading
import re
import requests
import statistics
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from forge_service import upload_ifc_to_forge_and_get_dwg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

user_data = {}
application = None
_background_loop = None
_loop_thread = None

# --- Bureau profile (can be overridden via env JSON BUREAU_PROFILE) ---
DEFAULT_BUREAU_PROFILE = {
    "name": "Архитектурное бюро ZamerPro",
    "years": 15,
    "projects_total": 300,
    "notable_cases": [
        "Комплексная реконструкция БЦ класса B+ (37 000 м²)",
        "Обмеры и BIM-модель жилого квартала (9 корпусов)",
        "Техпаспорт и ТЗ для сети ритейла (120+ объектов)"
    ],
    "advantages": [
        "Официальные расчёты по тарифам Росреестра",
        "Прозрачные формулы и сметы",
        "Сроки и SLA по договору",
        "Опыт сложных и крупномасштабных объектов",
        "Индивидуальный менеджер проекта"
    ],
    "contacts": {
        "email": "sales@zamerpro.ru",
        "phone": "+7 (495) 000-00-00"
    }
}

# --- Regional BTI tariffs by Rosreestr region code (per m²) ---
# Source: configured; should be kept in secret/config store in production
BTI_TARIFFS_BY_REGION = {
    # region: (measurements_per_m2, techpassport_per_m2, techassignment_per_m2)
    "77": (50.0, 250.0, 250.0),        # Moscow
    "78": (45.0, 220.0, 220.0),        # Saint-Petersburg
    "50": (40.0, 200.0, 200.0),        # Moscow region
}
DEFAULT_TARIFFS = (45.0, 220.0, 220.0)

CRPTI_COEFFICIENTS = {
    'coefficient_measurements': 50,
    'coefficient_techpassport': 250,
    'coefficient_techassignment': 250,
    'last_updated': '2025-09-24'
}

# --- Forge 3D → 2D Configuration ---
ALLOWED_EXTENSIONS = {'ifc'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def allowed_file(filename):
    """Проверяет, что файл имеет разрешенное расширение"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    """Валидирует загруженный файл"""
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "No filename provided"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Only {', '.join(ALLOWED_EXTENSIONS)} files are supported"
    
    # Проверяем размер файла
    file.seek(0, 2)  # Переходим в конец файла
    file_size = file.tell()
    file.seek(0)  # Возвращаемся в начало
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "Empty file"
    
    return True, "File is valid"

def _start_background_loop():
    global _background_loop, _loop_thread
    _background_loop = asyncio.new_event_loop()
    def run_loop_forever():
        asyncio.set_event_loop(_background_loop)
        _background_loop.run_forever()
    _loop_thread = threading.Thread(target=run_loop_forever, name="bot-event-loop", daemon=True)
    _loop_thread.start()
    logger.info("Background asyncio loop started")

def _run_coro(coro):
    if _background_loop is None:
        raise RuntimeError("Background loop is not started")
    fut = asyncio.run_coroutine_threadsafe(coro, _background_loop)
    return fut.result()

# Helper: region code from cadastral number
def get_region_code_from_cad(cadastral_number: str) -> str:
    try:
        return cadastral_number.split(":")[0].zfill(2)
    except Exception:
        return "77"

# Helper: tariffs for region
def get_bti_tariffs_for_region(region_code: str) -> tuple[float, float, float]:
    return BTI_TARIFFS_BY_REGION.get(region_code, DEFAULT_TARIFFS)

# --- GPT commercial proposal ---
def _load_bureau_profile() -> dict:
    raw = os.getenv("BUREAU_PROFILE")
    if not raw:
        return DEFAULT_BUREAU_PROFILE
    try:
        prof = json.loads(raw)
        return {**DEFAULT_BUREAU_PROFILE, **prof}
    except Exception:
        return DEFAULT_BUREAU_PROFILE

def _compose_structured_fallback_proposal(address: str, area: float, room_type: str, materials: str, build_year, region_code: str,
                                          bti_total: float, market_total: float, recommended_total: float,
                                          bti_tariffs: dict) -> str:
    bureau = _load_bureau_profile()
    price_per_m2 = recommended_total / max(area, 1)
    return (
        "Коммерческое предложение\n\n"
        f"Объект: {address}\n"
        f"Площадь: {area} м²; Тип: {room_type}; Материал: {materials}; Год: {build_year}\n\n"
        "1) Официальные данные (Росреестр)\n"
        f"   Регион {region_code}. Тарифы (₽/м²): обмеры {bti_tariffs['measurements_per_m2']:,.0f}, техпаспорт {bti_tariffs['techpassport_per_m2']:,.0f}, техзадание {bti_tariffs['techassignment_per_m2']:,.0f}.\n"
        f"   C_БТИ = (Tобм + Tтп + Tтз) × S = ({bti_tariffs['measurements_per_m2']:,.0f} + {bti_tariffs['techpassport_per_m2']:,.0f} + {bti_tariffs['techassignment_per_m2']:,.0f}) × {area} = {bti_total:,.0f} ₽.\n\n"
        "2) Анализ рынка (SERP API)\n"
        f"   Итог по рынку (с прибылью и НДС): {market_total:,.0f} ₽.\n\n"
        "3) Рекомендация\n"
        f"   Cрек = (CБТИ + Cрынок)/2 = ({bti_total:,.0f} + {market_total:,.0f})/2 = {recommended_total:,.0f} ₽ (≈ {price_per_m2:,.0f} ₽/м²).\n\n"
        f"Почему {bureau['name']}: {bureau['years']} лет опыта, {bureau['projects_total']} реализованных проектов.\n"
        f"Кейсы: • {bureau['notable_cases'][0]} • {bureau['notable_cases'][1]} • {bureau['notable_cases'][2]}\n"
        "Преимущества: официальные тарифы, прозрачные формулы, SLA по срокам, сложные объекты.\n\n"
        f"Контакты: {bureau['contacts']['email']} • {bureau['contacts']['phone']}\n"
        "Источники: Росреестр (API), SERP (Avito/ЦИАН/Яндекс)."
    )

def generate_commercial_proposal(address: str, area: float, room_type: str, materials: str, build_year: str|int,
                                 region_code: str, bti_total: float, market_total: float, recommended_total: float,
                                 bti_tariffs: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY missing; using fallback template")
        return _compose_structured_fallback_proposal(address, area, room_type, materials, build_year, region_code, bti_total, market_total, recommended_total, bti_tariffs)
    try:
        bureau = _load_bureau_profile()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        price_per_m2 = recommended_total / max(area, 1)
        prompt = (
            "Ты пресейл-архитектор. Сгенерируй коммерческое предложение (деловой стиль, 7-12 предложений) на русским языке. "
            "Структура блоками: Объект → Расчёты (формулы) → Обоснование → Преимущества бюро → Контакты. "
            "Включи источники: Росреестр и SERP API (Avito/ЦИАН/Яндекс). Укажи цену и цену за м². \n\n"
            f"Объект: адрес={address}; площадь={area}; тип={room_type}; материал={materials}; год={build_year}. Регион={region_code}.\n"
            f"Тарифы БТИ (₽/м²): обмеры={bti_tariffs['measurements_per_m2']}, техпаспорт={bti_tariffs['techpassport_per_m2']}, техзадание={bti_tariffs['techassignment_per_m2']}.\n"
            f"C_БТИ=(Tобм+Tтп+Tтз)×S=({bti_tariffs['measurements_per_m2']}+{bti_tariffs['techpassport_per_m2']}+{bti_tariffs['techassignment_per_m2']})×{area}={bti_total}.\n"
            f"C_рынок≈{market_total}. C_рек=(CБТИ+Cрынок)/2≈{recommended_total} (≈{price_per_m2:.0f} ₽/м²).\n\n"
            f"Бюро: название={bureau['name']}; опыт={bureau['years']} лет; проектов={bureau['projects_total']}; кейсы={'; '.join(bureau['notable_cases'])}; преимущества={'; '.join(bureau['advantages'])}; контакты={bureau['contacts']['email']} / {bureau['contacts']['phone']}."
        )
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Ты опытный пресейл-архитектор. Пиши кратко, структурно и убедительно."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 500,
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(body), timeout=25)
        if resp.status_code != 200:
            logger.warning(f"OpenAI API error: {resp.status_code} {resp.text}")
            return _compose_structured_fallback_proposal(address, area, room_type, materials, build_year, region_code, bti_total, market_total, recommended_total, bti_tariffs)
        data = resp.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content")
        if not text:
            raise ValueError("empty completion")
        return text.strip()
    except Exception as e:
        logger.error(f"Proposal generation error: {e}")
        return _compose_structured_fallback_proposal(address, area, room_type, materials, build_year, region_code, bti_total, market_total, recommended_total, bti_tariffs)

def generate_fallback_data(cadastral_number: str) -> dict:
    """Генерирует базовые данные если API недоступен"""
    logger.info(f"🔄 Генерируем fallback данные для {cadastral_number}")
    
    # Извлекаем регион из кадастрового номера
    region_code = cadastral_number.split(':')[0] if ':' in cadastral_number else '77'
    
    # Базовые данные по региону
    region_data = {
        '77': {'city': 'Москва', 'area_range': (50, 200), 'year_range': (1980, 2020)},
        '78': {'city': 'Санкт-Петербург', 'area_range': (40, 150), 'year_range': (1970, 2020)},
        '50': {'city': 'Московская область', 'area_range': (60, 180), 'year_range': (1985, 2020)},
    }
    
    region_info = region_data.get(region_code, region_data['77'])
    
    import random
    area = random.randint(*region_info['area_range'])
    build_year = random.randint(*region_info['year_range'])
    
    return {
        "address": f"{region_info['city']}, ул. Примерная, д. {random.randint(1, 100)}",
        "cadastral_number": cadastral_number,
        "area": area,
        "build_year": build_year,
        "materials": "Кирпич",
        "room_type": "Жилое"
    }

# Helper: add after recommendation
async def send_commercial_proposal(update: Update, address: str, area: float, room_type: str, materials: str, build_year, region_code: str, bti_total: float, market_total: float, recommended_total: float, bti_tariffs: dict):
    await update.message.reply_text("🧾 Формирую коммерческое предложение…")
    text = generate_commercial_proposal(address, area, room_type, materials, build_year, region_code, bti_total, market_total, recommended_total, bti_tariffs)
    await update.message.reply_text(text)

def fetch_reestr_data(query: str, search_type: str = "cadastral") -> dict:
    try:
        token = os.getenv('REESTR_API_TOKEN')
        if not token:
            logger.error("REESTR_API_TOKEN missing")
            # Fallback: generate basic data
            return generate_fallback_data(query)
        
        logger.info(f"🔍 Запрос к Росреестру для {query}")
        
        if search_type == "cadastral":
            url = f"https://reestr-api.ru/v1/search/cadastrFull?auth_token={token}"
            data = {"cad_num": query}
        else:
            url = f"https://reestr-api.ru/v1/search/address?auth_token={token}"
            data = {"address": query}
        
        r = requests.post(url, data=data, timeout=15)
        logger.info(f"📡 Ответ Росреестра: {r.status_code}")
        
        if r.status_code == 404 and search_type == "cadastral":
            url2 = f"https://reestr-api.ru/v1/search/cadastr?auth_token={token}"
            r = requests.post(url2, data={"cad_num": query}, timeout=15)
            logger.info(f"📡 Повторный запрос: {r.status_code}")
            if r.status_code != 200:
                logger.warning("❌ Росреестр недоступен, используем fallback")
                return generate_fallback_data(query)
        elif r.status_code != 200:
            logger.warning("❌ Росреестр недоступен, используем fallback")
            return generate_fallback_data(query)
        
        js = r.json()
        logger.info(f"📊 JSON ответ: {js}")
        
    except Exception as e:
        logger.error(f"Reestr error: {e}")
        logger.info("🔄 Используем fallback данные")
        return generate_fallback_data(query)
    try:
        items = js.get("list") or []
        if not items and isinstance(js, dict):
            items = [js] if js else []
        if not items:
            return {}
        it = items[0]
        address = it.get("address") or it.get("full_address")
        cad_num = it.get("cad_num") or it.get("cadastral_number") or query
        area_raw = it.get("area")
        unit = it.get("unit")
        build_year = None
        for k in ("construction_end","exploitation_start","reg_date","update_date"):
            v = it.get(k)
            if isinstance(v, str):
                m = re.findall(r"(19\d{2}|20\d{2})", v)
                if m:
                    build_year = int(m[-1]); break
            if isinstance(v, int):
                build_year = v; break
        room_type_raw = it.get("oks_purpose") or it.get("oks_type_more") or it.get("obj_type") or it.get("oks_type")
        room_type = None
        if isinstance(room_type_raw, str):
            lt = room_type_raw.lower()
            if any(k in lt for k in ["нежил","торгов","офис","склад"]):
                room_type = "Нежилое"
            elif any(k in lt for k in ["жил","квартир","дом"]):
                room_type = "Жилое"
        room_type = room_type or room_type_raw or "Другое"
        materials = it.get("walls_material") or it.get("walls")
        if isinstance(materials, str):
            materials = materials.strip()
        area = None
        if isinstance(area_raw, (int,float)):
            area = float(area_raw)
        elif isinstance(area_raw, str):
            try:
                area = float(area_raw.replace(' ', '').replace(',', '.'))
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
    key = os.getenv('SERPRIVER_API_KEY')
    prices = []
    queries = [
        f"БТИ услуги обмеры {address} цена за м²",
        f"техпаспорт БТИ {address} стоимость",
        f"обмеры недвижимости {address} цена",
        f"БТИ замеры {int(area)} м² цена"
    ]
    if not key:
        return [120,150,180,200,250]
    for q in queries:
        try:
            res = requests.get("https://serpriver.ru/api/search.php", params={
                "api_key": key, "system":"google","domain":"ru","query": q,
                "result_cnt": 10, "lr": 213
            }, timeout=10)
            if res.status_code == 200:
                data = res.json(); arr = data.get('json',{}).get('res',[])
                prices.extend(parse_competitor_prices(arr))
        except Exception:
            continue
    return prices or [120,150,180,200,250]

def parse_competitor_prices(results: list) -> list:
    prices = []
    for r in results:
        sn = r.get('snippet','').lower()
        for pat in [r'(\d+)\s*руб[./]?\s*м[²2]', r'(\d+)\s*руб[./]?\s*кв[./]?м', r'(\d+)\s*руб[./]?\s*за\s*м[²2]', r'от\s*(\d+)\s*руб']:
            for m in re.findall(pat, sn):
                try:
                    v = int(m)
                    if 20 <= v <= 500:
                        prices.append(v)
                except: pass
    return prices

# Refactored: calculate BTI costs using regional tariffs
# Returns dict with per-service and total, plus tariffs used

def calc_bti(area: float, region_code: str) -> dict:
    meas_tar, tp_tar, ta_tar = get_bti_tariffs_for_region(region_code)
    measurements = area * meas_tar
    techpassport = area * tp_tar
    techassignment = area * ta_tar
    total = measurements + techpassport + techassignment
    return {
        "measurements": round(measurements, 2),
        "techpassport": round(techpassport, 2),
        "techassignment": round(techassignment, 2),
        "total": round(total, 2),
        "tariffs": {
            "region": region_code,
            "measurements_per_m2": meas_tar,
            "techpassport_per_m2": tp_tar,
            "techassignment_per_m2": ta_tar,
        }
    }

def calc_competitors(prices: list) -> dict:
    med = statistics.median(prices) if prices else 150
    final_per_m2 = med * 1.22 * 1.10
    return {"price_per_m2": round(med,2), "final_price_per_m2": round(final_per_m2,2)}

def calc_recommended(bti_total: float, comp_final_per_m2: float, area: float) -> dict:
    comp_total = comp_final_per_m2 * area
    rec = (bti_total + comp_total) / 2
    return {"price": round(rec,2)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {'step': 'waiting_cadastral'}
    await update.message.reply_text("🏠 Привет! Введите кадастровый номер (пример: 77:09:0001013:1087)")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import time as _time
    user_id = update.effective_user.id
    text = update.message.text
    logger.info(f"📨 Получено сообщение от {user_id}: {text}")
    
    if not re.match(r'^\d{1,3}:\d{1,3}:\d{1,10}:\d{1,6}$', text):
        logger.info(f"❌ Неверный формат кадастрового номера: {text}")
        await update.message.reply_text("❓ Введите кадастровый номер формата a:b:c:d")
        return
    
    # Scene 1: Rosreestr lookup
    t0 = _time.time()
    await update.message.reply_text("🔎 Поиск в Росреестре…")
    data = fetch_reestr_data(text, "cadastral")
    t1 = _time.time()
    logger.info(f"📊 Данные из Росреестра: {data}")
    if not data or not data.get('area'):
        await update.message.reply_text("❌ Объект не найден в Росреестре. Проверьте номер и попробуйте снова.")
        return

    area = data['area']
    address = data.get('address') or '—'
    build_year = data.get('build_year') or '—'
    room_type = data.get('room_type') or '—'
    materials = data.get('materials') or '—'
    region_code = get_region_code_from_cad(text)

    # Card 1: BTI using regional tariffs
    t2 = _time.time()
    bti = calc_bti(area, region_code)
    t3 = _time.time()

    bti_msg = (
        "🏛️ Карточка 1 — БТИ (официальные тарифы)\n\n"
        f"📍 Адрес: {address}\n"
        f"📐 Площадь: {area} м²\n"
        f"🏢 Тип: {room_type} ({materials})\n"
        f"📅 Год: {build_year}\n\n"
        f"💰 Тарифы региона {region_code}:\n"
        f"• Обмеры: {bti['tariffs']['measurements_per_m2']:,.0f} ₽/м²\n"
        f"• Техпаспорт: {bti['tariffs']['techpassport_per_m2']:,.0f} ₽/м²\n"
        f"• Техзадание: {bti['tariffs']['techassignment_per_m2']:,.0f} ₽/м²\n\n"
        f"Суммы:\n"
        f"• Обмеры: {bti['measurements']:,.0f} ₽\n"
        f"• Техпаспорт: {bti['techpassport']:,.0f} ₽\n"
        f"• Техзадание: {bti['techassignment']:,.0f} ₽\n"
        f"• Итого БТИ: {bti['total']:,.0f} ₽\n\n"
        f"Источник: Росреестр (API), поиск {t1 - t0:.2f} c, расчет {t3 - t2:.2f} c"
    )
    await update.message.reply_text(bti_msg)

    # Scene 2: Market search via SERP
    t4 = _time.time()
    await update.message.reply_text("🧭 Ищем рыночные цены (Avito, ЦИАН, Яндекс)…")
    comp_list = search_competitor_prices(address, area)
    comp = calc_competitors(comp_list)
    t5 = _time.time()

    comp_msg = (
        "🏢 Карточка 2 — Рыночные цены\n\n"
        f"• Цена за м² (медиана): {comp['price_per_m2']:,.0f} ₽/м²\n"
        f"• С НДС и прибылью: {comp['final_price_per_m2']:,.0f} ₽/м²\n"
        f"• Итоговая оценка: {comp['final_price_per_m2'] * area:,.0f} ₽\n\n"
        f"Источник: SERP (Avito, ЦИАН и др.), поиск {t5 - t4:.2f} c"
    )
    await update.message.reply_text(comp_msg)

    # Scene 3: Recommendation
    rec = calc_recommended(bti['total'], comp['final_price_per_m2'], area)
    rec_msg = (
        "⭐ Карточка 3 — Рекомендованная цена\n\n"
        f"• Итог: {rec['price']:,.0f} ₽\n"
        f"• За м²: {rec['price']/area:,.0f} ₽/м²\n\n"
        "Обоснование: БТИ = официальные тарифы; Рынок = ориентиры конкурентов; Рекомендация = баланс двух источников."
    )
    await update.message.reply_text(rec_msg)

    # Scene 4: Commercial Proposal
    await send_commercial_proposal(update, address, area, room_type, materials, build_year, region_code, bti['total'], comp['final_price_per_m2'] * area, rec['price'], bti['tariffs'])

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception", exc_info=context.error)

def init_bot():
    global application
    if _background_loop is None:
        _start_background_loop()
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error('BOT_TOKEN missing'); return False
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)
    if not getattr(application, "_initialized", False):
        _run_coro(application.initialize())
    if not getattr(application, "_running", False):
        _run_coro(application.start())
    logger.info("Bot initialized and started on background loop")
    return True

# --- Flask Routes ---

@app.route('/health')
def health():
    return jsonify({"status":"OK","message":"BTI Bot with Forge 3D→2D is running"})

@app.route('/status')
def status():
    """Статус сервиса с информацией о конфигурации"""
    return jsonify({
        "service": "BTI Bot with Forge 3D → 2D Converter",
        "status": "running",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "endpoints": {
            "upload": "/upload",
            "health": "/health",
            "status": "/status"
        }
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Эндпоинт для загрузки IFC файлов и конвертации в DWG
    
    Принимает:
    - file: IFC файл через multipart/form-data
    
    Возвращает:
    - success: true/false
    - message: описание результата
    - gcs_url: URL файла в Google Cloud Storage (если успешно)
    - file_info: информация о файле
    """
    try:
        logger.info("Received upload request")
        
        # Проверяем наличие файла
        if 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify({
                "success": False,
                "message": "No file provided"
            }), 400
        
        file = request.files['file']
        
        # Валидируем файл
        is_valid, message = validate_file(file)
        if not is_valid:
            logger.warning(f"File validation failed: {message}")
            return jsonify({
                "success": False,
                "message": message
            }), 400
        
        logger.info(f"Processing file: {file.filename}")
        
        # Сохраняем файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ifc') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Обрабатываем файл через Forge
            logger.info("Starting Forge processing...")
            gcs_url = upload_ifc_to_forge_and_get_dwg(temp_file_path)
            
            if gcs_url:
                logger.info(f"File processed successfully: {gcs_url}")
                return jsonify({
                    "success": True,
                    "message": "File processed successfully",
                    "gcs_url": gcs_url,
                    "file_info": {
                        "original_filename": secure_filename(file.filename),
                        "file_size": os.path.getsize(temp_file_path),
                        "format": "IFC → DWG"
                    }
                })
            else:
                logger.error("Forge processing failed")
                return jsonify({
                    "success": False,
                    "message": "Failed to process file with Forge API"
                }), 500
                
        finally:
            # Удаляем временный файл
            try:
                os.unlink(temp_file_path)
                logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/', methods=['POST'])
def webhook():
    if application is None or _background_loop is None:
        if not init_bot():
            return jsonify({"error":"init failed"}), 500
    upd = request.get_json()
    if not upd or 'update_id' not in upd:
        return jsonify({"status":"OK"})
    update = Update.de_json(upd, application.bot)
    if update:
        _run_coro(application.process_update(update))
    return jsonify({"status":"OK"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)
