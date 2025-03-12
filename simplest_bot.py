#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import logging
import requests
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simplest_bot.log")
    ]
)

logger = logging.getLogger(__name__)

# Используем самый простой цикл без декораторов и сложной логики
def main():
    # Получаем токен
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Используем токен {token[:5]}...")
    
    # Отключаем вебхук
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            json={"drop_pending_updates": True}
        )
        logger.info(f"Отключение вебхука: {response.status_code} - {response.json() if response.text else 'Нет ответа'}")
    except Exception as e:
        logger.error(f"Ошибка при отключении вебхука: {e}")
    
    # Проверяем работу бота
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        result = response.json()
        if result.get("ok"):
            bot_info = result["result"]
            logger.info(f"Бот @{bot_info.get('username')} (ID: {bot_info.get('id')}) успешно запущен")
        else:
            logger.error(f"Ошибка при проверке бота: {result}")
            return False
    except Exception as e:
        logger.error(f"Исключение при проверке бота: {e}")
        return False
    
    # Основной цикл получения обновлений
    offset = 0
    logger.info("Запускаем основной цикл...")
    
    while True:
        try:
            # Получаем обновления
            logger.info(f"Запрашиваем обновления (offset={offset})...")
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 5
                }
            )
            
            # Проверяем результат
            if response.status_code != 200:
                logger.error(f"Ошибка при получении обновлений: {response.status_code} - {response.text}")
                time.sleep(3)
                continue
            
            # Разбираем результат
            result = response.json()
            if not result.get("ok"):
                logger.error(f"Ошибка API: {result}")
                time.sleep(3)
                continue
            
            # Обрабатываем обновления
            updates = result.get("result", [])
            logger.info(f"Получено {len(updates)} обновлений")
            
            for update in updates:
                # Обновляем offset
                offset = max(offset, update["update_id"] + 1)
                
                # Проверяем наличие сообщения
                if "message" not in update:
                    logger.info(f"Пропускаем обновление без сообщения: {update}")
                    continue
                
                message = update["message"]
                
                # Проверяем наличие текста
                if "text" not in message:
                    logger.info("Пропускаем сообщение без текста")
                    continue
                
                # Получаем данные сообщения
                chat_id = message["chat"]["id"]
                text = message["text"]
                user = message.get("from", {})
                
                logger.info(f"Получено сообщение от {chat_id}: {text}")
                
                # Обрабатываем команду /start
                if text == "/start":
                    # Формируем приветственное сообщение
                    name = user.get("first_name", "пользователь")
                    response_text = f"👋 Привет, {name}! Я самый простой бот для тестирования."
                    
                    # Отправляем ответ
                    try:
                        send_response = requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": response_text
                            }
                        )
                        
                        if send_response.status_code == 200 and send_response.json().get("ok"):
                            logger.info(f"Ответ на /start успешно отправлен пользователю {chat_id}")
                        else:
                            logger.error(f"Ошибка при отправке ответа: {send_response.status_code} - {send_response.text}")
                    
                    except Exception as e:
                        logger.error(f"Исключение при отправке ответа: {e}")
                
                # Любые другие сообщения
                else:
                    try:
                        send_response = requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": f"Вы отправили: {text}"
                            }
                        )
                        
                        if send_response.status_code == 200:
                            logger.info(f"Эхо-ответ успешно отправлен пользователю {chat_id}")
                        else:
                            logger.error(f"Ошибка при отправке эхо-ответа: {send_response.status_code} - {send_response.text}")
                    
                    except Exception as e:
                        logger.error(f"Исключение при отправке эхо-ответа: {e}")
            
            # Небольшая пауза между запросами
            time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания, останавливаем бота")
            break
        
        except Exception as e:
            logger.error(f"Неожиданное исключение в основном цикле: {e}")
            time.sleep(5)
    
    return True

if __name__ == "__main__":
    main()