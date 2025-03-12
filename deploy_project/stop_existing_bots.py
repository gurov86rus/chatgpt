#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для остановки всех запущенных экземпляров ботов перед запуском нового.
Гарантирует, что будет работать только один экземпляр бота.
"""
import os
import sys
import logging
import signal
import psutil
import time
import platform
import subprocess
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def kill_bot_processes():
    """
    Находит и останавливает все процессы Python, связанные с запуском ботов
    """
    current_pid = os.getpid()
    killed_count = 0
    bot_patterns = [
        "telegram_bot.py",
        "main.py",
        "bot.py",
        "tg_bot.py",
        "run_bot.py",
        "simple_bot.py",
        "simple_callback_bot.py"
    ]
    
    logger.info(f"Ищем запущенные экземпляры ботов (кроме текущего процесса {current_pid})...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Пропускаем текущий процесс
            if proc.info['pid'] == current_pid:
                continue
                
            # Пропускаем процессы не относящиеся к Python
            if not proc.info['name'] in ['python', 'python3', 'python3.10', 'python3.11']:
                continue
                
            cmdline = proc.info['cmdline']
            if not cmdline:
                continue
                
            # Ищем в командной строке процесса признаки запущенного бота
            is_bot = False
            for item in cmdline:
                for pattern in bot_patterns:
                    if pattern in item:
                        is_bot = True
                        break
                if is_bot:
                    break
                    
            if is_bot:
                pid = proc.info['pid']
                bot_script = cmdline[-1] if cmdline else "неизвестный скрипт"
                logger.info(f"Найден процесс бота: PID {pid}, скрипт: {bot_script}")
                
                # Отправляем сигнал SIGTERM для корректного завершения
                try:
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"Отправлен сигнал SIGTERM процессу {pid}")
                    killed_count += 1
                except Exception as e:
                    logger.warning(f"Не удалось остановить процесс {pid}: {e}")
                    
                    # На Windows используем taskkill для принудительного завершения
                    if platform.system() == 'Windows':
                        try:
                            subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                            logger.info(f"Процесс {pid} принудительно остановлен через taskkill")
                            killed_count += 1
                        except Exception as e:
                            logger.error(f"Не удалось остановить процесс {pid} через taskkill: {e}")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    return killed_count

def reset_webhook():
    """
    Сбрасывает вебхук бота для исключения конфликтов
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        try:
            # Пытаемся импортировать config для получения токена
            if os.path.exists("config.py"):
                sys.path.append(os.getcwd())
                import config
                token = config.TOKEN
            else:
                logger.warning("Файл config.py не найден")
        except Exception as e:
            logger.warning(f"Не удалось импортировать config: {e}")
    
    if not token:
        logger.warning("Токен бота не найден, пропускаем сброс вебхука")
        return False
        
    try:
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.warning(f"Не удалось сбросить вебхук: {response.text}")
            return False
    except Exception as e:
        logger.warning(f"Ошибка при сбросе вебхука: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("=" * 50)
    logger.info("Запуск скрипта для остановки запущенных ботов")
    logger.info("=" * 50)
    
    # Останавливаем запущенные боты
    killed_count = kill_bot_processes()
    
    # Даем время на корректное завершение процессов
    if killed_count > 0:
        logger.info(f"Ждем {killed_count} секунд для корректного завершения процессов...")
        time.sleep(min(killed_count, 3))  # Ждем не более 3 секунд
        
    # Сбрасываем вебхук
    reset_webhook()
    
    logger.info(f"Остановлено ботов: {killed_count}")
    return killed_count

if __name__ == "__main__":
    main()