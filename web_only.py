#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import sys
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
    
    # Запуск Flask
    logger.info("Starting web server on port 5000 (Web Only mode)")
    app.run(host='0.0.0.0', port=5000, threaded=True)