#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Точка входа для Google Cloud Run
@app.route("/", methods=["POST"])
def handler():
    update = request.get_json()
    
    if not update or "message" not in update:
        return {"ok": True}
    
    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")
    
    # Обработка команды /start
    if text == "/start":
        send_message(chat_id, "🏠 Добро пожаловать в BTI Bot!\n\nВведите кадастровый номер для расчета стоимости БТИ.")
        return {"ok": True}
    
    # Проверяем формат кадастрового номера
    if not validate_cadastral(text):
        send_message(chat_id, "❌ Введите корректный кадастровый номер в формате 00:00:0000000:0000")
        return {"ok": True}
    
    try:
        # Запрос в Росреестр (примерный эндпоинт, заменить на реальный)
        data = get_cadastral_data(text)
        send_message(chat_id, format_response(data))
    except Exception as e:
        send_message(chat_id, f"❌ Ошибка при обработке: {e}")
    
    return {"ok": True}

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

def validate_cadastral(number: str) -> bool:
    """Проверка формата кадастрового номера"""
    if not number or ":" not in number:
        return False
    
    parts = number.split(":")
    if len(parts) != 4:
        return False
    
    # Проверяем, что все части состоят из цифр
    for part in parts:
        if not part.isdigit():
            return False
    
    return True

def get_cadastral_data(number: str) -> dict:
    """Получение данных из Росреестра"""
    # TODO: заменить на реальный API Росреестра
    # Пока возвращаем тестовые данные
    return {
        "address": f"Адрес по кадастровому номеру {number}",
        "area": "50.5 кв.м",
        "cost": "15,000 руб",
        "cadastral_number": number
    }

def format_response(data: dict) -> str:
    """Форматирование ответа пользователю"""
    address = data.get("address", "Адрес не найден")
    area = data.get("area", "Нет данных")
    cost = data.get("cost", "Нет данных")
    
    return f"""🏠 **Адрес:** {address}
📐 **Площадь:** {area}
💰 **Стоимость БТИ:** {cost}

📞 Для заказа звоните: +7 (495) 123-45-67"""

def send_message(chat_id: int, text: str):
    """Отправка сообщения в Telegram"""
    url = f"{API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
