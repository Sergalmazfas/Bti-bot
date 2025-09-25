import json
import os
from flask import Flask, request, jsonify
import main  # our module with webhook function

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['POST'])
def webhook():
    # Прямой вызов webhook функции из main.py
    try:
        # Получаем данные из request
        update_data = request.get_json()
        
        # Вызываем функцию webhook из main.py
        result = main.webhook()
        if isinstance(result, tuple):
            return result[0], result[1]
        return result
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8080')))
