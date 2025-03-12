# Vehicle Maintenance Telegram Bot with Database

## Overview
This Telegram bot allows users to track and manage vehicle maintenance records, including routine service, repairs, and fuel consumption. The bot uses a SQLite database for persistent data storage, supporting multiple vehicles and providing detailed maintenance history and statistics.

## Features
- 🚛 **Multi-vehicle support**: Manage multiple vehicles with their individual maintenance records
- 📝 **Vehicle information**: Store detailed vehicle data including VIN, registration number, and technical specifications
- 🔧 **Maintenance tracking**: Record regular maintenance activities with date, mileage, and work details
- 🛠️ **Repair history**: Log repairs with costs and descriptions
- ⛽ **Fuel tracking**: Monitor fuel consumption, costs, and efficiency
- 📊 **Statistics**: View statistics on maintenance costs and fuel efficiency
- ⚠️ **Maintenance alerts**: Get notified when regular maintenance is due based on mileage

## Technical Implementation
- **Language**: Python 3.11
- **Framework**: aiogram 3.x (Telegram Bot API)
- **Database**: SQLite
- **State Management**: FSM (Finite State Machine) for dialog flows

## Database Structure
The bot uses a SQLite database with the following tables:
- **vehicles**: Stores vehicle information (model, VIN, mileage, etc.)
- **maintenance**: Records regular maintenance history
- **repairs**: Tracks repair records with optional cost information
- **refueling**: Logs fuel purchases with volume and cost details

## Usage
1. **Start the bot**: Send `/start` to view the main menu
2. **Select or add a vehicle**: Choose a vehicle from the list or add a new one
3. **Access vehicle functions**:
   - View vehicle information
   - Update mileage
   - Record maintenance or repairs
   - Log fuel purchases
   - View statistics and history

## Commands
- `/start` - Show the main menu with vehicle selection
- `/help` - Display help information

## Setup Instructions
1. Install required packages:
   ```
   pip install aiogram python-dotenv
   ```

2. Configure environment variables in `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

3. Run the database initialization script:
   ```
   python db_init.py
   ```

4. Start the bot:
   ```
   python main_db.py
   ```

## Database-Based vs. In-Memory Implementation
The bot is available in two versions:
- **In-memory version** (main.py): Stores data in memory, suitable for testing or single-vehicle use
- **Database version** (main_db.py): Uses SQLite for persistent storage, supports multiple vehicles

## Files
- **main_db.py**: Main bot implementation with database support
- **db_init.py**: Database initialization script
- **db_operations.py**: Database access functions
- **states_db.py**: FSM state definitions for dialogs
- **services_db.py**: Utility functions for data validation and processing