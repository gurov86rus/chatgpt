import logging
import sqlite3
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from db_init import init_database

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure database is initialized
init_database()

# Admin list - add your Telegram ID here
ADMIN_IDS = [123456789]  # Замените на ваш Telegram ID

# Add additional command to help with admin setup
@dp.message(Command("myid"))
async def show_my_id(message: types.Message):
    """Handler to show user's Telegram ID"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    await message.answer(
        f"👤 **Информация о пользователе**\n\n"
        f"🆔 Ваш Telegram ID: `{user_id}`\n"
        f"👤 Имя: {user_name}\n"
        f"🔑 Статус: {'Администратор' if is_admin(user_id) else 'Обычный пользователь'}\n\n"
        f"ℹ️ Чтобы стать администратором, добавьте ваш ID в список ADMIN_IDS в файле telegram_bot.py",
        parse_mode="Markdown"
    )

# Function to check if user is admin
def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

# Decorator for admin-only functions
def admin_required(func):
    """Decorator to restrict function to admins only"""
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if not is_admin(user_id):
            if isinstance(event, types.CallbackQuery):
                await event.answer("⚠️ У вас нет прав администратора для выполнения этой операции", show_alert=True)
                return
            elif isinstance(event, types.Message):
                await event.answer("⚠️ У вас нет прав администратора для выполнения этой операции")
                return
        return await func(event, *args, **kwargs)
    return wrapper

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States for form input
class MaintenanceState(StatesGroup):
    date = State()
    mileage = State()
    works = State()

class RepairState(StatesGroup):
    date = State()
    mileage = State()
    description = State()
    cost = State()

class MileageUpdateState(StatesGroup):
    mileage = State()
    
class EditState(StatesGroup):
    field = State()
    value = State()

class MaintenanceEditState(StatesGroup):
    maintenance_id = State()
    date = State()
    mileage = State()
    works = State()
    
class MaintenanceDeleteState(StatesGroup):
    maintenance_id = State()

# Helper functions
def get_vehicle_buttons():
    """Create keyboard with vehicle selection buttons"""
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, model, reg_number FROM vehicles ORDER BY model")
    vehicles = cursor.fetchall()
    conn.close()

    keyboard = []
    for vehicle in vehicles:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🚛 {vehicle['model']} ({vehicle['reg_number']})", 
                callback_data=f"vehicle_{vehicle['id']}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_vehicle_card(vehicle_id, user_id=None):
    """
    Generate detailed vehicle information card with all available data
    
    Args:
        vehicle_id (int): Vehicle ID
        user_id (int, optional): User ID, to check admin rights
    """
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get vehicle data with all fields from enhanced schema
    cursor.execute("""
        SELECT * FROM vehicles WHERE id = ?
    """, (vehicle_id,))
    vehicle = cursor.fetchone()
    
    if not vehicle:
        conn.close()
        return "Автомобиль не найден", None
    
    # Get maintenance history
    cursor.execute("""
        SELECT date, mileage, works FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
    """, (vehicle_id,))
    to_history = cursor.fetchall()
    
    # Get repair history
    cursor.execute("""
        SELECT date, mileage, description, cost FROM repairs 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
    """, (vehicle_id,))
    repairs = cursor.fetchall()
    
    # Generate vehicle card with enhanced information
    card = (
        f"🚛 **{vehicle['model']} ({vehicle['reg_number']})**\n\n"
        f"📋 **Основная информация:**\n"
        f"📜 **VIN:** `{vehicle['vin'] or '-'}`\n"
        f"🔖 **Категория:** `{vehicle['category'] or '-'}`\n"
        f"🏷 **Квалификация:** `{vehicle['qualification'] or '-'}`\n"
        f"🔢 **Пробег:** `{vehicle['mileage'] or 0} км`\n"
        f"🛠 **Тахограф:** {'✅ Требуется' if vehicle['tachograph_required'] else '❌ Не требуется'}\n\n"
        
        f"📝 **Документы и даты:**\n"
        f"📅 **ОСАГО до:** `{vehicle['osago_valid'] or '-'}`\n"
        f"🔧 **Техосмотр до:** `{vehicle['tech_inspection_valid'] or '-'}`\n"
    )
    
    # Add SKZI information if tachograph is required
    if vehicle['tachograph_required']:
        card += (
            f"🔐 **СКЗИ установлен:** `{vehicle['skzi_install_date'] or '-'}`\n"
            f"🔐 **СКЗИ действует до:** `{vehicle['skzi_valid_date'] or '-'}`\n"
        )
    
    # Add maintenance and fuel information if available
    if vehicle['next_to'] or vehicle['last_to_date'] or vehicle['next_to_date']:
        card += f"\n🔧 **Обслуживание:**\n"
        if vehicle['last_to_date']:
            card += f"📆 **Последнее ТО:** `{vehicle['last_to_date']}`\n"
        if vehicle['next_to_date']:
            card += f"📆 **Следующее ТО:** `{vehicle['next_to_date']}`\n"
        if vehicle['next_to']:
            remaining = vehicle['next_to'] - vehicle['mileage']
            card += f"🔄 **Осталось до ТО:** `{remaining} км`\n"
            if remaining <= 0:
                card += "⚠️ **ВНИМАНИЕ! ТО просрочено!**\n"
            elif remaining <= 1000:
                card += "⚠️ **Приближается плановое ТО!**\n"
    
    # Add fuel information if available
    if vehicle['fuel_type'] or vehicle['fuel_tank_capacity'] or vehicle['avg_fuel_consumption']:
        card += f"\n⛽ **Информация о топливе:**\n"
        if vehicle['fuel_type']:
            card += f"🛢 **Тип топлива:** `{vehicle['fuel_type']}`\n"
        if vehicle['fuel_tank_capacity']:
            card += f"🛢 **Объем бака:** `{vehicle['fuel_tank_capacity']} л`\n"
        if vehicle['avg_fuel_consumption']:
            card += f"🛢 **Средний расход:** `{vehicle['avg_fuel_consumption']} л/100км`\n"
    
    # Add notes if available
    if vehicle['notes']:
        card += f"\n📝 **Примечания:** {vehicle['notes']}\n"
    
    # Add maintenance history
    card += f"\n📜 **История ТО:**\n"
    if to_history:
        for record in to_history:
            card += f"📅 `{record['date']}` – `{record['mileage']} км` – {record['works']}\n"
    else:
        card += "🔹 Нет данных о техническом обслуживании\n"
    
    # Add repair history
    card += f"\n🛠 **Внеплановые ремонты:**\n"
    if repairs:
        for record in repairs:
            cost_text = f" – 💰 `{record['cost']} руб.`" if record['cost'] else ""
            card += f"🔧 `{record['date']}` – `{record['mileage']} км` – {record['description']}{cost_text}\n"
    else:
        card += "🔹 Нет данных о ремонтах\n"
    
    # Create action keyboard based on user's admin status
    keyboard_buttons = []
    
    # Check if user is admin
    is_user_admin = is_admin(user_id) if user_id is not None else False
    
    # For regular users, only show back button
    if not is_user_admin:
        keyboard_buttons = [
            [InlineKeyboardButton(text="⬅ Назад к списку", callback_data="back")]
        ]
    else:
        # For admins, show all control buttons
        keyboard_buttons = [
            [InlineKeyboardButton(text="🔄 Обновить пробег", callback_data=f"update_mileage_{vehicle_id}")],
            [InlineKeyboardButton(text="➕ Добавить ТО", callback_data=f"add_to_{vehicle_id}")],
            [InlineKeyboardButton(text="🛠 Добавить ремонт", callback_data=f"add_repair_{vehicle_id}")],
            [InlineKeyboardButton(text="✏️ Редактировать ТС", callback_data=f"edit_{vehicle_id}")],
            [InlineKeyboardButton(text="📋 Управление ТО", callback_data=f"manage_to_{vehicle_id}")],
            [InlineKeyboardButton(text="🔧 Управление ремонтами", callback_data=f"manage_repairs_{vehicle_id}")],
            [InlineKeyboardButton(text="⬅ Назад к списку", callback_data="back")]
        ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    conn.close()
    return card, keyboard

# Command handlers
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Handler for /start command"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # Show user ID
    user_id_info = f"🆔 Ваш Telegram ID: {user_id}"
    if is_admin(user_id):
        user_id_info += " (Вы администратор)"
    else:
        user_id_info += " (Обычный пользователь)"
    
    await message.answer(
        f"👋 Добро пожаловать, {user_name}, в систему учета автопарка!\n\n"
        f"{user_id_info}\n\n"
        f"🚗 Здесь вы можете:\n"
        f"- Просматривать информацию об автомобилях\n"
        f"- Отслеживать историю обслуживания\n"
        f"- Добавлять записи о ТО и ремонтах (только админ)\n"
        f"- Обновлять текущий пробег (только админ)\n\n"
        f"Выберите автомобиль из списка:",
        reply_markup=get_vehicle_buttons()
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Handler for /help command"""
    await message.answer(
        "ℹ️ **Справка по использованию бота:**\n\n"
        "🚗 **Основные команды:**\n"
        "/start - Показать список автомобилей\n"
        "/help - Показать эту справку\n\n"
        "⚙️ **Работа с автомобилем:**\n"
        "- Нажмите на автомобиль в списке, чтобы увидеть подробную информацию\n"
        "- Используйте кнопки под карточкой автомобиля для внесения новых данных\n\n"
        "📊 **Доступные функции:**\n"
        "- Обновление текущего пробега\n"
        "- Внесение данных о плановом ТО\n"
        "- Запись о внеплановом ремонте\n"
        "- Редактирование данных ТС\n\n"
        "🔔 **Уведомления:**\n"
        "Система автоматически предупредит об истечении сроков документов и необходимости ТО"
    )

