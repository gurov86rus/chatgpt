#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import logging
import requests
import subprocess
import time
import psutil

# Настройка логирования с самым подробным уровнем
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_launcher.log")
    ]
)

logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

def kill_existing_bots():
    """Останавливает все существующие процессы бота"""
    logger.info("Проверка и остановка существующих процессов бота...")
    current_pid = os.getpid()
    telegram_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'python' in cmdline and ('telegram_bot' in cmdline or 'bot.py' in cmdline or 'main.py' in cmdline):
                    logger.info(f"Найден процесс бота: PID {proc.info['pid']}, CMD: {cmdline[:50]}...")
                    telegram_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if telegram_processes:
        logger.warning(f"Останавливаем процессы бота: {telegram_processes}")
        for pid in telegram_processes:
            try:
                logger.info(f"Завершение процесса {pid}...")
                psutil.Process(pid).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"Не удалось завершить процесс {pid}: {e}")
        
        # Даем время на завершение процессов
        time.sleep(2)
        
        # Проверяем, остались ли какие-то процессы
        for pid in telegram_processes:
            try:
                if psutil.pid_exists(pid):
                    logger.warning(f"Процесс {pid} все еще работает, принудительное завершение...")
                    psutil.Process(pid).kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    else:
        logger.info("Существующих процессов бота не найдено")

def reset_webhook():
    """Сбрасывает вебхук бота"""
    logger.info("Сброс вебхука...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
        webhook_result = response.json()
        if webhook_result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
            return True
        else:
            logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
    
    return False

def check_api_connection():
    """Проверяет соединение с API Telegram"""
    logger.info("Проверка соединения с API Telegram...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                bot_username = bot_data.get('username', 'Unknown')
                bot_id = bot_data.get('id', 'Unknown')
                logger.info(f"✅ Соединение с API успешно установлено! Бот @{bot_username} (ID: {bot_id})")
                return True
            else:
                logger.error(f"Ошибка API: {bot_info}")
        else:
            logger.error(f"Ошибка соединения с API Telegram: Код {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения с API: {e}")
    
    return False

def run_minimal_bot():
    """Запускает минимальный тестовый бот"""
    logger.info("Запуск минимального тестового бота...")
    try:
        process = subprocess.Popen(["python", "minimal_test_bot.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        logger.info(f"Минимальный тестовый бот запущен с PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске минимального бота: {e}")
        return None

def main():
    """Основная функция"""
    logger.info("====================================")
    logger.info("Запуск процесса управления ботом")
    logger.info("====================================")
    
    # Останавливаем существующие процессы бота
    kill_existing_bots()
    
    # Сбрасываем вебхук
    if not reset_webhook():
        logger.error("Не удалось сбросить вебхук, но продолжаем...")
    
    # Проверяем соединение с API
    if not check_api_connection():
        logger.error("Не удалось установить соединение с API Telegram")
        return 1
    
    # Запускаем минимальный тестовый бот
    bot_process = run_minimal_bot()
    if not bot_process:
        logger.error("Не удалось запустить тестовый бот")
        return 1
    
    # Ждем некоторое время, чтобы увидеть вывод бота
    logger.info("Ожидаем запуска бота...")
    time.sleep(5)
    
    # Проверяем, работает ли бот все еще
    if bot_process.poll() is not None:
        stdout, stderr = bot_process.communicate()
        logger.error(f"Бот завершился с кодом {bot_process.returncode}")
        logger.error(f"Вывод бота (stdout): {stdout}")
        logger.error(f"Ошибки бота (stderr): {stderr}")
        return 1
    
    logger.info("Бот успешно запущен и работает")
    logger.info("Для остановки бота используйте Ctrl+C")
    
    try:
        # Ждем сигнала остановки
        bot_process.wait()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки, завершаем бота...")
        bot_process.terminate()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())