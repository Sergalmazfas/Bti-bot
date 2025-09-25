import json
import os
from flask import Flask, request, jsonify
import main  # PTB webhook flow
import index  # JSON cadastral flow (junior implementation)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['POST'])
def webhook():
    try:
        payload = request.get_json(silent=True) or {}
        # Dual-mode routing: JSON cadastral flow vs Telegram/PTB flow
        if isinstance(payload, dict) and 'cadastral_number' in payload:
            event = {'body': json.dumps(payload, ensure_ascii=False)}
            resp = index.handler(event, None)
            status = resp.get('statusCode', 200)
            headers = resp.get('headers', {"Content-Type": "application/json"})
            body = resp.get('body', '{}')
            return body, status, headers
        # Otherwise delegate to PTB webhook in main.py
        result = main.webhook()
        if isinstance(result, tuple):
            return result
        return result
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8080')))
