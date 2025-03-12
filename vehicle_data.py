# This file contains the vehicle data structure and functions to manipulate it

# Sample vehicle data
vehicle_data = {
    "model": "КамАЗ-43118-15",
    "number": "Х445ОЕ96",
    "vin": "X7926047C0008204",
    "mileage": 125000,  # Текущий пробег
    "next_to": 130000,  # Следующее ТО
    "last_to": "10.02.2025",  # Дата последнего ТО
    "next_to_date": "10.06.2025",  # Дата следующего ТО
    "osago_valid": "23.02.2026",  # Дата окончания ОСАГО
    "tachograph_required": True,  # Требуется тахограф или нет
    "to_history": [
        {"date": "10.02.2025", "mileage": 120000, "works": "Замена масла, фильтров"},
        {"date": "10.10.2024", "mileage": 110000, "works": "Проверка ходовой"},
    ],
    "repairs": []
}

# Function to update vehicle mileage
def update_mileage(new_mileage):
    """
    Update the vehicle's mileage
    
    Args:
        new_mileage (int): New mileage value
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    if new_mileage < vehicle_data["mileage"]:
        return False
    
    vehicle_data["mileage"] = new_mileage
    return True

# Function to add a repair record
def add_repair(date, mileage, repair_details, cost):
    """
    Add a new repair record
    
    Args:
        date (str): Date of repair
        mileage (int): Mileage at repair time
        repair_details (str): Repair details
        cost (int): Repair cost
        
    Returns:
        bool: True if added successfully
    """
    repair_record = {
        "date": date,
        "mileage": mileage,
        "repair": repair_details,
        "cost": cost
    }
    
    vehicle_data["repairs"].append(repair_record)
    return True

# Function to get formatted vehicle card
def get_vehicle_card():
    """
    Get formatted vehicle information card
    
    Returns:
        str: Formatted vehicle information
    """
    remaining_km = max(0, vehicle_data["next_to"] - vehicle_data["mileage"])
    tachograph_status = "✔ Требуется" if vehicle_data["tachograph_required"] else "❌ Не требуется"

    card = (
        f"🚛 **{vehicle_data['model']} ({vehicle_data['number']})**\n"
        f"📜 **VIN:** {vehicle_data['vin']}\n"
        f"📏 **Пробег:** {vehicle_data['mileage']} км\n"
        f"🔧 **Последнее ТО:** {vehicle_data['last_to']} ({vehicle_data['next_to'] - 10000} км)\n"
        f"🔜 **Следующее ТО:** {vehicle_data['next_to_date']} (через {remaining_km} км)\n"
        f"📅 **ОСАГО действительно до:** {vehicle_data['osago_valid']}\n"
        f"🛠 **Тахограф:** {tachograph_status}\n"
        f"\n📜 **История ТО:**\n"
    )

    for record in vehicle_data["to_history"]:
        card += f"📅 {record['date']} – {record['mileage']} км – {record['works']}\n"

    card += "\n🛠 **Внеплановые ремонты:**\n"
    if vehicle_data["repairs"]:
        for repair in vehicle_data["repairs"]:
            card += f"🔧 {repair['date']} – {repair['mileage']} км – {repair['repair']} – 💰 {repair['cost']} руб.\n"
    else:
        card += "🔹 Нет внеплановых ремонтов.\n"

    return card

# Function to get maintenance history
def get_maintenance_history():
    """
    Get formatted maintenance history
    
    Returns:
        str: Formatted maintenance history
    """
    history = "📋 **История технического обслуживания**\n\n"
    
    if not vehicle_data["to_history"]:
        return history + "🔹 История ТО пуста."
    
    for i, record in enumerate(vehicle_data["to_history"], 1):
        history += f"{i}. 📅 **{record['date']}** – {record['mileage']} км\n"
        history += f"   🔧 Выполненные работы: {record['works']}\n\n"
    
    return history
