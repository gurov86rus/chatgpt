#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска приложения в режиме деплоя.
Отвечает за запуск веб-интерфейса и Telegram бота.
"""
import os
import sys
import logging
import threading
import time
import subprocess

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deploy.log")
    ]
)

logger = logging.getLogger(__name__)

def update_token():
    """Обновляет токен Telegram бота при запуске"""
    try:
        # Запускаем скрипт обновления токена
        logger.info("Запуск обновления токена...")
        
        # Сначала запускаем startup_token_fix.py, если он существует
        if os.path.exists("startup_token_fix.py"):
            import startup_token_fix
            startup_token_fix.main()
            logger.info("Токен успешно обновлен через startup_token_fix.py")
        else:
            logger.warning("Файл startup_token_fix.py не найден")
            
        # Принудительно устанавливаем токен
        NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        logger.info(f"Токен установлен принудительно: {NEW_TOKEN.split(':')[0]}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении токена: {e}")
        return False

def start_web_interface():
    """Запускает веб-интерфейс через deployment_start.py"""
    try:
        logger.info("Запуск веб-интерфейса...")
        process = subprocess.Popen([sys.executable, "deployment_start.py"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        logger.info(f"Процесс веб-интерфейса запущен (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса: {e}")
        return None

def start_telegram_bot():
    """Запускает Telegram бота через main.py"""
    try:
        logger.info("Запуск Telegram бота...")
        process = subprocess.Popen([sys.executable, "main.py"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        logger.info(f"Процесс Telegram бота запущен (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
        return None

def monitor_process(process, name):
    """Мониторит процесс и перезапускает его при необходимости"""
    if not process:
        logger.error(f"Процесс {name} не запущен")
        return
        
    while True:
        exit_code = process.poll()
        if exit_code is not None:
            logger.warning(f"Процесс {name} завершился с кодом {exit_code}, перезапуск...")
            
            if name == "web":
                process = start_web_interface()
            elif name == "bot":
                process = start_telegram_bot()
                
            if not process:
                logger.error(f"Не удалось перезапустить процесс {name}")
                break
                
        time.sleep(30)  # Проверка каждые 30 секунд

def main():
    """Основная функция запуска деплоя"""
    logger.info("=" * 50)
    logger.info("Запуск приложения в режиме деплоя")
    logger.info("=" * 50)
    
    # Обновляем токен
    update_token()
    
    # Запускаем веб-интерфейс
    web_process = start_web_interface()
    
    # Запускаем Telegram бота
    bot_process = start_telegram_bot()
    
    # Мониторинг процессов в отдельных потоках
    web_monitor = threading.Thread(target=monitor_process, args=(web_process, "web"), daemon=True)
    bot_monitor = threading.Thread(target=monitor_process, args=(bot_process, "bot"), daemon=True)
    
    web_monitor.start()
    bot_monitor.start()
    
    # Держим основной поток активным
    try:
        while True:
            time.sleep(300)  # Проверка каждые 5 минут
            logger.info("Приложение работает в режиме деплоя")
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка в основном потоке: {e}")
    finally:
        logger.info("Завершение работы приложения")
        
        # Останавливаем процессы
        if web_process and web_process.poll() is None:
            web_process.terminate()
        if bot_process and bot_process.poll() is None:
            bot_process.terminate()

if __name__ == "__main__":
    main()