#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import asyncio
import requests
import time
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("working_minimal_bot.log")
    ]
)

logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.last_update_id = 0
        self.running = False
        
    def send_request(self, method, params=None):
        """Отправляет запрос к API Telegram"""
        url = f"{self.api_url}{method}"
        try:
            if params:
                response = requests.post(url, json=params)
            else:
                response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка API запроса {method}: {e}")
            return None
            
    def get_me(self):
        """Получает информацию о боте"""
        return self.send_request("getMe")
        
    def delete_webhook(self):
        """Удаляет вебхук"""
        return self.send_request("deleteWebhook", {"drop_pending_updates": True})
        
    def get_updates(self, offset=None, timeout=30):
        """Получает обновления"""
        params = {"timeout": timeout}
        if offset:
            params["offset"] = offset
        result = self.send_request("getUpdates", params)
        if result and result.get("ok") and "result" in result:
            return result["result"]
        return []
        
    def send_message(self, chat_id, text):
        """Отправляет сообщение"""
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        return self.send_request("sendMessage", params)
        
    def run(self):
        """Запускает бота"""
        logger.info("Запуск бота через прямое API...")
        
        # Проверяем соединение
        me_info = self.get_me()
        if not me_info or not me_info.get("ok"):
            logger.error("Не удалось получить информацию о боте")
            return
            
        bot_info = me_info["result"]
        logger.info(f"Бот запущен: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
        
        # Удаляем вебхук
        webhook_result = self.delete_webhook()
        if not webhook_result or not webhook_result.get("ok"):
            logger.error("Не удалось удалить вебхук")
            return
            
        logger.info("Вебхук успешно удален")
        
        # Основной цикл
        self.running = True
        while self.running:
            try:
                # Получаем обновления
                updates = self.get_updates(offset=self.last_update_id + 1)
                
                # Обрабатываем обновления
                for update in updates:
                    self.last_update_id = update["update_id"]
                    
                    # Обрабатываем сообщения
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message["text"]
                        
                        # Обрабатываем команду /start
                        if text == "/start":
                            user = message.get("from", {})
                            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                            
                            response_text = (
                                f"👋 Привет, {full_name}!\n\n"
                                f"Я бот для учета данных транспортных средств.\n"
                                f"Через меня вы можете отслеживать техническое обслуживание, заправки и ремонты.\n\n"
                                f"Ваш ID: {user.get('id')}"
                            )
                            
                            self.send_message(chat_id, response_text)
                        else:
                            # Отвечаем на все остальные сообщения
                            self.send_message(chat_id, "Используйте команду /start для начала работы")
                            
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания")
                self.running = False
                break
                
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(5)  # Пауза перед следующей попыткой

def kill_existing_bots():
    """Останавливает существующие процессы бота"""
    try:
        os.system("pkill -f 'python.*bot' || true")
        time.sleep(2)  # Ждем остановки
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")

def main():
    logger.info("Запуск минимального бота Telegram...")
    
    # Получаем токен
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN не найден")
        return
        
    logger.info(f"Токен получен, начинается с {token[:5]}...")
    
    # Останавливаем существующие боты
    kill_existing_bots()
    
    # Запускаем бота
    bot = SimpleTelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()