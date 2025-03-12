#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import sys
import logging
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ultra_minimal_bot.log")
    ]
)

logger = logging.getLogger()

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Токен бота не найден в переменных окружения")
        return
    
    logger.info(f"Токен получен, начинается с {token[:5]}...")

    # Очищаем вебхук
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            json={"drop_pending_updates": True}
        )
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно удален")
        else:
            logger.error(f"Ошибка при удалении вебхука: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return

    # Проверяем работоспособность
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200 and response.json().get("ok"):
            bot_info = response.json()["result"]
            logger.info(f"Бот работает: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
        else:
            logger.error(f"Ошибка при проверке бота: {response.text}")
            return
    except Exception as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return

    # Запускаем цикл получения обновлений
    offset = 0
    logger.info("Запускаем цикл обработки сообщений")
    
    try:
        while True:
            try:
                logger.debug(f"Запрашиваем обновления, offset={offset}")
                response = requests.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении обновлений: {response.text}")
                    time.sleep(5)
                    continue
                
                updates = response.json().get("result", [])
                logger.debug(f"Получено {len(updates)} обновлений")
                
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        logger.info(f"Получено сообщение от {chat_id}: {text}")
                        
                        if text == "/start":
                            user = update["message"].get("from", {})
                            name = user.get("first_name", "пользователь")
                            
                            response_text = f"👋 Привет, {name}! Я ультра-минимальный бот для тестирования."
                            logger.info(f"Отправляем приветствие пользователю {chat_id}")
                            
                            requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={"chat_id": chat_id, "text": response_text}
                            )
                        elif text == "/ping":
                            logger.info(f"Отправляем пинг-ответ пользователю {chat_id}")
                            requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={"chat_id": chat_id, "text": "pong"}
                            )
                        else:
                            logger.info(f"Отправляем эхо-ответ пользователю {chat_id}")
                            requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={"chat_id": chat_id, "text": f"Вы отправили: {text}"}
                            )
            
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания, останавливаем бота")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки: {e}")
                time.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    
    logger.info("Бот завершил работу")

if __name__ == "__main__":
    main()