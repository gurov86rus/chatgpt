#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simple_callback_bot.log")
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
dp = Dispatcher()

# Простая клавиатура с кнопками
def get_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Кнопка 1", callback_data="btn_1"),
            InlineKeyboardButton(text="Кнопка 2", callback_data="btn_2")
        ],
        [InlineKeyboardButton(text="Кнопка 3", callback_data="btn_3")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я простой бот для тестирования кнопок!", reply_markup=get_keyboard())

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Я тестовый бот для проверки работы инлайн-кнопок. Нажми /start для начала.")

# Обработчик для кнопки 1
@dp.callback_query(F.data == "btn_1")
async def process_btn_1(callback: types.CallbackQuery):
    await callback.answer("Вы нажали кнопку 1!", show_alert=True)
    await callback.message.answer("Обработка нажатия кнопки 1 завершена.")

# Обработчик для кнопки 2
@dp.callback_query(F.data == "btn_2")
async def process_btn_2(callback: types.CallbackQuery):
    await callback.answer("Вы нажали кнопку 2!")
    await callback.message.answer("Обработка нажатия кнопки 2 завершена.")

# Обработчик для кнопки 3
@dp.callback_query(F.data == "btn_3")
async def process_btn_3(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Кнопка 3 была нажата. Вот новые кнопки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ])
    )

# Обработчик для кнопки "Назад"
@dp.callback_query(F.data == "back")
async def process_back(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Вернулись назад!", reply_markup=get_keyboard())

# Обработчик для любого текстового сообщения
@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}", reply_markup=get_keyboard())

# Основная функция
async def main():
    # Сброс вебхука и установка режима long polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск long polling
    logger.info("Запуск простого тестового бота с кнопками...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())