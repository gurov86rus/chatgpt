#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import logging
import requests
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simple_bot.log")
    ]
)

logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сброс вебхука...")
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true", 
            timeout=10
        )
        webhook_result = response.json()
        if webhook_result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
            return True
        else:
            logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
    
    return False

def main():
    """Основная функция"""
    logger.info("====================================")
    logger.info("Запуск Telegram бота")
    logger.info("====================================")
    
    # Сбрасываем вебхук
    if not reset_webhook():
        logger.error("Не удалось сбросить вебхук")
        return 1
    
    logger.info("Запуск основного цикла бота через aiogram...")
    
    # Импортируем и запускаем основную функцию бота
    try:
        # Используем конструкцию try/except для изоляции импорта
        try:
            from aiogram import Bot, Dispatcher, types
            from aiogram.filters import Command
            from aiogram.fsm.storage.memory import MemoryStorage
            logger.info("✅ Модули aiogram успешно импортированы")
        except ImportError as e:
            logger.error(f"Ошибка импорта модулей aiogram: {e}")
            return 1
        
        # Инициализация бота и диспетчера
        bot = Bot(token=TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Обработчик команды /start
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
            await message.answer(
                f"👋 Привет, {message.from_user.full_name}!\n\n"
                f"Это очень простой тестовый бот для проверки команды /start.\n"
                f"Ваш ID: {message.from_user.id}"
            )
        
        # Обработчик для всех остальных сообщений
        @dp.message()
        async def echo(message: types.Message):
            logger.info(f"Получено сообщение: '{message.text}' от пользователя {message.from_user.id}")
            await message.answer(f"Вы написали: {message.text}")
        
        # Асинхронная функция запуска бота
        async def start_bot():
            logger.info("Сброс вебхука через API aiogram...")
            await bot.delete_webhook(drop_pending_updates=True)
            
            logger.info("Запуск поллинга...")
            await dp.start_polling(bot)
        
        # Запуск бота
        import asyncio
        asyncio.run(start_bot())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())