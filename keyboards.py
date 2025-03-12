from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """
    Create main menu keyboard with inline buttons
    
    Returns:
        InlineKeyboardMarkup: Main menu keyboard
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить пробег", callback_data="update_mileage")],
        [InlineKeyboardButton(text="📜 История ТО", callback_data="show_history")],
        [InlineKeyboardButton(text="🛠 Внеплановый ремонт", callback_data="add_repair")],
        [InlineKeyboardButton(text="⛽ Заправка топлива", callback_data="add_refueling")],
        [InlineKeyboardButton(text="📊 Статистика топлива", callback_data="show_fuel_stats")],
    ])
    return keyboard

def get_cancel_keyboard():
    """
    Create keyboard with cancel button
    
    Returns:
        InlineKeyboardMarkup: Cancel keyboard
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])
    return keyboard

def get_back_keyboard():
    """
    Create keyboard with back to main menu button
    
    Returns:
        InlineKeyboardMarkup: Back keyboard
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_to_main")],
    ])
    return keyboard

def get_confirm_mileage_keyboard(mileage):
    """
    Create confirmation keyboard for mileage update
    
    Args:
        mileage (int): New mileage value to confirm
        
    Returns:
        InlineKeyboardMarkup: Confirmation keyboard
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Подтвердить: {mileage} км", callback_data=f"confirm_mileage_{mileage}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])
    return keyboard