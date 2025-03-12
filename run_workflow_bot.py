#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
import sys
import traceback
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("workflow_bot.log")
    ]
)

logger = logging.getLogger("workflow_bot")

# Функция для проверки существования и валидности токена
def check_token():
    logger.info("Проверка токена Telegram бота")
    
    # Загружаем переменные из .env
    try:
        load_dotenv()
        logger.info("Переменные окружения из .env загружены")
    except Exception as e:
        logger.warning(f"Ошибка при загрузке .env: {e}")
    
    # Получаем токен
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        logger.info("Доступные переменные окружения: " + ", ".join([k for k in os.environ.keys() if not k.startswith("_")]))
        return False
    
    # Проверяем формат токена
    token_parts = token.split(':')
    if len(token_parts) < 2:
        logger.error(f"Токен имеет неверный формат. Ожидается формат '123456789:ABC...XYZ', получен: {token[:5]}...")
        return False
    
    # Проверяем соединение с API Telegram
    try:
        logger.info("Тестирование соединения с API Telegram")
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_username = data['result'].get('username', 'Unknown')
                bot_id = data['result'].get('id', 'Unknown')
                logger.info(f"✅ Соединение с API успешно! Бот @{bot_username} (ID: {bot_id})")
                return True
            else:
                logger.error(f"Ошибка API: {data}")
        else:
            logger.error(f"Ошибка соединения: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
    except Exception as e:
        logger.error(f"Исключение при проверке API: {e}")
    
    return False

# Функция для запуска основного бота через импорт
def run_main_bot():
    logger.info("Запуск основного бота через модуль telegram_bot")
    
    try:
        import telegram_bot
        logger.info("Импорт модуля telegram_bot выполнен успешно")
        
        # Запуск основной функции
        asyncio.run(telegram_bot.main())
        return True
    except ImportError as e:
        logger.error(f"Ошибка импорта модуля telegram_bot: {e}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"Ошибка при запуске основного бота: {e}")
        logger.debug(traceback.format_exc())
    
    return False

# Функция для запуска тестового бота
def run_test_bot():
    logger.info("Запуск тестового бота")
    
    try:
        import test_simple_bot
        logger.info("Импорт тестового бота выполнен успешно")
        
        # Запуск основной функции тестового бота
        asyncio.run(test_simple_bot.main())
        return True
    except ImportError as e:
        logger.error(f"Ошибка импорта тестового бота: {e}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"Ошибка при запуске тестового бота: {e}")
        logger.debug(traceback.format_exc())
    
    return False

# Функция для запуска прямого API-бота
def run_direct_bot():
    logger.info("Запуск прямого бота через API")
    
    try:
        import run_direct_bot
        logger.info("Импорт модуля run_direct_bot выполнен успешно")
        
        # Запуск функции прямого бота
        run_direct_bot.run_simple_bot()
        return True
    except ImportError as e:
        logger.error(f"Ошибка импорта модуля run_direct_bot: {e}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"Ошибка при запуске прямого бота: {e}")
        logger.debug(traceback.format_exc())
    
    return False

# Основная функция
def main():
    logger.info("Старт диагностической программы для Telegram бота")
    
    # Сначала проверяем токен
    if not check_token():
        logger.error("Проверка токена не пройдена. Невозможно запустить бота.")
        sys.exit(1)
    
    # Пробуем запустить основного бота
    logger.info("Попытка запуска основного бота")
    if run_main_bot():
        logger.info("Основной бот успешно запущен и завершил работу")
        return

    # Если основной бот не запустился, пробуем запустить тестовый бот
    logger.info("Основной бот не запустился. Попытка запуска тестового бота")
    if run_test_bot():
        logger.info("Тестовый бот успешно запущен и завершил работу")
        return
    
    # Если и тестовый бот не запустился, пробуем прямой API
    logger.info("Тестовый бот не запустился. Попытка запуска прямого API-бота")
    if run_direct_bot():
        logger.info("Прямой API-бот успешно запущен и завершил работу")
        return
    
    logger.error("Все попытки запуска ботов завершились неудачно")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.debug(traceback.format_exc())