# Callback query handlers
@dp.callback_query(lambda c: c.data.startswith("vehicle_"))
async def show_vehicle(callback: types.CallbackQuery):
    """Handler for vehicle selection"""
    vehicle_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    card, keyboard = get_vehicle_card(vehicle_id, user_id)
    
    await callback.message.edit_text(
        card,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_to_menu(callback: types.CallbackQuery):
    """Handler for back button"""
    await callback.message.edit_text(
        "Выберите автомобиль из списка:",
        reply_markup=get_vehicle_buttons()
    )
    await callback.answer()

# Update mileage handlers
@dp.callback_query(lambda c: c.data.startswith("update_mileage_"))
@admin_required
async def update_mileage_start(callback: types.CallbackQuery, state: FSMContext):
    """Start mileage update process"""
    vehicle_id = int(callback.data.split("_")[2])
    await state.update_data(vehicle_id=vehicle_id)
    
    # Get current mileage
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()
    cursor.execute("SELECT mileage FROM vehicles WHERE id = ?", (vehicle_id,))
    current_mileage = cursor.fetchone()[0]
    conn.close()
    
    await callback.message.edit_text(
        f"📊 **Обновление пробега**\n\n"
        f"Текущий пробег: `{current_mileage} км`\n\n"
        f"Введите новое значение пробега (должно быть больше текущего):",
        parse_mode="Markdown"
    )
    await state.set_state(MileageUpdateState.mileage)
    await callback.answer()

@dp.message(MileageUpdateState.mileage)
async def process_mileage_update(message: types.Message, state: FSMContext):
    """Process mileage update input"""
    try:
        new_mileage = int(message.text)
        data = await state.get_data()
        vehicle_id = data["vehicle_id"]
        
        # Get current mileage
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        cursor.execute("SELECT mileage FROM vehicles WHERE id = ?", (vehicle_id,))
        current_mileage = cursor.fetchone()[0]
        
        # Validate new mileage
        if new_mileage <= current_mileage:
            await message.answer(
                f"⚠️ Ошибка: Новый пробег ({new_mileage} км) должен быть больше текущего ({current_mileage} км).\n\n"
                f"Введите корректное значение пробега:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отмена", callback_data=f"vehicle_{vehicle_id}")]
                ])
            )
            return
        
        # Update mileage
        cursor.execute("UPDATE vehicles SET mileage = ? WHERE id = ?", (new_mileage, vehicle_id))
        conn.commit()
        conn.close()
        
        await state.clear()
        card, keyboard = get_vehicle_card(vehicle_id)
        
        await message.answer(
            f"✅ Пробег успешно обновлен: {new_mileage} км", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться к карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
            ])
        )
        
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
            "Попробуйте снова:"
        )

