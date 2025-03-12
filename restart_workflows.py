#!/usr/bin/env python3
import os
import sys
import logging
import time
import requests
import json

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("restart_workflow.log")
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Перезапускает workflow для бота Telegram и веб-приложения
    """
    logger.info("=== Перезапуск Workflow ===")
    
    # Получаем переменные окружения
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Проверяем наличие токена
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    # Сброс вебхука для бота
    try:
        logger.info("Сброс вебхука бота...")
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
        else:
            logger.error(f"Ошибка при сбросе вебхука: {result}")
    except Exception as e:
        logger.error(f"Не удалось сбросить вебхук: {e}")
    
    # Расчищаем процессы с помощью bash kill
    try:
        logger.info("Остановка всех процессов бота...")
        os.system("pkill -f 'python.*bot'")
        logger.info("Процессы остановлены")
    except Exception as e:
        logger.error(f"Ошибка при остановке процессов: {e}")
    
    # Небольшая пауза чтобы система успела обработать остановку
    time.sleep(2)
    
    logger.info("🔄 Перезапуск воркфлоу завершен.")
    logger.info("👉 Для запуска телеграм-бота используйте: python bot_launcher.py")
    logger.info("👉 Веб-интерфейс должен автоматически перезапуститься")
    
    print("=" * 60)
    print("🔄 Перезапуск воркфлоу завершен.")
    print("=" * 60)
    print("👉 Для запуска телеграм-бота используйте: python bot_launcher.py")
    print("👉 Веб-интерфейс должен автоматически перезапуститься")
    print("=" * 60)

if __name__ == "__main__":
    main()