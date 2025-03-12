#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной скрипт для запуска полнофункционального Telegram бота автопарка
"""
import os
import logging
import subprocess
import sys
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def stop_existing_bots():
    """Останавливает все запущенные экземпляры ботов, кроме текущего"""
    logger.info("Останавливаем все запущенные боты...")
    try:
        # Не убиваем текущий процесс
        current_pid = os.getpid()
        logger.info(f"Текущий PID: {current_pid}")
        # Получаем список всех процессов python с 'bot' в команде, кроме текущего
        ps_cmd = f"ps aux | grep 'python.*bot' | grep -v {current_pid} | grep -v grep | awk '{{print $2}}'"
        output = subprocess.check_output(ps_cmd, shell=True).decode().strip()
        
        if output:
            pids = output.split('\n')
            for pid in pids:
                if pid.isdigit():
                    try:
                        subprocess.run(["kill", pid], check=False)
                        logger.info(f"Остановлен процесс с PID {pid}")
                    except Exception as e:
                        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
        else:
            logger.info("Других экземпляров бота не найдено")
            
        logger.info("Боты остановлены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def check_token():
    """Проверяет доступность токена"""
    logger.info("Проверяем токен...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        try:
            from config import TOKEN
            token = TOKEN
        except:
            logger.error("Токен не найден ни в переменных окружения, ни в config.py")
            return False
    
    if not token:
        logger.error("Токен пустой")
        return False
    
    logger.info("Токен доступен")
    return True

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сбрасываем вебхук...")
    try:
        import requests
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            from config import TOKEN
            token = TOKEN
            
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
    logger.info("Запускаем полнофункциональный бот автопарка...")
    
    # Останавливаем все запущенные боты
    stop_existing_bots()
    
    # Проверяем токен
    if not check_token():
        logger.error("Ошибка проверки токена. Бот не запущен.")
        return
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем полнофункциональный бот
    try:
        # Пробуем загрузить основной модуль бота
        try:
            import telegram_bot
            logger.info("Запускаем telegram_bot.py")
            asyncio.run(telegram_bot.main())
        except ImportError:
            try:
                import main_db
                logger.info("Запускаем main_db.py")
                asyncio.run(main_db.main())
            except ImportError:
                import fixed_bot
                logger.info("Запускаем fixed_bot.py")
                asyncio.run(fixed_bot.main())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
