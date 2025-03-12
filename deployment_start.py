import os
import logging
import sys
import asyncio
from db_init import init_database
from telegram_bot import main as run_telegram_bot
from app import app
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

# Check for token
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    sys.exit(1)

# Initialize database
try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    logger.error(f"Stack trace: {sys.exc_info()}")

# Run both web server and telegram bot
if __name__ == "__main__":
    # Start the Telegram bot in a separate thread
    logger.info("Starting Telegram bot")
    bot_thread = Thread(target=lambda: asyncio.run(run_telegram_bot()))
    bot_thread.daemon = True
    bot_thread.start()

    # Start Flask web server in the main thread
    logger.info("Starting web server on port 5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)