#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для перезапуска workflows Telegram бота и веб-приложения.
Используется для быстрого перезапуска сервисов через командную строку.
"""
import os
import sys
import logging
import subprocess
import time
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("restart_workflow.log")
    ]
)

logger = logging.getLogger("RestartWorkflows")

def restart_web_workflow():
    """Перезапускает workflow веб-интерфейса"""
    logger.info("Перезапуск workflow 'Start application'...")
    try:
        subprocess.run(["replit", "run", "-w", "Start application"], check=False)
        logger.info("✅ Команда перезапуска веб-интерфейса выполнена")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка перезапуска веб-интерфейса: {e}")
        return False

def restart_bot_workflow():
    """Перезапускает workflow Telegram бота"""
    logger.info("Перезапуск workflow 'telegram_bot'...")
    try:
        # Сбрасываем вебхук перед перезапуском
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            try:
                requests.get(
                    f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", 
                    timeout=5
                )
                logger.info("✅ Вебхук Telegram бота сброшен")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка сброса вебхука: {e}")
        
        # Перезапускаем бота
        subprocess.run(["replit", "run", "-w", "telegram_bot"], check=False)
        logger.info("✅ Команда перезапуска Telegram бота выполнена")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка перезапуска Telegram бота: {e}")
        return False

def main():
    """
    Перезапускает workflow для бота Telegram и веб-приложения
    """
    print("=" * 50)
    print("ПЕРЕЗАПУСК WORKFLOW СИСТЕМЫ")
    print("=" * 50)
    
    # Перезапускаем веб-интерфейс
    print("\nПерезапуск веб-интерфейса...")
    if restart_web_workflow():
        print("✅ Веб-интерфейс перезапущен")
    else:
        print("❌ Ошибка перезапуска веб-интерфейса")
    
    # Небольшая пауза между перезапусками
    time.sleep(3)
    
    # Перезапускаем Telegram бот
    print("\nПерезапуск Telegram бота...")
    if restart_bot_workflow():
        print("✅ Telegram бот перезапущен")
    else:
        print("❌ Ошибка перезапуска Telegram бота")
    
    print("\n" + "=" * 50)
    print("Перезапуск workflow завершен")
    print("=" * 50)

if __name__ == "__main__":
    main()