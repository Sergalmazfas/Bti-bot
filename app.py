import json
import os
from flask import Flask, request, jsonify
import index  # our module with handler(event, context)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['POST'])
def webhook():
    # Cloud Run HTTP handler adapts to our Yandex-like handler(event, context)
    body_bytes = request.get_data() or b''
    try:
        body_str = body_bytes.decode('utf-8')
    except Exception:
        body_str = ''
    event = {'body': body_str}
    result = index.handler(event, None)  # context is not used
    status = result.get('statusCode', 200)
    body = result.get('body', 'OK')
    return body, status, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8080')))
