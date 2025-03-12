#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска стабильной версии бота через workflow.
Останавливает все предыдущие боты и запускает новую версию.
"""
import os
import logging
import subprocess
import signal
import sys
import time
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_stable_bot.log")
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

async def main():
    """Основная функция запуска бота"""
    logger.info("Запускаем скрипт стабильного бота...")
    
    # Останавливаем все запущенные боты
    kill_existing_bots()
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем стабильную версию бота
    logger.info("Запускаем стабильную версию бота...")
    try:
        # Запускаем бота напрямую
        import stable_bot
        stable_bot.main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    
    logger.info("Работа скрипта завершена")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())