#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-интерфейса системы управления автопарком.
Производит проверку доступности порта и инициализацию базы данных.
"""
import os
import sys
import logging
import socket
import subprocess
import signal
import time
import threading
import psutil
import requests

from db_init import init_database
from app import app

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

def check_port_available(port):
    """Проверяет, доступен ли указанный порт"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(('0.0.0.0', port))
        result = True
    except socket.error:
        logger.warning(f"Порт {port} уже занят")
    finally:
        sock.close()
    return result

def find_process_using_port(port):
    """Находит PID процесса, использующего указанный порт"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
    except Exception as e:
        logger.error(f"Ошибка при поиске процесса: {e}")
    return None

def kill_process(pid):
    """Останавливает процесс по PID"""
    logger.info(f"Попытка остановить процесс с PID {pid}")
    try:
        # Сначала пытаемся корректно завершить процесс
        os.kill(pid, signal.SIGTERM)
        
        # Даем процессу время на корректное завершение
        for _ in range(5):  # Ждем не более 5 секунд
            if not psutil.pid_exists(pid):
                logger.info(f"Процесс {pid} успешно остановлен")
                return True
            time.sleep(1)
        
        # Если процесс не завершился, принудительно останавливаем
        os.kill(pid, signal.SIGKILL)
        logger.info(f"Процесс {pid} принудительно остановлен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
        return False

def ensure_port_available(port):
    """Обеспечивает доступность порта, при необходимости останавливая процессы"""
    if check_port_available(port):
        logger.info(f"Порт {port} доступен")
        return True
    
    pid = find_process_using_port(port)
    if not pid:
        logger.warning(f"Порт {port} занят, но не удалось найти соответствующий процесс")
        return False
    
    return kill_process(pid)

def reset_telegram_webhook():
    """Сбрасывает вебхук для избежания конфликтов"""
    logger.info("Сброс вебхука Telegram...")
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            try:
                import config
                token = config.TOKEN
            except Exception:
                logger.warning("Не удалось получить токен Telegram для сброса вебхука")
                return False
        
        # Формируем URL для запроса
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        
        # Отправляем запрос
        response = requests.get(url)
        
        # Проверяем ответ
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.warning(f"Не удалось сбросить вебхук: {response.text}")
            return False
    except Exception as e:
        logger.warning(f"Ошибка при сбросе вебхука: {e}")
        return False

def init_db():
    """Инициализирует базу данных"""
    logger.info("Инициализация базы данных...")
    try:
        init_database()
        logger.info("База данных успешно инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

def start_token_monitor():
    """Запускает мониторинг токена в фоновом режиме"""
    logger.info("Запуск мониторинга токена...")
    try:
        if os.path.exists("token_monitor.py"):
            import token_monitor
            token_monitor.start_monitor_thread()
            logger.info("✅ Запущен фоновый мониторинг токена")
            return True
        else:
            logger.warning("Файл token_monitor.py не найден")
            return False
    except Exception as e:
        logger.warning(f"Ошибка при запуске мониторинга токена: {e}")
        return False

def start_bot_thread():
    """Запускает Telegram бота в отдельном потоке"""
    logger.info("Запуск Telegram бота в отдельном потоке...")
    
    def run_bot():
        try:
            # Останавливаем существующие боты
            if os.path.exists("stop_existing_bots.py"):
                logger.info("Останавливаем существующие боты...")
                import stop_existing_bots
                stopped_count = stop_existing_bots.main()
                logger.info(f"Остановлено {stopped_count} экземпляров ботов")
            
            # Запускаем бота через основной скрипт
            logger.info("Запуск main.py для запуска бота...")
            subprocess.run([sys.executable, "main.py"], check=False)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram бот запущен в фоновом режиме")
    return bot_thread

def get_replit_domain():
    """Получает домен Replit для доступа к приложению извне"""
    replit_domain = None
    try:
        replit_domain = os.environ.get("REPL_SLUG")
        replit_id = os.environ.get("REPL_ID")
        replit_owner = os.environ.get("REPL_OWNER")
        
        if replit_id and replit_owner:
            replit_domain = f"{replit_id}-00-{replit_owner}"
        
        logger.info(f"Домен Replit: {replit_domain}")
    except Exception as e:
        logger.warning(f"Не удалось определить домен Replit: {e}")
        
    return replit_domain

def main():
    """Основная функция запуска веб-интерфейса"""
    logger.info("=" * 50)
    logger.info("Запуск веб-интерфейса системы управления автопарком")
    logger.info("=" * 50)
    
    # Проверка и обновление токена
    try:
        if os.path.exists("startup_token_fix.py"):
            import startup_token_fix
            startup_token_fix.main()
            logger.info("Токен успешно обновлен")
    except Exception as e:
        logger.warning(f"Ошибка при обновлении токена: {e}")
    
    # Запуск мониторинга токена
    start_token_monitor()
    
    # Инициализация базы данных
    init_db()
    
    # Сброс вебхука Telegram
    reset_telegram_webhook()
    
    # Проверка доступности порта
    port = 5000
    if not ensure_port_available(port):
        logger.error(f"Не удалось освободить порт {port}")
        sys.exit(1)
    
    # Получение домена Replit
    replit_domain = get_replit_domain()
    logger.info(f"Домен Replit для доступа извне: {replit_domain}")
    
    # Запуск бота в отдельном потоке
    bot_thread = None
    if 'BOT_DISABLED' not in os.environ:
        bot_thread = start_bot_thread()
    
    # Запуск веб-сервера
    logger.info(f"Запуск веб-сервера на порту {port} (режим: только веб)")
    if replit_domain:
        logger.info(f"Веб-интерфейс будет доступен по адресу: http://{replit_domain}.replit.dev:{port}")
    
    # Запускаем Flask-приложение
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()