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

# Сначала пытаемся загрузить переменные из .env файла (для локальной разработки)
try:
    logger.info("Попытка загрузки переменных окружения из .env файла")
    load_dotenv()
    logger.info("Файл .env обработан")
except Exception as e:
    logger.warning(f"Ошибка при загрузке .env файла: {e}")

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
    else:
        logger.warning(f"Токен найден, но имеет неожиданный формат (длина: {len(TOKEN)})")
else:
    logger.error("Токен TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    logger.error("Переменные окружения: " + ", ".join(env_vars))
    logger.error("Пожалуйста, установите TELEGRAM_BOT_TOKEN в Secrets (в разделе 'Tools' -> 'Secrets')")
    sys.exit(1)  # Останавливаем программу, если токен не найден