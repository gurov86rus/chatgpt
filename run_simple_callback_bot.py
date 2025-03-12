#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import subprocess
import sys
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_callback_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_existing_bots():
    """Останавливает все существующие процессы бота"""
    logger.info("Останавливаем все существующие процессы бота...")
    try:
        subprocess.run(["pkill", "-f", "python.*bot"], check=False)
        logger.info("Боты остановлены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сбрасываем вебхук...")
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            try:
                from config import TOKEN
                token = TOKEN
            except ImportError:
                logger.error("Токен не найден")
                return False
        
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

def main():
    """Основная функция"""
    # Останавливаем все запущенные боты
    kill_existing_bots()
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем тестовый бот с callback-кнопками
    logger.info("Запускаем тестовый бот с callback-кнопками...")
    try:
        # Используем subprocess для запуска тестового бота в отдельном процессе
        process = subprocess.Popen(
            [sys.executable, "simple_callback_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Бот запущен с PID {process.pid}")
        
        # Выводим информацию о боте
        logger.info("Тестовый бот запущен. Доступные команды:")
        logger.info("/start - Запустить бот и показать тестовые кнопки")
        logger.info("/help - Показать справку")
        
        # Ожидаем завершения процесса
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Бот завершился с ошибкой: {stderr.decode('utf-8')}")
        else:
            logger.info(f"Бот завершился нормально: {stdout.decode('utf-8')}")
    
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(f"Подробнее: {sys.exc_info()}")

if __name__ == "__main__":
    main()