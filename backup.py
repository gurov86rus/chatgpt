import os
import datetime
import sqlite3
import shutil
import asyncio
import logging
from aiogram import Bot
from config import TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)

# ID администраторов - должны соответствовать списку в telegram_bot.py
ADMIN_IDS = [936544929]  # Убедитесь, что ID совпадает с ID в telegram_bot.py

# Папка для хранения резервных копий
BACKUP_DIR = "backups"

# Имя файла базы данных
DB_FILE = "vehicles.db"

async def create_backup():
    """
    Создать резервную копию базы данных
    
    Returns:
        str: Путь к файлу резервной копии
    """
    # Создаем директорию для резервных копий, если она не существует
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Формируем имя файла резервной копии с датой и временем
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"vehicles_backup_{timestamp}.db")
    
    try:
        # Проверяем, открыта ли база данных
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA quick_check")
        conn.close()
        
        # Создаем резервную копию базы данных
        shutil.copy2(DB_FILE, backup_file)
        logging.info(f"Резервная копия создана: {backup_file}")
        
        # Удаляем старые резервные копии (оставляем только 10 последних)
        cleanup_old_backups()
        
        return backup_file
    except Exception as e:
        logging.error(f"Ошибка при создании резервной копии: {e}")
        return None

def cleanup_old_backups(max_backups=10):
    """
    Удалить старые резервные копии, оставив только определенное количество
    
    Args:
        max_backups (int): Максимальное количество резервных копий для хранения
    """
    try:
        if not os.path.exists(BACKUP_DIR):
            return
            
        # Получаем список файлов резервных копий
        backup_files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) 
                        if f.startswith("vehicles_backup_") and f.endswith(".db")]
        
        # Сортируем по времени создания (самые старые в начале)
        backup_files.sort(key=lambda x: os.path.getmtime(x))
        
        # Удаляем старые файлы, если их больше max_backups
        if len(backup_files) > max_backups:
            for old_file in backup_files[:-max_backups]:
                os.remove(old_file)
                logging.info(f"Удалена старая резервная копия: {old_file}")
    except Exception as e:
        logging.error(f"Ошибка при очистке старых резервных копий: {e}")

async def send_backup_to_admin(admin_id, backup_file):
    """
    Отправить резервную копию администратору через Telegram
    
    Args:
        admin_id (int): ID администратора
        backup_file (str): Путь к файлу резервной копии
    """
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(backup_file):
            await bot.send_message(admin_id, "❌ Ошибка: файл резервной копии не найден")
            return False
            
        # Отправляем файл
        # В новых версиях aiogram нужно использовать FSInputFile
        from aiogram.types import FSInputFile
        
        document = FSInputFile(backup_file)
        await bot.send_document(
            admin_id,
            document=document,
            caption=f"📁 Резервная копия базы данных от {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке резервной копии: {e}")
        # Пытаемся отправить сообщение об ошибке
        try:
            await bot.send_message(admin_id, f"❌ Ошибка при отправке резервной копии: {str(e)}")
        except:
            pass
        return False

async def scheduled_backup(hour=3, minute=0):
    """
    Запланированное создание резервной копии и отправка администраторам
    
    Args:
        hour (int): Час для ежедневного создания резервной копии (0-23)
        minute (int): Минута для ежедневного создания резервной копии (0-59)
    """
    while True:
        try:
            # Получаем текущее время
            now = datetime.datetime.now()
            
            # Вычисляем время до следующего запуска
            target_time = datetime.datetime(now.year, now.month, now.day, hour, minute)
            if now > target_time:
                # Если целевое время уже прошло сегодня, планируем на завтра
                target_time += datetime.timedelta(days=1)
                
            # Ждем до нужного времени
            wait_seconds = (target_time - now).total_seconds()
            logging.info(f"Следующее автоматическое резервное копирование запланировано через {wait_seconds // 3600:.1f} часов")
            await asyncio.sleep(wait_seconds)
            
            # Создаем и отправляем резервную копию
            backup_file = await create_backup()
            if backup_file:
                for admin_id in ADMIN_IDS:
                    success = await send_backup_to_admin(admin_id, backup_file)
                    if success:
                        logging.info(f"Резервная копия успешно отправлена администратору {admin_id}")
                    else:
                        logging.error(f"Не удалось отправить резервную копию администратору {admin_id}")
                logging.info("Резервное копирование выполнено")
        except Exception as e:
            logging.error(f"Ошибка в запланированном резервном копировании: {e}")
            # Ждем 1 час перед повторной попыткой в случае ошибки
            await asyncio.sleep(3600)

# Функция для ручного создания резервной копии
async def manual_backup(admin_id):
    """
    Создать резервную копию вручную и отправить администратору
    
    Args:
        admin_id (int): ID администратора, запросившего резервную копию
        
    Returns:
        bool: True, если резервная копия успешно создана и отправлена
    """
    backup_file = await create_backup()
    if backup_file:
        return await send_backup_to_admin(admin_id, backup_file)
    return False

# Основная функция для запуска планировщика (если скрипт запускается отдельно)
async def main():
    # Запускаем планировщик резервного копирования (по умолчанию в 3:00)
    await scheduled_backup()

if __name__ == "__main__":
    asyncio.run(main())