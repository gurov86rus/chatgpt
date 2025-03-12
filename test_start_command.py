#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_start_command.log")
    ]
)

logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        logger.debug(f"Получена команда /start от пользователя {message.from_user.id}")
        await message.answer(
            f"👋 Привет, {message.from_user.full_name}!\n\n"
            f"Это очень упрощенный тестовый бот для проверки команды /start.\n"
            f"Ваш ID: {message.from_user.id}"
        )
        logger.info(f"Ответ на команду /start отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Обработчик для всех других сообщений
@dp.message()
async def echo(message: types.Message):
    logger.debug(f"Получено сообщение: '{message.text}' от пользователя {message.from_user.id}")
    try:
        await message.answer(
            "Это очень простой тестовый бот.\n"
            "Поддерживается только команда /start."
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}")

async def main():
    logger.info("Запуск тестового бота для проверки команды /start...")
    
    # Сброс вебхука перед запуском
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск поллинга
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Останавливаем все экземпляры ботов через os.system
    import os
    os.system("pkill -f 'python.*bot' || true")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        import traceback
        logger.critical(traceback.format_exc())