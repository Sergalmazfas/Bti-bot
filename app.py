import os
import json
import logging
import asyncio
import threading
import re
import requests
import statistics
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

user_data = {}
application = None
_background_loop = None
_loop_thread = None

CRPTI_COEFFICIENTS = {
    'coefficient_measurements': 50,
    'coefficient_techpassport': 250,
    'coefficient_techassignment': 250,
    'last_updated': '2025-09-24'
}

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

def fetch_reestr_data(query: str, search_type: str = "cadastral") -> dict:
    try:
        token = os.getenv('REESTR_API_TOKEN')
        if not token:
            logger.error("REESTR_API_TOKEN missing")
            return {}
        if search_type == "cadastral":
            url = f"https://reestr-api.ru/v1/search/cadastrFull?auth_token={token}"
            data = {"cad_num": query}
        else:
            url = f"https://reestr-api.ru/v1/search/address?auth_token={token}"
            data = {"address": query}
        r = requests.post(url, data=data, timeout=15)
        if r.status_code == 404 and search_type == "cadastral":
            url2 = f"https://reestr-api.ru/v1/search/cadastr?auth_token={token}"
            r = requests.post(url2, data={"cad_num": query}, timeout=15)
            if r.status_code != 200:
                return {}
        elif r.status_code != 200:
            return {}
        js = r.json()
    except Exception as e:
        logger.error(f"Reestr error: {e}")
        return {}
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

def calc_bti(area: float) -> dict:
    m = area * CRPTI_COEFFICIENTS['coefficient_measurements']
    tp = area * CRPTI_COEFFICIENTS['coefficient_techpassport']
    ta = area * CRPTI_COEFFICIENTS['coefficient_techassignment']
    total = m + tp + ta
    return {"measurements": round(m,2), "techpassport": round(tp,2), "techassignment": round(ta,2), "total": round(total,2)}

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
    user_id = update.effective_user.id
    text = update.message.text
    if not re.match(r'^\d{1,3}:\d{1,3}:\d{1,10}:\d{1,6}$', text):
        await update.message.reply_text("❓ Введите кадастровый номер формата a:b:c:d")
        return
    await update.message.reply_text(f"🔍 Ищу данные по кадастру {text} в Росреестре...")
    data = fetch_reestr_data(text, "cadastral")
    if not data or not data.get('area'):
        await update.message.reply_text("❌ Объект не найден или нет площади.")
        return
    area = data['area']; address = data.get('address') or 'Москва'
    bti = calc_bti(area)
    comp_list = search_competitor_prices(address, area)
    comp = calc_competitors(comp_list)
    rec = calc_recommended(bti['total'], comp['final_price_per_m2'], area)
    msg = f"""📊 ТРИ КАРТОЧКИ ЦЕН для {area} м² ({data.get('room_type')}, {data.get('materials')}, {data.get('build_year')} г.):

🏛️ КАРТОЧКА 1: БТИ
• Обмеры: {bti['measurements']:,.0f} руб.
• Техпаспорт: {bti['techpassport']:,.0f} руб.
• Техзадание: {bti['techassignment']:,.0f} руб.
• Итого БТИ: {bti['total']:,.0f} руб.

🏢 КАРТОЧКА 2: Конкуренты
• Цена за м²: {comp['price_per_m2']:,.0f} руб/м²
• С НДС и прибылью: {comp['final_price_per_m2']:,.0f} руб/м²
• Итоговая: {comp['final_price_per_m2']*area:,.0f} руб.

⭐ КАРТОЧКА 3: Рекомендуемая цена
• Итоговая сумма: {rec['price']:,.0f} руб.
"""
    await update.message.reply_text(msg)

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

@app.route('/health')
def health():
    return jsonify({"status":"OK","message":"Bot is running"})

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
