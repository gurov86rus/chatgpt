import re
from datetime import datetime

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

def format_date(date_str, input_format="%d.%m.%Y", output_format="%d.%m.%Y"):
    """
    Format date string
    
    Args:
        date_str (str): Date string to format
        input_format (str): Input date format
        output_format (str): Output date format
        
    Returns:
        str: Formatted date string or original string if invalid
    """
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_str