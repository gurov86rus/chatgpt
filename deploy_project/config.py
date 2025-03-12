#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурационный файл приложения.
Содержит основные параметры и токен Telegram бота.
"""
import os
import logging
import dotenv
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Принудительная установка токена
NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
logger.info(f"ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ НОВЫЙ ТОКЕН (ID: {NEW_TOKEN.split(':')[0]})")

# Загрузка переменных окружения из файла .env
try:
    logger.info("Попытка загрузки переменных окружения из .env файла")
    dotenv.load_dotenv(".env")
    logger.info("Файл .env обработан")
except Exception as e:
    logger.warning(f"Ошибка при загрузке .env файла: {e}")

# Доступные переменные окружения (для отладки)
try:
    env_vars = ", ".join(list(os.environ.keys()))
    logger.info(f"Доступные переменные окружения: {env_vars}")
except Exception as e:
    logger.warning(f"Не удалось получить список переменных окружения: {e}")

# Получение токена из переменных окружения
try:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if TOKEN:
        token_id = TOKEN.split(':')[0] if ':' in TOKEN else "неизвестный формат"
        token_length = len(TOKEN)
        logger.info(f"Токен найден в переменных окружения (ID: {token_id}, длина: {token_length} символов)")
    else:
        TOKEN = NEW_TOKEN
        logger.warning("Токен не найден в переменных окружения, используем захардкоженный токен")
except Exception as e:
    logger.error(f"Ошибка при получении токена: {e}")
    TOKEN = NEW_TOKEN

# База данных
DB_PATH = "autopark.db"

# Настройки приложения
APP_NAME = "Система управления автопарком"
VERSION = "1.0.0"
DEBUG = False

# Права администратора (ID пользователей Telegram)
ADMIN_IDS = [
    123456789,  # Замените на реальные ID администраторов
    987654321
]

# Интервал ТО (в километрах)
TO_INTERVAL = 10000

# Максимальное количество хранимых резервных копий
MAX_BACKUPS = 10

# Настройки резервного копирования
BACKUP_FOLDER = "backups"
if not os.path.exists(BACKUP_FOLDER):
    try:
        os.makedirs(BACKUP_FOLDER)
        logger.info(f"Создана папка для резервных копий: {BACKUP_FOLDER}")
    except Exception as e:
        logger.error(f"Ошибка при создании папки для резервных копий: {e}")

# Проверка токена при запуске
def check_token():
    """
    Проверяет доступность токена и выводит информацию о нем
    """
    if TOKEN:
        token_id = TOKEN.split(':')[0] if ':' in TOKEN else "неизвестный формат"
        token_length = len(TOKEN)
        logger.info(f"Проверка токена: ID {token_id}, длина {token_length} символов")
    else:
        logger.error("Токен недоступен, проверьте переменные окружения или файл .env")
    return TOKEN is not None

# Принудительная установка токена при импорте модуля
check_token()