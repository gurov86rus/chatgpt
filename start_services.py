#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска всех сервисов приложения: веб-интерфейса и Telegram бота.
Скрипт проверяет доступность портов, останавливает конфликтующие процессы
и обеспечивает корректный запуск компонентов.
"""
import os
import sys
import subprocess
import logging
import time
import signal
import psutil
import requests
import socket
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("services.log")
    ]
)

logger = logging.getLogger("ServiceManager")

def check_port_available(port):
    """Проверяет, доступен ли указанный порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except socket.error:
            return False

def find_process_using_port(port):
    """Находит PID процесса, использующего указанный порт"""
    try:
        output = subprocess.check_output(f"lsof -i :{port} -t", shell=True).decode().strip()
        if output:
            return int(output)
    except subprocess.CalledProcessError:
        pass
    return None

def kill_process(pid):
    """Останавливает процесс по PID"""
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)  # Даём процессу время на завершение
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
        return False

def kill_processes_by_name(pattern):
    """Останавливает процессы, соответствующие указанному шаблону"""
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if pattern in cmdline:
                logger.info(f"Найден процесс {pattern}: PID {proc.info['pid']}")
                kill_process(proc.info['pid'])
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed

def ensure_port_available(port):
    """Обеспечивает доступность порта, при необходимости останавливая процессы"""
    if check_port_available(port):
        logger.info(f"Порт {port} доступен")
        return True
    
    pid = find_process_using_port(port)
    if pid:
        logger.warning(f"Порт {port} занят процессом с PID {pid}")
        if kill_process(pid):
            logger.info(f"Процесс с PID {pid} остановлен")
            time.sleep(1)  # Даём порту время на освобождение
            return check_port_available(port)
    else:
        logger.warning(f"Не удалось найти процесс, занимающий порт {port}")
    
    return False

def check_telegram_token():
    """Проверяет доступность токена Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Токен Telegram бота не установлен")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if response.status_code == 200 and response.json().get("ok"):
            username = response.json().get("result", {}).get("username")
            logger.info(f"✅ Токен Telegram бота верный (бот: {username})")
            return True
        else:
            logger.error(f"❌ Ошибка API Telegram: {response.json()}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка связи с API Telegram: {e}")
        return False

def reset_telegram_webhook():
    """Сбрасывает вебхук Telegram бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Токен Telegram бота не установлен")
        return False
    
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true",
            timeout=5
        )
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("✅ Вебхук Telegram бота успешно сброшен")
            return True
        else:
            logger.error(f"❌ Ошибка сброса вебхука: {response.json()}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка связи с API Telegram: {e}")
        return False

def start_web_interface():
    """Запускает веб-интерфейс"""
    logger.info("Запуск веб-интерфейса...")
    
    # Проверяем доступность порта 5000
    if not ensure_port_available(5000):
        logger.error("Не удалось освободить порт 5000, веб-интерфейс не может быть запущен")
        return None
    
    # Останавливаем предыдущие экземпляры веб-интерфейса
    kill_processes_by_name("deployment_start.py")
    
    # Запускаем веб-интерфейс через workflow
    try:
        process = subprocess.Popen(
            ["replit", "run", "-w", "Start application"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Веб-интерфейс запущен (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса: {e}")
        try:
            # Альтернативный метод запуска
            process = subprocess.Popen(
                [sys.executable, "deployment_start.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Веб-интерфейс запущен альтернативным методом (PID: {process.pid})")
            return process
        except Exception as e2:
            logger.error(f"Ошибка при альтернативном запуске веб-интерфейса: {e2}")
            return None

def start_telegram_bot():
    """Запускает Telegram бота"""
    logger.info("Запуск Telegram бота...")
    
    # Проверяем токен Telegram
    if not check_telegram_token():
        logger.error("Проблема с токеном Telegram, бот не может быть запущен")
        return None
    
    # Сбрасываем вебхук
    reset_telegram_webhook()
    
    # Останавливаем предыдущие экземпляры бота
    kill_processes_by_name("main.py")
    kill_processes_by_name("telegram_bot.py")
    
    # Запускаем бота через workflow
    try:
        process = subprocess.Popen(
            ["replit", "run", "-w", "telegram_bot"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Telegram бот запущен (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
        try:
            # Альтернативный метод запуска
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Telegram бот запущен альтернативным методом (PID: {process.pid})")
            return process
        except Exception as e2:
            logger.error(f"Ошибка при альтернативном запуске Telegram бота: {e2}")
            return None

def monitor_processes(web_process, bot_process):
    """Мониторит запущенные процессы и перезапускает их при необходимости"""
    def check_web():
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_bot():
        # Проверяем, что процесс бота существует
        if bot_process and bot_process.poll() is None:
            return True
        return False
    
    while True:
        logger.info("Проверка состояния сервисов...")
        
        # Проверяем веб-интерфейс
        if not check_web():
            logger.warning("Веб-интерфейс не отвечает, перезапуск...")
            if web_process:
                try:
                    web_process.terminate()
                    time.sleep(1)
                except:
                    pass
            web_process = start_web_interface()
        
        # Проверяем Telegram бота
        if not check_bot():
            logger.warning("Telegram бот не отвечает, перезапуск...")
            if bot_process:
                try:
                    bot_process.terminate()
                    time.sleep(1)
                except:
                    pass
            bot_process = start_telegram_bot()
        
        # Ждем до следующей проверки
        logger.info("Сервисы работают нормально, следующая проверка через 60 секунд")
        time.sleep(60)

def main():
    """Основная функция запуска и мониторинга сервисов"""
    logger.info("=" * 50)
    logger.info("Запуск всех сервисов системы")
    logger.info("=" * 50)
    
    # Запускаем веб-интерфейс
    web_process = start_web_interface()
    
    # Даём веб-интерфейсу время на запуск
    time.sleep(5)
    
    # Запускаем Telegram бота
    bot_process = start_telegram_bot()
    
    # Запускаем мониторинг в отдельном потоке
    monitor_thread = threading.Thread(
        target=monitor_processes,
        args=(web_process, bot_process),
        daemon=True
    )
    monitor_thread.start()
    
    logger.info("Все сервисы запущены, мониторинг активен")
    logger.info("Нажмите Ctrl+C для завершения")
    
    try:
        # Бесконечный цикл, чтобы программа не завершалась
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Завершение работы...")
        # Останавливаем процессы при выходе
        if web_process:
            web_process.terminate()
        if bot_process:
            bot_process.terminate()

if __name__ == "__main__":
    main()