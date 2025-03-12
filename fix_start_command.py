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
        logging.FileHandler("fix_start_command.log")
    ]
)

logger = logging.getLogger(__name__)

# Корректная инициализация бота
async def create_bot():
    # Получение токена из переменных окружения
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return None, None
    
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
                f"Это исправленный тестовый бот для проверки команды /start.\n"
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
                f"Это фиксированный тестовый бот.\n"
                f"Поддерживается только команда /start."
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа: {e}")
    
    return bot, dp

async def main():
    logger.info("Запуск исправленного бота для проверки команды /start...")
    
    # Останавливаем все экземпляры ботов через os.system
    try:
        import os, time
        os.system("pkill -f 'python.*bot' || true")
        time.sleep(1)  # Даем время на остановку процессов
    except Exception as e:
        logger.error(f"Ошибка при остановке других ботов: {e}")
    
    # Создаем экземпляр бота и диспетчера
    bot, dp = await create_bot()
    if not bot or not dp:
        logger.critical("Не удалось создать экземпляр бота")
        return
    
    # Сброс вебхука перед запуском
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхук успешно сброшен")
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
    
    # Проверка соединения с API
    try:
        me = await bot.get_me()
        logger.info(f"Бот успешно подключен: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.critical(f"Ошибка подключения к Telegram API: {e}")
        return
    
    # Запуск поллинга
    try:
        logger.info("Запуск polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        import traceback
        logger.critical(traceback.format_exc())