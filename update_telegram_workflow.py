#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления и запуска Telegram бота в workflow
"""
import os
import sys
import logging
import subprocess
import signal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("update_workflow.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_existing_bots():
    """Останавливаем все предыдущие экземпляры ботов"""
    logger.info("Останавливаем все запущенные экземпляры ботов...")
    try:
        subprocess.run(["pkill", "-f", "python.*bot"], check=False)
        logger.info("Боты остановлены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def update_main_script():
    """Обновляем скрипт main.py для запуска полнофункционального бота"""
    logger.info("Обновляем скрипт main.py...")
    
    try:
        with open("main.py", "w") as f:
            f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Основной скрипт для запуска полнофункционального Telegram бота автопарка
\"\"\"
import os
import logging
import subprocess
import sys
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_bot.log")
    ]
)

logger = logging.getLogger(__name__)

def stop_existing_bots():
    \"\"\"Останавливает все запущенные экземпляры ботов\"\"\"
    logger.info("Останавливаем все запущенные боты...")
    try:
        subprocess.run(["pkill", "-f", "python.*bot"], check=False)
        logger.info("Боты остановлены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def check_token():
    \"\"\"Проверяет доступность токена\"\"\"
    logger.info("Проверяем токен...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        try:
            from config import TOKEN
            token = TOKEN
        except:
            logger.error("Токен не найден ни в переменных окружения, ни в config.py")
            return False
    
    if not token:
        logger.error("Токен пустой")
        return False
    
    logger.info("Токен доступен")
    return True

def reset_webhook():
    \"\"\"Сбрасывает вебхук бота\"\"\"
    logger.info("Сбрасываем вебхук...")
    try:
        import requests
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            from config import TOKEN
            token = TOKEN
            
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(url)
        
        if response.status_code == 200 and response.json().get("ok"):
            logger.info("Вебхук успешно сброшен")
            return True
        else:
            logger.error(f"Ошибка при сбросе вебхука: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сбросе вебхука: {e}")
        return False

def main():
    \"\"\"Основная функция\"\"\"
    logger.info("Запускаем полнофункциональный бот автопарка...")
    
    # Останавливаем все запущенные боты
    stop_existing_bots()
    
    # Проверяем токен
    if not check_token():
        logger.error("Ошибка проверки токена. Бот не запущен.")
        return
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем полнофункциональный бот
    try:
        import asyncio
        # Пробуем загрузить основной модуль бота
        try:
            import telegram_bot
            logger.info("Запускаем telegram_bot.py")
            asyncio.run(telegram_bot.main())
        except ImportError:
            try:
                import main_db
                logger.info("Запускаем main_db.py")
                asyncio.run(main_db.main())
            except ImportError:
                import fixed_bot
                logger.info("Запускаем fixed_bot.py")
                asyncio.run(fixed_bot.main())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
""")
        logger.info("Файл main.py успешно обновлен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении main.py: {e}")
        return False

def restart_workflow():
    """Перезапускаем workflow Telegram бота"""
    logger.info("Перезапускаем workflow 'telegram_bot'...")
    try:
        # Попытка перезапустить workflow через restart_workflows.py
        if os.path.exists("restart_workflows.py"):
            subprocess.run([sys.executable, "restart_workflows.py"], check=False)
            logger.info("Скрипт restart_workflows.py выполнен")
        else:
            logger.warning("Файл restart_workflows.py не найден")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при перезапуске workflow: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("Запуск скрипта обновления Telegram бота...")
    
    # Останавливаем все запущенные боты
    kill_existing_bots()
    
    # Обновляем основной скрипт
    update_main_script()
    
    # Перезапускаем workflow
    restart_workflow()
    
    logger.info("Обновление завершено. Бот должен запуститься автоматически через workflow.")
    print("\n\nАвтопарк Telegram бот обновлен!")
    print("Для запуска бота перезапустите workflow 'telegram_bot' в панели Replit.\n")

if __name__ == "__main__":
    main()