#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import subprocess
import os
import signal
import time
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simple_bot_launcher.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_existing_bots():
    """Останавливает все существующие процессы бота"""
    logger.info("Остановка существующих ботов...")
    try:
        subprocess.run("pkill -f 'python.*bot' || true", shell=True)
        logger.info("Существующие боты остановлены")
        time.sleep(1)  # Даем время на остановку процессов
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сброс вебхука...")
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не найден")
            return False
            
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
    logger.info("Запуск простого тестового бота...")
    
    # Убиваем все запущенные экземпляры бота
    kill_existing_bots()
    
    # Сбрасываем вебхук
    if not reset_webhook():
        logger.warning("Проблемы при сбросе вебхука, но продолжаем работу")
    
    # Запускаем наш простой бот
    logger.info("Запуск test_start_command.py...")
    try:
        subprocess.run(["python", "test_start_command.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    
    logger.info("Работа скрипта завершена")

if __name__ == "__main__":
    main()