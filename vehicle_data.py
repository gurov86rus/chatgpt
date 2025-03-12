# Vehicle data storage module

# Example data for one vehicle
vehicle_data = {
    "model": "КамАЗ-43118-15",
    "number": "Х445ОЕ96",
    "vin": "X7926047C0008204",
    "mileage": 125000,  # Current mileage
    "next_to": 130000,  # Next maintenance
    "last_to": "10.02.2025",  # Date of last maintenance
    "next_to_date": "10.06.2025",  # Date of next maintenance
    "osago_valid": "23.02.2026",  # OSAGO insurance expiration
    "tachograph_required": True,  # Tachograph requirement
    "fuel_type": "ДТ", # Diesel fuel
    "fuel_tank_capacity": 350, # Liters
    "avg_fuel_consumption": 32.5, # L/100km
    "to_history": [
        {"date": "10.02.2025", "mileage": 120000, "works": "Замена масла, фильтров"},
        {"date": "10.10.2024", "mileage": 110000, "works": "Проверка ходовой"},
    ],
    "repairs": [],
    "refueling": [
        {"date": "05.03.2025", "mileage": 124000, "liters": 300, "cost_per_liter": 62.5},
        {"date": "25.02.2025", "mileage": 122500, "liters": 320, "cost_per_liter": 61.8},
    ]
}

