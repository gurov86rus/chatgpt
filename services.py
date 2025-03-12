import re
from datetime import datetime
from vehicle_data import update_mileage, add_repair, add_refueling

def validate_date(date_str):
    """
    Validate date string format (DD.MM.YYYY)
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Pattern for DD.MM.YYYY format
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    
    if not re.match(pattern, date_str):
        return False
    
    # Check if it's a valid date
    try:
        day, month, year = map(int, date_str.split('.'))
        datetime(year, month, day)
        return True
    except ValueError:
        return False

def validate_mileage(mileage_str):
    """
    Validate mileage value
    
    Args:
        mileage_str (str): Mileage string to validate
        
    Returns:
        tuple: (is_valid, mileage_value or error_message)
    """
    try:
        mileage = int(mileage_str)
        if mileage <= 0:
            return False, "Пробег должен быть положительным числом"
        return True, mileage
    except ValueError:
        return False, "Пробег должен быть числом"

def validate_float(value_str, field_name="значение"):
    """
    Validate float value
    
    Args:
        value_str (str): Float string to validate
        field_name (str): Name of the field for error message
        
    Returns:
        tuple: (is_valid, float_value or error_message)
    """
    try:
        # Replace comma with dot for Russian locale
        value = float(value_str.replace(',', '.'))
        
        # Check if positive
        if value <= 0:
            return False, f"{field_name.capitalize()} должно быть положительным числом"
        
        return True, value
    except ValueError:
        return False, f"{field_name.capitalize()} должно быть числом"

async def process_repair_data(state_data):
    """
    Process repair data from FSM state
    
    Args:
        state_data (dict): Data from FSM state
        
    Returns:
        bool: True if processed successfully
    """
    try:
        date = state_data.get("date")
        mileage = state_data.get("mileage")
        repair_details = state_data.get("issues")
        cost = state_data.get("cost")
        
        # Add repair record
        return add_repair(date, mileage, repair_details, cost)
    except Exception as e:
        print(f"Error processing repair data: {e}")
        return False

async def process_mileage_update(new_mileage):
    """
    Process mileage update
    
    Args:
        new_mileage (int): New mileage value
        
    Returns:
        bool: True if updated successfully
    """
    try:
        return update_mileage(new_mileage)
    except Exception as e:
        print(f"Error updating mileage: {e}")
        return False

async def process_refueling_data(state_data):
    """
    Process refueling data from FSM state
    
    Args:
        state_data (dict): Data from FSM state
        
    Returns:
        bool: True if processed successfully
    """
    try:
        date = state_data.get("date")
        mileage = state_data.get("mileage")
        liters = state_data.get("liters")
        cost_per_liter = state_data.get("cost_per_liter")
        
        # Add refueling record
        return add_refueling(date, mileage, liters, cost_per_liter)
    except Exception as e:
        print(f"Error processing refueling data: {e}")
        return False