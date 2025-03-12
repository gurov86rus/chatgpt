
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-интерфейса системы управления автопарком.
Производит проверку доступности порта и инициализацию базы данных.
"""
import os
import logging
import sys
import socket
import requests
import time
import psutil
import signal
from db_init import init_database
from app import app

# Порт для веб-интерфейса
WEB_PORT = 5000

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("web_application.log")
    ]
)

logger = logging.getLogger(__name__)

def check_port_available(port):
    """Проверяет, доступен ли указанный порт"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    available = True
    try:
        sock.bind(('0.0.0.0', port))
    except socket.error:
        available = False
    finally:
        sock.close()
    return available

def find_process_using_port(port):
    """Находит PID процесса, использующего указанный порт"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == port:
                        return proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"Ошибка при поиске процесса, использующего порт {port}: {e}")
    return None

def kill_process(pid):
    """Останавливает процесс по PID"""
    try:
        current_pid = os.getpid()
        if pid != current_pid:  # Не убиваем самих себя
            logger.info(f"Останавливаем процесс с PID {pid}")
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)  # Даем процессу время на завершение
            
            # Проверяем, завершился ли процесс
            if psutil.pid_exists(pid):
                logger.warning(f"Процесс {pid} не завершился, принудительная остановка")
                os.kill(pid, signal.SIGKILL)
            
            return True
    except Exception as e:
        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
    
    return False

def ensure_port_available(port):
    """Обеспечивает доступность порта, при необходимости останавливая процессы"""
    if check_port_available(port):
        logger.info(f"Порт {port} доступен")
        return True
    
    logger.warning(f"Порт {port} занят")
    pid = find_process_using_port(port)
    
    if pid:
        logger.info(f"Порт {port} используется процессом с PID {pid}")
        if kill_process(pid):
            time.sleep(1)  # Даем время на освобождение порта
            if check_port_available(port):
                logger.info(f"Порт {port} успешно освобожден")
                return True
            else:
                logger.error(f"Не удалось освободить порт {port}")
                return False
    else:
        # Альтернативный способ, если psutil не смог найти процесс
        try:
            logger.info(f"Попытка освободить порт {port} через команду fuser")
            os.system(f"fuser -k {port}/tcp 2>/dev/null || true")
            time.sleep(2)
            
            if check_port_available(port):
                logger.info(f"Порт {port} успешно освобожден через fuser")
                return True
        except Exception as e:
            logger.error(f"Ошибка при использовании fuser: {e}")
        
        logger.error(f"Не удалось освободить порт {port}")
        return False

def reset_telegram_webhook():
    """Сбрасывает вебхук для избежания конфликтов"""
    # Принудительно устанавливаем новый токен бота
    NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
    os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
    logger.info(f"Принудительно установлен новый токен бота (ID: {NEW_TOKEN.split(':')[0]})")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не найден. Веб-интерфейс будет запущен без бота.")
        return True
    
    try:
        logger.info("Сброс вебхука для избежания конфликтов...")
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
        webhook_result = response.json()
        
        if webhook_result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
            return True
        else:
            logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
    except Exception as e:
        logger.warning(f"Ошибка при попытке сбросить вебхук: {e}")
    
    return False

def init_db():
    """Инициализирует базу данных"""
    try:
        init_database()
        logger.info("База данных успешно инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        logger.error(f"Трассировка стека: {sys.exc_info()}")
        return False

def main():
    """Основная функция запуска веб-интерфейса"""
    logger.info("=" * 50)
    logger.info("Запуск веб-интерфейса системы управления автопарком")
    logger.info("=" * 50)
    
    # Проверяем и освобождаем порт, если занят
    if not ensure_port_available(WEB_PORT):
        logger.error(f"Не удалось обеспечить доступность порта {WEB_PORT}. Веб-интерфейс не запущен.")
        return 1
    
    # Сбрасываем вебхук для избежания конфликтов
    reset_telegram_webhook()
    
    # Инициализируем базу данных
    if not init_db():
        logger.warning("Инициализация базы данных не удалась. Возможны проблемы с функциональностью.")
    
    # Получаем информацию о домене Replit
    replit_domain = os.environ.get("REPLIT_DOMAINS", "").split(",")[0]
    logger.info(f"Домен Replit для доступа извне: {replit_domain}")
    
    # Запускаем Flask-приложение
    logger.info(f"Запуск веб-сервера на порту {WEB_PORT} (режим: только веб)")
    try:
        logger.info(f"Веб-интерфейс будет доступен по адресу: http://{replit_domain if replit_domain else '0.0.0.0'}:{WEB_PORT}")
        app.run(host='0.0.0.0', port=WEB_PORT, threaded=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-сервера: {e}")
        return 1
    
    return 0

# Основная точка входа скрипта
if __name__ == "__main__":
    sys.exit(main())