# Maintenance record handlers
@dp.callback_query(lambda c: c.data.startswith("add_to_"))
@admin_required
async def add_to_start(callback: types.CallbackQuery, state: FSMContext):
    """Start maintenance record addition"""
    vehicle_id = int(callback.data.split("_")[2])
    await state.update_data(vehicle_id=vehicle_id)
    
    await callback.message.edit_text(
        "📅 **Добавление записи о техническом обслуживании**\n\n"
        "Введите дату ТО в формате ДД.ММ.ГГГГ (например, 15.03.2025):",
        parse_mode="Markdown"
    )
    await state.set_state(MaintenanceState.date)
    await callback.answer()

@dp.message(MaintenanceState.date)
async def process_to_date(message: types.Message, state: FSMContext):
    """Process maintenance date input"""
    await state.update_data(date=message.text)
    await message.answer(
        "🔢 Введите текущий пробег на момент ТО (в км):"
    )
    await state.set_state(MaintenanceState.mileage)

@dp.message(MaintenanceState.mileage)
async def process_to_mileage(message: types.Message, state: FSMContext):
    """Process maintenance mileage input"""
    try:
        mileage = int(message.text)
        await state.update_data(mileage=mileage)
        await message.answer(
            "📝 Опишите выполненные работы:"
        )
        await state.set_state(MaintenanceState.works)
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
            "Попробуйте снова:"
        )

@dp.message(MaintenanceState.works)
async def process_to_works(message: types.Message, state: FSMContext):
    """Process maintenance works description and save record"""
    data = await state.get_data()
    vehicle_id = data["vehicle_id"]
    
    # Also update vehicle's last_to_date
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()
    
    # Add maintenance record
    cursor.execute(
        "INSERT INTO maintenance (vehicle_id, date, mileage, works) VALUES (?, ?, ?, ?)",
        (vehicle_id, data["date"], data["mileage"], message.text)
    )
    
    # Update vehicle's last_to_date
    cursor.execute(
        "UPDATE vehicles SET last_to_date = ? WHERE id = ?",
        (data["date"], vehicle_id)
    )
    
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(
        "✅ Запись о техническом обслуживании успешно добавлена!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться к карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
        ])
    )

