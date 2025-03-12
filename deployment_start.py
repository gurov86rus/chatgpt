
import os
import logging
import sys
import signal
import asyncio
from db_init import init_database
from telegram_bot import main as run_telegram_bot
from app import app
import threading
import time

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

# Start Flask web server in a separate thread
def start_web_server():
    # This ensures the Flask app opens on the network interface, not just localhost
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key, value)

        def load(self):
            return self.application

    options = {
        'bind': '0.0.0.0:5000',
        'workers': 1,
    }
    
    logger.info("Starting web server on port 5000")
    StandaloneApplication(app, options).run()

# Start the web server in a separate thread
web_thread = threading.Thread(target=start_web_server)
web_thread.daemon = True
web_thread.start()

# Wait a moment for the web server to start
time.sleep(2)

# Start the Telegram bot (this will run in the main thread)
logger.info("Starting Telegram bot")
try:
    # Add a dedicated cleanup function
    def cleanup():
        logger.info("Cleaning up and exiting...")
        sys.exit(0)

    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda s, f: cleanup())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup())
    
    # Run the bot
    asyncio.run(run_telegram_bot())
except KeyboardInterrupt:
    logger.info("Bot stopped by user")
except Exception as e:
    logger.error(f"Critical error in bot: {e}")
    logger.error(f"Stack trace: {sys.exc_info()}")
