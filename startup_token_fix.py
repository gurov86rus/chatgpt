#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления токена Telegram бота при запуске системы.
Запускается из каждого workflow для гарантии использования нового токена.
"""
import os
import logging
from pathlib import Path
import subprocess

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("startup_token_fix.log")
    ]
)

logger = logging.getLogger(__name__)

# Новый токен бота
NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"

def set_token_in_environment():
    """Устанавливает новый токен в переменных окружения"""
    try:
        # Устанавливаем токен в текущем процессе
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        
        # Записываем в лог
        logger.info(f"Установлен новый токен бота в переменных окружения: ID {NEW_TOKEN.split(':')[0]}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке токена в переменных окружения: {e}")
        return False

def update_env_file():
    """Обновляет файл .env с новым токеном"""
    try:
        env_path = Path('.env')
        
        # Проверяем содержимое файла
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
                if NEW_TOKEN in content:
                    logger.info("Файл .env уже содержит правильный токен")
                    return True
        
        # Обновляем файл
        with open(env_path, 'w') as f:
            f.write(f"# Telegram Bot Token (replace with your actual token)\n")
            f.write(f"TELEGRAM_BOT_TOKEN={NEW_TOKEN}\n\n")
            f.write(f"# DO NOT commit this file to version control\n")
        
        logger.info("Файл .env успешно обновлен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении файла .env: {e}")
        return False

def update_workflow_environment():
    """Обновляет переменную окружения в текущем workflow"""
    try:
        # Определяем имя текущего workflow
        workflow_name = os.environ.get("REPL_SLUG", "unknown")
        workflow_id = os.environ.get("REPL_ID", "unknown")
        
        logger.info(f"Текущий workflow: {workflow_name} (ID: {workflow_id})")
        
        # Добавляем заметку в журнал запуска для операторов
        print(f"⚠️ Startup Token Fix: установлен токен бота ID {NEW_TOKEN.split(':')[0]}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении workflow: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("Запуск обновления токена при старте системы...")
    
    # Обновляем токен в переменных окружения
    if not set_token_in_environment():
        logger.warning("Не удалось обновить токен в переменных окружения")
    
    # Обновляем файл .env
    if not update_env_file():
        logger.warning("Не удалось обновить файл .env")
    
    # Обновляем workflow
    if not update_workflow_environment():
        logger.warning("Не удалось обновить workflow")
    
    logger.info("Обновление токена при старте системы завершено")

if __name__ == "__main__":
    main()