# Repair record handlers
@dp.callback_query(lambda c: c.data.startswith("add_repair_"))
@admin_required
async def add_repair_start(callback: types.CallbackQuery, state: FSMContext):
    """Start repair record addition"""
    vehicle_id = int(callback.data.split("_")[2])
    await state.update_data(vehicle_id=vehicle_id)
    
    await callback.message.edit_text(
        "🛠 **Добавление записи о ремонте**\n\n"
        "Введите дату ремонта в формате ДД.ММ.ГГГГ (например, 15.03.2025):",
        parse_mode="Markdown"
    )
    await state.set_state(RepairState.date)
    await callback.answer()

@dp.message(RepairState.date)
async def process_repair_date(message: types.Message, state: FSMContext):
    """Process repair date input for adding new repair"""
    data = await state.get_data()
    
    # Check if we're editing an existing repair
    if 'repair_id' in data:
        # Handle edit mode
        if message.text.strip() == "":
            await state.update_data(new_date=data['current_date'])
        else:
            await state.update_data(new_date=message.text)
        
        await message.answer(
            f"🔢 **Текущий пробег:** {data['current_mileage']} км\n\n"
            f"Введите новое значение пробега в км (или оставьте текущее):",
            parse_mode="Markdown"
        )
    else:
        # Handle add mode
        await state.update_data(date=message.text)
        await message.answer(
            "🔢 Введите текущий пробег на момент ремонта (в км):"
        )
    
    await state.set_state(RepairState.mileage)

@dp.message(RepairState.mileage)
async def process_repair_mileage(message: types.Message, state: FSMContext):
    """Process repair mileage input"""
    data = await state.get_data()
    
    try:
        # Check if we're editing an existing repair
        if 'repair_id' in data:
            # Handle edit mode - use current mileage if input is empty
            if message.text.strip() == "":
                await state.update_data(new_mileage=data['current_mileage'])
            else:
                new_mileage = int(message.text)
                await state.update_data(new_mileage=new_mileage)
            
            await message.answer(
                f"📝 **Текущее описание ремонта:**\n{data['current_description']}\n\n"
                f"Введите новое описание выполненных работ (или оставьте текущее):",
                parse_mode="Markdown"
            )
        else:
            # Handle add mode
            mileage = int(message.text)
            await state.update_data(mileage=mileage)
            await message.answer(
                "📝 Опишите выполненные ремонтные работы:"
            )
        
        await state.set_state(RepairState.description)
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
            "Попробуйте снова:"
        )

@dp.message(RepairState.description)
async def process_repair_description(message: types.Message, state: FSMContext):
    """Process repair description input"""
    data = await state.get_data()
    
    # Check if we're editing an existing repair
    if 'repair_id' in data:
        # Handle edit mode - use current description if input is empty
        if message.text.strip() == "":
            await state.update_data(new_description=data['current_description'])
        else:
            await state.update_data(new_description=message.text)
        
        await message.answer(
            f"💰 **Текущая стоимость:** {data['current_cost']} ₽\n\n"
            f"Введите новую стоимость ремонта в рублях (или оставьте текущую, или введите 0):",
            parse_mode="Markdown"
        )
    else:
        # Handle add mode
        await state.update_data(description=message.text)
        await message.answer(
            "💰 Укажите стоимость ремонта в рублях (или введите 0, если неизвестно):"
        )
    
    await state.set_state(RepairState.cost)

@dp.message(RepairState.cost)
async def process_repair_cost(message: types.Message, state: FSMContext):
    """Process repair cost input and save record"""
    try:
        data = await state.get_data()
        
        # Check if we're editing an existing repair
        if 'repair_id' in data:
            # Handle edit mode
            if message.text.strip() == "":
                new_cost = data['current_cost']
            else:
                new_cost = int(message.text)
            
            # Update repair record
            conn = sqlite3.connect('vehicles.db')
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE repairs SET date = ?, mileage = ?, description = ?, cost = ? WHERE id = ?",
                (
                    data['new_date'], 
                    data['new_mileage'], 
                    data['new_description'], 
                    new_cost if new_cost > 0 else None,
                    data['repair_id']
                )
            )
            conn.commit()
            conn.close()
            
            await state.clear()
            await message.answer(
                "✅ Запись о ремонте успешно обновлена!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔧 К списку ремонтов", callback_data=f"manage_repairs_{data['vehicle_id']}")],
                    [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{data['vehicle_id']}")]
                ])
            )
        else:
            # Handle add mode
            cost = int(message.text)
            vehicle_id = data["vehicle_id"]
            
            conn = sqlite3.connect('vehicles.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO repairs (vehicle_id, date, mileage, description, cost) VALUES (?, ?, ?, ?, ?)",
                (vehicle_id, data["date"], data["mileage"], data["description"], cost if cost > 0 else None)
            )
            conn.commit()
            conn.close()
            
            await state.clear()
            await message.answer(
                "✅ Запись о ремонте успешно добавлена!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться к карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
                ])
            )
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
            "Попробуйте снова:"
        )

