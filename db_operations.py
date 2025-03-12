import sqlite3
import logging
from typing import List, Dict, Tuple, Optional, Union, Any

def get_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect('vehicles.db')

# Vehicle operations
def get_all_vehicles() -> List[Dict]:
    """
    Get all vehicles from the database
    
    Returns:
        List of dictionaries with vehicle data
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM vehicles ORDER BY model")
        vehicles = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return vehicles
    except Exception as e:
        logging.error(f"Error retrieving vehicles: {e}")
        return []

def get_vehicle(vehicle_id: int) -> Optional[Dict]:
    """
    Get a vehicle by ID
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        Dictionary with vehicle data or None if not found
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        vehicle = cursor.fetchone()
        
        conn.close()
        return dict(vehicle) if vehicle else None
    except Exception as e:
        logging.error(f"Error retrieving vehicle {vehicle_id}: {e}")
        return None

def update_vehicle_mileage(vehicle_id: int, new_mileage: int) -> bool:
    """
    Update a vehicle's mileage
    
    Args:
        vehicle_id (int): The vehicle ID
        new_mileage (int): The new mileage value
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current mileage
        cursor.execute("SELECT mileage FROM vehicles WHERE id = ?", (vehicle_id,))
        current_mileage = cursor.fetchone()[0]
        
        # Check if new mileage is greater than current
        if new_mileage <= current_mileage:
            conn.close()
            return False
        
        # Update mileage
        cursor.execute("UPDATE vehicles SET mileage = ? WHERE id = ?", (new_mileage, vehicle_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error updating mileage for vehicle {vehicle_id}: {e}")
        return False

def add_vehicle(
    model: str, 
    reg_number: str, 
    vin: str = None,
    year: int = None,
    mileage: int = 0,
    tachograph_required: bool = False,
    osago_valid: str = None,
    next_to: int = None,
    tech_inspection_valid: str = None,
    last_to_date: str = None,
    next_to_date: str = None,
    fuel_type: str = None,
    fuel_tank_capacity: float = None,
    avg_fuel_consumption: float = None
) -> int:
    """
    Add a new vehicle to the database
    
    Args:
        Multiple vehicle properties
        
    Returns:
        int: The ID of the new vehicle, or -1 if an error occurred
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO vehicles (
            model, reg_number, vin, year, mileage, tachograph_required,
            osago_valid, next_to, tech_inspection_valid, last_to_date,
            next_to_date, fuel_type, fuel_tank_capacity, avg_fuel_consumption
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model, reg_number, vin, year, mileage, tachograph_required,
            osago_valid, next_to, tech_inspection_valid, last_to_date,
            next_to_date, fuel_type, fuel_tank_capacity, avg_fuel_consumption
        ))
        
        vehicle_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return vehicle_id
    except Exception as e:
        logging.error(f"Error adding vehicle: {e}")
        return -1

# Maintenance operations
def get_maintenance_history(vehicle_id: int) -> List[Dict]:
    """
    Get maintenance history for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        List of dictionaries with maintenance records
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
        """, (vehicle_id,))
        
        maintenance = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return maintenance
    except Exception as e:
        logging.error(f"Error retrieving maintenance history for vehicle {vehicle_id}: {e}")
        return []

def add_maintenance(vehicle_id: int, date: str, mileage: int, works: str) -> bool:
    """
    Add a maintenance record
    
    Args:
        vehicle_id (int): The vehicle ID
        date (str): Date of maintenance
        mileage (int): Mileage at maintenance
        works (str): Description of maintenance works
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO maintenance (vehicle_id, date, mileage, works) 
        VALUES (?, ?, ?, ?)
        """, (vehicle_id, date, mileage, works))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error adding maintenance record for vehicle {vehicle_id}: {e}")
        return False

# Repair operations
def get_repairs(vehicle_id: int) -> List[Dict]:
    """
    Get repair records for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        List of dictionaries with repair records
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM repairs 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
        """, (vehicle_id,))
        
        repairs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return repairs
    except Exception as e:
        logging.error(f"Error retrieving repairs for vehicle {vehicle_id}: {e}")
        return []

def add_repair(vehicle_id: int, date: str, mileage: int, description: str, cost: float = None) -> bool:
    """
    Add a repair record
    
    Args:
        vehicle_id (int): The vehicle ID
        date (str): Date of repair
        mileage (int): Mileage at repair
        description (str): Description of repair
        cost (float): Cost of repair
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO repairs (vehicle_id, date, mileage, description, cost) 
        VALUES (?, ?, ?, ?, ?)
        """, (vehicle_id, date, mileage, description, cost))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error adding repair record for vehicle {vehicle_id}: {e}")
        return False

