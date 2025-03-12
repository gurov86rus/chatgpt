import os
import logging
import asyncio
import datetime
from aiogram import Bot
from utils import generate_expiration_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Add admin IDs here
ADMIN_IDS = [936544929]  # Replace with your Telegram ID

async def send_daily_report():
    """Generate and send daily report to admin users"""
    # Create a bot instance
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Generate the report
        logger.info("Generating daily report...")
        report_path = generate_expiration_report()
        
        # Get current date
        today = datetime.datetime.now()
        date_str = today.strftime('%d.%m.%Y')
        
        # Send the report to each admin
        for admin_id in ADMIN_IDS:
            try:
                # Send a message with the report
                await bot.send_message(
                    admin_id,
                    f"📊 Ежедневный отчет об истечении сроков документов от {date_str}"
                )
                
                # Send the PDF file
                with open(report_path, 'rb') as pdf:
                    await bot.send_document(
                        admin_id,
                        pdf,
                        caption="Отчет содержит информацию о сроках действия документов для всех транспортных средств."
                    )
                
                logger.info(f"Report sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send report to admin {admin_id}: {e}")
        
        # Cleanup the file
        os.remove(report_path)
        logger.info("Report file cleaned up")
    
    except Exception as e:
        logger.error(f"Error in send_daily_report: {e}")
    
    finally:
        # Close the bot session
        await bot.session.close()

async def schedule_daily_report(hour=8, minute=0):
    """Schedule the daily report to run at specified time"""
    while True:
        now = datetime.datetime.now()
        
        # Calculate the time for next report
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= target_time:
            # If we've already passed the target time today, schedule for tomorrow
            target_time += datetime.timedelta(days=1)
        
        # Calculate seconds until next report
        seconds_until_target = (target_time - now).total_seconds()
        
        logger.info(f"Scheduled next report in {seconds_until_target/3600:.2f} hours")
        
        # Wait until it's time to send the report
        await asyncio.sleep(seconds_until_target)
        
        # Send the report
        await send_daily_report()
        
        # Wait a minute to avoid sending multiple reports
        await asyncio.sleep(60)

if __name__ == "__main__":
    # Run the scheduler
    asyncio.run(schedule_daily_report())