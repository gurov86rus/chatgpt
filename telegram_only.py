#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
import sys
from db_init import init_database
from telegram_bot import main as run_telegram_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_only.log")
    ]
)

logger = logging.getLogger(__name__)

# Check for token
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    sys.exit(1)

# Initialize database
try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    logger.error(f"Stack trace: {sys.exc_info()}")

# Основная функция
if __name__ == "__main__":
    try:
        # Сброс вебхука для избежания конфликтов
        import requests
        logger.info("Trying to delete webhook...")
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
        webhook_result = response.json()
        if webhook_result.get('ok'):
            logger.info("✅ Webhook successfully deleted")
        else:
            logger.warning(f"Problem while deleting webhook: {webhook_result}")
    except Exception as e:
        logger.warning(f"Error while trying to delete webhook: {e}")
    
    # Запуск Telegram бота
    logger.info("Starting Telegram bot process")
    asyncio.run(run_telegram_bot())