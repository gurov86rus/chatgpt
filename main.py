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
    
    # Проверка наличия переменной окружения с токеном
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
        logger.info("Пожалуйста, установите переменную TELEGRAM_BOT_TOKEN в Secrets (в разделе 'Tools' -> 'Secrets')")
        # Вывод список всех доступных переменных окружения для диагностики
        env_vars = [k for k in os.environ.keys() if not k.startswith("_")]
        logger.info(f"Доступные переменные окружения: {', '.join(env_vars)}")
        sys.exit(1)
    else:
        # Логирование части токена для диагностики (безопасно, только первые цифры)
        token_parts = token.split(':')
        if len(token_parts) >= 2:
            token_id = token_parts[0]
            token_length = len(token)
            logger.info(f"Токен бота найден (ID: {token_id}, длина: {token_length} символов)")
        else:
            logger.warning("Формат токена может быть некорректным, проверьте его")
    
    # Проверяем, нет ли других экземпляров бота
    try:
        # Попытка получить список запущенных процессов
        import psutil
        current_pid = os.getpid()
        telegram_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] != current_pid:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'python' in cmdline and ('telegram_bot' in cmdline or 'main.py' in cmdline):
                        telegram_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if telegram_processes:
            logger.warning(f"Обнаружены другие процессы бота: {telegram_processes}")
            # В данный момент мы просто логируем, но не останавливаем их
    except ImportError:
        logger.info("Модуль psutil не найден, пропускаем проверку процессов")
    except Exception as e:
        logger.warning(f"Ошибка при проверке процессов: {e}")
    
    # Проверка доступности API Telegram
    try:
        # Сброс вебхука для работы в режиме polling
        logger.info("Сброс вебхука...")
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
        webhook_result = response.json()
        if webhook_result.get('ok'):
            logger.info("✅ Вебхук успешно сброшен")
        else:
            logger.warning(f"Проблема при сбросе вебхука: {webhook_result}")
        
        # Тест соединения с API Telegram через getMe
        logger.info("Проверка соединения с API Telegram...")
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                bot_username = bot_data.get('username', 'Unknown')
                bot_id = bot_data.get('id', 'Unknown')
                logger.info(f"✅ Соединение с API успешно установлено! Бот @{bot_username} (ID: {bot_id})")
            else:
                logger.error(f"Ошибка API: {bot_info}")
        else:
            logger.error(f"Ошибка соединения с API Telegram: Код {response.status_code}")
            logger.debug(f"Ответ API: {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Не удалось подключиться к API Telegram: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при проверке API: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)
    
    # Запуск бота через aiogram
    try:
        logger.info("Запуск минимального тестового бота...")
        
        # Сначала пробуем запустить минимальный тестовый бот
        try:
            from minimal_test_bot import main as run_minimal_bot
            logger.info("✅ Модуль minimal_test_bot успешно импортирован")
            logger.info("Запуск минимального тестового бота...")
            asyncio.run(run_minimal_bot())
            sys.exit(0)  # Выход после запуска тестового бота
        except ImportError as e:
            logger.warning(f"Модуль minimal_test_bot не найден: {e}, запускаем основной бот")
        
        # Если тестовый бот не найден, запускаем основной бот
        try:
            from telegram_bot import main as run_telegram_bot
            logger.info("✅ Модуль telegram_bot успешно импортирован")
        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать модуль telegram_bot: {e}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        
        # Запуск бота
        logger.info("Запуск основного цикла бота...")
        asyncio.run(run_telegram_bot())
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)