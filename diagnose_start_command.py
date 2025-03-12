#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
import sys
import requests

# Настройка логирования с самым подробным уровнем
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("diagnose_start_command.log")
    ]
)

logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

# Проверяем, работает ли бот вообще
def test_telegram_api():
    """Тестирование соединения с API Telegram без aiogram"""
    logger.info("Тестирование прямого соединения с API Telegram...")
    
    try:
        # Сброс вебхука для режима polling
        logger.info("Сброс вебхука...")
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true")
        webhook_result = response.json()
        if webhook_result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
        else:
            logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
        
        # Тест соединения с API Telegram через getMe
        logger.info("Получение информации о боте через getMe...")
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                bot_username = bot_data.get('username', 'Unknown')
                bot_id = bot_data.get('id', 'Unknown')
                logger.info(f"✅ Соединение с API успешно установлено! Бот @{bot_username} (ID: {bot_id})")
                return True
            else:
                logger.error(f"Ошибка API: {bot_info}")
        else:
            logger.error(f"Ошибка соединения с API Telegram: Код {response.status_code}")
            logger.debug(f"Ответ API: {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Не удалось подключиться к API Telegram: {e}")
        import traceback
        logger.debug(traceback.format_exc())
    
    return False

# Проверяем команду /start
def test_start_command():
    """Тестирование команды /start через прямые API вызовы"""
    logger.info("Тестирование команды /start через прямые API вызовы...")
    
    # Получаем обновления для бота
    try:
        logger.info("Получение последних обновлений...")
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?limit=10", timeout=10)
        
        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok'):
                updates_data = updates.get('result', [])
                logger.info(f"Получено обновлений: {len(updates_data)}")
                
                if updates_data:
                    for update in updates_data:
                        logger.debug(f"Обновление: {update}")
                        
                        # Проверяем, есть ли в обновлении команда /start
                        message = update.get('message', {})
                        text = message.get('text', '')
                        if text == '/start':
                            logger.info("✅ Найдена команда /start в обновлениях")
                            
                            # Получаем информацию о пользователе
                            user = message.get('from', {})
                            chat_id = message.get('chat', {}).get('id')
                            user_id = user.get('id')
                            user_name = user.get('first_name', '') + ' ' + user.get('last_name', '')
                            
                            logger.info(f"Отправка ответа на команду /start пользователю {user_id}...")
                            
                            # Отправляем тестовый ответ
                            response = requests.post(
                                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                json={
                                    'chat_id': chat_id,
                                    'text': f"👋 Привет, {user_name}! Это тестовый ответ на команду /start",
                                    'parse_mode': 'Markdown'
                                },
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('ok'):
                                    logger.info("✅ Ответ на команду /start успешно отправлен")
                                    return True
                                else:
                                    logger.error(f"Ошибка при отправке ответа: {result}")
                            else:
                                logger.error(f"Ошибка соединения при отправке ответа: Код {response.status_code}")
                                logger.debug(f"Ответ API: {response.text}")
                else:
                    logger.warning("Не найдено обновлений с командой /start")
            else:
                logger.error(f"Ошибка API: {updates}")
        else:
            logger.error(f"Ошибка соединения при получении обновлений: Код {response.status_code}")
            logger.debug(f"Ответ API: {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при тестировании команды /start: {e}")
        import traceback
        logger.debug(traceback.format_exc())
    
    return False

# Основная функция
def main():
    """Основная функция для диагностики команды /start"""
    logger.info("Запуск диагностики команды /start...")
    
    # Тестируем соединение с API Telegram
    if not test_telegram_api():
        logger.error("Не удалось установить соединение с API Telegram")
        return 1
    
    # Тестируем команду /start
    if test_start_command():
        logger.info("✅ Команда /start работает корректно")
    else:
        logger.warning("⚠️ Не удалось провести полный тест команды /start")
    
    logger.info("Диагностика завершена")
    return 0

if __name__ == "__main__":
    sys.exit(main())