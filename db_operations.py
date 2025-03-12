import sqlite3
import logging
import datetime
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
    category: str = None,
    qualification: str = None,
    year: int = None,
    mileage: int = 0,
    tachograph_required: bool = False,
    osago_valid: str = None,
    tech_inspection_date: str = None,
    tech_inspection_valid: str = None,
    skzi_install_date: str = None,
    skzi_valid_date: str = None,
    next_to: int = None,
    last_to_date: str = None,
    next_to_date: str = None,
    fuel_type: str = None,
    fuel_tank_capacity: float = None,
    avg_fuel_consumption: float = None,
    notes: str = None
) -> int:
    """
    Add a new vehicle to the database
    
    Args:
        Multiple vehicle properties with enhanced fields
        
    Returns:
        int: The ID of the new vehicle, or -1 if an error occurred
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO vehicles (
            model, reg_number, vin, category, qualification, year, mileage, 
            tachograph_required, osago_valid, tech_inspection_date, tech_inspection_valid,
            skzi_install_date, skzi_valid_date, next_to, last_to_date,
            next_to_date, fuel_type, fuel_tank_capacity, avg_fuel_consumption, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model, reg_number, vin, category, qualification, year, mileage,
            tachograph_required, osago_valid, tech_inspection_date, tech_inspection_valid,
            skzi_install_date, skzi_valid_date, next_to, last_to_date,
            next_to_date, fuel_type, fuel_tank_capacity, avg_fuel_consumption, notes
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

# User operations 
def register_user(user_id: int, username: str, full_name: str, is_admin: bool = False) -> bool:
    """
    Register a new user or update existing user's information
    
    Args:
        user_id (int): Telegram user ID
        username (str): Username
        full_name (str): Full name
        is_admin (bool): Whether the user is an admin
        
    Returns:
        bool: True if registered/updated successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if user:
            # Update existing user
            cursor.execute("""
            UPDATE users 
            SET username = ?, full_name = ?, last_activity = ?, interaction_count = interaction_count + 1
            WHERE id = ?
            """, (username, full_name, current_time, user_id))
        else:
            # Register new user
            cursor.execute("""
            INSERT INTO users (id, username, full_name, is_admin, first_seen, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, is_admin, current_time, current_time))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error registering user {user_id}: {e}")
        return False

def get_all_users() -> List[Dict]:
    """
    Get all registered users
    
    Returns:
        List of dictionaries with user data
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY first_seen DESC")
        users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return users
    except Exception as e:
        logging.error(f"Error retrieving users: {e}")
        return []

def set_admin_status(user_id: int, is_admin: bool) -> bool:
    """
    Set a user's admin status
    
    Args:
        user_id (int): Telegram user ID
        is_admin (bool): Whether the user should be an admin
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (is_admin, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error setting admin status for user {user_id}: {e}")
        return False

def get_user_stats() -> Dict:
    """
    Get user statistics
    
    Returns:
        Dictionary with user statistics
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get total number of users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Get number of active users (active in the last 7 days)
        seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_activity > ?", (seven_days_ago,))
        active_users = cursor.fetchone()[0]
        
        # Get number of new users in the last 30 days
        thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT COUNT(*) FROM users WHERE first_seen > ?", (thirty_days_ago,))
        new_users = cursor.fetchone()[0]
        
        # Get number of admins
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users,
            "admin_count": admin_count
        }
    except Exception as e:
        logging.error(f"Error getting user stats: {e}")
        return {
            "total_users": 0,
            "active_users": 0,
            "new_users": 0,
            "admin_count": 0
        }

def is_user_admin(user_id: int) -> bool:
    """
    Check if a user is an admin
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if the user is an admin, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return bool(user[0])
        
        # Изменим сообщение об ошибке, чтобы оно не путалось с ID технического обслуживания
        logging.warning(f"Пользователь с Telegram ID {user_id} не зарегистрирован в системе")
        return False
    except Exception as e:
        logging.error(f"Error checking admin status for user {user_id}: {e}")
        return False