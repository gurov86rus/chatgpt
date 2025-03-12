
import os
import logging
import asyncio
from telegram_bot import main as run_telegram_bot
from db_init import init_database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

# Инициализация базы данных
init_database()

# Запуск бота
logger.info("Запуск бота через bot_start.py")
asyncio.run(run_telegram_bot())
