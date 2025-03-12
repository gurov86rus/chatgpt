#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
import time
import logging
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("direct_bot.log")
    ]
)

logger = logging.getLogger(__name__)

class DirectTelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.last_update_id = 0
        self.running = False
    
    def api_request(self, method, params=None):
        """Отправляет запрос к API Telegram"""
        url = self.api_url + method
        try:
            response = requests.post(url, json=params) if params else requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка API запроса {method}: {e}")
            return None
    
    def get_me(self):
        """Получает информацию о боте"""
        result = self.api_request("getMe")
        if result and result.get("ok"):
            return result["result"]
        return None
    
    def delete_webhook(self):
        """Удаляет вебхук"""
        result = self.api_request("deleteWebhook", {"drop_pending_updates": True})
        if result and result.get("ok"):
            logger.info("Вебхук успешно удален")
            return True
        logger.error(f"Ошибка при удалении вебхука: {result}")
        return False
    
    def get_updates(self, offset=None, timeout=30):
        """Получает обновления от Telegram"""
        params = {
            "timeout": timeout
        }
        if offset:
            params["offset"] = offset
        
        result = self.api_request("getUpdates", params)
        if result and result.get("ok"):
            return result["result"]
        return []
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Отправляет сообщение пользователю"""
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            params["reply_markup"] = reply_markup
        
        result = self.api_request("sendMessage", params)
        if result and result.get("ok"):
            logger.info(f"Сообщение отправлено пользователю {chat_id}")
            return True
        logger.error(f"Ошибка при отправке сообщения: {result}")
        return False
    
    def handle_start_command(self, message):
        """Обрабатывает команду /start"""
        chat_id = message["chat"]["id"]
        user = message.get("from", {})
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        
        response_text = (
            f"👋 Привет, {full_name}!\n\n"
            f"Я бот для учета данных транспортных средств.\n"
            f"Через меня вы можете отслеживать техническое обслуживание, заправки и ремонты.\n\n"
            f"Ваш ID: {user.get('id')}"
        )
        
        self.send_message(chat_id, response_text)
    
    def handle_message(self, message):
        """Обрабатывает входящее сообщение"""
        if "text" not in message:
            return
        
        text = message["text"]
        chat_id = message["chat"]["id"]
        
        # Обработка команды /start
        if text == "/start":
            logger.info(f"Получена команда /start от пользователя {chat_id}")
            self.handle_start_command(message)
        else:
            # Эхо-ответ для всех остальных сообщений
            self.send_message(chat_id, f"Вы отправили: {text}\n\nЭто тестовый бот, используйте /start")
    
    def run(self):
        """Запускает цикл обработки сообщений"""
        logger.info("Запуск бота через прямые вызовы API...")
        
        # Удаляем вебхук перед запуском
        if not self.delete_webhook():
            logger.warning("Не удалось удалить вебхук, но продолжаем работу")
        
        # Получаем информацию о боте
        me = self.get_me()
        if not me:
            logger.critical("Не удалось получить информацию о боте. Проверьте токен.")
            return
        
        logger.info(f"Бот запущен: @{me.get('username')} (ID: {me.get('id')})")
        
        self.running = True
        while self.running:
            try:
                updates = self.get_updates(offset=self.last_update_id + 1)
                for update in updates:
                    # Обновляем last_update_id
                    self.last_update_id = update["update_id"]
                    
                    # Обрабатываем сообщение
                    if "message" in update:
                        self.handle_message(update["message"])
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания, останавливаем бота")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки сообщений: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(5)  # Пауза перед следующей попыткой

def main():
    # Получаем токен из переменных окружения
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return
    
    # Останавливаем все запущенные боты
    try:
        os.system("pkill -f 'python.*bot' || true")
        time.sleep(1)  # Даем время на остановку процессов
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
    
    # Создаем экземпляр бота и запускаем его
    bot = DirectTelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()