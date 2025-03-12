#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования с самым подробным уровнем
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simple_test_bot.log")
    ]
)

logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Простой обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.debug(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        f"Это простой тестовый бот для проверки команды /start.\n"
        f"Ваш ID: {message.from_user.id}"
    )
    logger.info(f"Ответ на команду /start отправлен пользователю {message.from_user.id}")

# Эхо-обработчик для всех остальных сообщений
@dp.message()
async def echo(message: types.Message):
    logger.debug(f"Получено сообщение: '{message.text}' от пользователя {message.from_user.id}")
    await message.answer(f"Вы написали: {message.text}")
    logger.info(f"Эхо-ответ отправлен пользователю {message.from_user.id}")

# Функция для очистки и настройки перед запуском бота
async def on_startup():
    # Сброс вебхука для режима polling
    logger.info("Сброс вебхука...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Вебхук сброшен")
    logger.info("Бот готов к работе")

# Основная функция запуска бота
async def main():
    logger.info("Запуск тестового бота...")
    
    # Регистрация обработчика запуска
    dp.startup.register(on_startup)
    
    try:
        # Запуск поллинга
        logger.info("Запуск polling...")
        await dp.start_polling(bot, polling_timeout=30)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1
    finally:
        logger.info("Бот остановлен")
        await bot.session.close()
    
    return 0

# Запуск основной функции
if __name__ == "__main__":
    logger.info("Запуск программы")
    try:
        sys.exit(asyncio.run(main()))
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен!")