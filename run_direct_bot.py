#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio
import multiprocessing
import time
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_direct.log")
    ]
)

logger = logging.getLogger("bot")

def test_telegram_api():
    """Тестирование соединения с API Telegram без aiogram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Тестирование API Telegram с токеном (ID: {token.split(':')[0]})")
    
    try:
        # Базовый запрос getMe
        url = f"https://api.telegram.org/bot{token}/getMe"
        logger.info(f"Отправка запроса к {url}")
        
        response = requests.get(url, timeout=10)
        logger.info(f"Получен ответ: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API ответ: {data}")
            if data.get('ok'):
                bot_username = data['result'].get('username')
                logger.info(f"Успешное соединение с ботом @{bot_username}")
                return True
            else:
                logger.error(f"API вернул ошибку: {data}")
        else:
            logger.error(f"Ошибка соединения: {response.status_code}")
            logger.error(f"Тело ответа: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при тестировании API: {e}")
    
    return False

def run_simple_bot():
    """Запуск простого бота через прямые API вызовы"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден")
        return
    
    # Первая проверка API
    if not test_telegram_api():
        logger.error("Тест API завершился с ошибкой. Невозможно продолжить.")
        return
    
    logger.info("Запуск простого бота через polling...")
    
    # Сброс webhook на всякий случай
    try:
        url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        response = requests.get(url)
        logger.info(f"Сброс webhook: {response.json()}")
    except Exception as e:
        logger.error(f"Ошибка при сбросе webhook: {e}")
    
    # Основной цикл polling
    offset = None
    
    try:
        while True:
            try:
                # Запрос обновлений
                params = {'timeout': 30}
                if offset:
                    params['offset'] = offset
                
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                response = requests.get(url, params=params, timeout=35)
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении обновлений: {response.status_code}")
                    logger.error(response.text)
                    time.sleep(5)
                    continue
                
                updates = response.json()
                
                if not updates.get('ok'):
                    logger.error(f"API вернул ошибку: {updates}")
                    time.sleep(5)
                    continue
                
                results = updates.get('result', [])
                
                if results:
                    logger.info(f"Получено {len(results)} обновлений")
                    
                    # Обновляем offset - берем ID последнего обновления + 1
                    offset = results[-1]['update_id'] + 1
                    
                    # Обрабатываем каждое обновление
                    for update in results:
                        logger.info(f"Обработка обновления: {update}")
                        
                        # Если есть сообщение
                        if 'message' in update and 'text' in update['message']:
                            chat_id = update['message']['chat']['id']
                            message_text = update['message']['text']
                            
                            logger.info(f"Получено сообщение от {chat_id}: {message_text}")
                            
                            # Если это команда /start
                            if message_text == '/start':
                                reply = "👋 Привет! Я простой тестовый бот."
                            # Если это любое другое сообщение
                            else:
                                reply = f"Вы написали: {message_text}"
                            
                            # Отправляем ответ
                            send_url = f"https://api.telegram.org/bot{token}/sendMessage"
                            send_data = {
                                'chat_id': chat_id,
                                'text': reply
                            }
                            
                            send_response = requests.post(send_url, json=send_data)
                            logger.info(f"Ответ отправлен: {send_response.status_code}")
                
                time.sleep(1)  # Небольшая пауза
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка сети: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(5)
                
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

if __name__ == "__main__":
    logger.info("Запуск программы тестирования Telegram API")
    
    try:
        # Запуск в отдельном процессе для изоляции
        bot_process = multiprocessing.Process(target=run_simple_bot)
        bot_process.start()
        logger.info(f"Бот запущен в процессе {bot_process.pid}")
        
        # Ожидание завершения процесса
        bot_process.join()
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())