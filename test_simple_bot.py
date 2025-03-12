#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования для лучшей диагностики
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_bot.log")
    ]
)

logger = logging.getLogger("testbot")

# Получение токена из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

# Инициализация бота и диспетчера
try:
    logger.info("Инициализация бота...")
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info("Бот и диспетчер успешно инициализированы")
except Exception as e:
    logger.error(f"Ошибка при инициализации бота: {e}")
    sys.exit(1)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer("👋 Привет! Это тестовый бот для проверки работы aiogram.")

# Обработчик команды /test
@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    logger.info(f"Получена команда /test от пользователя {message.from_user.id}")
    await message.answer("✅ Тест пройден успешно!")

# Обработчик всех текстовых сообщений
@dp.message()
async def echo(message: types.Message):
    logger.info(f"Получено сообщение от {message.from_user.id}: {message.text}")
    await message.answer(f"Вы написали: {message.text}")

# Функция, которая будет выполнена при запуске бота
async def on_startup():
    logger.info("Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook успешно удален")

# Основная функция
async def main():
    logger.info("Запуск тестового Telegram бота")
    
    # Действия при запуске
    await on_startup()
    
    try:
        # Запуск бота
        logger.info("Запуск polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        logger.info("Запуск программы...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())