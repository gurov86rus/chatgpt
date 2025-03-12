#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fixed_bot.log")
    ]
)

logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    exit(1)

# Инициализация бота, хранилища и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Проверка наличия базы данных
def check_database():
    """Проверка наличия базы данных и основных таблиц"""
    if not os.path.exists('vehicles.db'):
        logger.warning("База данных не найдена. Пробуем инициализировать...")
        try:
            from db_init import init_database
            init_database()
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            return False
    
    # Проверка основных таблиц
    try:
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        
        # Проверка таблицы vehicles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        if not cursor.fetchone():
            logger.error("Таблица vehicles не найдена в базе данных")
            conn.close()
            return False
        
        # Проверка наличия хотя бы одной записи
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        logger.info(f"В базе данных найдено {count} транспортных средств")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке базы данных: {e}")
        return False

# Функция для получения списка транспортных средств
def get_vehicle_buttons():
    """Create keyboard with vehicle selection buttons"""
    try:
        conn = sqlite3.connect('vehicles.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получение всех транспортных средств
        cursor.execute("SELECT id, model, reg_number FROM vehicles ORDER BY model")
        vehicles = cursor.fetchall()
        conn.close()
        
        if not vehicles:
            logger.warning("В базе данных нет транспортных средств")
            # Return keyboard with message
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚠️ Нет доступных ТС. Обратитесь к администратору.", callback_data="no_action")]
            ])
        
        # Create keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = []
        
        for vehicle in vehicles:
            button_text = f"{vehicle['model']} ({vehicle['reg_number']})"
            keyboard.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"vehicle_{vehicle['id']}"
            )])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка транспортных средств: {e}")
        # Return error keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚠️ Ошибка загрузки данных", callback_data="no_action")]
        ])

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Handler for /start command"""
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    
    try:
        greeting = f"👋 Привет, {message.from_user.full_name}!\n\n"
        greeting += "Это бот для управления автопарком и контроля технического обслуживания.\n\n"
        
        # Проверяем базу данных
        if not check_database():
            logger.error("Проблема с базой данных при обработке команды /start")
            await message.answer(
                greeting + "⚠️ Возникла проблема с базой данных. Пожалуйста, обратитесь к администратору."
            )
            return
        
        # Получаем клавиатуру с транспортными средствами
        keyboard = get_vehicle_buttons()
        
        await message.answer(
            greeting + "👇 *Выберите автомобиль из списка для начала работы:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Ответ на команду /start успешно отправлен пользователю {message.from_user.id}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Отправляем сообщение об ошибке
        try:
            await message.answer(
                "❌ Произошла ошибка при обработке команды /start.\n"
                "Пожалуйста, попробуйте позже или обратитесь к администратору."
            )
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")

# Обработчик команды /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Handler for /help command"""
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    try:
        help_text = (
            "ℹ️ **Справка по использованию бота:**\n\n"
            "🚗 **Основные команды:**\n"
            "/start - Показать список автомобилей\n"
            "/help - Показать эту справку\n"
            "/myid - Показать ваш Telegram ID\n\n"
            "⚙️ **Работа с автомобилем:**\n"
            "- Нажмите на автомобиль в списке, чтобы увидеть подробную информацию\n"
            "- Используйте кнопки под карточкой автомобиля для внесения новых данных\n\n"
        )
        
        await message.answer(help_text, parse_mode="Markdown")
        logger.info(f"Ответ на команду /help успешно отправлен пользователю {message.from_user.id}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /help: {e}")

# Обработчик команды /myid
@dp.message(Command("myid"))
async def show_my_id(message: types.Message):
    """Handler to show user's Telegram ID"""
    logger.info(f"Получена команда /myid от пользователя {message.from_user.id}")
    try:
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        
        await message.answer(
            f"👤 **Информация о пользователе**\n\n"
            f"🆔 Ваш Telegram ID: `{user_id}`\n"
            f"👤 Имя: {user_name}",
            parse_mode="Markdown"
        )
        logger.info(f"Ответ на команду /myid успешно отправлен пользователю {message.from_user.id}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /myid: {e}")

# Обработчик для всех других сообщений (эхо)
@dp.message()
async def echo(message: types.Message):
    """Echo handler for all other messages"""
    logger.info(f"Получено сообщение: '{message.text}' от пользователя {message.from_user.id}")
    try:
        await message.answer(
            "Я понимаю только команды /start, /help и /myid.\n"
            "Используйте кнопки для взаимодействия с ботом."
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")

# Обработчик для кнопки без действия
@dp.callback_query(lambda c: c.data == "no_action")
async def no_action(callback: types.CallbackQuery):
    """Handler for empty action"""
    await callback.answer("Это информационное сообщение, действий не требуется")

# Функция для запуска бота
async def main():
    """Main function to run the bot"""
    logger.info("Запуск фиксированного бота для тестирования команды /start...")
    
    # Сброс вебхука перед запуском для избежания конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск поллинга
    logger.info("Запуск поллинга...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            polling_timeout=30
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        import traceback
        logger.critical(traceback.format_exc())