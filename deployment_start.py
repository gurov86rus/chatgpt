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
        # Получаем токен из переменных окружения
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            try:
                # Если токена нет в переменных, пытаемся импортировать модуль config
                import config
                token = getattr(config, "TOKEN", None)
                if not token:
                    logger.warning("Не найден токен в модуле config")
                    return False
            except Exception as e:
                logger.warning(f"Не удалось импортировать модуль config: {e}")
                return False
        
        # Пробуем загрузить токен из deploy_project/config.py если есть
        if not token and os.path.exists("deploy_project/config.py"):
            sys.path.append("deploy_project")
            try:
                import config as deploy_config
                token = getattr(deploy_config, "TOKEN", None)
                if token:
                    logger.info(f"Найден токен в deploy_project/config.py")
            except Exception as e:
                logger.warning(f"Не удалось импортировать deploy_project/config.py: {e}")
        
        if not token:
            logger.warning("Не удалось получить токен Telegram, невозможно сбросить вебхук")
            return False
            
        # Проверка токена
        logger.info(f"Используется токен с ID: {token.split(':')[0] if ':' in token else '?'}")
            
        # Формируем URL для сброса вебхука
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        
        # Отправляем запрос
        response = requests.get(url, timeout=10)
        
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
        # Попытка импортировать модуль из корневой директории
        if os.path.exists("db_init.py"):
            logger.info("Импорт db_init.py из корневой директории")
            sys.path.append(os.getcwd())
            import db_init
            db_init.init_database()
            logger.info("База данных успешно инициализирована")
            return True
            
        # Попытка импортировать модуль из директории deploy_project
        elif os.path.exists("deploy_project/db_init.py"):
            logger.info("Импорт db_init.py из директории deploy_project")
            sys.path.append(os.path.join(os.getcwd(), "deploy_project"))
            from deploy_project import db_init
            db_init.init_database()
            logger.info("База данных успешно инициализирована")
            return True
            
        else:
            logger.warning("Не найден файл db_init.py")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

def start_bot_thread():
    """Запускает Telegram бота в отдельном потоке"""
    logger.info("Запуск Telegram бота в отдельном потоке...")
    
    def run_bot():
        try:
            # Проверяем наличие файлов для запуска
            if os.path.exists("main.py"):
                logger.info("Запуск main.py для запуска бота...")
                subprocess.run([sys.executable, "main.py"], check=False)
            elif os.path.exists("telegram_bot.py"):
                logger.info("Запуск telegram_bot.py...")
                subprocess.run([sys.executable, "telegram_bot.py"], check=False)
            else:
                logger.warning("Не найдены файлы main.py или telegram_bot.py для запуска бота")
                
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
        replit_slug = os.environ.get("REPL_SLUG")
        replit_id = os.environ.get("REPL_ID")
        replit_owner = os.environ.get("REPL_OWNER")
        
        if replit_id and replit_owner:
            replit_domain = f"https://{replit_id}.{replit_owner}.repl.co"
            logger.info(f"Домен Replit: {replit_domain}")
        elif replit_slug:
            logger.info(f"Slug Replit: {replit_slug}")
        
    except Exception as e:
        logger.warning(f"Не удалось определить домен Replit: {e}")
        
    return replit_domain

def main():
    """Основная функция запуска веб-интерфейса"""
    logger.info("=" * 50)
    logger.info("Запуск веб-интерфейса системы управления автопарком")
    logger.info("=" * 50)
    
    # Проверка наличия модуля config
    try:
        # Сначала пытаемся импортировать из папки deploy_project
        if os.path.exists("deploy_project/config.py"):
            sys.path.insert(0, os.path.join(os.getcwd(), "deploy_project"))
            import config
            logger.info("Модуль config.py из deploy_project успешно импортирован")
        # Если не удалось, пытаемся импортировать из корневой директории
        elif os.path.exists("config.py"):
            sys.path.insert(0, os.getcwd())
            import config
            logger.info("Модуль config.py из корневой директории успешно импортирован")
    except Exception as e:
        logger.warning(f"Ошибка при импорте модуля config: {e}")
    
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
    if replit_domain:
        logger.info(f"Веб-интерфейс будет доступен по адресу: {replit_domain}")
    
    # Запуск бота в отдельном потоке, если он не запрещен переменной окружения
    bot_thread = None
    if not os.environ.get("BOT_DISABLED"):
        bot_thread = start_bot_thread()
    
    # Запуск веб-сервера
    logger.info(f"Запуск веб-сервера на порту {port}")
    
    # Запускаем Flask-приложение
    try:
        # Сначала пытаемся импортировать из папки deploy_project
        if os.path.exists("deploy_project/app.py"):
            sys.path.insert(0, os.path.join(os.getcwd(), "deploy_project"))
            from app import app
            logger.info("Запуск веб-приложения из deploy_project/app.py")
        # Если не удалось, пытаемся импортировать из корневой директории
        elif os.path.exists("app.py"):
            from app import app
            logger.info("Запуск веб-приложения из app.py")
        else:
            logger.error("Не найден файл app.py")
            sys.exit(1)
            
        # Запускаем приложение
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске Flask-приложения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()