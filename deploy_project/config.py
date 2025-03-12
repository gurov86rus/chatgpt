#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурационный файл приложения.
Содержит основные параметры и токен Telegram бота.
"""
import os
import logging
import dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Загрузка переменных окружения из .env файла, если он существует
if os.path.exists(".env"):
    logger.info("Попытка загрузки переменных окружения из .env файла")
    dotenv.load_dotenv()
    logger.info("Файл .env обработан")

# Список переменных окружения
logger.debug(f"Доступные переменные окружения: {' '.join(os.environ.keys())}")

# Токен Telegram бота
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    logger.warning("ТОКЕН БОТА НЕ НАЙДЕН В ПЕРЕМЕННЫХ ОКРУЖЕНИЯ, УСТАНАВЛИВАЕМ ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ")
    # Если токена нет в переменных окружения, устанавливаем его принудительно
    TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
    os.environ["TELEGRAM_BOT_TOKEN"] = TOKEN
    logger.info(f"ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ НОВЫЙ ТОКЕН (ID: {TOKEN.split(':')[0] if ':' in TOKEN else 'неизвестный формат'})")
else:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    token_id = TOKEN.split(':')[0] if ':' in TOKEN else "неизвестный формат"
    token_length = len(TOKEN)
    logger.info(f"Токен найден в переменных окружения (ID: {token_id}, длина: {token_length} символов)")

# Настройки базы данных
DB_PATH = os.environ.get("DB_PATH", "vehicles.db")

# Настройки мониторинга
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 1800))  # 30 минут

# Настройки аутентификации
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "12345,67890").split(",") if id.strip()]

# Настройки для веб-интерфейса
WEB_HOST = os.environ.get("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("WEB_PORT", 5000))
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

def check_token():
    """
    Проверяет доступность токена и выводит информацию о нем
    """
    if not TOKEN:
        logger.error("Токен Telegram бота не найден!")
        return False
        
    token_id = TOKEN.split(':')[0] if ':' in TOKEN else "неизвестный формат"
    token_length = len(TOKEN)
    logger.info(f"Используется токен бота с ID: {token_id}, длина токена: {token_length} символов")
    
    return True

if __name__ == "__main__":
    check_token()