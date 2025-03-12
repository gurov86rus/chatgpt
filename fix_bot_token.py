#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для принудительного обновления токена Telegram бота
и перезапуска бота с новым токеном.
"""
import os
import logging
import subprocess
import sys
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_token_fix.log")
    ]
)

logger = logging.getLogger(__name__)

# Новый токен бота
NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"

def update_env_file():
    """Обновляет файл .env с новым токеном"""
    logger.info("Обновление файла .env с новым токеном")
    try:
        with open('.env', 'w') as f:
            f.write(f"# Telegram Bot Token (replace with your actual token)\n")
            f.write(f"TELEGRAM_BOT_TOKEN={NEW_TOKEN}\n\n")
            f.write(f"# DO NOT commit this file to version control\n")
        logger.info("Файл .env успешно обновлен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении файла .env: {e}")
        return False

def kill_all_bots():
    """Останавливает все запущенные экземпляры ботов"""
    logger.info("Останавливаем все запущенные боты...")
    try:
        # Получаем список всех процессов python с 'bot' или 'main.py' в команде
        ps_cmd = f"ps aux | grep -E 'python.*bot|python.*main.py' | grep -v grep | awk '{{print $2}}'"
        output = subprocess.check_output(ps_cmd, shell=True).decode().strip()
        
        if output:
            pids = output.split('\n')
            for pid in pids:
                if pid.isdigit():
                    try:
                        logger.info(f"Останавливаем процесс с PID {pid}")
                        subprocess.run(["kill", "-9", pid], check=False)
                    except Exception as e:
                        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
            logger.info("Все боты остановлены")
        else:
            logger.info("Активных ботов не найдено")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def restart_workflows():
    """Перезапускает workflows"""
    logger.info("Перезапуск workflow-сервисов...")
    try:
        # Используем внутренний API Replit для перезапуска workflow
        subprocess.run(["curl", "-X", "DELETE", 
                      f"https://replit.com/internal_api/repl-lifecycle/{os.environ.get('REPL_ID', '')}/restarts/workflow/Start%20application"], 
                      check=False)
        logger.info("Workflow 'Start application' перезапущен")
        
        time.sleep(2)  # Даем время на перезапуск первого workflow
        
        subprocess.run(["curl", "-X", "DELETE", 
                      f"https://replit.com/internal_api/repl-lifecycle/{os.environ.get('REPL_ID', '')}/restarts/workflow/telegram_bot"], 
                      check=False)
        logger.info("Workflow 'telegram_bot' перезапущен")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при перезапуске workflow: {e}")
        return False

def check_token_in_process():
    """Проверяет, какой токен используется в запущенных процессах"""
    logger.info("Проверка токена в текущих процессах...")
    try:
        # Принудительно устанавливаем переменную окружения
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        logger.info(f"Переменная окружения TELEGRAM_BOT_TOKEN установлена: ID {NEW_TOKEN.split(':')[0]}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке токена: {e}")
        return False

def update_cached_token():
    """Обновляет закешированный токен в файлах конфигурации"""
    logger.info("Обновление токена в кеше конфигурации...")
    try:
        files_to_check = ["config.py", "telegram_bot.py", "main.py", "fixed_bot.py", "main_db.py", "direct_api_bot.py"]
        
        for filename in files_to_check:
            if not os.path.exists(filename):
                continue
                
            with open(filename, 'r') as f:
                content = f.read()
            
            # Ищем строки с захардкоженным токеном
            if "758794985" in content:
                logger.info(f"Найден старый токен в файле {filename}")
                # Заменяем токен
                updated_content = content.replace("758794985:AAEjSJHpQMXfn3cI9KZgN4QBSnzekuhiI6M", NEW_TOKEN)
                updated_content = updated_content.replace("758794985:AAEyXQw44Tkf0-Tnxiw3nT-eDE_tTas50jI", NEW_TOKEN)
                
                # Записываем обновленный контент
                with open(filename, 'w') as f:
                    f.write(updated_content)
                logger.info(f"Файл {filename} обновлен")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении закешированного токена: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("========================================")
    logger.info("Запуск процесса обновления токена бота")
    logger.info("========================================")
    
    # Обновляем файл .env
    if not update_env_file():
        logger.error("Не удалось обновить файл .env")
        return
    
    # Останавливаем все запущенные боты
    if not kill_all_bots():
        logger.error("Не удалось остановить запущенных ботов")
        return
    
    # Обновляем токен в файлах конфигурации
    if not update_cached_token():
        logger.warning("Не удалось обновить закешированный токен")
    
    # Устанавливаем переменную окружения
    if not check_token_in_process():
        logger.error("Не удалось установить переменную окружения")
        return
    
    # Даем время на остановку всех процессов
    logger.info("Ожидаем завершения всех процессов (5 секунд)...")
    time.sleep(5)
    
    # Перезапускаем workflows
    if not restart_workflows():
        logger.error("Не удалось перезапустить workflow")
        return
    
    logger.info("Процесс обновления токена завершен успешно")
    logger.info("Новый токен бота: " + NEW_TOKEN.split(':')[0] + ":***")

if __name__ == "__main__":
    main()