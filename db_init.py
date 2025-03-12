import sqlite3
import logging

def init_database():
    """
    Initialize the SQLite database and create necessary tables with enhanced schema
    """
    try:
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        
        # Create enhanced vehicles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            reg_number TEXT NOT NULL UNIQUE,
            vin TEXT UNIQUE,
            category TEXT,
            qualification TEXT,
            year INTEGER,
            mileage INTEGER DEFAULT 0,
            tachograph_required BOOLEAN DEFAULT FALSE,
            osago_valid TEXT,
            tech_inspection_date TEXT,
            tech_inspection_valid TEXT,
            skzi_install_date TEXT,
            skzi_valid_date TEXT,
            next_to INTEGER,
            last_to_date TEXT,
            next_to_date TEXT,
            fuel_type TEXT,
            fuel_tank_capacity REAL,
            avg_fuel_consumption REAL,
            notes TEXT
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
        
        # Add test vehicles if no vehicles exist
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Sample vehicles from provided data
            vehicles_data = [
                ("УАЗ-220695", "О607АС196", "XTT220695M1206564", "M2", "Автобусы (9-15 чел.)", 
                 2021, 125000, 1, "22.01.2026", None, "31.12.2024", None, "31.12.2024", 
                 15000, "15.01.2025", "15.01.2026", "Дизель", 70.0, 12.5, 
                 "Требуется установка тахографа"),
                
                ("ГАЗ-3295А1", "А442ЕМ186", "XUL3295A1G0000091", "M2", "Автобусы (9-15 чел.)", 
                 2020, 98000, 1, "24.10.2025", None, "31.12.2024", None, "25.04.2026", 
                 10000, "10.11.2024", "10.11.2025", "Дизель", 75.0, 14.0, "-"),
                
                ("УАЗ-Патриот 3163", "Т796УА96", "XTT316300C0006693", "M1", "Легковые авто (100-150 л.с.)", 
                 2018, 75800, 0, "22.05.2025", "19.02.2026", "19.02.2026", None, None, 
                 10000, "22.05.2024", "22.05.2025", "Бензин", 68.0, 11.5, 
                 "Тахограф не требуется"),
                 
                ("КамАЗ-43118-15", "Х445ОЕ96", "X7926047C0008204", "M3", "Автобусы (16-30 чел.)", 
                 2023, 125000, 1, "23.02.2026", "15.05.2025", "15.05.2025", "17.04.2022", "17.04.2026", 
                 130000, "10.02.2025", "10.06.2025", "Дизель", 350, 32.5, "-")
            ]
            
            cursor.executemany('''
                INSERT OR IGNORE INTO vehicles (
                    model, reg_number, vin, category, qualification, year, mileage,
                    tachograph_required, osago_valid, tech_inspection_date, tech_inspection_valid,
                    skzi_install_date, skzi_valid_date, next_to, last_to_date, next_to_date,
                    fuel_type, fuel_tank_capacity, avg_fuel_consumption, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', vehicles_data)
            
            # Add maintenance history
            maintenance_data = [
                (4, "10.02.2025", 120000, "Замена масла, фильтров"),
                (4, "10.10.2024", 110000, "Проверка ходовой"),
                (1, "15.01.2025", 120000, "Плановое ТО"),
                (2, "10.11.2024", 88000, "Замена ремня ГРМ"),
                (3, "22.05.2024", 65800, "Замена масла, свечей зажигания")
            ]
            
            cursor.executemany('''
                INSERT INTO maintenance (vehicle_id, date, mileage, works)
                VALUES (?, ?, ?, ?)
            ''', maintenance_data)
            
            # Add repair records
            repair_data = [
                (1, "10.03.2024", 113000, "Замена лобового стекла", 15000.0),
                (2, "15.08.2024", 85000, "Ремонт коробки передач", 42000.0),
                (4, "05.01.2025", 115000, "Замена тормозных колодок", 8500.0)
            ]
            
            cursor.executemany('''
                INSERT INTO repairs (vehicle_id, date, mileage, description, cost)
                VALUES (?, ?, ?, ?, ?)
            ''', repair_data)
            
            # Add refueling records
            refueling_data = [
                (4, "05.03.2025", 124000, 300, 62.5),
                (4, "25.02.2025", 122500, 320, 61.8),
                (1, "01.03.2025", 123000, 60, 65.2),
                (2, "20.02.2025", 95000, 65, 64.0),
                (3, "18.02.2025", 72500, 45, 55.5)
            ]
            
            cursor.executemany('''
                INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter)
                VALUES (?, ?, ?, ?, ?)
            ''', refueling_data)
        
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