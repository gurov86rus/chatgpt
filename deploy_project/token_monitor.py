#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для периодической проверки токена Telegram бота.
Запускается в фоновом режиме для обеспечения актуальности токена.
"""
import os
import time
import threading
import logging
import requests
import config

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("token_monitor.log")
    ]
)

logger = logging.getLogger(__name__)

# Интервал проверки токена (в секундах)
CHECK_INTERVAL = 60 * 30  # 30 минут

def monitor_token():
    """
    Мониторит текущий токен и обновляет его при необходимости.
    Эта функция запускается в отдельном потоке.
    """
    logger.debug(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Запущен мониторинг токена")
    
    while True:
        try:
            # Проверяем и обновляем токен
            check_and_update_token()
            
            # Ждем указанный интервал времени
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Ошибка в потоке мониторинга токена: {e}")
            time.sleep(60)  # При ошибке проверяем через минуту

def check_and_update_token():
    """
    Проверяет текущий токен и обновляет его, если нужно.
    """
    try:
        # Получаем текущий токен из переменных окружения
        current_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        # Проверяем валидность токена через API Telegram
        if current_token:
            url = f"https://api.telegram.org/bot{current_token}/getMe"
            response = requests.get(url)
            
            if response.status_code == 200 and response.json().get("ok"):
                # Токен валидный
                token_id = current_token.split(':')[0] if ':' in current_token else "неизвестный формат"
                logger.debug(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Токен актуален: {token_id}")
                return True
            else:
                # Токен невалидный, обновляем
                logger.warning(f"Текущий токен недействителен: {response.text}")
        else:
            logger.warning("Токен не найден в переменных окружения")
            
        # Обновляем токен
        new_token = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
        os.environ["TELEGRAM_BOT_TOKEN"] = new_token
        token_id = new_token.split(':')[0] if ':' in new_token else "неизвестный формат"
        logger.info(f"Токен обновлен: {token_id}")
        
        # Проверяем обновленный токен
        url = f"https://api.telegram.org/bot{new_token}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200 and response.json().get("ok"):
            # Обновленный токен валидный
            logger.info(f"Обновленный токен успешно проверен")
            return True
        else:
            # Обновленный токен тоже невалидный
            logger.error(f"Обновленный токен недействителен: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при проверке/обновлении токена: {e}")
        return False

def start_monitor_thread():
    """
    Запускает поток мониторинга токена.
    """
    try:
        # Создаем и запускаем поток мониторинга токена
        monitor_thread = threading.Thread(target=monitor_token, daemon=True)
        monitor_thread.start()
        thread_id = monitor_thread.ident
        logger.info(f"Запущен поток мониторинга токена (ID: {thread_id})")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске потока мониторинга токена: {e}")
        return False

if __name__ == "__main__":
    # Запускаем поток мониторинга токена
    start_monitor_thread()
    
    # Держим основной поток активным (для тестирования)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Мониторинг токена остановлен")