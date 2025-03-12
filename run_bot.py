import os
import logging
import asyncio
import requests
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler("bot_debug.log"),  # Запись в файл
    ]
)

# Установка уровня логирования для других модулей
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("telegram").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

async def main():
    try:
        # Проверка переменной окружения и вывод больше информации
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
            logger.info("Доступные переменные окружения: " + ", ".join(os.environ.keys()))
            return
        else:
            logger.info(f"Токен бота найден. ID бота: {token.split(':')[0]}")

        # Проверка работы API Telegram
        try:
            logger.info("Проверка API Telegram...")
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Бот доступен: {bot_info}")
            else:
                logger.error(f"Ошибка при проверке API: {response.text}")
                return
        except Exception as e:
            logger.error(f"Не удалось подключиться к API Telegram: {e}")
            logger.error(traceback.format_exc())
            return

        # Сброс webhook через API
        try:
            logger.info("Сброс webhook...")
            response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
            logger.info(f"Webhook сброшен: {response.json()}")
        except Exception as e:
            logger.error(f"Ошибка при сбросе webhook: {e}")
            logger.error(traceback.format_exc())
        
        # Импортируем только после проверки переменных окружения
        logger.info("Импорт модуля telegram_bot...")
        from telegram_bot import main as run_telegram_bot
        
        # Инициализация базы данных
        logger.info("Инициализация базы данных...")
        from db_init import init_database
        init_database()
        
        # Запускаем бот
        logger.info("Запуск Telegram бота...")
        await run_telegram_bot()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        # Вывод подробного трейсбека
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())