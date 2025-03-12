import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def init_sample_data():
    """
    Initialize the database with sample vehicle data from the provided script
    """
    try:
        # Connect to database
        logging.info("Connecting to database...")
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        
        # Check if vehicles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        if not cursor.fetchone():
            logging.error("Vehicles table does not exist. Run db_init.py first.")
            conn.close()
            return False
        
        # Check if we already have data and clear it if requested
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        
        if count > 0:
            logging.info(f"Database already contains {count} vehicles. Clearing existing data...")
            cursor.execute("DELETE FROM refueling")
            cursor.execute("DELETE FROM repairs")
            cursor.execute("DELETE FROM maintenance")
            cursor.execute("DELETE FROM vehicles")
            conn.commit()
            logging.info("Existing data cleared. Proceeding with sample data initialization.")
        
        # Sample vehicle data from the provided script
        logging.info("Adding sample vehicle data...")
        vehicles_data = [
            ("УАЗ-220695", "XTT220695M1206564", "M2", "О607АС196", "Автобусы (9-15 чел.)", 
             1, "22.01.2026", None, "31.12.2024", None, "31.12.2024", "Требуется установка тахографа"),
            
            ("ГАЗ-3295А1", "XUL3295A1G0000091", "M2", "А442ЕМ186", "Автобусы (9-15 чел.)", 
             1, "24.10.2025", None, "31.12.2024", None, "26.04.2026", "-"),
            
            ("ГАЗ-3295А1", "XUL3295A1L0000557", "M2", "О874ЕУ196", "Автобусы (9-15 чел.)", 
             1, "23.02.2026", "18.10.2025", "18.10.2025", None, "19.03.2027", "-"),
            
            ("ГАЗ-3295", "X89329527COВR9016", "M2", "Т780ТК96", "Автобусы (9-15 чел.)", 
             1, "23.03.2026", "16.06.2025", "16.06.2025", None, "12.01.2026", "-"),
            
            ("КамАЗ-43118-15", "X7926047C0008204", "M3", "Х445ОЕ96", "Автобусы (16-30 чел.)", 
             1, "23.02.2026", "15.05.2025", "15.05.2025", "17.04.2026", "17.04.2026", "-"),
            
            ("НЕФАЗ-4208-48", "X1F4208ROL2001001", "M3", "О535ЕО196", "Автобусы на базе грузовых авто", 
             1, "22.03.2026", "25.10.2025", "25.10.2025", "19.02.2028", "19.02.2028", "-"),
            
            ("УАЗ-390945", "XTT390945F1219059", "N1", "М823ВМ186", "Грузопассажирские авто (до 3,5 т)", 
             0, "09.11.2025", "08.10.2026", "08.10.2026", None, None, "Тахограф не требуется"),
            
            ("УАЗ-390945", "XTT390945M1206572", "N1", "О610АС196", "Грузопассажирские авто (до 3,5 т)", 
             0, "22.01.2026", "19.02.2027", "19.02.2027", None, None, "Тахограф не требуется"),
            
            ("УАЗ-390945", "XTT390995M1208719", "N1", "Н728МЕ196", "Грузопассажирские авто (до 3,5 т)", 
             0, "22.01.2026", "19.02.2027", "19.02.2027", None, None, "Тахограф не требуется"),
            
            ("УАЗ-Патриот 3163", "XTT316300C0006693", "M1", "Т796УА96", "Легковые авто (100-150 л.с.)", 
             0, "22.05.2025", "19.02.2026", "19.02.2026", None, None, "Тахограф не требуется"),
            
            ("МАЗ-5337 (КС-35715)", "XVN357150V0000491", "N3", "Х117СК96", "Автокран", 
             0, "27.03.2026", "05.08.2021", "05.08.2021", None, None, "Тахограф не требуется"),
            
            ("УМД-67-07-02", None, None, "5772ЕВ66", "Трактор", 
             0, "08.12.2025", "31.08.2025", "31.08.2025", None, None, "Тахограф не требуется"),
            
            ("Торнадо М-200", None, None, "ЕА013166", "Прицепы со спец. оборудованием", 
             0, None, None, None, None, None, "Тахограф не требуется")
        ]
        
        # Add more fields to make it work with our enhanced schema
        enhanced_vehicles_data = []
        for vehicle in vehicles_data:
            # Generate default values for missing fields
            # (model, vin, category, reg_number, qualification, tachograph_required, 
            #  osago_valid, tech_inspection_date, tech_inspection_valid, skzi_install_date, skzi_valid_date, notes)
            # Adding: year, mileage, next_to, last_to_date, next_to_date, fuel_type, fuel_tank_capacity, avg_fuel_consumption
            
            # Default year based on registration plate pattern
            year = 2020
            if "96" in vehicle[3] or "186" in vehicle[3]:
                year = 2022
            
            # Default mileage based on vehicle type
            mileage = 0
            if "УАЗ" in vehicle[0]:
                mileage = 75000
            elif "ГАЗ" in vehicle[0]:
                mileage = 95000
            elif "КамАЗ" in vehicle[0]:
                mileage = 120000
            elif "НЕФАЗ" in vehicle[0]:
                mileage = 110000
            elif "МАЗ" in vehicle[0]:
                mileage = 85000
            
            # Default next TO mileage
            next_to = mileage + 15000 if mileage > 0 else None
            
            # Default last_to_date - 6 months ago from tech_inspection_date
            last_to_date = None
            if vehicle[8]:
                parts = vehicle[8].split(".")
                if len(parts) == 3:
                    month = int(parts[1]) - 6
                    year = int(parts[2])
                    if month <= 0:
                        month += 12
                        year -= 1
                    last_to_date = f"{parts[0]}.{month:02d}.{year}"
            
            # Default next_to_date - 6 months from now
            next_to_date = None
            if last_to_date:
                parts = last_to_date.split(".")
                if len(parts) == 3:
                    month = int(parts[1]) + 6
                    year = int(parts[2])
                    if month > 12:
                        month -= 12
                        year += 1
                    next_to_date = f"{parts[0]}.{month:02d}.{year}"
            
            # Default fuel type based on vehicle type
            fuel_type = None
            fuel_tank_capacity = None
            avg_fuel_consumption = None
            
            if "УАЗ" in vehicle[0]:
                fuel_type = "Бензин"
                fuel_tank_capacity = 70
                avg_fuel_consumption = 13.5
            elif "ГАЗ" in vehicle[0]:
                fuel_type = "Бензин"
                fuel_tank_capacity = 80
                avg_fuel_consumption = 15.0
            elif "КамАЗ" in vehicle[0] or "НЕФАЗ" in vehicle[0] or "МАЗ" in vehicle[0]:
                fuel_type = "Дизель"
                fuel_tank_capacity = 300
                avg_fuel_consumption = 30.0
            
            # Create enhanced vehicle data
            enhanced_vehicle = (
                vehicle[0],  # model
                vehicle[3],  # reg_number
                vehicle[1],  # vin
                vehicle[2],  # category
                vehicle[4],  # qualification
                year,
                mileage,
                vehicle[5],  # tachograph_required
                vehicle[6],  # osago_valid
                vehicle[7],  # tech_inspection_date
                vehicle[8],  # tech_inspection_valid
                vehicle[9],  # skzi_install_date
                vehicle[10], # skzi_valid_date
                next_to,
                last_to_date,
                next_to_date,
                fuel_type,
                fuel_tank_capacity,
                avg_fuel_consumption,
                vehicle[11]  # notes
            )
            enhanced_vehicles_data.append(enhanced_vehicle)
        
        # Insert data using OR IGNORE to handle unique constraint violations
        cursor.executemany('''
            INSERT OR IGNORE INTO vehicles (
                model, reg_number, vin, category, qualification, year, mileage,
                tachograph_required, osago_valid, tech_inspection_date, tech_inspection_valid,
                skzi_install_date, skzi_valid_date, next_to, last_to_date, next_to_date,
                fuel_type, fuel_tank_capacity, avg_fuel_consumption, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', enhanced_vehicles_data)
        
        # Sample maintenance data
        logging.info("Adding sample maintenance records...")
        maintenance_data = []
        
        # Generate some maintenance records for each vehicle
        for vehicle_id in range(1, len(enhanced_vehicles_data) + 1):
            # Skip the last vehicle (trailer)
            if vehicle_id == len(enhanced_vehicles_data):
                continue
                
            vehicle = enhanced_vehicles_data[vehicle_id - 1]
            mileage = vehicle[6]  # Current mileage
            
            # Generate 2-3 maintenance records per vehicle
            for i in range(1, 4):
                if i == 3 and vehicle_id % 2 == 0:  # Skip the 3rd record for some vehicles
                    continue
                    
                # Calculate record date and mileage
                past_mileage = max(0, mileage - i * 10000)
                
                # Generate maintenance description based on mileage
                work_desc = ""
                if past_mileage % 30000 < 10000:
                    work_desc = "Полное ТО: замена масла, фильтров, диагностика, регулировка"
                elif past_mileage % 20000 < 10000:
                    work_desc = "Среднее ТО: замена масла, фильтров, диагностика"
                else:
                    work_desc = "Малое ТО: замена масла, диагностика"
                
                # Add record
                record_date = f"{10+i}.{(vehicle_id % 12)+1}.2024"
                maintenance_data.append((vehicle_id, record_date, past_mileage, work_desc))
        
        # Insert maintenance records
        cursor.executemany('''
            INSERT INTO maintenance (vehicle_id, date, mileage, works) 
            VALUES (?, ?, ?, ?)
        ''', maintenance_data)
        
        # Sample repair data
        logging.info("Adding sample repair records...")
        repair_data = []
        
        # Generate some repair records (fewer than maintenance)
        for vehicle_id in range(1, len(enhanced_vehicles_data) + 1):
            # Skip some vehicles
            if vehicle_id % 3 == 0 or vehicle_id == len(enhanced_vehicles_data):
                continue
                
            vehicle = enhanced_vehicles_data[vehicle_id - 1]
            mileage = vehicle[6]  # Current mileage
            
            # Generate 1-2 repair records per vehicle
            for i in range(1, 3):
                if i == 2 and vehicle_id % 2 == 0:  # Skip the 2nd record for some vehicles
                    continue
                
                # Calculate record date and mileage
                past_mileage = max(0, mileage - 5000 - i * 8000)
                
                # Generate repair description and cost based on vehicle type
                if "УАЗ" in vehicle[0]:
                    if i == 1:
                        repair_desc = "Замена лобового стекла"
                        cost = 12000
                    else:
                        repair_desc = "Ремонт ходовой части"
                        cost = 15000
                elif "ГАЗ" in vehicle[0]:
                    if i == 1:
                        repair_desc = "Ремонт тормозной системы"
                        cost = 18000
                    else:
                        repair_desc = "Замена сцепления"
                        cost = 22000
                else:
                    if i == 1:
                        repair_desc = "Ремонт электрооборудования"
                        cost = 25000
                    else:
                        repair_desc = "Капитальный ремонт двигателя"
                        cost = 120000
                
                # Add record
                record_date = f"{(vehicle_id % 28)+1}.{(vehicle_id % 12)+1}.2024"
                repair_data.append((vehicle_id, record_date, past_mileage, repair_desc, cost))
        
        # Insert repair records
        cursor.executemany('''
            INSERT INTO repairs (vehicle_id, date, mileage, description, cost) 
            VALUES (?, ?, ?, ?, ?)
        ''', repair_data)
        
        # Sample refueling data
        logging.info("Adding sample refueling records...")
        refueling_data = []
        
        # Generate some refueling records
        for vehicle_id in range(1, len(enhanced_vehicles_data) + 1):
            # Skip the last vehicle (trailer) and some others
            if vehicle_id == len(enhanced_vehicles_data) or not enhanced_vehicles_data[vehicle_id - 1][16]:
                continue
                
            vehicle = enhanced_vehicles_data[vehicle_id - 1]
            mileage = vehicle[6]  # Current mileage
            fuel_tank = vehicle[17] or 70  # Fuel tank capacity
            
            # Generate 2-4 refueling records per vehicle
            for i in range(1, 5):
                if (i == 4 and vehicle_id % 2 == 0) or (i == 3 and vehicle_id % 3 == 0):
                    continue  # Skip some records for variety
                
                # Calculate record date, mileage, and amount
                past_mileage = max(0, mileage - i * 2000)
                
                # Fuel amount and cost depends on vehicle type
                if "Дизель" in vehicle[16]:
                    amount = round(fuel_tank * 0.7, 1)  # 70% of tank
                    cost_per_liter = 62.5
                else:
                    amount = round(fuel_tank * 0.8, 1)  # 80% of tank
                    cost_per_liter = 52.8
                
                # Small random variation in cost
                cost_per_liter += (vehicle_id % 5) * 0.3
                cost_per_liter = round(cost_per_liter, 1)
                
                # Add record
                record_date = f"{(5*i+vehicle_id) % 28 + 1}.{(vehicle_id % 2)+1}.2025"
                refueling_data.append((vehicle_id, record_date, past_mileage, amount, cost_per_liter))
        
        # Insert refueling records
        cursor.executemany('''
            INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter) 
            VALUES (?, ?, ?, ?, ?)
        ''', refueling_data)
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully initialized database with {len(enhanced_vehicles_data)} vehicles")
        logging.info(f"Added {len(maintenance_data)} maintenance records")
        logging.info(f"Added {len(repair_data)} repair records")
        logging.info(f"Added {len(refueling_data)} refueling records")
        
        return True
    
    except Exception as e:
        logging.error(f"Error initializing sample data: {e}")
        return False

if __name__ == "__main__":
    init_sample_data()