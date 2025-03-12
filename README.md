# Vehicle Maintenance Tracking Bot

A Telegram bot for tracking vehicle maintenance, service intervals, and repair history.

## Features

- Display vehicle information including mileage, service intervals, and insurance details
- Track maintenance history
- Record unplanned repairs with costs
- Update vehicle mileage
- View service and repair history

## Setup

1. Create a `.env` file in the root directory with your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```
   python main.py
   ```

## Commands

- `/start` - Show vehicle information and main menu
- `/help` - Display help information

## Bot Structure

- `main.py` - Main bot file with handlers
- `config.py` - Configuration and environment variables
- `keyboards.py` - Telegram inline keyboards
- `states.py` - FSM states for multi-step operations
- `services.py` - Validation and data processing functions
- `vehicle_data.py` - Vehicle data storage and operations