def update_mileage(new_mileage):
    """
    Update the vehicle's mileage
    
    Args:
        new_mileage (int): New mileage value
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    # Validate the mileage (should be greater than current)
    if new_mileage < vehicle_data["mileage"]:
        return False
    
    # Update the mileage
    vehicle_data["mileage"] = new_mileage
    return True

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

def get_maintenance_alert():
    """
    Get maintenance alert message if maintenance is needed soon
    
    Returns:
        str: Alert message or empty string if no alert
    """
    remaining_km = vehicle_data["next_to"] - vehicle_data["mileage"]
    
    if remaining_km <= 0:
        return "⚠️ **ВНИМАНИЕ!** Техническое обслуживание просрочено! Требуется немедленное ТО!\n\n"
    elif remaining_km <= 500:
        return f"⚠️ **ВНИМАНИЕ!** Техническое обслуживание требуется в ближайшее время (осталось {remaining_km} км)!\n\n"
    elif remaining_km <= 1000:
        return f"⚠️ Приближается плановое ТО (осталось {remaining_km} км)!\n\n"
    
    return ""

def get_vehicle_card():
    """
    Get formatted vehicle information card
    
    Returns:
        str: Formatted vehicle information
    """
    remaining_km = max(0, vehicle_data["next_to"] - vehicle_data["mileage"])
    tachograph_status = "✔ Требуется" if vehicle_data["tachograph_required"] else "❌ Не требуется"
    
    # Add maintenance alert if needed
    alert = get_maintenance_alert()
    
    card = (
        f"{alert}🚛 **{vehicle_data['model']} ({vehicle_data['number']})**\n"
        f"📜 **VIN:** {vehicle_data['vin']}\n"
        f"📏 **Пробег:** {vehicle_data['mileage']} км\n"
        f"🔧 **Последнее ТО:** {vehicle_data['last_to']} ({vehicle_data['next_to'] - 10000} км)\n"
        f"🔜 **Следующее ТО:** {vehicle_data['next_to_date']} (через {remaining_km} км)\n"
        f"📅 **ОСАГО действительно до:** {vehicle_data['osago_valid']}\n"
        f"🛠 **Тахограф:** {tachograph_status}\n"
    )
    
    return card

def add_refueling(date, mileage, liters, cost_per_liter):
    """
    Add a new refueling record
    
    Args:
        date (str): Date of refueling
        mileage (int): Mileage at refueling time
        liters (float): Liters of fuel
        cost_per_liter (float): Cost per liter
        
    Returns:
        bool: True if added successfully
    """
    refueling_record = {
        "date": date,
        "mileage": mileage,
        "liters": liters,
        "cost_per_liter": cost_per_liter
    }
    
    vehicle_data["refueling"].append(refueling_record)
    return True

def get_fuel_stats():
    """
    Calculate fuel statistics
    
    Returns:
        dict: Fuel statistics
    """
    if len(vehicle_data["refueling"]) < 2:
        return {
            "avg_consumption": vehicle_data["avg_fuel_consumption"],
            "total_fuel_cost": sum(r["liters"] * r["cost_per_liter"] for r in vehicle_data["refueling"]),
            "total_fuel_liters": sum(r["liters"] for r in vehicle_data["refueling"]),
            "avg_cost_per_liter": sum(r["cost_per_liter"] for r in vehicle_data["refueling"]) / len(vehicle_data["refueling"]) if vehicle_data["refueling"] else 0
        }
    
    # Sort refueling records by mileage
    sorted_refueling = sorted(vehicle_data["refueling"], key=lambda x: x["mileage"])
    
    # Calculate actual consumption
    total_distance = sorted_refueling[-1]["mileage"] - sorted_refueling[0]["mileage"]
    total_fuel = sum(r["liters"] for r in sorted_refueling[1:])  # Exclude the first refueling
    
    if total_distance > 0:
        actual_consumption = (total_fuel / total_distance) * 100
    else:
        actual_consumption = vehicle_data["avg_fuel_consumption"]
    
    return {
        "avg_consumption": round(actual_consumption, 2),
        "total_fuel_cost": sum(r["liters"] * r["cost_per_liter"] for r in vehicle_data["refueling"]),
        "total_fuel_liters": sum(r["liters"] for r in vehicle_data["refueling"]),
        "avg_cost_per_liter": round(sum(r["cost_per_liter"] for r in vehicle_data["refueling"]) / len(vehicle_data["refueling"]) if vehicle_data["refueling"] else 0, 2)
    }

def get_refueling_history():
    """
    Get formatted refueling history
    
    Returns:
        str: Formatted refueling history
    """
    history = "\n⛽ **История заправок:**\n"
    
    if vehicle_data["refueling"]:
        # Sort by date (newest first)
        sorted_refueling = sorted(vehicle_data["refueling"], key=lambda x: x["date"], reverse=True)
        
        for refuel in sorted_refueling:
            total_cost = refuel["liters"] * refuel["cost_per_liter"]
            history += (
                f"📅 {refuel['date']} – {refuel['mileage']} км – "
                f"{refuel['liters']} л. × {refuel['cost_per_liter']} руб/л = "
                f"💰 {total_cost} руб.\n"
            )
    else:
        history += "🔹 Нет записей о заправках.\n"
    
    # Add fuel statistics if available
    stats = get_fuel_stats()
    history += (
        f"\n📊 **Статистика расхода топлива:**\n"
        f"🚗 Средний расход: {stats['avg_consumption']} л/100км\n"
        f"💰 Средняя цена: {stats['avg_cost_per_liter']} руб/л\n"
        f"⛽ Всего заправлено: {stats['total_fuel_liters']} л\n"
        f"💵 Общие затраты на топливо: {stats['total_fuel_cost']} руб\n"
    )
    
    return history

def get_maintenance_history():
    """
    Get formatted maintenance history
    
    Returns:
        str: Formatted maintenance history
    """
    history = "\n📜 **История ТО:**\n"
    
    for record in vehicle_data["to_history"]:
        history += f"📅 {record['date']} – {record['mileage']} км – {record['works']}\n"
    
    history += "\n🛠 **Внеплановые ремонты:**\n"
    if vehicle_data["repairs"]:
        for repair in vehicle_data["repairs"]:
            history += f"🔧 {repair['date']} – {repair['mileage']} км – {repair['repair']} – 💰 {repair['cost']} руб.\n"
    else:
        history += "🔹 Нет внеплановых ремонтов.\n"
    
    return history