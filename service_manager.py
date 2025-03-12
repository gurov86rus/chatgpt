#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для интерактивного управления сервисами системы автопарка.
Позволяет запускать, останавливать и перезапускать компоненты системы.
"""
import os
import sys
import subprocess
import time
import logging
import requests
import signal
import psutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("service_manager.log")
    ]
)

logger = logging.getLogger("ServiceManager")

def display_menu():
    """Отображает меню управления сервисами"""
    print("\n" + "=" * 40)
    print("Управление сервисами системы автопарка")
    print("=" * 40)
    print("1. Перезапустить веб-интерфейс")
    print("2. Перезапустить Telegram бот")
    print("3. Перезапустить все сервисы")
    print("4. Проверить статус сервисов")
    print("5. Запустить мониторинг сервисов (автоматический перезапуск)")
    print("0. Выход")
    print("=" * 40)

def start_web_interface():
    """Запускает веб-интерфейс через workflow"""
    try:
        subprocess.run(["replit", "run", "-w", "Start application"])
        logger.info("Команда запуска веб-интерфейса выполнена")
        print("✅ Веб-интерфейс запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса: {e}")
        print(f"❌ Ошибка при запуске веб-интерфейса: {e}")

def start_telegram_bot():
    """Запускает Telegram бот через workflow"""
    try:
        subprocess.run(["replit", "run", "-w", "telegram_bot"])
        logger.info("Команда запуска Telegram бота выполнена")
        print("✅ Telegram бот запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
        print(f"❌ Ошибка при запуске Telegram бота: {e}")

def check_web_interface():
    """Проверяет, работает ли веб-интерфейс"""
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Веб-интерфейс работает нормально")
            print("✅ Веб-интерфейс работает нормально")
            return True
        else:
            logger.warning(f"⚠️ Веб-интерфейс вернул код {response.status_code}")
            print(f"⚠️ Веб-интерфейс вернул код {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Веб-интерфейс недоступен: {e}")
        print(f"❌ Веб-интерфейс недоступен: {type(e).__name__}")
        return False

def check_telegram_bot():
    """Проверяет, работает ли Telegram бот"""
    # Проверяем токен и API
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ Токен Telegram бота не установлен")
        print("❌ Токен Telegram бота не установлен")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if response.status_code == 200 and response.json().get("ok"):
            username = response.json().get("result", {}).get("username")
            logger.info(f"✅ Telegram бот ({username}) отвечает на API запросы")
            print(f"✅ Telegram бот ({username}) отвечает на API запросы")
            
            # Проверка процесса
            bot_process_found = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'python' in cmdline and ('main.py' in cmdline or 'telegram_bot.py' in cmdline):
                        logger.info(f"✅ Найден процесс Telegram бота: PID {proc.info['pid']}")
                        print(f"✅ Найден процесс Telegram бота: PID {proc.info['pid']}")
                        bot_process_found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if not bot_process_found:
                logger.warning("⚠️ Процесс Telegram бота не найден, возможно работает в другом окружении")
                print("⚠️ Процесс Telegram бота не найден, возможно работает в другом окружении")
            
            return True
        else:
            logger.error(f"❌ Ошибка API Telegram: {response.json()}")
            print(f"❌ Ошибка API Telegram: {response.json().get('description', 'Неизвестная ошибка')}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка связи с API Telegram: {e}")
        print(f"❌ Ошибка связи с API Telegram: {type(e).__name__}")
        return False

def run_auto_restart():
    """Запускает скрипт auto_restart.py"""
    print("Запуск проверки и перезапуска сервисов...")
    try:
        result = subprocess.run(
            [sys.executable, "auto_restart.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Ошибки: {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"auto_restart.py завершился с кодом {result.returncode}")
            print(f"❌ Перезапуск завершился с ошибкой (код {result.returncode})")
        else:
            logger.info("Перезапуск успешно выполнен")
            print("✅ Перезапуск успешно выполнен")
    except Exception as e:
        logger.error(f"Ошибка при запуске auto_restart.py: {e}")
        print(f"❌ Ошибка при выполнении перезапуска: {e}")

def start_monitoring():
    """Запускает scheduled_restart.py в фоновом режиме"""
    print("Запуск автоматического мониторинга сервисов...")
    try:
        # Запускаем в фоновом режиме
        subprocess.Popen(
            [sys.executable, "scheduled_restart.py"],
            stdout=open("scheduled_restart_output.log", "a"),
            stderr=open("scheduled_restart_error.log", "a"),
            start_new_session=True
        )
        logger.info("Мониторинг сервисов запущен")
        print("✅ Мониторинг сервисов запущен в фоновом режиме")
    except Exception as e:
        logger.error(f"Ошибка при запуске мониторинга: {e}")
        print(f"❌ Ошибка при запуске мониторинга: {e}")

def main():
    """Основная функция управления сервисами"""
    print("Запуск менеджера сервисов системы автопарка")
    
    while True:
        display_menu()
        choice = input("Выберите действие (0-5): ")
        
        if choice == '1':
            print("Перезапуск веб-интерфейса...")
            start_web_interface()
        elif choice == '2':
            print("Перезапуск Telegram бота...")
            start_telegram_bot()
        elif choice == '3':
            print("Перезапуск всех сервисов...")
            start_web_interface()
            start_telegram_bot()
        elif choice == '4':
            print("\nПроверка статуса сервисов...")
            check_web_interface()
            check_telegram_bot()
        elif choice == '5':
            start_monitoring()
        elif choice == '0':
            print("Выход из программы управления сервисами")
            break
        else:
            print("❌ Неверный выбор. Пожалуйста, выберите действие из меню (0-5).")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    main()