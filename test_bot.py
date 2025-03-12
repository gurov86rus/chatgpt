#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Получение токена бота
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения!")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer("👋 Привет! Это тестовый бот для проверки подключения.")

# Обработчик команды /test
@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    logger.info(f"Получена команда /test от пользователя {message.from_user.id}")
    await message.answer("✅ Бот работает корректно!")

# Обработчик для всех остальных сообщений
@dp.message()
async def echo(message: types.Message):
    logger.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.text}")
    await message.answer(f"Вы написали: {message.text}")

# Обработчик ошибок
async def on_startup():
    logger.info("Бот запущен!")
    # Попытка получить информацию о боте
    try:
        bot_info = await bot.get_me()
        logger.info(f"Подключен бот @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"Ошибка при получении информации о боте: {e}")
        return False
    return True

async def main():
    logger.info("Запуск тестового бота...")
    
    # Проверка соединения с API Telegram
    if not await on_startup():
        logger.error("Не удалось установить соединение с API Telegram!")
        return
    
    # Запуск бота в режиме long polling
    logger.info("Запуск поллинга...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен!")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())