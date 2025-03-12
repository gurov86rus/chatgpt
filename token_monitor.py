#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для периодической проверки токена Telegram бота.
Запускается в фоновом режиме для обеспечения актуальности токена.
"""
import os
import logging
import time
import threading
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("token_monitor.log")
    ]
)

logger = logging.getLogger(__name__)

# Новый токен бота
NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"

def monitor_token():
    """
    Мониторит текущий токен и обновляет его при необходимости.
    Эта функция запускается в отдельном потоке.
    """
    while True:
        try:
            check_and_update_token()
            # Проверяем каждые 5 минут
            time.sleep(300)
        except Exception as e:
            logger.error(f"Ошибка в мониторинге токена: {e}")
            # В случае ошибки сокращаем интервал до 1 минуты
            time.sleep(60)

def check_and_update_token():
    """
    Проверяет текущий токен и обновляет его, если нужно.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not current_token:
        logger.warning(f"{current_time} - Токен не найден в переменных окружения")
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        logger.info(f"{current_time} - Токен установлен: {NEW_TOKEN.split(':')[0]}")
        return
    
    if current_token != NEW_TOKEN:
        logger.warning(f"{current_time} - Обнаружен неверный токен: {current_token.split(':')[0]}")
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        logger.info(f"{current_time} - Токен обновлен на: {NEW_TOKEN.split(':')[0]}")
    else:
        logger.debug(f"{current_time} - Токен актуален: {NEW_TOKEN.split(':')[0]}")

def start_monitor_thread():
    """
    Запускает поток мониторинга токена.
    """
    try:
        thread = threading.Thread(target=monitor_token, daemon=True)
        thread.start()
        logger.info(f"Запущен поток мониторинга токена (ID: {thread.ident})")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске потока мониторинга: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск мониторинга токена Telegram бота...")
    start_monitor_thread()
    
    # Чтобы скрипт не завершался при запуске напрямую
    try:
        while True:
            time.sleep(3600)  # Проверка раз в час
            logger.info("Мониторинг токена активен")
    except KeyboardInterrupt:
        logger.info("Мониторинг токена остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")