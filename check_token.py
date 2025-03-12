#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()

def main():
    # Получаем токен
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return
    
    logger.info(f"Получен токен {token}")
    
    # Проверяем бота через getMe
    logger.info("Проверка соединения с API Telegram через getMe...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        logger.info(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Результат: {result}")
            
            if result.get("ok"):
                bot_info = result["result"]
                logger.info(f"Бот работает: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
            else:
                logger.error(f"Ошибка API: {result.get('description')}")
        else:
            logger.error(f"Ошибка соединения: {response.text}")
    
    except Exception as e:
        logger.error(f"Исключение при проверке токена: {e}")

if __name__ == "__main__":
    main()