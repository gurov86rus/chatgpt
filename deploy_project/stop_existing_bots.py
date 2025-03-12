#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для остановки всех запущенных экземпляров ботов перед запуском нового.
Гарантирует, что будет работать только один экземпляр бота.
"""
import os
import sys
import logging
import subprocess
import time
import signal
import psutil
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_killer.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_bot_processes():
    """
    Находит и останавливает все процессы Python, связанные с запуском ботов
    """
    bot_scripts = [
        "telegram_bot.py", 
        "main.py", 
        "bot_launcher.py",
        "direct_api_bot.py", 
        "enhanced_bot.py", 
        "fixed_bot.py", 
        "simple_callback_bot.py",
        "simple_test_bot.py",
        "stable_bot.py",
        "minimal_test_bot.py"
    ]
    
    current_pid = os.getpid()
    killed_processes = 0
    
    logger.info(f"Ищем запущенные экземпляры ботов (кроме текущего процесса {current_pid})...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Пропускаем текущий процесс
            if proc.info['pid'] == current_pid:
                continue
                
            # Проверяем, является ли процесс Python
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                
                # Проверяем аргументы командной строки
                if cmdline and len(cmdline) > 1:
                    script_name = os.path.basename(cmdline[1])
                    
                    # Проверяем, является ли это процессом бота
                    if script_name in bot_scripts:
                        logger.info(f"Найден процесс бота: PID {proc.info['pid']}, скрипт: {script_name}")
                        
                        # Отправляем сигнал SIGTERM
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        logger.info(f"Отправлен сигнал SIGTERM процессу {proc.info['pid']}")
                        
                        # Даем процессу время на корректное завершение
                        time.sleep(1)
                        
                        # Проверяем, завершился ли процесс
                        if psutil.pid_exists(proc.info['pid']):
                            # Если процесс все еще существует, отправляем SIGKILL
                            os.kill(proc.info['pid'], signal.SIGKILL)
                            logger.info(f"Отправлен сигнал SIGKILL процессу {proc.info['pid']}")
                        
                        killed_processes += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            logger.error(f"Ошибка при попытке завершить процесс: {e}")
            
    logger.info(f"Завершено процессов ботов: {killed_processes}")
    return killed_processes

def reset_webhook():
    """
    Сбрасывает вебхук бота для исключения конфликтов
    """
    try:
        # Проверяем наличие токена в переменных окружения
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            # Пробуем получить токен из конфигурационного файла
            try:
                import config
                token = config.TOKEN
            except Exception as e:
                logger.warning(f"Не удалось получить токен из config.py: {e}")
                return False
            
        # Формируем URL для удаления вебхука
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        
        # Отправляем запрос
        response = requests.get(url)
        
        # Проверяем результат
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.warning(f"Не удалось сбросить вебхук: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("=" * 50)
    logger.info("Запуск скрипта для остановки запущенных ботов")
    logger.info("=" * 50)
    
    # Останавливаем запущенные боты
    killed_count = kill_bot_processes()
    logger.info(f"Остановлено экземпляров ботов: {killed_count}")
    
    # Сбрасываем вебхук
    reset_webhook()
    
    logger.info("Скрипт завершен успешно")
    return killed_count

if __name__ == "__main__":
    main()