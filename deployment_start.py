
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

# Функция для запуска только веб-приложения
def run_web_only():
    logger.info("Starting web server on port 5000 (Web only mode)")
    app.run(host='0.0.0.0', port=5000, threaded=True)

# Функция для запуска Telegram бота в отдельном процессе
def run_telegram_bot_process():
    import asyncio
    logger.info("Starting Telegram bot process")
    asyncio.run(run_telegram_bot())

# Основная функция
if __name__ == "__main__":
    # Определяем режим работы: если указана переменная WEB_ONLY=1, запускаем только веб
    web_only = os.environ.get('WEB_ONLY', '0').lower() in ('1', 'true', 'yes')
    
    # Запуск в зависимости от режима
    if web_only:
        # Запуск только Flask в основном процессе
        run_web_only()
    else:
        # Запуск Telegram бота в отдельном процессе
        logger.info("Starting Telegram bot in separate process")
        bot_process = multiprocessing.Process(target=run_telegram_bot_process)
        bot_process.daemon = True
        bot_process.start()
        
        # Запуск Flask в основном процессе
        logger.info("Starting web server on port 5000")
        app.run(host='0.0.0.0', port=5000, threaded=True)
