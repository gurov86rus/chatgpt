import logging
import sqlite3
import asyncio
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

def get_vehicle_card(vehicle_id):
    """Generate detailed vehicle information card with all available data"""
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
    
    # Create action keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить пробег", callback_data=f"update_mileage_{vehicle_id}")],
        [InlineKeyboardButton(text="➕ Добавить ТО", callback_data=f"add_to_{vehicle_id}")],
        [InlineKeyboardButton(text="🛠 Добавить ремонт", callback_data=f"add_repair_{vehicle_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{vehicle_id}")],
        [InlineKeyboardButton(text="⬅ Назад к списку", callback_data="back")]
    ])
    
    conn.close()
    return card, keyboard

# Command handlers
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Handler for /start command"""
    await message.answer(
        "👋 Добро пожаловать в систему учета автопарка!\n\n"
        "🚗 Здесь вы можете:\n"
        "- Просматривать информацию об автомобилях\n"
        "- Отслеживать историю обслуживания\n"
        "- Добавлять записи о ТО и ремонтах\n"
        "- Обновлять текущий пробег\n\n"
        "Выберите автомобиль из списка:",
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
        "- Запись о внеплановом ремонте\n\n"
        "🔔 **Уведомления:**\n"
        "Система автоматически предупредит об истечении сроков документов и необходимости ТО"
    )

# Callback query handlers
@dp.callback_query(lambda c: c.data.startswith("vehicle_"))
async def show_vehicle(callback: types.CallbackQuery):
    """Handler for vehicle selection"""
    vehicle_id = int(callback.data.split("_")[1])
    card, keyboard = get_vehicle_card(vehicle_id)
    
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
    """Process repair date input"""
    await state.update_data(date=message.text)
    await message.answer(
        "🔢 Введите текущий пробег на момент ремонта (в км):"
    )
    await state.set_state(RepairState.mileage)

@dp.message(RepairState.mileage)
async def process_repair_mileage(message: types.Message, state: FSMContext):
    """Process repair mileage input"""
    try:
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
    await state.update_data(description=message.text)
    await message.answer(
        "💰 Укажите стоимость ремонта в рублях (или введите 0, если неизвестно):"
    )
    await state.set_state(RepairState.cost)

@dp.message(RepairState.cost)
async def process_repair_cost(message: types.Message, state: FSMContext):
    """Process repair cost input and save record"""
    try:
        cost = int(message.text)
        data = await state.get_data()
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

# Main function to run the bot
async def main():
    # Initialize database
    init_database()
    
    # Start polling
    logging.info("Starting vehicle maintenance bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())