#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска всех компонентов системы при старте приложения.
Этот скрипт должен запускаться первым и гарантирует, что
веб-интерфейс и Telegram бот корректно запущены.
"""
import os
import sys
import time
import logging
import subprocess

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("startup.log")
    ]
)

logger = logging.getLogger("Startup")

def check_token():
    """Проверяет наличие токена Telegram бота"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Токен Telegram найден (ID: {token.split(':')[0]}, длина: {len(token)} символов)")
    return True

def start_web_interface():
    """Запускает веб-интерфейс"""
    logger.info("Запуск веб-интерфейса...")
    try:
        # Запуск через workflow
        subprocess.Popen(["replit", "run", "-w", "Start application"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        logger.info("Веб-интерфейс запущен через workflow")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса через workflow: {e}")
        try:
            # Альтернативный способ запуска
            subprocess.Popen([sys.executable, "deployment_start.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
            logger.info("Веб-интерфейс запущен напрямую")
            return True
        except Exception as e2:
            logger.error(f"Ошибка при прямом запуске веб-интерфейса: {e2}")
            return False

def start_telegram_bot():
    """Запускает Telegram бота"""
    logger.info("Запуск Telegram бота...")
    try:
        # Запуск через workflow
        subprocess.Popen(["replit", "run", "-w", "telegram_bot"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        logger.info("Telegram бот запущен через workflow")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота через workflow: {e}")
        try:
            # Альтернативный способ запуска
            subprocess.Popen([sys.executable, "main.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
            logger.info("Telegram бот запущен напрямую")
            return True
        except Exception as e2:
            logger.error(f"Ошибка при прямом запуске Telegram бота: {e2}")
            return False

def main():
    """Основная функция"""
    logger.info("=" * 60)
    logger.info("Запуск системы управления автопарком")
    logger.info("=" * 60)
    
    # Проверяем наличие токена
    if not check_token():
        logger.error("Токен Telegram бота не найден. Веб-интерфейс будет запущен, но бот не будет работать.")
    
    # Запускаем веб-интерфейс
    web_started = start_web_interface()
    
    # Даем время на инициализацию веб-интерфейса
    time.sleep(3)
    
    # Запускаем Telegram бота
    bot_started = start_telegram_bot()
    
    # Проверяем результаты запуска
    if web_started and bot_started:
        logger.info("✅ Все компоненты системы успешно запущены")
    elif web_started:
        logger.warning("⚠️ Веб-интерфейс запущен, но возникли проблемы с запуском Telegram бота")
    elif bot_started:
        logger.warning("⚠️ Telegram бот запущен, но возникли проблемы с запуском веб-интерфейса")
    else:
        logger.error("❌ Не удалось запустить ни один компонент системы")
    
    logger.info("Запуск компонентов системы завершен")

if __name__ == "__main__":
    main()