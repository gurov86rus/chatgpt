#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
import sys
import requests
import psutil
import signal
import time
from db_init import init_database

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stable_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_existing_bots():
    """Останавливает все существующие процессы бота"""
    logger.info("Поиск и остановка существующих процессов бота...")
    current_pid = os.getpid()
    killed = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Ищем процессы Python с ключевыми словами, связанными с ботом
                if 'python' in cmdline and any(x in cmdline for x in ['telegram_bot', 'bot.py', 'minimal_test_bot']):
                    logger.info(f"Останавливаем процесс бота: PID {proc.info['pid']}, команда: {cmdline}")
                    try:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        killed = True
                    except Exception as e:
                        logger.error(f"Не удалось остановить процесс {proc.info['pid']}: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Ждем некоторое время, чтобы процессы успели завершиться
    if killed:
        logger.info("Ожидание завершения процессов...")
        time.sleep(2)
    
    return killed

def reset_webhook():
    """Сбрасывает вебхук бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    try:
        logger.info("Сброс вебхука...")
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
            return True
        else:
            logger.error(f"Ошибка при сбросе вебхука: {result}")
            return False
    except Exception as e:
        logger.error(f"Не удалось сбросить вебхук: {e}")
        return False

async def main():
    """Основная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("Запуск стабильной версии бота")
    logger.info("=" * 50)
    
    # Проверка наличия токена
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    # Убиваем все существующие процессы бота
    kill_existing_bots()
    
    # Сбрасываем вебхук
    if not reset_webhook():
        logger.warning("Не удалось сбросить вебхук, но продолжаем запуск")
    
    # Инициализация базы данных
    try:
        init_database()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    # Запускаем бот
    try:
        logger.info("Импорт модуля telegram_bot...")
        from telegram_bot import main as run_telegram_bot
        
        logger.info("Запуск основного бота...")
        await run_telegram_bot()
    except ImportError as e:
        logger.error(f"Не удалось импортировать модуль telegram_bot: {e}")
        
        # Попробуем запустить минимальный тестовый бот
        try:
            logger.info("Попытка запуска минимального тестового бота...")
            from minimal_test_bot import main as run_minimal_bot
            await run_minimal_bot()
        except ImportError:
            logger.error("Не удалось импортировать модуль minimal_test_bot")
            logger.error("Все попытки запуска бота неудачны")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        import traceback
        logger.critical(traceback.format_exc())