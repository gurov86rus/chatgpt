#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматического запуска обоих компонентов системы:
1. Веб-интерфейс (workflow: Start application)
2. Telegram бот (workflow: telegram_bot)

Скрипт также проверяет состояние работающих процессов и 
при необходимости перезапускает их.
"""
import os
import sys
import subprocess
import time
import logging
import requests
import socket
import signal
import psutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auto_restart.log")
    ]
)

logger = logging.getLogger("AutoRestart")

def check_port_in_use(port):
    """Проверяет, занят ли порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Освобождает указанный порт, завершая процесс, который его использует"""
    logger.info(f"Попытка освободить порт {port}...")
    try:
        # Находим PID процесса, который занимает порт
        output = subprocess.check_output(f"lsof -i :{port} -t", shell=True).decode().strip()
        if output:
            pid = int(output)
            logger.info(f"Найден процесс с PID {pid}, использующий порт {port}")
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)  # Даём процессу время на завершение
            if psutil.pid_exists(pid):
                logger.warning(f"Процесс {pid} всё ещё работает, применяем SIGKILL")
                os.kill(pid, signal.SIGKILL)
            logger.info(f"Порт {port} освобождён")
            return True
    except subprocess.CalledProcessError:
        logger.info(f"Не найден процесс, использующий порт {port}")
    except Exception as e:
        logger.error(f"Ошибка при освобождении порта {port}: {e}")
    
    return False

def restart_web_workflow():
    """Перезапускает веб-интерфейс"""
    logger.info("Перезапуск веб-интерфейса (workflow: Start application)...")
    
    # Проверяем, занят ли порт 5000
    if check_port_in_use(5000):
        logger.warning("Порт 5000 занят, попытка освободить...")
        try:
            # Используем альтернативный метод, если lsof не установлен
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'python' in cmdline and 'deployment_start.py' in cmdline:
                        logger.info(f"Найден процесс веб-интерфейса: PID {proc.info['pid']}")
                        psutil.Process(proc.info['pid']).terminate()
                        time.sleep(1)
                        if psutil.pid_exists(proc.info['pid']):
                            psutil.Process(proc.info['pid']).kill()
                        logger.info(f"Процесс веб-интерфейса остановлен")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.error(f"Ошибка при освобождении порта 5000: {e}")
    
    # Запускаем веб-интерфейс
    try:
        subprocess.Popen(["replit", "run", "-w", "Start application"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
        logger.info("Команда запуска веб-интерфейса выполнена")
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-интерфейса: {e}")
        try:
            # Альтернативный метод запуска
            subprocess.Popen([sys.executable, "deployment_start.py"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            logger.info("Веб-интерфейс запущен альтернативным методом")
        except Exception as e2:
            logger.error(f"Ошибка при альтернативном запуске веб-интерфейса: {e2}")

def restart_bot_workflow():
    """Перезапускает Telegram бот"""
    logger.info("Перезапуск Telegram бота (workflow: telegram_bot)...")
    
    # Останавливаем текущие экземпляры бота
    try:
        # Ищем процессы бота, исключая этот скрипт
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] != current_pid:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'python' in cmdline and ('main.py' in cmdline or 'telegram_bot.py' in cmdline):
                        logger.info(f"Найден процесс бота: PID {proc.info['pid']}")
                        psutil.Process(proc.info['pid']).terminate()
                        time.sleep(1)
                        if psutil.pid_exists(proc.info['pid']):
                            psutil.Process(proc.info['pid']).kill()
                        logger.info(f"Процесс бота остановлен")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"Ошибка при остановке процессов бота: {e}")
    
    # Запускаем Telegram бот
    try:
        subprocess.Popen(["replit", "run", "-w", "telegram_bot"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
        logger.info("Команда запуска Telegram бота выполнена")
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
        try:
            # Альтернативный метод запуска
            subprocess.Popen([sys.executable, "main.py"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            logger.info("Telegram бот запущен альтернативным методом")
        except Exception as e2:
            logger.error(f"Ошибка при альтернативном запуске Telegram бота: {e2}")

def check_web_interface():
    """Проверяет, работает ли веб-интерфейс"""
    logger.info("Проверка работы веб-интерфейса...")
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Веб-интерфейс работает нормально")
            return True
        else:
            logger.warning(f"Веб-интерфейс вернул код {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Веб-интерфейс недоступен: {e}")
        return False

def check_telegram_bot():
    """Проверяет, работает ли Telegram бот"""
    logger.info("Проверка работы Telegram бота...")
    # Проверяем по наличию процесса
    bot_running = False
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'python' in cmdline and ('main.py' in cmdline or 'telegram_bot.py' in cmdline):
                    logger.info(f"✅ Найден процесс Telegram бота: PID {proc.info['pid']}")
                    bot_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"Ошибка при проверке процессов Telegram бота: {e}")
    
    if not bot_running:
        logger.warning("Процесс Telegram бота не найден")
    
    return bot_running

def main():
    """Основная функция"""
    logger.info("=" * 50)
    logger.info("Запуск системы автоматического перезапуска компонентов")
    logger.info("=" * 50)
    
    # Проверяем состояние веб-интерфейса и при необходимости перезапускаем
    if not check_web_interface():
        logger.warning("Веб-интерфейс не работает, перезапуск...")
        restart_web_workflow()
    
    # Проверяем состояние Telegram бота и при необходимости перезапускаем
    if not check_telegram_bot():
        logger.warning("Telegram бот не работает, перезапуск...")
        restart_bot_workflow()
    
    logger.info("Система автоматического перезапуска завершила работу")

if __name__ == "__main__":
    main()