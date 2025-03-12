from aiogram.fsm.state import State, StatesGroup

# State for unplanned repair flow
class RepairFSM(StatesGroup):
    date = State()        # Date of repair
    mileage = State()     # Mileage at repair time
    issues = State()      # Repair details
    cost = State()        # Repair cost

# State for mileage update flow
class MileageFSM(StatesGroup):
    input_mileage = State()  # New mileage value
