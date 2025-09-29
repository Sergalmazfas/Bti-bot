import os
import tempfile
import logging
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from forge_service import upload_ifc_to_forge_and_get_dwg

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация
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

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "OK",
        "message": "Forge 3D to 2D service is running",
        "version": "1.0.0"
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

@app.route('/status')
def status():
    """Статус сервиса с информацией о конфигурации"""
    return jsonify({
        "service": "Forge 3D to 2D Converter",
        "status": "running",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "endpoints": {
            "upload": "/upload",
            "health": "/health",
            "status": "/status"
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port, debug=False)
