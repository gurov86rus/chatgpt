#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для периодической проверки и перезапуска компонентов системы.
Запускает auto_restart.py через равные промежутки времени.
"""
import os
import sys
import time
import logging
import subprocess
import asyncio
import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scheduled_restart.log")
    ]
)

logger = logging.getLogger("ScheduledRestart")

# Интервал проверки (в секундах)
CHECK_INTERVAL = 15 * 60  # 15 минут

async def run_auto_restart():
    """Запускает скрипт auto_restart.py"""
    logger.info(f"Запуск проверки состояния сервисов ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    try:
        # Используем subprocess для запуска скрипта
        process = await asyncio.create_subprocess_exec(
            sys.executable, "auto_restart.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if stdout:
            logger.info(f"Вывод auto_restart.py: {stdout.decode()}")
        if stderr:
            logger.warning(f"Ошибки auto_restart.py: {stderr.decode()}")
            
        if process.returncode != 0:
            logger.error(f"auto_restart.py завершился с кодом {process.returncode}")
        else:
            logger.info("Проверка успешно завершена")
    except Exception as e:
        logger.error(f"Ошибка при запуске auto_restart.py: {e}")

async def main():
    """Основная функция запуска периодической проверки"""
    logger.info("=" * 50)
    logger.info("Запуск системы периодического мониторинга сервисов")
    logger.info("=" * 50)
    logger.info(f"Интервал проверки: {CHECK_INTERVAL} секунд")
    
    while True:
        try:
            # Запускаем проверку
            await run_auto_restart()
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
        
        # Ждем до следующей проверки
        logger.info(f"Следующая проверка через {CHECK_INTERVAL} секунд")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Запускаем асинхронный цикл
    asyncio.run(main())