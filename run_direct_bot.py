#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_direct_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def stop_existing_bots():
    """Останавливает все запущенные боты"""
    logger.info("Останавливаем все запущенные боты...")
    try:
        os.system("pkill -f 'python.*bot' || true")
        time.sleep(2)  # Даем время на остановку процессов
        logger.info("Все запущенные боты остановлены")
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")

def check_token():
    """Проверяет наличие токена в переменных окружения"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Токен найден, начинается с {token[:5]}...")
    return True

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сбрасываем вебхук бота...")
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
    """Основная функция"""
    logger.info("Начинаем запуск прямого API бота...")
    
    # Проверяем наличие токена
    if not check_token():
        return
    
    # Останавливаем все запущенные боты
    stop_existing_bots()
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем прямой API бот
    logger.info("Запускаем прямой API бот...")
    try:
        subprocess.run(["python", "direct_api_bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    
    logger.info("Работа скрипта завершена")

if __name__ == "__main__":
    main()