#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import subprocess
import sys
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("main_wrapper.log")
    ]
)

logger = logging.getLogger(__name__)

def stop_existing_bots():
    """Останавливает все запущенные экземпляры ботов"""
    try:
        logger.info("Останавливаю все запущенные экземпляры ботов...")
        os.system("pkill -f 'python.*bot' || true")
        time.sleep(2)
        logger.info("Все боты остановлены")
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")

def check_token():
    """Проверяет доступность токена"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Токен найден, начинается с {token[:5]}...")
    return True

def reset_webhook():
    """Сбрасывает вебхук бота"""
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        import requests
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.error(f"Ошибка при сбросе вебхука: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
        return False

def main():
    """Основная функция запуска бота"""
    logger.info("Начинаем запуск бота...")
    
    # Проверяем токен
    if not check_token():
        return
    
    # Останавливаем существующие боты
    stop_existing_bots()
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем стабильную версию бота
    logger.info("Запускаем стабильную версию бота...")
    try:
        # Запускаем бота напрямую, без subprocess
        import stable_bot
        stable_bot.main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    
    logger.info("Работа скрипта завершена")

if __name__ == "__main__":
    main()