#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import logging
import requests
import json
from datetime import datetime

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("enhanced_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def main():
    # Получаем токен
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Используем токен {token[:5]}...")
    
    # Отключаем вебхук с дополнительной проверкой
    try:
        logger.info("Отключаем вебхук...")
        response = requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            json={"drop_pending_updates": True}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Результат отключения вебхука: {result}")
            
            # Проверяем статус вебхука после отключения
            check_response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            if check_response.status_code == 200:
                webhook_info = check_response.json()
                logger.info(f"Информация о вебхуке после отключения: {webhook_info}")
        else:
            logger.error(f"Ошибка при отключении вебхука: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Исключение при отключении вебхука: {e}")
    
    # Проверяем доступность API
    try:
        logger.info("Проверяем доступность API...")
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result["result"]
                logger.info(f"Бот @{bot_info.get('username')} (ID: {bot_info.get('id')}) готов к работе")
            else:
                logger.error(f"API вернул ошибку: {result}")
                return False
        else:
            logger.error(f"Ошибка при проверке API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Исключение при проверке API: {e}")
        return False
    
    # Проверка существующих обновлений перед запуском
    try:
        logger.info("Проверяем наличие ожидающих обновлений...")
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"limit": 5, "timeout": 5}
        )
        
        if response.status_code == 200:
            result = response.json()
            updates = result.get("result", [])
            logger.info(f"Найдено {len(updates)} ожидающих обновлений перед запуском")
            
            if updates:
                for update in updates:
                    logger.info(f"Ожидающее обновление: {json.dumps(update, ensure_ascii=False)}")
                
                # Используем последний update_id как начальный offset
                last_update_id = updates[-1]["update_id"]
                offset = last_update_id + 1
                logger.info(f"Установлен начальный offset={offset} на основе ожидающих обновлений")
            else:
                offset = 0
                logger.info("Ожидающих обновлений нет, устанавливаем offset=0")
        else:
            logger.error(f"Ошибка при проверке обновлений: {response.status_code} - {response.text}")
            offset = 0
    except Exception as e:
        logger.error(f"Исключение при проверке обновлений: {e}")
        offset = 0
    
    # Основной цикл получения обновлений
    logger.info(f"Запускаем основной цикл с offset={offset}...")
    last_request_time = time.time()
    
    try:
        while True:
            try:
                current_time = time.time()
                time_since_last = current_time - last_request_time
                logger.debug(f"Прошло {time_since_last:.2f} сек. с последнего запроса")
                
                # Запрашиваем обновления
                logger.info(f"Запрашиваем обновления с offset={offset}...")
                response = requests.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={
                        "offset": offset,
                        "timeout": 10
                    }
                )
                last_request_time = time.time()
                request_duration = last_request_time - current_time
                logger.debug(f"Запрос занял {request_duration:.2f} сек.")
                
                # Проверяем результат
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении обновлений: {response.status_code} - {response.text}")
                    time.sleep(5)
                    continue
                
                # Разбираем результат
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"Ошибка API: {result}")
                    time.sleep(5)
                    continue
                
                # Обрабатываем обновления
                updates = result.get("result", [])
                logger.info(f"Получено {len(updates)} обновлений")
                
                if updates:
                    for update in updates:
                        logger.info(f"Обрабатываем обновление: {json.dumps(update, ensure_ascii=False)}")
                        
                        # Обновляем offset
                        offset = update["update_id"] + 1
                        logger.debug(f"Обновлен offset={offset}")
                        
                        # Проверяем наличие сообщения
                        if "message" not in update:
                            logger.info(f"Пропускаем обновление без сообщения")
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
                        
                        logger.info(f"Получено сообщение от {chat_id} (user_id: {user.get('id')}): {text}")
                        
                        # Обрабатываем команду /start
                        if text == "/start":
                            # Формируем приветственное сообщение
                            name = user.get("first_name", "пользователь")
                            response_text = f"👋 Привет, {name}! Я улучшенный тестовый бот."
                            
                            # Отправляем ответ
                            logger.info(f"Отправляем приветственное сообщение в чат {chat_id}")
                            send_response = requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={
                                    "chat_id": chat_id,
                                    "text": response_text
                                }
                            )
                            
                            if send_response.status_code == 200:
                                send_result = send_response.json()
                                if send_result.get("ok"):
                                    logger.info(f"Ответ на /start успешно отправлен: {send_result}")
                                else:
                                    logger.error(f"API вернул ошибку при отправке: {send_result}")
                            else:
                                logger.error(f"Ошибка при отправке: {send_response.status_code} - {send_response.text}")
                        
                        # Обрабатываем команду /ping
                        elif text == "/ping":
                            logger.info(f"Отправляем pong в чат {chat_id}")
                            send_response = requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={
                                    "chat_id": chat_id,
                                    "text": f"pong! Время сервера: {datetime.now().strftime('%H:%M:%S')}"
                                }
                            )
                            
                            if send_response.status_code == 200:
                                logger.info("Pong успешно отправлен")
                            else:
                                logger.error(f"Ошибка при отправке pong: {send_response.status_code} - {send_response.text}")
                        
                        # Обрабатываем команду /info
                        elif text == "/info":
                            info_text = (
                                f"📊 Информация о боте:\n"
                                f"- ID бота: 1023647955\n"
                                f"- Имя: @check_vin_avtobot\n"
                                f"- Текущее время: {datetime.now().strftime('%H:%M:%S')}\n"
                                f"- Текущий offset: {offset}\n"
                                f"- Ваш ID: {user.get('id')}\n"
                                f"- Ваш username: @{user.get('username', 'отсутствует')}"
                            )
                            
                            logger.info(f"Отправляем информацию в чат {chat_id}")
                            send_response = requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={
                                    "chat_id": chat_id,
                                    "text": info_text
                                }
                            )
                            
                            if send_response.status_code == 200:
                                logger.info("Информация успешно отправлена")
                            else:
                                logger.error(f"Ошибка при отправке информации: {send_response.status_code} - {send_response.text}")
                        
                        # Любые другие сообщения
                        else:
                            logger.info(f"Отправляем эхо-ответ в чат {chat_id}")
                            send_response = requests.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={
                                    "chat_id": chat_id,
                                    "text": f"Вы отправили: {text}"
                                }
                            )
                            
                            if send_response.status_code == 200:
                                logger.info("Эхо-ответ успешно отправлен")
                            else:
                                logger.error(f"Ошибка при отправке эхо-ответа: {send_response.status_code} - {send_response.text}")
                else:
                    logger.debug("Ожидание новых сообщений...")
                
                # Небольшая пауза между запросами, если не было обновлений
                if not updates:
                    time.sleep(1)
            
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания, останавливаем бота")
                break
            
            except Exception as e:
                logger.error(f"Неожиданное исключение в основном цикле: {e}", exc_info=True)
                time.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    
    logger.info("Бот завершил работу")
    return True

if __name__ == "__main__":
    main()