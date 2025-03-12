import sqlite3
import logging

def init_database():
    """
    Initialize the SQLite database and create necessary tables
    """
    try:
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        
        # Create vehicles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            vin TEXT,
            year INTEGER,
            reg_number TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            tachograph_required BOOLEAN DEFAULT FALSE,
            osago_valid TEXT,
            next_to INTEGER,
            tech_inspection_valid TEXT,
            last_to_date TEXT,
            next_to_date TEXT,
            fuel_type TEXT,
            fuel_tank_capacity REAL,
            avg_fuel_consumption REAL
        )
        ''')
        
        # Create maintenance history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            works TEXT NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Create repairs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            description TEXT NOT NULL,
            cost REAL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Create refueling table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS refueling (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            liters REAL NOT NULL,
            cost_per_liter REAL NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Add test vehicle if no vehicles exist
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute('''
            INSERT INTO vehicles (
                model, vin, year, reg_number, mileage, tachograph_required,
                osago_valid, next_to, tech_inspection_valid, last_to_date,
                next_to_date, fuel_type, fuel_tank_capacity, avg_fuel_consumption
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "КамАЗ-43118-15", "X7926047C0008204", 2023, "Х445ОЕ96", 
                125000, True, "23.02.2026", 130000, "15.04.2026", 
                "10.02.2025", "10.06.2025", "ДТ", 350, 32.5
            ))
            
            # Add maintenance history
            cursor.execute('''
            INSERT INTO maintenance (vehicle_id, date, mileage, works)
            VALUES (?, ?, ?, ?)
            ''', (1, "10.02.2025", 120000, "Замена масла, фильтров"))
            
            cursor.execute('''
            INSERT INTO maintenance (vehicle_id, date, mileage, works)
            VALUES (?, ?, ?, ?)
            ''', (1, "10.10.2024", 110000, "Проверка ходовой"))
            
            # Add refueling records
            cursor.execute('''
            INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter)
            VALUES (?, ?, ?, ?, ?)
            ''', (1, "05.03.2025", 124000, 300, 62.5))
            
            cursor.execute('''
            INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter)
            VALUES (?, ?, ?, ?, ?)
            ''', (1, "25.02.2025", 122500, 320, 61.8))
        
        conn.commit()
        conn.close()
        
        logging.info("Database initialized successfully")
        return True
    
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()