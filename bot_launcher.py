#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import logging
import requests
import psutil
import time
import subprocess
import signal

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_launcher.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_existing_bots():
    """Останавливает все существующие процессы бота"""
    logger.info("Поиск и остановка существующих процессов бота...")
    current_pid = os.getpid()
    killed = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Ищем процессы Python с ключевыми словами, связанными с ботом
                if 'python' in cmdline and any(x in cmdline for x in ['telegram_bot', 'bot.py', 'minimal_test_bot']):
                    logger.info(f"Останавливаем процесс бота: PID {proc.info['pid']}, команда: {cmdline}")
                    try:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        killed = True
                    except Exception as e:
                        logger.error(f"Не удалось остановить процесс {proc.info['pid']}: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Ждем некоторое время, чтобы процессы успели завершиться
    if killed:
        logger.info("Ожидание завершения процессов...")
        time.sleep(2)
    
    return killed

def reset_webhook():
    """Сбрасывает вебхук бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    try:
        logger.info("Сброс вебхука...")
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
            return True
        else:
            logger.error(f"Ошибка при сбросе вебхука: {result}")
            return False
    except Exception as e:
        logger.error(f"Не удалось сбросить вебхук: {e}")
        return False

def check_api_connection():
    """Проверяет соединение с API Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    try:
        logger.info("Проверка соединения с API Telegram...")
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                bot_username = bot_data.get('username', 'Unknown')
                bot_id = bot_data.get('id', 'Unknown')
                logger.info(f"✅ Соединение с API успешно! Бот @{bot_username} (ID: {bot_id})")
                return True
            else:
                logger.error(f"Ошибка API: {bot_info}")
                return False
        else:
            logger.error(f"Ошибка соединения с API Telegram: Код {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Не удалось подключиться к API Telegram: {e}")
        return False

def run_minimal_bot():
    """Запускает минимальный тестовый бот"""
    logger.info("Запуск минимального тестового бота...")
    try:
        # Проверяем, существует ли файл
        if not os.path.exists("minimal_test_bot.py"):
            logger.error("Файл minimal_test_bot.py не найден")
            return False
        
        # Запускаем бот в отдельном процессе
        process = subprocess.Popen([sys.executable, "minimal_test_bot.py"], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # Даем боту время на инициализацию
        time.sleep(3)
        
        # Проверяем, не завершился ли процесс с ошибкой
        if process.poll() is not None:
            out, err = process.communicate()
            logger.error(f"Бот завершился с кодом {process.returncode}")
            logger.error(f"Вывод: {out}")
            logger.error(f"Ошибки: {err}")
            return False
        
        logger.info(f"✅ Минимальный тестовый бот успешно запущен (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("=" * 50)
    logger.info("Запуск лаунчера бота")
    logger.info("=" * 50)
    
    # Остановка существующих экземпляров бота
    kill_existing_bots()
    
    # Сброс вебхука
    if not reset_webhook():
        logger.warning("Продолжаем несмотря на проблемы со сбросом вебхука")
    
    # Проверка соединения с API
    if not check_api_connection():
        logger.error("❌ Не удалось подтвердить соединение с API Telegram")
        sys.exit(1)
    
    # Запуск минимального бота для тестирования
    if run_minimal_bot():
        logger.info("✅ Тестовый бот успешно запущен")
    else:
        logger.error("❌ Не удалось запустить тестовый бот")
        sys.exit(1)
    
    logger.info("Лаунчер бота завершил работу")

if __name__ == "__main__":
    main()