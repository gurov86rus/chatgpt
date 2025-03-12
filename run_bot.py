import os
import logging
import asyncio
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
    ]
)

logger = logging.getLogger(__name__)

async def main():
    # Проверка переменной окружения
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return

    # Сброс webhook через API
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
        logger.info(f"Webhook сброшен: {response.json()}")
    except Exception as e:
        logger.error(f"Ошибка при сбросе webhook: {e}")
    
    try:
        # Импортируем только после проверки переменных окружения
        from telegram_bot import main as run_telegram_bot
        logger.info("Запуск Telegram бота...")
        
        # Запускаем бот
        await run_telegram_bot()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        # Вывод подробного трейсбека
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())