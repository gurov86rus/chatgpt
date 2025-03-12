#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска полной версии бота автопарка из telegram_bot.py
Останавливает все предыдущие экземпляры ботов и запускает бот с полной функциональностью.
"""
import os
import logging
import subprocess
import signal
import sys
import time
import requests
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_full_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_existing_bots():
    """Останавливает все существующие процессы бота"""
    logger.info("Останавливаем все запущенные боты...")
    try:
        subprocess.run(["pkill", "-f", "python.*bot"], check=False)
        time.sleep(2)  # Ждем завершения процессов
        logger.info("Все боты остановлены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сбрасываем вебхук...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        from config import TOKEN
        token = TOKEN
        
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(url)
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.error(f"Ошибка при сбросе вебхука: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
        return False

def check_database():
    """Проверяет и инициализирует базу данных при необходимости"""
    logger.info("Проверяем наличие базы данных...")
    
    try:
        # Импортируем функцию инициализации базы данных
        from db_init import init_database
        
        # Инициализируем БД если нужно
        init_database()
        logger.info("База данных проверена и готова к работе")
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке базы данных: {e}")
        return False

async def run_full_bot():
    """Запускает полнофункциональный бот из telegram_bot.py"""
    logger.info("Запускаем полнофункциональный бот из telegram_bot.py...")
    
    try:
        # Импортируем модуль с полным ботом
        import telegram_bot
        
        # Вызываем основную функцию из модуля
        await telegram_bot.main()
        return True
    except ImportError:
        logger.error("Модуль telegram_bot.py не найден или возникла ошибка импорта")
        try:
            # Пробуем альтернативную версию
            import main_db
            logger.info("Используем альтернативный модуль main_db.py")
            await main_db.main()
            return True
        except Exception as e:
            logger.error(f"Ошибка запуска альтернативной версии: {e}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Основная функция запуска полного бота"""
    logger.info("Запускаем скрипт полного бота для автопарка...")
    
    # Останавливаем все запущенные боты
    kill_existing_bots()
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Проверяем и инициализируем базу данных
    check_database()
    
    # Запускаем полнофункциональный бот с обработкой ошибок
    try:
        await run_full_bot()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Работа скрипта завершена")

if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())