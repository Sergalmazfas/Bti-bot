@app.route('/', methods=['POST'])
def webhook():
    """Webhook для Cloud Run"""
    try:
        # Ленивая инициализация бота при первом запросе
        global application, db
        
        # Инициализация базы данных
        db = EnhancedDatabase()
        
        if application is None:
            logger.info('🚀 Инициализация BTI Bot при первом запросе...')
            main()  # Инициализируем бота только при первом запросе
            
        # Проверяем, что application инициализирован
        if application is None:
            logger.error('Application not initialized')
            return jsonify({"error": "Application not initialized"}), 500
            
        update = Update.de_json(request.get_json(), application.bot)
        asyncio.run(application.process_update(update))
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500
