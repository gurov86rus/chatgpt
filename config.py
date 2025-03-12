import os
from dotenv import load_dotenv
import logging
import sys

# Настройка логирования для диагностики
logging.basicConfig(
    level=logging.DEBUG,  # Изменено на DEBUG для более подробных логов
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_debug.log")
    ]
)

logger = logging.getLogger(__name__)

# ПРИНУДИТЕЛЬНОЕ ИСПОЛЬЗОВАНИЕ НОВОГО ТОКЕНА
NEW_TOKEN = "1023647955:AAGaw1_vRdWNOyfzGwSVrhzH9bWxGejiHm8"
logger.info(f"ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ НОВЫЙ ТОКЕН (ID: {NEW_TOKEN.split(':')[0]})")
os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN

# Сначала пытаемся загрузить переменные из .env файла (для локальной разработки)
try:
    logger.info("Попытка загрузки переменных окружения из .env файла")
    load_dotenv(override=True)  # Включаем override для гарантированной перезаписи
    logger.info("Файл .env обработан")
    
    # Проверяем, обновилась ли переменная окружения после load_dotenv
    if os.getenv("TELEGRAM_BOT_TOKEN") != NEW_TOKEN:
        logger.warning("Токен в переменных окружения не обновился после load_dotenv")
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        logger.info("Токен принудительно установлен в переменных окружения")
except Exception as e:
    logger.warning(f"Ошибка при загрузке .env файла: {e}")
    # При ошибке также устанавливаем новый токен
    os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN

# Вывод всех переменных окружения для диагностики (без значений)
env_vars = [k for k in os.environ.keys() if not k.startswith("_")]
logger.info(f"Доступные переменные окружения: {', '.join(env_vars)}")

# Получаем токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверка наличия токена с расширенной диагностикой
if TOKEN:
    # Маскируем токен для безопасности
    token_parts = TOKEN.split(':')
    if len(token_parts) >= 2:
        token_id = token_parts[0]
        token_length = len(TOKEN)
        logger.info(f"Токен найден в переменных окружения (ID: {token_id}, длина: {token_length} символов)")
        
        # Дополнительно проверяем, что токен соответствует новому
        if token_id != NEW_TOKEN.split(':')[0]:
            logger.warning(f"Токен в переменных окружения ({token_id}) не соответствует новому токену ({NEW_TOKEN.split(':')[0]})")
            os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
            TOKEN = NEW_TOKEN
            logger.info(f"Токен принудительно обновлен на новый (ID: {TOKEN.split(':')[0]})")
    else:
        logger.warning(f"Токен найден, но имеет неожиданный формат (длина: {len(TOKEN)})")
        os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
        TOKEN = NEW_TOKEN
else:
    logger.error("Токен TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    logger.error("Переменные окружения: " + ", ".join(env_vars))
    logger.error("Устанавливаем новый токен принудительно")
    os.environ["TELEGRAM_BOT_TOKEN"] = NEW_TOKEN
    TOKEN = NEW_TOKEN