# Edit vehicle handlers
@dp.callback_query(lambda c: c.data.startswith("edit_") and not c.data.startswith("edit_field_") and not c.data.startswith("edit_repair_") and not c.data.startswith("edit_maintenance_"))
@admin_required
async def edit_vehicle_start(callback: types.CallbackQuery, state: FSMContext):
    """Start vehicle editing process"""
    vehicle_id = int(callback.data.split("_")[1])
    await state.update_data(vehicle_id=vehicle_id)
    
    # List of editable fields
    fields = [
        "model", "vin", "category", "reg_number", "qualification", "tachograph_required",
        "osago_valid", "tech_inspection_date", "tech_inspection_valid", "skzi_install_date",
        "skzi_valid_date", "notes", "mileage"
    ]
    
    # Create keyboard with field buttons and user-friendly names
    keyboard = []
    field_names = {
        "model": "🚗 Модель ТС",
        "vin": "🔢 VIN номер",
        "category": "📋 Категория",
        "reg_number": "🔢 Гос. номер",
        "qualification": "📄 Квалификация",
        "tachograph_required": "📟 Тахограф (0/1)",
        "osago_valid": "📝 Срок ОСАГО",
        "tech_inspection_date": "🔍 Дата тех. осмотра",
        "tech_inspection_valid": "📆 Срок тех. осмотра",
        "skzi_install_date": "🔐 Дата уст. СКЗИ",
        "skzi_valid_date": "📆 Срок СКЗИ",
        "notes": "📝 Примечания",
        "mileage": "🔄 Пробег"
    }
    
    for i, field in enumerate(fields):
        keyboard.append([
            InlineKeyboardButton(
                text=field_names.get(field, field), 
                callback_data=f"edit_field_{vehicle_id}_{i}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Отмена", 
            callback_data=f"vehicle_{vehicle_id}"
        )
    ])
    
    await callback.message.edit_text(
        "✏️ **Редактирование данных ТС**\n\n"
        "Выберите поле для редактирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_field_"))
async def select_edit_field(callback: types.CallbackQuery, state: FSMContext):
    """Handler for selecting field to edit"""
    parts = callback.data.split("_")
    vehicle_id = int(parts[2])
    field_index = int(parts[3])
    
    # Store field index in state
    await state.update_data(field_index=field_index)
    
    # List of editable fields
    fields = [
        "model", "vin", "category", "reg_number", "qualification", "tachograph_required",
        "osago_valid", "tech_inspection_date", "tech_inspection_valid", "skzi_install_date",
        "skzi_valid_date", "notes", "mileage"
    ]
    
    selected_field = fields[field_index]
    field_format = ""
    
    # User-friendly field names
    field_names = {
        "model": "Модель ТС",
        "vin": "VIN номер",
        "category": "Категория",
        "reg_number": "Государственный номер",
        "qualification": "Квалификация",
        "tachograph_required": "Наличие тахографа",
        "osago_valid": "Срок действия ОСАГО",
        "tech_inspection_date": "Дата технического осмотра",
        "tech_inspection_valid": "Срок действия техосмотра",
        "skzi_install_date": "Дата установки СКЗИ",
        "skzi_valid_date": "Срок действия СКЗИ",
        "notes": "Примечания",
        "mileage": "Пробег"
    }
    
    # Add format hints for specific fields
    if selected_field == "tachograph_required":
        field_format = " (введите 0 или 1)"
    elif "_date" in selected_field or "_valid" in selected_field:
        field_format = " (формат: ДД.ММ.ГГГГ)"
    elif selected_field == "mileage":
        field_format = " (введите число в километрах)"
    
    field_display_name = field_names.get(selected_field, selected_field)
    
    await callback.message.edit_text(
        f"✏️ **Редактирование поля '{field_display_name}'**\n\n"
        f"Введите новое значение{field_format}:",
        parse_mode="Markdown"
    )
    
    await state.set_state(EditState.value)
    await callback.answer()

@dp.message(EditState.value)
async def process_edit_value(message: types.Message, state: FSMContext):
    """Process edit value input"""
    try:
        data = await state.get_data()
        vehicle_id = data["vehicle_id"]
        field_index = data["field_index"]
        value = message.text
        
        # List of editable fields
        fields = [
            "model", "vin", "category", "reg_number", "qualification", "tachograph_required",
            "osago_valid", "tech_inspection_date", "tech_inspection_valid", "skzi_install_date",
            "skzi_valid_date", "notes", "mileage"
        ]
        
        selected_field = fields[field_index]
        
        # User-friendly field names
        field_names = {
            "model": "Модель ТС",
            "vin": "VIN номер",
            "category": "Категория",
            "reg_number": "Государственный номер",
            "qualification": "Квалификация",
            "tachograph_required": "Наличие тахографа",
            "osago_valid": "Срок действия ОСАГО",
            "tech_inspection_date": "Дата технического осмотра",
            "tech_inspection_valid": "Срок действия техосмотра",
            "skzi_install_date": "Дата установки СКЗИ",
            "skzi_valid_date": "Срок действия СКЗИ",
            "notes": "Примечания",
            "mileage": "Пробег"
        }
        
        field_display_name = field_names.get(selected_field, selected_field)
        
        # Convert specific fields to proper types
        if selected_field in ["tachograph_required", "mileage"]:
            value = int(value)
        
        # Update database
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE vehicles SET {selected_field} = ? WHERE id = ?", 
            (value, vehicle_id)
        )
        conn.commit()
        conn.close()
        
        await state.clear()
        
        await message.answer(
            f"✅ Поле '{field_display_name}' успешно обновлено!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться к карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
            ])
        )
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Неверный формат данных. Пожалуйста, введите корректное значение.\n\n"
            "Попробуйте снова:"
        )

