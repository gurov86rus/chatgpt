import os
from dotenv import load_dotenv
import logging

# Настройка логирования для диагностики
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

# Сначала пытаемся загрузить переменные из .env файла (для локальной разработки)
try:
    logger.info("Попытка загрузки переменных окружения из .env файла")
    load_dotenv()
    logger.info("Файл .env обработан")
except Exception as e:
    logger.warning(f"Ошибка при загрузке .env файла: {e}")

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
    logger.info("Переменные окружения: " + ", ".join([k for k in os.environ.keys() if not k.startswith("_")]))
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables. Please set it in Replit Secrets or .env file.")