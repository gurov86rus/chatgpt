from app import app

# This file allows both configurations to work:
# 1. The Web Application workflow uses this as "main:app"
# 2. The Telegram Bot workflow runs "python main.py" which uses the code below

if __name__ == "__main__":
    # When run directly, start the Telegram bot
    import logging
    import asyncio
    from main_db import main as run_telegram_bot
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the Telegram bot
    try:
        asyncio.run(run_telegram_bot())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")