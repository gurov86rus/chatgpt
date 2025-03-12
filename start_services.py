#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска всех сервисов приложения: веб-интерфейса и Telegram бота.
Скрипт проверяет доступность портов, останавливает конфликтующие процессы
и обеспечивает корректный запуск компонентов.
"""
import os
import sys
import time
import socket
import logging
import psutil
import subprocess
import signal
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("services.log")
    ]
)

logger = logging.getLogger(__name__)

# Порт для веб-интерфейса
WEB_PORT = 5000

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
                connections = proc.info.get('connections', [])
                if connections:
                    for conn in connections:
                        if conn.laddr.port == port:
                            return proc.info['pid']
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
            process = psutil.Process(pid)
            process.terminate()
            
            # Даем процессу время на корректное завершение
            gone, alive = psutil.wait_procs([process], timeout=3)
            
            # Если процесс все еще работает, принудительно завершаем
            if process in alive:
                logger.warning(f"Процесс {pid} не завершился, принудительная остановка")
                process.kill()
            
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при остановке процесса {pid}: {e}")
    
    return False

def kill_processes_by_name(pattern):
    """Останавливает процессы, соответствующие указанному шаблону"""
    current_pid = os.getpid()
    killed = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue  # Пропускаем текущий процесс
                
            cmdline = ' '.join(proc.info.get('cmdline') or [])
            if pattern in cmdline:
                # Не останавливаем процессы workflow
                if 'workflow' not in cmdline and 'replit' not in cmdline:
                    logger.info(f"Найден процесс для остановки: PID {proc.info['pid']}, команда: {cmdline[:50]}...")
                    if kill_process(proc.info['pid']):
                        killed.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return killed

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
        logger.error(f"Не удалось определить процесс, использующий порт {port}")
        return False

def check_telegram_token():
    """Проверяет доступность токена Telegram"""
    logger.info("Проверка токена Telegram...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    # Проверяем соединение с API
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                bot_username = bot_data.get('username', 'Unknown')
                bot_id = bot_data.get('id', 'Unknown')
                logger.info(f"Соединение с API Telegram успешно! Бот @{bot_username} (ID: {bot_id})")
                return True
        
        logger.error(f"Ошибка при проверке токена: {response.text}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения с API Telegram: {e}")
        return False

def reset_telegram_webhook():
    """Сбрасывает вебхук Telegram бота"""
    logger.info("Сброс вебхука Telegram...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
        if response.status_code == 200 and response.json().get('ok'):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.error(f"Ошибка при сбросе вебхука: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
        return False

def start_web_interface():
    """Запускает веб-интерфейс"""
    logger.info("Запуск веб-интерфейса...")
    
    # Проверяем доступность порта для веб-интерфейса
    if not ensure_port_available(WEB_PORT):
        logger.error(f"Не удалось обеспечить доступность порта {WEB_PORT}")
        return None
    
    try:
        # Запускаем веб-интерфейс в отдельном процессе
        process = subprocess.Popen(
            [sys.executable, "deployment_start.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Веб-интерфейс запущен с PID {process.pid}")
        
        # Даем время на запуск
        time.sleep(3)
        
        # Проверяем, не завершился ли процесс с ошибкой
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Веб-интерфейс завершился с кодом {process.returncode}")
            logger.error(f"Вывод: {stdout}")
            logger.error(f"Ошибки: {stderr}")
            return None
        
        logger.info("Веб-интерфейс успешно запущен")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса: {e}")
        return None

def start_telegram_bot():
    """Запускает Telegram бота"""
    logger.info("Запуск Telegram бота...")
    
    if not check_telegram_token():
        logger.error("Проблема с токеном Telegram")
        return None
    
    if not reset_telegram_webhook():
        logger.warning("Проблема со сбросом вебхука, но продолжаем...")
    
    try:
        # Запускаем бота в отдельном процессе
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Telegram бот запущен с PID {process.pid}")
        
        # Даем время на запуск
        time.sleep(3)
        
        # Проверяем, не завершился ли процесс с ошибкой
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Telegram бот завершился с кодом {process.returncode}")
            logger.error(f"Вывод: {stdout}")
            logger.error(f"Ошибки: {stderr}")
            return None
        
        logger.info("Telegram бот успешно запущен")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
        return None

def monitor_processes(web_process, bot_process):
    """Мониторит запущенные процессы и перезапускает их при необходимости"""
    logger.info("Начало мониторинга процессов...")
    
    try:
        while True:
            # Проверяем веб-интерфейс
            if web_process and web_process.poll() is not None:
                logger.warning("Веб-интерфейс остановился, перезапуск...")
                web_process = start_web_interface()
            
            # Проверяем Telegram бота
            if bot_process and bot_process.poll() is not None:
                logger.warning("Telegram бот остановился, перезапуск...")
                bot_process = start_telegram_bot()
            
            # Пауза между проверками
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки мониторинга")
        
        # Корректно останавливаем процессы
        if web_process and web_process.poll() is None:
            logger.info("Останавливаем веб-интерфейс...")
            web_process.terminate()
        
        if bot_process and bot_process.poll() is None:
            logger.info("Останавливаем Telegram бота...")
            bot_process.terminate()
        
        logger.info("Мониторинг процессов завершен")

def main():
    """Основная функция запуска и мониторинга сервисов"""
    logger.info("=" * 50)
    logger.info("Запуск сервисов приложения")
    logger.info("=" * 50)
    
    # Останавливаем все существующие экземпляры приложения
    kill_processes_by_name("deployment_start.py")
    kill_processes_by_name("telegram_bot.py")
    kill_processes_by_name("main.py")
    
    # Запускаем веб-интерфейс
    web_process = start_web_interface()
    if not web_process:
        logger.error("Не удалось запустить веб-интерфейс")
        return 1
    
    # Запускаем Telegram бота
    bot_process = start_telegram_bot()
    if not bot_process:
        logger.error("Не удалось запустить Telegram бота")
        # Останавливаем веб-интерфейс
        if web_process and web_process.poll() is None:
            web_process.terminate()
        return 1
    
    # Мониторим процессы
    monitor_processes(web_process, bot_process)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())