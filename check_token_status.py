#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки статуса токена Telegram бота во всех компонентах системы
"""
import os
import sys
import logging
import requests
import dotenv
import importlib.util
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("token_status.log")
    ]
)

logger = logging.getLogger(__name__)

# Ожидаемый новый токен (маскированный для логов)
NEW_TOKEN_ID = "1023647955"
OLD_TOKEN_ID = "758794985"

def check_env_variable():
    """Проверяет переменную окружения TELEGRAM_BOT_TOKEN"""
    logger.info("Проверка переменной окружения TELEGRAM_BOT_TOKEN...")
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        token_id = token.split(':')[0] if ':' in token else "неизвестно"
        logger.info(f"Найден токен с ID: {token_id}")
        
        if token_id == NEW_TOKEN_ID:
            logger.info("✅ Переменная окружения содержит новый токен")
            return True
        elif token_id == OLD_TOKEN_ID:
            logger.error("⚠️ Переменная окружения содержит СТАРЫЙ токен")
            return False
        else:
            logger.warning(f"⚠️ Переменная окружения содержит неизвестный токен: {token_id}")
            return False
    else:
        logger.error("❌ Переменная окружения TELEGRAM_BOT_TOKEN не найдена")
        return False

def check_env_file():
    """Проверяет файл .env"""
    logger.info("Проверка файла .env...")
    
    env_path = Path('.env')
    if not env_path.exists():
        logger.error("❌ Файл .env не найден")
        return False
    
    # Загружаем переменные из .env
    env_vars = dotenv.dotenv_values('.env')
    token = env_vars.get("TELEGRAM_BOT_TOKEN")
    
    if token:
        token_id = token.split(':')[0] if ':' in token else "неизвестно"
        logger.info(f"Найден токен с ID: {token_id}")
        
        if token_id == NEW_TOKEN_ID:
            logger.info("✅ Файл .env содержит новый токен")
            return True
        elif token_id == OLD_TOKEN_ID:
            logger.error("⚠️ Файл .env содержит СТАРЫЙ токен")
            return False
        else:
            logger.warning(f"⚠️ Файл .env содержит неизвестный токен: {token_id}")
            return False
    else:
        logger.error("❌ Переменная TELEGRAM_BOT_TOKEN не найдена в файле .env")
        return False

def check_config_module():
    """Проверяет модуль config.py"""
    logger.info("Проверка модуля config.py...")
    
    config_path = Path('config.py')
    if not config_path.exists():
        logger.error("❌ Файл config.py не найден")
        return False
    
    try:
        # Загружаем модуль config.py
        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        # Проверяем токен
        token = getattr(config, 'TOKEN', None)
        
        if token:
            token_id = token.split(':')[0] if ':' in token else "неизвестно"
            logger.info(f"Найден токен с ID: {token_id}")
            
            if token_id == NEW_TOKEN_ID:
                logger.info("✅ Модуль config.py содержит новый токен")
                return True
            elif token_id == OLD_TOKEN_ID:
                logger.error("⚠️ Модуль config.py содержит СТАРЫЙ токен")
                return False
            else:
                logger.warning(f"⚠️ Модуль config.py содержит неизвестный токен: {token_id}")
                return False
        else:
            logger.error("❌ Переменная TOKEN не найдена в модуле config.py")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке модуля config.py: {e}")
        return False

def check_api_connection():
    """Проверяет соединение с API Telegram"""
    logger.info("Проверка соединения с API Telegram...")
    
    # Используем переменную окружения
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ Переменная окружения TELEGRAM_BOT_TOKEN не найдена")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                bot_username = bot_data.get('username', 'Unknown')
                bot_id = bot_data.get('id', 'Unknown')
                logger.info(f"✅ Соединение с API успешно установлено! Бот @{bot_username} (ID: {bot_id})")
                
                if str(bot_id) == NEW_TOKEN_ID:
                    logger.info("✅ API возвращает информацию для нового токена")
                    return True
                elif str(bot_id) == OLD_TOKEN_ID:
                    logger.error("⚠️ API возвращает информацию для СТАРОГО токена")
                    return False
                else:
                    logger.warning(f"⚠️ API возвращает информацию для неизвестного токена: {bot_id}")
                    return False
            else:
                logger.error(f"❌ Ошибка API: {bot_info}")
                return False
        else:
            logger.error(f"❌ Ошибка соединения с API Telegram: Код {response.status_code}")
            logger.debug(f"Ответ API: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при подключении к API Telegram: {e}")
        return False

def check_file_for_hardcoded_tokens(file_path, file_desc=""):
    """Проверяет файл на наличие захардкоженных токенов"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if OLD_TOKEN_ID in content:
            logger.warning(f"⚠️ В файле {file_path} найден СТАРЫЙ токен")
            return False
        else:
            logger.info(f"✅ В файле {file_path} не найден старый токен")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке файла {file_path}: {e}")
        return False

def check_key_files():
    """Проверяет основные файлы на наличие захардкоженных токенов"""
    logger.info("Проверка основных файлов на наличие захардкоженных токенов...")
    
    key_files = [
        "deployment_start.py",
        "main.py",
        "telegram_bot.py",
        "main_db.py",
        "app.py",
        "diagnose_start_command.py",
        "fix_bot_token.py",
        "direct_api_bot.py"
    ]
    
    all_clean = True
    for file in key_files:
        if os.path.exists(file):
            if not check_file_for_hardcoded_tokens(file):
                all_clean = False
        else:
            logger.info(f"Файл {file} не найден (пропущен)")
    
    return all_clean

def main():
    """Основная функция"""
    logger.info("=" * 60)
    logger.info("Запуск проверки статуса токена Telegram бота")
    logger.info("=" * 60)
    
    # Список проверок и их результатов
    checks = [
        ("Переменная окружения", check_env_variable()),
        ("Файл .env", check_env_file()),
        ("Модуль config.py", check_config_module()),
        ("Соединение с API", check_api_connection()),
        ("Проверка захардкоженных токенов", check_key_files())
    ]
    
    # Выводим итоговые результаты
    logger.info("\n" + "=" * 60)
    logger.info("ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    
    all_ok = True
    for check_name, result in checks:
        status = "✅ УСПЕШНО" if result else "❌ ОШИБКА"
        logger.info(f"{check_name}: {status}")
        if not result:
            all_ok = False
    
    if all_ok:
        logger.info("=" * 60)
        logger.info("✅ ВСЕ ПРОВЕРКИ УСПЕШНО ПРОЙДЕНЫ!")
        logger.info("Система использует новый токен Telegram бота во всех компонентах")
        logger.info("=" * 60)
        return 0
    else:
        logger.info("=" * 60)
        logger.info("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        logger.info("Некоторые компоненты системы могут использовать старый токен")
        logger.info("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())