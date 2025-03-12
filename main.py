#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной скрипт для запуска полнофункционального Telegram бота автопарка
"""
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
    """Останавливает все запущенные экземпляры ботов, кроме текущего"""
    logger.info("Останавливаем все запущенные боты...")
    try:
        # Если существует новый скрипт для остановки ботов, используем его
        if os.path.exists("stop_existing_bots.py"):
            logger.info("Используем stop_existing_bots.py для остановки ботов")
            import stop_existing_bots
            stopped_count = stop_existing_bots.main()
            logger.info(f"Остановлено {stopped_count} экземпляров ботов")
            return True
            
        # Запасной вариант - стандартный метод остановки ботов
        # Не убиваем текущий процесс
        current_pid = os.getpid()
        logger.info(f"Текущий PID: {current_pid}")
        # Получаем список всех процессов python с 'bot' в команде, кроме текущего
        ps_cmd = f"ps aux | grep 'python.*bot' | grep -v {current_pid} | grep -v grep | awk '{{print $2}}'"
        output = subprocess.check_output(ps_cmd, shell=True).decode().strip()
        
        if output:
            pids = output.split('\n')
            for pid in pids:
                if pid.isdigit():
                    try:
                        subprocess.run(["kill", "-9", pid], check=False)
                        logger.info(f"Остановлен процесс с PID {pid}")
                    except Exception as e:
                        logger.error(f"Ошибка при остановке процесса {pid}: {e}")
        else:
            logger.info("Других экземпляров бота не найдено")
            
        logger.info("Боты остановлены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке ботов: {e}")
        return False

def check_token():
    """Проверяет доступность токена и гарантирует использование нового токена"""
    logger.info("Проверяем токен...")
    
    # Принудительно устанавливаем новый токен бота
    NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
    os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
    logger.info(f"Принудительно установлен новый токен бота (ID: {NEW_TOKEN.split(':')[0]})")
    
    # Проверяем токен в переменных окружения
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        try:
            from config import TOKEN
            token = TOKEN
            logger.info(f"Токен загружен из config.py (ID: {token.split(':')[0] if ':' in token else 'неизвестный формат'})")
        except Exception as e:
            logger.error(f"Токен не найден ни в переменных окружения, ни в config.py: {e}")
            return False
    
    if not token:
        logger.error("Токен пустой")
        return False
    else:
        token_id = token.split(':')[0] if ':' in token else "неизвестно"
        logger.info(f"Используется токен с ID: {token_id}")
    
    # Запускаем скрипт startup_token_fix.py для дополнительной гарантии
    try:
        if os.path.exists("startup_token_fix.py"):
            import startup_token_fix
            startup_token_fix.main()
            logger.info("Запущен startup_token_fix.py для дополнительной фиксации токена")
    except Exception as e:
        logger.warning(f"Ошибка при запуске startup_token_fix.py: {e}")
    
    logger.info("Токен доступен и готов к использованию")
    return True

def reset_webhook():
    """Сбрасывает вебхук бота и очищает очередь обновлений"""
    logger.info("Сбрасываем вебхук и очищаем очередь обновлений...")
    try:
        # Пробуем использовать более надежный метод сброса вебхука
        result = False
        
        # Метод 1: Через requests
        try:
            import requests
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            if not token:
                from config import TOKEN
                token = TOKEN
                
            url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
            response = requests.get(url)
            
            if response.status_code == 200 and response.json().get("ok"):
                logger.info("Метод 1: Вебхук успешно сброшен через requests")
                result = True
            else:
                logger.warning(f"Метод 1: Не удалось сбросить вебхук через requests: {response.text}")
        except Exception as e:
            logger.warning(f"Метод 1: Ошибка при сбросе вебхука через requests: {e}")
        
        # Метод 2: Через curl (если requests не сработал)
        if not result:
            try:
                token = os.environ.get("TELEGRAM_BOT_TOKEN")
                if not token:
                    from config import TOKEN
                    token = TOKEN
                    
                curl_cmd = f"curl -s 'https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true'"
                output = subprocess.check_output(curl_cmd, shell=True).decode()
                
                if '"ok":true' in output:
                    logger.info("Метод 2: Вебхук успешно сброшен через curl")
                    result = True
                else:
                    logger.warning(f"Метод 2: Не удалось сбросить вебхук через curl: {output}")
            except Exception as e:
                logger.warning(f"Метод 2: Ошибка при сбросе вебхука через curl: {e}")
        
        # Метод 3: Используем новый модуль stop_existing_bots
        if not result and os.path.exists("stop_existing_bots.py"):
            try:
                import stop_existing_bots
                if stop_existing_bots.reset_webhook():
                    logger.info("Метод 3: Вебхук успешно сброшен через stop_existing_bots.py")
                    result = True
                else:
                    logger.warning("Метод 3: Не удалось сбросить вебхук через stop_existing_bots.py")
            except Exception as e:
                logger.warning(f"Метод 3: Ошибка при сбросе вебхука через stop_existing_bots.py: {e}")
        
        # Дополнительная проверка успешности сброса вебхука
        if result:
            logger.info("Вебхук успешно сброшен")
        else:
            logger.warning("Не удалось сбросить вебхук ни одним из методов")
            
        return result
    except Exception as e:
        logger.error(f"Критическая ошибка при сбросе вебхука: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("Запускаем полнофункциональный бот автопарка...")
    
    # Останавливаем все запущенные боты
    stop_existing_bots()
    
    # Проверяем токен
    if not check_token():
        logger.error("Ошибка проверки токена. Бот не запущен.")
        return
    
    # Сбрасываем вебхук
    reset_webhook()
    
    # Запускаем мониторинг токена в фоновом режиме
    try:
        if os.path.exists("token_monitor.py"):
            import token_monitor
            token_monitor.start_monitor_thread()
            logger.info("Запущен фоновый мониторинг токена")
    except Exception as e:
        logger.warning(f"Не удалось запустить мониторинг токена: {e}")
        
    # Запускаем полнофункциональный бот
    try:
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
