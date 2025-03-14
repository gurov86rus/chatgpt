#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import sys
import requests
from db_init import init_database
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("web_only.log")
    ]
)

logger = logging.getLogger(__name__)

# Initialize database
try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    logger.error(f"Stack trace: {sys.exc_info()}")

# Основная функция
if __name__ == "__main__":
    # Указываем, что это только веб-приложение без Telegram бота
    os.environ['WEB_ONLY'] = '1'
    
    # Сброс webhook, чтобы не было конфликтов при запуске бота в другом процессе
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        try:
            logger.info("Сброс вебхука для избежания конфликтов...")
            response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
            webhook_result = response.json()
            if webhook_result.get('ok'):
                logger.info("✅ Вебхук успешно сброшен")
            else:
                logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
        except Exception as e:
            logger.warning(f"Ошибка при попытке сбросить вебхук: {e}")
    
    # Запуск Flask
    logger.info("Starting web server on port 5000 (Web Only mode)")
    app.run(host='0.0.0.0', port=5000, threaded=True)