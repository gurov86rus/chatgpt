
import os
import logging
import asyncio
import time
import traceback
from telegram_bot import main as run_telegram_bot
from db_init import init_database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_debug.log"),
    ]
)

logger = logging.getLogger(__name__)

# Функция для повторных попыток запуска бота
async def run_with_retry(max_retries=5, delay=5):
    retries = 0
    
    # Инициализация базы данных
    try:
        init_database()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        logger.debug(traceback.format_exc())
    
    while retries < max_retries:
        try:
            logger.info(f"Попытка запуска бота #{retries+1}")
            
            # Проверка наличия токена
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not token:
                logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
                raise ValueError("Отсутствует токен бота")
            
            logger.info("Запуск основной функции бота...")
            await run_telegram_bot()
            break
        except Exception as e:
            retries += 1
            logger.error(f"Ошибка при запуске бота (попытка {retries}/{max_retries}): {e}")
            logger.debug(traceback.format_exc())
            
            if retries < max_retries:
                logger.info(f"Повторная попытка через {delay} секунд...")
                time.sleep(delay)
            else:
                logger.error("Достигнуто максимальное количество попыток. Запуск бота прекращен.")
                raise

# Запуск бота с обработкой ошибок
if __name__ == "__main__":
    logger.info("Запуск скрипта bot_start.py для деплоя бота")
    try:
        asyncio.run(run_with_retry())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        logger.debug(traceback.format_exc())