# Refueling operations
def get_refueling_history(vehicle_id: int) -> List[Dict]:
    """
    Get refueling records for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        List of dictionaries with refueling records
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM refueling 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
        """, (vehicle_id,))
        
        refueling = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return refueling
    except Exception as e:
        logging.error(f"Error retrieving refueling records for vehicle {vehicle_id}: {e}")
        return []

def add_refueling(vehicle_id: int, date: str, mileage: int, liters: float, cost_per_liter: float) -> bool:
    """
    Add a refueling record
    
    Args:
        vehicle_id (int): The vehicle ID
        date (str): Date of refueling
        mileage (int): Mileage at refueling
        liters (float): Liters of fuel
        cost_per_liter (float): Cost per liter
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter) 
        VALUES (?, ?, ?, ?, ?)
        """, (vehicle_id, date, mileage, liters, cost_per_liter))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error adding refueling record for vehicle {vehicle_id}: {e}")
        return False

def calculate_fuel_stats(vehicle_id: int) -> Dict:
    """
    Calculate fuel statistics for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        Dictionary with fuel statistics
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get vehicle data
        cursor.execute("SELECT avg_fuel_consumption FROM vehicles WHERE id = ?", (vehicle_id,))
        vehicle = cursor.fetchone()
        avg_consumption = vehicle[0] if vehicle else 0
        
        # Get refueling records
        cursor.execute("""
        SELECT mileage, liters, cost_per_liter FROM refueling 
        WHERE vehicle_id = ? 
        ORDER BY mileage
        """, (vehicle_id,))
        
        refueling = cursor.fetchall()
        conn.close()
        
        if len(refueling) < 2:
            total_fuel_cost = sum(r[1] * r[2] for r in refueling)
            total_fuel_liters = sum(r[1] for r in refueling)
            avg_cost_per_liter = sum(r[2] for r in refueling) / len(refueling) if refueling else 0
            
            return {
                "avg_consumption": avg_consumption,
                "total_fuel_cost": total_fuel_cost,
                "total_fuel_liters": total_fuel_liters,
                "avg_cost_per_liter": round(avg_cost_per_liter, 2)
            }
        
        # Calculate actual consumption
        total_distance = refueling[-1][0] - refueling[0][0]
        total_fuel = sum(r[1] for r in refueling[1:])  # Exclude the first refueling
        
        if total_distance > 0:
            actual_consumption = (total_fuel / total_distance) * 100
        else:
            actual_consumption = avg_consumption
        
        total_fuel_cost = sum(r[1] * r[2] for r in refueling)
        total_fuel_liters = sum(r[1] for r in refueling)
        avg_cost_per_liter = sum(r[2] for r in refueling) / len(refueling) if refueling else 0
        
        return {
            "avg_consumption": round(actual_consumption, 2),
            "total_fuel_cost": round(total_fuel_cost, 2),
            "total_fuel_liters": round(total_fuel_liters, 2),
            "avg_cost_per_liter": round(avg_cost_per_liter, 2)
        }
    except Exception as e:
        logging.error(f"Error calculating fuel stats for vehicle {vehicle_id}: {e}")
        return {
            "avg_consumption": 0,
            "total_fuel_cost": 0,
            "total_fuel_liters": 0,
            "avg_cost_per_liter": 0
        }

def get_maintenance_alert(vehicle_id: int) -> str:
    """
    Get maintenance alert message if maintenance is needed soon
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        str: Alert message or empty string if no alert
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT mileage, next_to FROM vehicles WHERE id = ?", (vehicle_id,))
        vehicle = cursor.fetchone()
        conn.close()
        
        if not vehicle:
            return ""
        
        current_mileage = vehicle[0]
        next_to_mileage = vehicle[1]
        
        if not next_to_mileage:
            return ""
        
        remaining_km = next_to_mileage - current_mileage
        
        if remaining_km <= 0:
            return "⚠️ **ВНИМАНИЕ!** Техническое обслуживание просрочено! Требуется немедленное ТО!\n\n"
        elif remaining_km <= 500:
            return f"⚠️ **ВНИМАНИЕ!** Техническое обслуживание требуется в ближайшее время (осталось {remaining_km} км)!\n\n"
        elif remaining_km <= 1000:
            return f"⚠️ Приближается плановое ТО (осталось {remaining_km} км)!\n\n"
        
        return ""
    except Exception as e:
        logging.error(f"Error getting maintenance alert for vehicle {vehicle_id}: {e}")
        return ""