from app import app
import os
import sys
import logging
import asyncio
import traceback
import requests

# This file allows both configurations to work:
# 1. The Web Application workflow uses this as "main:app"
# 2. The Telegram Bot workflow runs "python main.py" which uses the code below

# Улучшенная настройка логирования для отладки
logging.basicConfig(
    level=logging.DEBUG,  # Изменено с INFO на DEBUG для большей детализации
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Добавлен обработчик для вывода логов в консоль
        logging.FileHandler("bot_workflow.log")  # Запись логов в файл
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("========================")
    logger.info("Запуск Telegram бота")
    logger.info("========================")
    
    # Запуск нашего стабильного скрипта запуска бота
    try:
        logger.info("Запуск стабильной версии бота...")
        
        # Пробуем запустить наш новый скрипт запуска
        try:
            from run_stable_bot import main as run_stable_bot
            logger.info("✅ Скрипт run_stable_bot.py найден")
            asyncio.run(run_stable_bot())
            sys.exit(0)  # Выход после запуска бота
        except ImportError as e:
            logger.warning(f"Скрипт run_stable_bot.py не найден: {e}")
            
            # Если не найден, пробуем запустить минимальный тестовый бот
            try:
                from minimal_test_bot import main as run_minimal_bot
                logger.info("✅ Запуск минимального тестового бота...")
                asyncio.run(run_minimal_bot())
                sys.exit(0)  # Выход после запуска тестового бота
            except ImportError as e:
                logger.warning(f"Модуль minimal_test_bot.py не найден: {e}")
                
                # Теперь пробуем telegram_only.py
                try:
                    logger.info("Пробуем запустить telegram_only.py...")
                    import subprocess
                    subprocess.run([sys.executable, "telegram_only.py"])
                    sys.exit(0)
                except Exception as e:
                    logger.warning(f"Ошибка при запуске telegram_only.py: {e}")
        
        # Если все предыдущие попытки не удались, запускаем стандартный бот
        try:
            from telegram_bot import main as run_telegram_bot
            logger.info("✅ Модуль telegram_bot успешно импортирован")
            logger.info("Запуск стандартного бота...")
            
            # Сброс вебхука для работы в режиме polling
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if token:
                try:
                    logger.info("Сброс вебхука...")
                    response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
                    webhook_result = response.json()
                    if webhook_result.get('ok'):
                        logger.info("✅ Вебхук успешно сброшен")
                    else:
                        logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
                except Exception as e:
                    logger.warning(f"Ошибка при сбросе вебхука: {e}")
            
            # Запуск основного бота
            asyncio.run(run_telegram_bot())
        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать модуль telegram_bot: {e}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)