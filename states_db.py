from aiogram.fsm.state import State, StatesGroup

class RepairState(StatesGroup):
    date = State()        # Date of repair
    mileage = State()     # Mileage at repair time
    description = State() # Repair details
    cost = State()        # Repair cost

class MaintenanceState(StatesGroup):
    date = State()        # Date of maintenance
    mileage = State()     # Mileage at maintenance time
    works = State()       # Maintenance works performed

class RefuelingState(StatesGroup):
    date = State()            # Date of refueling
    mileage = State()         # Mileage at refueling time
    liters = State()          # Liters of fuel
    cost_per_liter = State()  # Cost per liter

class VehicleState(StatesGroup):
    model = State()           # Vehicle model
    reg_number = State()      # Registration number
    vin = State()             # VIN number
    mileage = State()         # Current mileage
    update_mileage = State()  # For mileage update