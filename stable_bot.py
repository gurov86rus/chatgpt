#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import logging
import requests
import sys
import signal

# Настройка логирования - сделаем его максимально подробным
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stable_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info("Получен сигнал завершения работы {}".format(sig))
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class SimpleBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.running = True
        logger.info("Бот инициализирован")
    
    def api_request(self, method, params=None, json_data=None):
        """Отправляет запрос к API Telegram"""
        url = f"{self.api_url}/{method}"
        try:
            if json_data:
                response = requests.post(url, json=json_data, params=params)
            else:
                response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка API {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка запроса к API: {e}")
            return None
    
    def delete_webhook(self):
        """Удаляет вебхук"""
        logger.info("Удаляем вебхук...")
        result = self.api_request("deleteWebhook", json_data={"drop_pending_updates": True})
        if result and result.get("ok"):
            logger.info("Вебхук успешно удален")
            return True
        return False
    
    def get_me(self):
        """Получает информацию о боте"""
        logger.info("Получаем информацию о боте...")
        result = self.api_request("getMe")
        if result and result.get("ok"):
            bot_info = result.get("result", {})
            logger.info(f"Бот @{bot_info.get('username')} (ID: {bot_info.get('id')}) работает")
            return bot_info
        return None
    
    def get_updates(self, timeout=30):
        """Получает обновления от Telegram"""
        logger.debug(f"Получаем обновления (offset={self.offset}, timeout={timeout})...")
        params = {
            "offset": self.offset,
            "timeout": timeout
        }
        result = self.api_request("getUpdates", params=params)
        if result and result.get("ok"):
            updates = result.get("result", [])
            if updates:
                # Обновляем offset на последнее обновление + 1
                self.offset = updates[-1]["update_id"] + 1
                logger.debug(f"Новый offset: {self.offset}")
            return updates
        return []
    
    def send_message(self, chat_id, text):
        """Отправляет сообщение пользователю"""
        logger.info(f"Отправка сообщения в чат {chat_id}: {text[:30]}...")
        json_data = {
            "chat_id": chat_id,
            "text": text
        }
        result = self.api_request("sendMessage", json_data=json_data)
        if result and result.get("ok"):
            logger.info("Сообщение успешно отправлено")
            return True
        else:
            logger.error(f"Ошибка при отправке сообщения: {result}")
            return False
    
    def handle_message(self, message):
        """Обрабатывает входящее сообщение"""
        if not message.get("text"):
            logger.info("Пропуск сообщения без текста")
            return
        
        chat_id = message["chat"]["id"]
        text = message["text"]
        user = message.get("from", {})
        
        logger.info(f"Получено сообщение от {chat_id}: {text}")
        
        if text == "/start":
            # Приветственное сообщение
            name = user.get("first_name", "пользователь")
            response = f"👋 Привет, {name}! Я бот для управления автопарком.\n\nЯ могу помочь отслеживать:\n- Техническое обслуживание\n- Расход топлива\n- Ремонты\n- Пробеги автомобилей\n\nДля помощи отправьте /help"
            self.send_message(chat_id, response)
        elif text == "/help":
            # Вывод справки
            help_text = "📚 Доступные команды:\n\n/start - Начать работу с ботом\n/help - Вывести это сообщение\n/info - Информация о боте\n/ping - Проверка соединения"
            self.send_message(chat_id, help_text)
        elif text == "/info":
            # Вывод информации
            info_text = "ℹ️ Информация о боте:\n- Версия: Стабильная 1.0\n- Имя: @check_vin_avtobot\n- Ваш ID: {}\n- Текущее время: {}".format(
                user.get("id"), 
                time.strftime("%d.%m.%Y %H:%M:%S")
            )
            self.send_message(chat_id, info_text)
        elif text == "/ping":
            # Проверка соединения
            self.send_message(chat_id, "pong! ⏱️ Задержка минимальная")
        else:
            # Эхо-ответ на остальные сообщения
            self.send_message(chat_id, f"Вы написали: {text}")
    
    def run(self):
        """Запускает бота в бесконечном цикле"""
        if not self.delete_webhook():
            logger.error("Не удалось удалить вебхук, остановка бота")
            return False
        
        bot_info = self.get_me()
        if not bot_info:
            logger.error("Не удалось получить информацию о боте, остановка бота")
            return False
        
        logger.info("Запускаем основной цикл обработки сообщений...")
        
        # Пробуем получить последние обновления перед запуском основного цикла
        updates = self.get_updates(timeout=1)
        if updates:
            logger.info(f"Получено {len(updates)} ожидающих обновлений")
            for update in updates:
                if "message" in update:
                    self.handle_message(update["message"])
        
        # Основной цикл обработки
        while self.running:
            try:
                updates = self.get_updates(timeout=30)
                
                for update in updates:
                    if "message" in update:
                        self.handle_message(update["message"])
                
                # Задержка между запросами только если не было обновлений
                if not updates:
                    time.sleep(1)
            
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания, останавливаем бота")
                self.running = False
            
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(5)  # Пауза перед повторной попыткой
        
        logger.info("Бот остановлен")
        return True

def main():
    # Проверяем наличие токена
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info(f"Токен получен, начинается с {token[:5]}...")
    
    # Создаем и запускаем бота
    bot = SimpleBot(token)
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")