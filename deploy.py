#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска приложения в режиме деплоя.
Отвечает за запуск веб-интерфейса и Telegram бота.
"""
import os
import sys
import logging
import subprocess
import time
import signal
import threading
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deployment.log")
    ]
)

logger = logging.getLogger(__name__)

def update_token():
    """Обновляет токен Telegram бота при запуске"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        # Если токена нет в переменных окружения, устанавливаем его принудительно
        token = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
        os.environ["TELEGRAM_BOT_TOKEN"] = token
        logger.info(f"Токен установлен (ID: {token.split(':')[0]})")
    else:
        logger.info(f"Найден токен (ID: {token.split(':')[0]})")
        
    # Проверка валидности токена
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Токен успешно проверен")
            return True
        else:
            logger.warning(f"Токен недействителен: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.warning(f"Ошибка при проверке токена: {e}")
        return False

def start_web_interface():
    """Запускает веб-интерфейс через deployment_start.py"""
    logger.info("Запуск веб-интерфейса...")
    
    try:
        # Сначала проверяем наличие файла в папке deploy_project
        if os.path.exists("deploy_project/deployment_start.py"):
            process = subprocess.Popen(
                [sys.executable, "deploy_project/deployment_start.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Веб-интерфейс запущен (PID: {process.pid})")
            return process
        
        # Если файла нет в deploy_project, ищем в корневой директории
        elif os.path.exists("deployment_start.py"):
            process = subprocess.Popen(
                [sys.executable, "deployment_start.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Веб-интерфейс запущен (PID: {process.pid})")
            return process
        
        else:
            logger.error("Не найден файл deployment_start.py")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса: {e}")
        return None

def start_telegram_bot():
    """Запускает Telegram бота через main.py"""
    logger.info("Запуск Telegram бота...")
    
    # Останавливаем все запущенные боты
    try:
        if os.path.exists("deploy_project/stop_existing_bots.py"):
            subprocess.run([sys.executable, "deploy_project/stop_existing_bots.py"], check=False)
        elif os.path.exists("stop_existing_bots.py"):
            subprocess.run([sys.executable, "stop_existing_bots.py"], check=False)
    except Exception as e:
        logger.warning(f"Не удалось остановить существующие боты: {e}")
    
    try:
        # Сначала проверяем наличие файла
        if os.path.exists("main.py"):
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Telegram бот запущен (PID: {process.pid})")
            return process
        else:
            logger.error("Не найден файл main.py")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
        return None

def monitor_process(process, name):
    """Мониторит процесс и перезапускает его при необходимости"""
    if not process:
        logger.warning(f"Не удалось запустить {name}")
        return
        
    while True:
        try:
            # Проверяем, работает ли процесс
            if process.poll() is not None:
                return_code = process.poll()
                logger.warning(f"{name} завершил работу с кодом {return_code}")
                
                # Получаем вывод процесса
                stdout, stderr = process.communicate()
                if stdout:
                    logger.info(f"Вывод {name}:\n{stdout.decode('utf-8', errors='replace')}")
                if stderr:
                    logger.error(f"Ошибки {name}:\n{stderr.decode('utf-8', errors='replace')}")
                
                # Перезапускаем процесс
                logger.info(f"Перезапуск {name}...")
                
                if name == "веб-интерфейс":
                    process = start_web_interface()
                else:
                    process = start_telegram_bot()
                    
                if not process:
                    logger.error(f"Не удалось перезапустить {name}")
                    break
            
            # Пауза между проверками
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания, завершаем мониторинг...")
            break
            
        except Exception as e:
            logger.error(f"Ошибка при мониторинге {name}: {e}")
            time.sleep(30)  # При ошибке делаем паузу подольше

def main():
    """Основная функция запуска деплоя"""
    logger.info("=" * 50)
    logger.info("Запуск деплоя приложения")
    logger.info("=" * 50)
    
    # Обновляем токен
    update_token()
    
    # Запускаем веб-интерфейс
    web_process = start_web_interface()
    
    # Даем веб-интерфейсу время на инициализацию
    time.sleep(3)
    
    # Запускаем Telegram бота
    bot_process = start_telegram_bot()
    
    # Запускаем мониторинг процессов в отдельных потоках
    web_monitor = threading.Thread(
        target=monitor_process,
        args=(web_process, "веб-интерфейс"),
        daemon=True
    )
    web_monitor.start()
    
    bot_monitor = threading.Thread(
        target=monitor_process,
        args=(bot_process, "Telegram бот"),
        daemon=True
    )
    bot_monitor.start()
    
    # Ожидаем сигнала прерывания
    try:
        logger.info("Приложение запущено. Нажмите Ctrl+C для завершения.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершаем работу...")
        
        # Останавливаем процессы
        if web_process and web_process.poll() is None:
            web_process.terminate()
            logger.info("Веб-интерфейс остановлен")
            
        if bot_process and bot_process.poll() is None:
            bot_process.terminate()
            logger.info("Telegram бот остановлен")
            
        logger.info("Приложение остановлено")

if __name__ == "__main__":
    main()