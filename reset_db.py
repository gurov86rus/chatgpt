import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)

def reset_database():
    """
    Reset the database by removing the existing file and recreating it with the proper schema
    """
    try:
        logging.info("Resetting database...")
        
        # Remove existing database file if it exists
        if os.path.exists('vehicles.db'):
            logging.info("Removing existing database file...")
            os.remove('vehicles.db')
            logging.info("Database file removed.")
        
        # Now import and run the database initialization
        from db_init import init_database
        
        success = init_database()
        if success:
            logging.info("Database reset and initialized successfully.")
            return True
        else:
            logging.error("Failed to initialize database after reset.")
            return False
            
    except Exception as e:
        logging.error(f"Error resetting database: {e}")
        return False

if __name__ == "__main__":
    reset_database()