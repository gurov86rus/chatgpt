#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import signal
import subprocess
import sys
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_fixed_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def stop_existing_bots():
    """Останавливает все работающие экземпляры ботов"""
    logger.info("Останавливаем все работающие экземпляры ботов...")
    try:
        # Используем pkill для остановки всех процессов с "bot" в командной строке
        os.system("pkill -f 'python.*bot'")
        os.system("pkill -f 'telegram_bot'")
        # Даем время на остановку процессов
        time.sleep(2)
        logger.info("Все работающие экземпляры ботов остановлены")
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сбрасываем вебхук бота...")
    try:
        # Получаем токен из переменных окружения
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не найден")
            return False
        
        # Отправляем запрос на сброс вебхука
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

def run_fixed_bot():
    """Запускает исправленного бота"""
    logger.info("Запускаем исправленного бота...")
    try:
        # Запускаем исправленного бота и ждем результата
        process = subprocess.Popen(["python", "fix_start_command.py"])
        logger.info(f"Бот запущен с PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return None

def main():
    """Основная функция"""
    logger.info("Начинаем запуск исправленного бота...")
    
    # Останавливаем все запущенные боты
    stop_existing_bots()
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем исправленного бота
    bot_process = run_fixed_bot()
    
    if bot_process:
        logger.info("Бот успешно запущен, ожидаем завершения...")
        try:
            # Ждем завершения процесса
            bot_process.wait()
            logger.info("Процесс бота завершен")
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания, останавливаем бота...")
            bot_process.terminate()
            bot_process.wait()
            logger.info("Бот остановлен")
    else:
        logger.error("Не удалось запустить бота")

if __name__ == "__main__":
    main()