# Maintenance Management Handlers
@dp.callback_query(lambda c: c.data.startswith("manage_to_"))
async def manage_maintenance(callback: types.CallbackQuery):
    """Handler for managing maintenance records"""
    vehicle_id = int(callback.data.split("_")[2])
    
    # Get maintenance records
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, mileage, works FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
    """, (vehicle_id,))
    maintenance_records = cursor.fetchall()
    conn.close()
    
    # Create keyboard with maintenance records
    keyboard = []
    if maintenance_records:
        for record in maintenance_records:
            # Limit works description to 30 chars
            works_short = record['works'][:30] + ('...' if len(record['works']) > 30 else '')
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📅 {record['date']} | {record['mileage']} км | {works_short}", 
                    callback_data=f"maintenance_{record['id']}"
                )
            ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="🔹 Нет записей о ТО", 
                callback_data=f"no_action"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад к ТС", 
            callback_data=f"vehicle_{vehicle_id}"
        )
    ])
    
    await callback.message.edit_text(
        "📋 **Управление записями о ТО**\n\n"
        "Выберите запись для просмотра:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("maintenance_"))
async def show_maintenance_record(callback: types.CallbackQuery):
    """Handler for showing maintenance record details"""
    maintenance_id = int(callback.data.split("_")[1])
    
    # Get maintenance record
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.date, m.mileage, m.works, m.vehicle_id, v.model, v.reg_number
        FROM maintenance m
        JOIN vehicles v ON m.vehicle_id = v.id
        WHERE m.id = ?
    """, (maintenance_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        await callback.answer("⚠️ Запись не найдена")
        return
    
    # Check if user is admin
    user_id = callback.from_user.id
    admin = is_admin(user_id)
    
    # Create keyboard with actions based on user role
    if admin:
        keyboard = [
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_maintenance_{maintenance_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_maintenance_{maintenance_id}")],
            [InlineKeyboardButton(text="⬅ Назад к списку", callback_data=f"manage_to_{record['vehicle_id']}")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="⬅ Назад к списку", callback_data=f"manage_to_{record['vehicle_id']}")]
        ]
    
    await callback.message.edit_text(
        f"📋 **Запись о ТО #{maintenance_id}**\n\n"
        f"🚗 **ТС:** {record['model']} ({record['reg_number']})\n"
        f"📅 **Дата:** {record['date']}\n"
        f"🔢 **Пробег:** {record['mileage']} км\n\n"
        f"📝 **Выполненные работы:**\n{record['works']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_maintenance_"))
@admin_required
async def edit_maintenance_start(callback: types.CallbackQuery, state: FSMContext):
    """Handler for starting maintenance record edit"""
    maintenance_id = int(callback.data.split("_")[2])
    
    # Get maintenance record
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, mileage, works, vehicle_id FROM maintenance WHERE id = ?", (maintenance_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        await callback.answer("⚠️ Запись не найдена")
        return
    
    # Save record data to state
    await state.update_data(
        maintenance_id=maintenance_id,
        vehicle_id=record['vehicle_id'],
        current_date=record['date'],
        current_mileage=record['mileage'],
        current_works=record['works']
    )
    
    await callback.message.edit_text(
        f"✏️ **Редактирование записи о ТО #{maintenance_id}**\n\n"
        f"Текущая дата: {record['date']}\n\n"
        f"Введите новую дату в формате ДД.ММ.ГГГГ (или оставьте текущую):",
        parse_mode="Markdown"
    )
    
    await state.set_state(MaintenanceEditState.date)
    await callback.answer()

@dp.message(MaintenanceEditState.date)
async def process_maintenance_edit_date(message: types.Message, state: FSMContext):
    """Process maintenance edit date input"""
    data = await state.get_data()
    
    # Use current date if input is empty
    if message.text.strip() == "":
        await state.update_data(new_date=data['current_date'])
    else:
        await state.update_data(new_date=message.text)
    
    await message.answer(
        f"🔢 **Текущий пробег:** {data['current_mileage']} км\n\n"
        f"Введите новое значение пробега в км (или оставьте текущее):",
        parse_mode="Markdown"
    )
    await state.set_state(MaintenanceEditState.mileage)

