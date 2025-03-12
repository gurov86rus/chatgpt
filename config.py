import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Check if token is available
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables. Please set it in .env file.")