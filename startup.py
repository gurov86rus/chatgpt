#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска всех компонентов системы при старте приложения.
Этот скрипт должен запускаться первым и гарантирует, что
веб-интерфейс и Telegram бот корректно запущены.
"""
import os
import sys
import logging
import subprocess
import time
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("startup.log")
    ]
)

logger = logging.getLogger("Startup")

def check_token():
    """Проверяет наличие токена Telegram бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ Ошибка: токен Telegram бота не установлен")
        print("❌ Ошибка: токен Telegram бота не установлен")
        print("Пожалуйста, добавьте переменную окружения TELEGRAM_BOT_TOKEN")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if response.status_code == 200 and response.json().get("ok"):
            bot_name = response.json().get("result", {}).get("username")
            logger.info(f"✅ Токен Telegram бота валиден (бот: @{bot_name})")
            print(f"✅ Токен Telegram бота валиден (бот: @{bot_name})")
            return True
        else:
            error = response.json().get("description", "Неизвестная ошибка")
            logger.error(f"❌ Ошибка проверки токена Telegram: {error}")
            print(f"❌ Ошибка проверки токена Telegram: {error}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка соединения с API Telegram: {e}")
        print(f"❌ Ошибка соединения с API Telegram: {e}")
        return False

def start_web_interface():
    """Запускает веб-интерфейс"""
    logger.info("Запуск веб-интерфейса...")
    print("Запуск веб-интерфейса...")
    
    try:
        subprocess.run(["replit", "run", "-w", "Start application"], check=False)
        logger.info("✅ Команда запуска веб-интерфейса выполнена")
        print("✅ Веб-интерфейс запущен")
        
        # Даём время на запуск
        time.sleep(5)
        
        # Проверяем, запустился ли веб-интерфейс
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Веб-интерфейс доступен по адресу http://localhost:5000")
                print("✅ Веб-интерфейс доступен по адресу http://localhost:5000")
                return True
            else:
                logger.warning(f"⚠️ Веб-интерфейс вернул код {response.status_code}")
                print(f"⚠️ Веб-интерфейс вернул код {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Веб-интерфейс не отвечает: {e}")
            print(f"⚠️ Веб-интерфейс не отвечает. Попробуйте перезапустить службу вручную")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-интерфейса: {e}")
        print(f"❌ Ошибка запуска веб-интерфейса: {e}")
        return False

def start_telegram_bot():
    """Запускает Telegram бота"""
    logger.info("Запуск Telegram бота...")
    print("Запуск Telegram бота...")
    
    try:
        # Сбрасываем вебхук
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            try:
                requests.get(
                    f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", 
                    timeout=5
                )
                logger.info("✅ Вебхук сброшен")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка сброса вебхука: {e}")
        
        # Запускаем бота
        subprocess.run(["replit", "run", "-w", "telegram_bot"], check=False)
        logger.info("✅ Команда запуска Telegram бота выполнена")
        print("✅ Telegram бот запущен")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
        print(f"❌ Ошибка запуска Telegram бота: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 50)
    print("ЗАПУСК СИСТЕМЫ УПРАВЛЕНИЯ АВТОПАРКОМ")
    print("=" * 50)
    print()
    
    # Проверяем токен
    if not check_token():
        print("\n⚠️ Продолжение с ограниченной функциональностью (без Telegram бота)")
    else:
        print()
    
    # Запускаем компоненты
    web_started = start_web_interface()
    bot_started = start_telegram_bot() if check_token() else False
    
    # Выводим сводку и инструкции
    print("\n" + "=" * 50)
    print("СТАТУС ЗАПУСКА СИСТЕМЫ")
    print("=" * 50)
    print(f"Веб-интерфейс: {'✅ Запущен' if web_started else '❌ Не запущен'}")
    print(f"Telegram бот: {'✅ Запущен' if bot_started else '❌ Не запущен'}")
    print()
    print("Инструкции по управлению системой:")
    print("1. Для мониторинга и автоматического перезапуска сервисов:")
    print("   python scheduled_restart.py")
    print("2. Для ручного управления сервисами:")
    print("   python service_manager.py")
    print("3. Для одновременного запуска и мониторинга сервисов:")
    print("   python start_services.py")
    print("=" * 50)

if __name__ == "__main__":
    main()