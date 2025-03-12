from aiogram.fsm.state import State, StatesGroup

class RepairFSM(StatesGroup):
    date = State()        # Date of repair
    mileage = State()     # Mileage at repair time
    issues = State()      # Repair details
    cost = State()        # Repair cost

class MileageFSM(StatesGroup):
    input_mileage = State()  # New mileage value
    
class RefuelingFSM(StatesGroup):
    date = State()            # Date of refueling
    mileage = State()         # Mileage at refueling time
    liters = State()          # Liters of fuel
    cost_per_liter = State()  # Cost per liter