@dp.message(MaintenanceEditState.mileage)
async def process_maintenance_edit_mileage(message: types.Message, state: FSMContext):
    """Process maintenance edit mileage input"""
    data = await state.get_data()
    
    try:
        # Use current mileage if input is empty
        if message.text.strip() == "":
            await state.update_data(new_mileage=data['current_mileage'])
        else:
            new_mileage = int(message.text)
            await state.update_data(new_mileage=new_mileage)
        
        await message.answer(
            f"📝 **Текущее описание работ:**\n{data['current_works']}\n\n"
            f"Введите новое описание выполненных работ (или оставьте текущее):",
            parse_mode="Markdown"
        )
        await state.set_state(MaintenanceEditState.works)
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
            "Попробуйте снова:"
        )

@dp.message(MaintenanceEditState.works)
async def process_maintenance_edit_works(message: types.Message, state: FSMContext):
    """Process maintenance edit works input and save changes"""
    data = await state.get_data()
    
    # Use current works if input is empty
    if message.text.strip() == "":
        new_works = data['current_works']
    else:
        new_works = message.text
    
    # Update maintenance record
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE maintenance SET date = ?, mileage = ?, works = ? WHERE id = ?",
        (data['new_date'], data['new_mileage'], new_works, data['maintenance_id'])
    )
    
    # If this is the most recent maintenance, update vehicle's last_to_date
    cursor.execute("""
        SELECT id FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC 
        LIMIT 1
    """, (data['vehicle_id'],))
    latest_maintenance = cursor.fetchone()
    
    if latest_maintenance and latest_maintenance[0] == data['maintenance_id']:
        cursor.execute(
            "UPDATE vehicles SET last_to_date = ? WHERE id = ?",
            (data['new_date'], data['vehicle_id'])
        )
    
    conn.commit()
    conn.close()
    
    await state.clear()
    
    await message.answer(
        "✅ Запись о техническом обслуживании успешно обновлена!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку ТО", callback_data=f"manage_to_{data['vehicle_id']}")],
            [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{data['vehicle_id']}")]
        ])
    )

