import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

def update_mileage():
    """
    Ensure the vehicles table has a mileage column and update specific mileage values
    """
    try:
        # Connect to the database
        logging.info("Connecting to database...")
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        
        # Check if mileage column exists
        cursor.execute('PRAGMA table_info(vehicles)')
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'mileage' not in columns:
            logging.info("Adding mileage column to vehicles table...")
            cursor.execute('ALTER TABLE vehicles ADD COLUMN mileage INTEGER DEFAULT 0')
            logging.info("Mileage column added.")
        else:
            logging.info("Mileage column already exists.")
        
        # Get all vehicles
        cursor.execute("SELECT id, vin, model, reg_number FROM vehicles")
        vehicles = cursor.fetchall()
        
        # Set default mileage for each vehicle type
        mileage_updates = []
        for vehicle in vehicles:
            vehicle_id, vin, model, reg_number = vehicle
            
            # Default mileage based on vehicle type
            mileage = 0
            if "УАЗ" in model:
                mileage = 75000
            elif "ГАЗ" in model:
                mileage = 95000
            elif "КамАЗ" in model:
                mileage = 120000
            elif "НЕФАЗ" in model:
                mileage = 110000
            elif "МАЗ" in model:
                mileage = 85000
            
            # For the specific vehicle (КамАЗ-43118-15), set a specific mileage
            if vin == 'X7926047C0008204':
                mileage = 125000
                
            mileage_updates.append((mileage, vehicle_id))
            logging.info(f"Setting mileage for {model} ({reg_number}): {mileage} km")
        
        # Update all vehicles
        cursor.executemany('UPDATE vehicles SET mileage = ? WHERE id = ?', mileage_updates)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully updated mileage for {len(mileage_updates)} vehicles")
        return True
        
    except Exception as e:
        logging.error(f"Error updating mileage: {e}")
        return False

if __name__ == "__main__":
    update_mileage()