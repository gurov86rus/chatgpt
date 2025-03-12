import logging
from datetime import datetime

from vehicle_data import vehicle_data, update_mileage, add_repair

logger = logging.getLogger(__name__)

# Validate date format
def validate_date(date_str):
    """
    Validate date string format (DD.MM.YYYY)
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False

# Validate mileage
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
        if mileage < 0:
            return False, "Пробег не может быть отрицательным"
        
        if mileage < vehicle_data["mileage"]:
            return False, f"Новый пробег ({mileage} км) меньше текущего ({vehicle_data['mileage']} км)"
            
        return True, mileage
    except ValueError:
        return False, "Пробег должен быть числом"

# Process repair data
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
        issues = state_data.get("issues")
        cost = state_data.get("cost")
        
        add_repair(date, mileage, issues, cost)
        logger.info(f"Added repair record: {date}, {mileage} km, {issues}, {cost} RUB")
        return True
    except Exception as e:
        logger.error(f"Error processing repair data: {e}")
        return False

# Process mileage update
async def process_mileage_update(new_mileage):
    """
    Process mileage update
    
    Args:
        new_mileage (int): New mileage value
        
    Returns:
        bool: True if updated successfully
    """
    try:
        result = update_mileage(new_mileage)
        if result:
            logger.info(f"Updated mileage to {new_mileage} km")
        else:
            logger.warning(f"Failed to update mileage to {new_mileage} km")
        return result
    except Exception as e:
        logger.error(f"Error updating mileage: {e}")
        return False