@dp.callback_query(lambda c: c.data.startswith("delete_maintenance_"))
@admin_required
async def delete_maintenance_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Handler for confirming maintenance record deletion"""
    maintenance_id = int(callback.data.split("_")[2])
    
    # Get maintenance record
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, mileage, works, vehicle_id FROM maintenance WHERE id = ?", (maintenance_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        await callback.answer("⚠️ Запись не найдена")
        return
    
    # Save maintenance_id and vehicle_id to state
    await state.update_data(
        maintenance_id=maintenance_id,
        vehicle_id=record['vehicle_id']
    )
    await state.set_state(MaintenanceDeleteState.maintenance_id)
    
    # Create confirmation keyboard
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_maintenance_{maintenance_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"maintenance_{maintenance_id}")]
    ]
    
    await callback.message.edit_text(
        f"⚠️ **Подтверждение удаления**\n\n"
        f"Вы действительно хотите удалить запись о ТО от {record['date']} (пробег: {record['mileage']} км)?\n\n"
        f"Это действие нельзя отменить.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("confirm_delete_maintenance_"))
@admin_required
async def delete_maintenance_execute(callback: types.CallbackQuery, state: FSMContext):
    """Handler for executing maintenance record deletion"""
    data = await state.get_data()
    vehicle_id = data['vehicle_id']
    maintenance_id = data['maintenance_id']
    
    # Delete maintenance record
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()
    
    # Check if this is the latest maintenance record
    cursor.execute("""
        SELECT id FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC 
        LIMIT 1
    """, (vehicle_id,))
    latest_maintenance = cursor.fetchone()
    
    # Delete the record
    cursor.execute("DELETE FROM maintenance WHERE id = ?", (maintenance_id,))
    
    # If this was the latest record, update the vehicle's last_to_date
    if latest_maintenance and latest_maintenance[0] == maintenance_id:
        # Get the new latest record
        cursor.execute("""
            SELECT date FROM maintenance 
            WHERE vehicle_id = ? 
            ORDER BY date DESC, mileage DESC 
            LIMIT 1
        """, (vehicle_id,))
        new_latest = cursor.fetchone()
        
        if new_latest:
            cursor.execute(
                "UPDATE vehicles SET last_to_date = ? WHERE id = ?",
                (new_latest[0], vehicle_id)
            )
        else:
            cursor.execute(
                "UPDATE vehicles SET last_to_date = NULL WHERE id = ?",
                (vehicle_id,)
            )
    
    conn.commit()
    conn.close()
    
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Запись о техническом обслуживании успешно удалена!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку ТО", callback_data=f"manage_to_{vehicle_id}")],
            [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
        ])
    )
    await callback.answer()

# Repair Management Handlers
@dp.callback_query(lambda c: c.data.startswith("manage_repairs_"))
async def manage_repairs(callback: types.CallbackQuery):
    """Handler for managing repair records"""
    vehicle_id = int(callback.data.split("_")[2])
    
    # Get repair records
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, mileage, description, cost FROM repairs 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
    """, (vehicle_id,))
    repair_records = cursor.fetchall()
    conn.close()
    
    # Create keyboard with repair records
    keyboard = []
    if repair_records:
        for record in repair_records:
            # Limit description to 30 chars
            desc_short = record['description'][:30] + ('...' if len(record['description']) > 30 else '')
            cost_text = f" | {record['cost']} ₽" if record['cost'] else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🛠 {record['date']} | {record['mileage']} км{cost_text}", 
                    callback_data=f"repair_{record['id']}"
                )
            ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="🔹 Нет записей о ремонтах", 
                callback_data=f"no_action"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад к ТС", 
            callback_data=f"vehicle_{vehicle_id}"
        )
    ])
    
    await callback.message.edit_text(
        "🔧 **Управление записями о ремонтах**\n\n"
        "Выберите запись для просмотра:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "no_action")
async def no_action(callback: types.CallbackQuery):
    """Handler for empty action"""
    await callback.answer("Нет доступных записей")

@dp.callback_query(lambda c: c.data.startswith("repair_"))
async def show_repair_record(callback: types.CallbackQuery):
    """Handler for showing repair record details"""
    repair_id = int(callback.data.split("_")[1])
    
    # Get repair record
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.date, r.mileage, r.description, r.cost, r.vehicle_id, v.model, v.reg_number
        FROM repairs r
        JOIN vehicles v ON r.vehicle_id = v.id
        WHERE r.id = ?
    """, (repair_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        await callback.answer("⚠️ Запись не найдена")
        return
    
    # Format cost display
    cost_display = f"{record['cost']} ₽" if record['cost'] else "Не указана"
    
    # Check if user is admin
    user_id = callback.from_user.id
    admin = is_admin(user_id)
    
    # Create keyboard with actions based on user role
    if admin:
        keyboard = [
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_repair_{repair_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_repair_{repair_id}")],
            [InlineKeyboardButton(text="⬅ Назад к списку", callback_data=f"manage_repairs_{record['vehicle_id']}")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="⬅ Назад к списку", callback_data=f"manage_repairs_{record['vehicle_id']}")]
        ]
    
    await callback.message.edit_text(
        f"🛠 **Запись о ремонте #{repair_id}**\n\n"
        f"🚗 **ТС:** {record['model']} ({record['reg_number']})\n"
        f"📅 **Дата:** {record['date']}\n"
        f"🔢 **Пробег:** {record['mileage']} км\n"
        f"💰 **Стоимость:** {cost_display}\n\n"
        f"📝 **Описание работ:**\n{record['description']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_repair_"))
@admin_required
async def edit_repair_start(callback: types.CallbackQuery, state: FSMContext):
    """Handler for starting repair record edit"""
    repair_id = int(callback.data.split("_")[2])
    
    # Get repair record
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, mileage, description, cost, vehicle_id FROM repairs WHERE id = ?", (repair_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        await callback.answer("⚠️ Запись не найдена")
        return
    
    # Save record data to state
    await state.update_data(
        repair_id=repair_id,
        vehicle_id=record['vehicle_id'],
        current_date=record['date'],
        current_mileage=record['mileage'],
        current_description=record['description'],
        current_cost=record['cost'] or 0
    )
    
    await callback.message.edit_text(
        f"✏️ **Редактирование записи о ремонте #{repair_id}**\n\n"
        f"Текущая дата: {record['date']}\n\n"
        f"Введите новую дату в формате ДД.ММ.ГГГГ (или оставьте текущую):",
        parse_mode="Markdown"
    )
    
    await state.set_state(RepairState.date)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("delete_repair_"))
@admin_required
async def delete_repair_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Handler for confirming repair record deletion"""
    repair_id = int(callback.data.split("_")[2])
    
    # Get repair record
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, mileage, description, vehicle_id FROM repairs WHERE id = ?", (repair_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        await callback.answer("⚠️ Запись не найдена")
        return
    
    # Save repair_id and vehicle_id to state
    await state.update_data(
        repair_id=repair_id,
        vehicle_id=record['vehicle_id']
    )
    
    # Create confirmation keyboard
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_repair_{repair_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"repair_{repair_id}")]
    ]
    
    await callback.message.edit_text(
        f"⚠️ **Подтверждение удаления**\n\n"
        f"Вы действительно хотите удалить запись о ремонте от {record['date']} (пробег: {record['mileage']} км)?\n\n"
        f"Это действие нельзя отменить.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("confirm_delete_repair_"))
@admin_required
async def delete_repair_execute(callback: types.CallbackQuery, state: FSMContext):
    """Handler for executing repair record deletion"""
    data = await state.get_data()
    vehicle_id = data['vehicle_id']
    repair_id = data['repair_id']
    
    # Delete repair record
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM repairs WHERE id = ?", (repair_id,))
    conn.commit()
    conn.close()
    
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Запись о ремонте успешно удалена!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 К списку ремонтов", callback_data=f"manage_repairs_{vehicle_id}")],
            [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
        ])
    )
    await callback.answer()

# Main function to run the bot
async def main():
    # Initialize database
    init_database()
    
    # Start polling
    logging.info("Starting vehicle maintenance bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())