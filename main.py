from app import app
import os
import sys
import logging
import asyncio

# This file allows both configurations to work:
# 1. The Web Application workflow uses this as "main:app"
# 2. The Telegram Bot workflow runs "python main.py" which uses the code below

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # Check if TOKEN environment variable is available
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logging.error("TELEGRAM_BOT_TOKEN environment variable is not set.")
        logging.info("Please set the TELEGRAM_BOT_TOKEN environment variable and try again.")
        sys.exit(1)
        
    # Attempt to reset webhook first via API call
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
        logging.info(f"Webhook reset: {response.json()}")
    except Exception as e:
        logging.warning(f"Could not reset webhook via API: {e}")
        
    # When run directly, start the Telegram bot
    from telegram_bot import main as run_telegram_bot
    
    # Run the Telegram bot
    try:
        asyncio.run(run_telegram_bot())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")