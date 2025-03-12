
import os
import logging
import sys
import multiprocessing
from db_init import init_database
from telegram_bot import main as run_telegram_bot
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
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

# Функция для запуска Telegram бота в отдельном процессе
def run_telegram_bot_process():
    import asyncio
    asyncio.run(run_telegram_bot())

# Основная функция
if __name__ == "__main__":
    # Запуск Telegram бота в отдельном процессе
    logger.info("Starting Telegram bot in separate process")
    bot_process = multiprocessing.Process(target=run_telegram_bot_process)
    bot_process.daemon = True
    bot_process.start()
    
    # Запуск Flask в основном процессе
    logger.info("Starting web server on port 5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)
