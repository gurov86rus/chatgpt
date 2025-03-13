import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN
from db_init import init_database
import db_operations as db
from services_db import validate_date, validate_mileage, validate_float
from states_db import MaintenanceState, RepairState, RefuelingState, VehicleState

# Configure logging
logging.basicConfig(level=logging.INFO)

# Text filter for callback queries
class TextFilter:
    def __init__(self, text):
        self.text = text

    async def __call__(self, callback_query: types.CallbackQuery):
        return callback_query.data == self.text

def Text(text):
    return TextFilter(text)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Helper functions for UI
def get_main_menu_keyboard():
    """
    Create the main menu keyboard with vehicle selection
    """
    vehicles = db.get_all_vehicles()

    keyboard = []
    for vehicle in vehicles:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🚛 {vehicle['model']} ({vehicle['reg_number']})", 
                callback_data=f"vehicle_{vehicle['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="➕ Добавить автомобиль", callback_data="add_vehicle")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_vehicle_keyboard(vehicle_id):
    """
    Create keyboard for vehicle menu
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить пробег", callback_data=f"update_mileage_{vehicle_id}")],
        [InlineKeyboardButton(text="📜 История ТО", callback_data=f"show_maintenance_{vehicle_id}")],
        [InlineKeyboardButton(text="🛠 Внеплановый ремонт", callback_data=f"add_repair_{vehicle_id}")],
        [InlineKeyboardButton(text="🔧 Управление ремонтами", callback_data=f"manage_repairs_{vehicle_id}")],
        [InlineKeyboardButton(text="⛽ Заправка топлива", callback_data=f"add_refueling_{vehicle_id}")],
        [InlineKeyboardButton(text="📊 Статистика топлива", callback_data=f"show_fuel_stats_{vehicle_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_main")],
    ])
    return keyboard

def get_back_keyboard(vehicle_id=None):
    """
    Create keyboard with back button
    """
    if vehicle_id:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"vehicle_{vehicle_id}")],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_main")],
        ])

def get_cancel_keyboard():
    """
    Create keyboard with cancel button
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])

def get_confirm_mileage_keyboard(vehicle_id, mileage):
    """
    Create confirmation keyboard for mileage update
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Подтвердить: {mileage} км", callback_data=f"confirm_mileage_{vehicle_id}_{mileage}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"vehicle_{vehicle_id}")],
    ])

def format_vehicle_card(vehicle_id):
    """
    Format vehicle information into a text card
    """
    vehicle = db.get_vehicle(vehicle_id)
    if not vehicle:
        return "❌ Автомобиль не найден"

    remaining_km = max(0, vehicle['next_to'] - vehicle['mileage']) if vehicle['next_to'] else "Не задано"
    tachograph_status = "✔ Требуется" if vehicle['tachograph_required'] else "❌ Не требуется"

    # Add maintenance alert if needed
    alert = db.get_maintenance_alert(vehicle_id)

    card = (
        f"{alert}🚛 **{vehicle['model']} ({vehicle['reg_number']})**\n"
        f"📜 **VIN:** {vehicle['vin'] or 'Не указан'}\n"
        f"📏 **Пробег:** {vehicle['mileage']} км\n"
    )

    if vehicle['last_to_date']:
        card += f"🔧 **Последнее ТО:** {vehicle['last_to_date']}\n"

    if vehicle['next_to'] and vehicle['next_to_date']:
        card += f"🔜 **Следующее ТО:** {vehicle['next_to_date']} (через {remaining_km} км)\n"

    if vehicle['osago_valid']:
        card += f"📅 **ОСАГО действительно до:** {vehicle['osago_valid']}\n"

    if vehicle['tech_inspection_valid']:
        card += f"🛠 **Техосмотр до:** {vehicle['tech_inspection_valid']}\n"

    card += f"🛠 **Тахограф:** {tachograph_status}\n"

    if vehicle['fuel_type']:
        card += f"⛽ **Тип топлива:** {vehicle['fuel_type']}\n"

    if vehicle['fuel_tank_capacity']:
        card += f"⛽ **Объем бака:** {vehicle['fuel_tank_capacity']} л\n"

    if vehicle['avg_fuel_consumption']:
        card += f"🚗 **Средний расход:** {vehicle['avg_fuel_consumption']} л/100км\n"

    return card

def format_maintenance_history(vehicle_id):
    """
    Format maintenance history into text
    """
    maintenance = db.get_maintenance_history(vehicle_id)
    repairs = db.get_repairs(vehicle_id)

    history = "\n📜 **История ТО:**\n"

    if maintenance:
        for record in maintenance:
            history += f"📅 {record['date']} – {record['mileage']} км – {record['works']}\n"
    else:
        history += "🔹 Нет записей о техническом обслуживании.\n"

    history += "\n🛠 **Внеплановые ремонты:**\n"

    if repairs:
        for repair in repairs:
            cost_info = f" – 💰 {repair['cost']} руб." if repair['cost'] else ""
            history += f"🔧 {repair['date']} – {repair['mileage']} км – {repair['description']}{cost_info}\n"
    else:
        history += "🔹 Нет внеплановых ремонтов.\n"

    return history

def get_repair_management_keyboard(vehicle_id, repairs):
    """
    Create keyboard for repair management
    """
    keyboard = []

    for repair in repairs:
        date_and_desc = f"{repair['date']} - {repair['description'][:20]}..."
        keyboard.append([
            InlineKeyboardButton(
                text=f"🛠 {date_and_desc}", 
                callback_data=f"show_repair_{repair['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="➕ Добавить ремонт", callback_data=f"add_repair_{vehicle_id}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"vehicle_{vehicle_id}")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.callback_query(lambda c: c.data.startswith("manage_repairs_"))
async def manage_repairs(callback_query: types.CallbackQuery):
    """Handler for repair management menu"""
    vehicle_id = int(callback_query.data.split("_")[2])
    vehicle = db.get_vehicle(vehicle_id)
    repairs = db.get_repairs(vehicle_id)

    text = f"🛠 **Управление ремонтами для {vehicle['model']} ({vehicle['reg_number']})**\n\n"
    text += "Выберите запись о ремонте для управления или добавьте новую:"

    await callback_query.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_repair_management_keyboard(vehicle_id, repairs)
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith("show_repair_"))
async def show_repair_details(callback_query: types.CallbackQuery):
    """Handler for showing repair details"""
    repair_id = int(callback_query.data.split("_")[2])

    try:
        conn = db.get_connection() # Assuming db_operations provides a get_connection function
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT r.*, v.model, v.reg_number 
        FROM repairs r
        JOIN vehicles v ON r.vehicle_id = v.id
        WHERE r.id = ?
        """, (repair_id,))

        record = cursor.fetchone()
        conn.close()

        if not record:
            await callback_query.answer("⚠️ Запись о ремонте не найдена")
            return

        vehicle_id = record["vehicle_id"]
        cost_info = f"\n💰 **Стоимость:** {record['cost']} руб." if record['cost'] else ""

        keyboard = [
            [InlineKeyboardButton(text="🗑 Удалить запись", callback_data=f"delete_repair_{repair_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manage_repairs_{vehicle_id}")]
        ]

        await callback_query.message.edit_text(
            f"🛠 **Детали ремонта**\n\n"
            f"🚗 **ТС:** {record['model']} ({record['reg_number']})\n"
            f"📅 **Дата:** {record['date']}\n"
            f"🔢 **Пробег:** {record['mileage']} км\n"
            f"📝 **Описание:** {record['description']}{cost_info}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Ошибка при отображении деталей ремонта: {e}")
        await callback_query.answer("⚠️ Произошла ошибка", show_alert=True)

def format_refueling_history(vehicle_id):
    """
    Format refueling history into text
    """
    refueling = db.get_refueling_history(vehicle_id)
    stats = db.calculate_fuel_stats(vehicle_id)

    history = "\n⛽ **История заправок:**\n"

    if refueling:
        for record in refueling:
            total_cost = record['liters'] * record['cost_per_liter']
            history += (
                f"📅 {record['date']} – {record['mileage']} км – "
                f"{record['liters']} л. × {record['cost_per_liter']} руб/л = "
                f"💰 {total_cost} руб.\n"
            )
    else:
        history += "🔹 Нет записей о заправках.\n"

    # Add fuel statistics
    history += (
        f"\n📊 **Статистика расхода топлива:**\n"
        f"🚗 Средний расход: {stats['avg_consumption']} л/100км\n"
        f"💰 Средняя цена: {stats['avg_cost_per_liter']} руб/л\n"
        f"⛽ Всего заправлено: {stats['total_fuel_liters']} л\n"
        f"💵 Общие затраты на топливо: {stats['total_fuel_cost']} руб\n"
    )

    return history

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handler for /start command"""
    await message.answer(
        "👋 Добро пожаловать в систему учета обслуживания автомобилей!\n\n"
        "Выберите автомобиль из списка или добавьте новый:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handler for /help command"""
    help_text = (
        "🔹 Это бот для учёта обслуживания автомобилей.\n\n"
        "Доступные команды:\n"
        "/start - Показать список автомобилей\n"
        "/help - Показать эту справку\n\n"
        "Функции системы:\n"
        "🚛 Управление несколькими автомобилями\n"
        "🔄 Обновление пробега\n"
        "📜 Ведение истории ТО\n"
        "🛠 Учет внеплановых ремонтов\n"
        "⛽ Учет заправок и расхода топлива\n"
        "📊 Статистика расходов на обслуживание\n"
        "⚠️ Уведомления о приближающемся ТО"
    )
    await message.answer(help_text)

# Main menu and navigation
@dp.callback_query(Text("back_to_main"))
@dp.callback_query(Text("cancel"))
async def back_to_main(callback_query: types.CallbackQuery, state: FSMContext = None):
    """Handler for back to main menu"""
    # Clear state if it exists
    if state:
        await state.clear()

    # Answer callback to remove loading indicator
    await callback_query.answer()

    # Show main menu
    await callback_query.message.edit_text(
        "Выберите автомобиль из списка или добавьте новый:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith("vehicle_"))
async def show_vehicle(callback_query: types.CallbackQuery):
    """Handler for vehicle selection"""
    vehicle_id = int(callback_query.data.split("_")[1])

    # Get vehicle information
    vehicle_card = format_vehicle_card(vehicle_id)

    await callback_query.answer()
    await callback_query.message.edit_text(
        vehicle_card,
        parse_mode="Markdown",
        reply_markup=get_vehicle_keyboard(vehicle_id)
    )

# Vehicle management
@dp.callback_query(Text("add_vehicle"))
async def add_vehicle_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for adding a new vehicle"""
    await callback_query.answer()
    await callback_query.message.edit_text(
        "🚛 **Добавление нового автомобиля**\n\n"
        "Введите модель автомобиля:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(VehicleState.model)

@dp.message(VehicleState.model)
async def vehicle_model_entered(message: types.Message, state: FSMContext):
    """Handler for vehicle model input"""
    await state.update_data(model=message.text.strip())
    await message.answer(
        "Введите регистрационный номер автомобиля:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(VehicleState.reg_number)

@dp.message(VehicleState.reg_number)
async def vehicle_reg_number_entered(message: types.Message, state: FSMContext):
    """Handler for vehicle registration number input"""
    await state.update_data(reg_number=message.text.strip())
    await message.answer(
        "Введите VIN номер автомобиля (или отправьте '-', если не хотите указывать):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(VehicleState.vin)

@dp.message(VehicleState.vin)
async def vehicle_vin_entered(message: types.Message, state: FSMContext):
    """Handler for vehicle VIN input"""
    vin = None if message.text.strip() == '-' else message.text.strip()
    await state.update_data(vin=vin)
    await message.answer(
        "Введите текущий пробег автомобиля (в километрах):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(VehicleState.mileage)

@dp.message(VehicleState.mileage)
async def vehicle_mileage_entered(message: types.Message, state: FSMContext):
    """Handler for vehicle mileage input"""
    try:
        mileage = int(message.text.strip())
        if mileage < 0:
            await message.answer(
                "❌ Пробег не может быть отрицательным. Пожалуйста, введите корректное значение:",
                reply_markup=get_cancel_keyboard()
            )
            return

        await state.update_data(mileage=mileage)

        # Save the vehicle data
        data = await state.get_data()
        vehicle_id = db.add_vehicle(
            model=data["model"],
            reg_number=data["reg_number"],
            vin=data.get("vin"),
            mileage=data["mileage"]
        )

        if vehicle_id > 0:
            await message.answer(
                f"✅ Автомобиль {data['model']} ({data['reg_number']}) успешно добавлен!"
            )

            # Clear state
            await state.clear()

            # Show the vehicle
            await message.answer(
                format_vehicle_card(vehicle_id),
                parse_mode="Markdown",
                reply_markup=get_vehicle_keyboard(vehicle_id)
            )
        else:
            await message.answer(
                "❌ Ошибка при добавлении автомобиля. Пожалуйста, попробуйте снова.",
                reply_markup=get_back_keyboard()
            )
            await state.clear()

    except ValueError:
        await message.answer(
            "❌ Пробег должен быть целым числом. Пожалуйста, введите корректное значение:",
            reply_markup=get_cancel_keyboard()
        )

# Mileage update handlers
@dp.callback_query(lambda c: c.data.startswith("update_mileage_"))
async def update_mileage_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for starting mileage update"""
    vehicle_id = int(callback_query.data.split("_")[2])

    await callback_query.answer()
    await callback_query.message.edit_text(
        "🔄 **Обновление пробега**\n\n"
        "Введите текущий пробег автомобиля (в километрах):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

    await state.set_state(VehicleState.update_mileage)
    await state.update_data(vehicle_id=vehicle_id)

@dp.message(VehicleState.update_mileage)
async def mileage_entered(message: types.Message, state: FSMContext):
    """Handler for mileage input"""
    # Validate mileage
    is_valid, result = validate_mileage(message.text)

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение пробега:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Get vehicle data
    data = await state.get_data()
    vehicle_id = data["vehicle_id"]

    # Store mileage in state
    await state.update_data(mileage=result)

    # Ask for confirmation
    await message.answer(
        f"🔄 Вы хотите установить пробег: **{result} км**?",
        parse_mode="Markdown",
        reply_markup=get_confirm_mileage_keyboard(vehicle_id, result)
    )

@dp.callback_query(lambda c: c.data.startswith("confirm_mileage_"))
async def confirm_mileage(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for mileage confirmation"""
    await callback_query.answer()

    # Get data from callback
    parts = callback_query.data.split("_")
    vehicle_id = int(parts[2])
    new_mileage = int(parts[3])

    # Update mileage
    success = db.update_vehicle_mileage(vehicle_id, new_mileage)

    if success:
        await callback_query.message.edit_text(
            "✅ Пробег успешно обновлен!",
            parse_mode="Markdown"
        )

        # Return to vehicle card after a short delay
        await asyncio.sleep(2)
        await callback_query.message.edit_text(
            format_vehicle_card(vehicle_id),
            parse_mode="Markdown",
            reply_markup=get_vehicle_keyboard(vehicle_id)
        )
    else:
        await callback_query.message.edit_text(
            "❌ Ошибка обновления пробега. Введенное значение меньше текущего пробега.",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard(vehicle_id)
        )

    # Clear state
    await state.clear()

# Maintenance history handlers
@dp.callback_query(lambda c: c.data.startswith("show_maintenance_"))
async def show_maintenance(callback_query: types.CallbackQuery):
    """Handler for showing maintenance history"""
    vehicle_id = int(callback_query.data.split("_")[2])

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"📜 **История обслуживания автомобиля**\n\n{format_maintenance_history(vehicle_id)}",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(vehicle_id)
    )

# Repair handlers
@dp.callback_query(lambda c: c.data.startswith("add_repair_"))
async def add_repair_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for starting repair addition"""
    vehicle_id = int(callback_query.data.split("_")[2])

    await callback_query.answer()
    await callback_query.message.edit_text(
        "🛠 **Добавление внепланового ремонта**\n\n"
        "Введите дату ремонта (в формате ДД.ММ.ГГГГ):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

    await state.set_state(RepairState.date)
    await state.update_data(vehicle_id=vehicle_id)

@dp.message(RepairState.date)
async def repair_date_entered(message: types.Message, state: FSMContext):
    """Handler for repair date input"""
    # Validate date
    if not validate_date(message.text):
        await message.answer(
            "❌ Некорректный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ (например, 15.03.2025):",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Store date in state
    await state.update_data(date=message.text)

    # Ask for mileage
    await message.answer(
        "🚗 Введите пробег на момент ремонта (в километрах):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RepairState.mileage)

@dp.message(RepairState.mileage)
async def repair_mileage_entered(message: types.Message, state: FSMContext):
    """Handler for repair mileage input"""
    # Validate mileage
    is_valid, result = validate_mileage(message.text)

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение пробега:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Store mileage in state
    await state.update_data(mileage=result)

    # Ask for repair details
    await message.answer(
        "🔧 Что ремонтировалось? Введите описание ремонта:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RepairState.description)

@dp.message(RepairState.description)
async def repair_description_entered(message: types.Message, state: FSMContext):
    """Handler for repair description input"""
    # Store repair details in state
    await state.update_data(description=message.text.strip())

    # Ask for repair cost
    await message.answer(
        "💰 Введите стоимость ремонта (в рублях, только цифры):\n"
        "Или отправьте '-', если не хотите указывать стоимость.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RepairState.cost)

@dp.message(RepairState.cost)
async def repair_cost_entered(message: types.Message, state: FSMContext):
    """Handler for repair cost input"""
    try:
        cost = None
        if message.text.strip() != '-':
            # Try to convert cost to integer
            cost = int(message.text)

            if cost < 0:
                raise ValueError("Cost must be positive")

        # Store cost in state
        await state.update_data(cost=cost)

        # Get repair data
        data = await state.get_data()

        # Add repair record
        success = db.add_repair(
            vehicle_id=data["vehicle_id"],
            date=data["date"],
            mileage=data["mileage"],
            description=data["description"],
            cost=data["cost"]
        )

        if success:
            await message.answer("✅ Ремонт успешно добавлен!")

            # Return to vehicle card after a short delay
            await asyncio.sleep(1)
            await message.answer(
                format_vehicle_card(data["vehicle_id"]),
                parse_mode="Markdown",
                reply_markup=get_vehicle_keyboard(data["vehicle_id"])
            )
        else:
            await message.answer(
                "❌ Ошибка при добавлении ремонта.",
                reply_markup=get_back_keyboard(data["vehicle_id"])
            )

        # Clear state
        await state.clear()

    except ValueError:
        await message.answer(
            "❌ Ошибка! Стоимость должна быть положительным числом. Пожалуйста, введите корректную сумму или '-':",
            reply_markup=get_cancel_keyboard()
        )

# Fuel tracking handlers
@dp.callback_query(lambda c: c.data.startswith("show_fuel_stats_"))
async def show_fuel_stats(callback_query: types.CallbackQuery):
    """Handler for showing fuel statistics"""
    vehicle_id = int(callback_query.data.split("_")[3])

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"⛽ **Статистика расхода топлива**\n\n{format_refueling_history(vehicle_id)}",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(vehicle_id)
    )

@dp.callback_query(lambda c: c.data.startswith("add_refueling_"))
async def add_refueling_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for starting refueling addition"""
    vehicle_id = int(callback_query.data.split("_")[2])

    await callback_query.answer()
    await callback_query.message.edit_text(
        "⛽ **Добавление заправки**\n\n"
        "Введите дату заправки (в формате ДД.ММ.ГГГГ):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

    await state.set_state(RefuelingState.date)
    await state.update_data(vehicle_id=vehicle_id)

@dp.message(RefuelingState.date)
async def refueling_date_entered(message: types.Message, state: FSMContext):
    """Handler for refueling date input"""
    # Validate date
    if not validate_date(message.text):
        await message.answer(
            "❌ Некорректный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ (например, 15.03.2025):",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Store date in state
    await state.update_data(date=message.text)

    # Ask for mileage
    await message.answer(
        "🚗 Введите пробег на момент заправки (в километрах):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RefuelingState.mileage)

@dp.message(RefuelingState.mileage)
async def refueling_mileage_entered(message: types.Message, state: FSMContext):
    """Handler for refueling mileage input"""
    # Validate mileage
    is_valid, result = validate_mileage(message.text)

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение пробега:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Store mileage in state
    await state.update_data(mileage=result)

    # Ask for liters
    await message.answer(
        "⛽ Введите количество заправленного топлива (в литрах):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RefuelingState.liters)

@dp.message(RefuelingState.liters)
async def refueling_liters_entered(message: types.Message, state: FSMContext):
    """Handler for fuel liters input"""
    # Validate liters
    is_valid, result = validate_float(message.text, "количество литров")

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Store liters in state
    await state.update_data(liters=result)

    # Ask for cost per liter
    await message.answer(
        "💰 Введите стоимость одного литра топлива (в рублях):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RefuelingState.cost_per_liter)

@dp.message(RefuelingState.cost_per_liter)
async def refueling_cost_entered(message: types.Message, state: FSMContext):
    """Handler for fuel cost input"""
    # Validate cost
    is_valid, result = validate_float(message.text, "стоимость")

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Get complete refueling data
    data = await state.get_data()
    vehicle_id = data["vehicle_id"]
    date = data["date"]
    mileage = data["mileage"]
    liters = data["liters"]
    cost_per_liter = result

    # Add refueling record
    success = db.add_refueling(
        vehicle_id=vehicle_id,
        date=date,
        mileage=mileage,
        liters=liters,
        cost_per_liter=cost_per_liter
    )

    if success:
        total_cost = liters * cost_per_liter
        await message.answer(
            f"✅ Заправка успешно добавлена!\n\n"
            f"📅 Дата: {date}\n"
            f"🚗 Пробег: {mileage} км\n"
            f"⛽ Топливо: {liters} л.\n"
            f"💰 Стоимость: {total_cost:.2f} руб. ({cost_per_liter:.2f} руб/л)"
        )

        # Return to vehicle card after a short delay
        await asyncio.sleep(1)
        await message.answer(
            format_vehicle_card(vehicle_id),
            parse_mode="Markdown",
            reply_markup=get_vehicle_keyboard(vehicle_id)
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении заправки.",
            reply_markup=get_back_keyboard(vehicle_id)
        )

    # Clear state
    await state.clear()

# Repair management handlers
@dp.callback_query(lambda c: c.data.startswith("delete_repair_"))
async def delete_repair_confirm(callback_query: types.CallbackQuery):
    """Handler for confirming repair record deletion"""
    repair_id = int(callback_query.data.split("_")[2])
    logging.debug(f"Запрос на подтверждение удаления ремонта с ID={repair_id}")

    try:
        conn = db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получение информации о ремонте перед удалением
        cursor.execute("""
        SELECT r.*, v.model, v.reg_number 
        FROM repairs r
        JOIN vehicles v ON r.vehicle_id = v.id
        WHERE r.id = ?
        """, (repair_id,))

        record = cursor.fetchone()
        conn.close()

        if not record:
            await callback_query.answer("⚠️ Запись о ремонте не найдена", show_alert=True)
            return

        vehicle_id = record["vehicle_id"]
        date = record["date"]
        cost = record.get("cost", 0)

        # Создаем клавиатуру для подтверждения
        keyboard = [
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"repair_delete_confirm_{repair_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"manage_repairs_{vehicle_id}")]
        ]

        await callback_query.message.edit_text(
            f"⚠️ **Подтверждение удаления**\n\n"
            f"Вы действительно хотите удалить запись о ремонте от {date}?\n\n"
            f"Это действие нельзя отменить.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback_query.answer()

    except Exception as e:
        logging.error(f"Ошибка при подготовке удаления записи о ремонте: {e}")
        await callback_query.answer("⚠️ Произошла ошибка", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("repair_delete_confirm_"))
async def repair_delete_execute(callback_query: types.CallbackQuery):
    """Handler for executing repair record deletion"""
    try:
        repair_id = int(callback_query.data.split("_")[3])
        logging.debug(f"Выполнение удаления ремонта с ID={repair_id}")

        # Получаем vehicle_id перед удалением
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id FROM repairs WHERE id = ?", (repair_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            await callback_query.answer("⚠️ Запись уже удалена", show_alert=True)
            return

        vehicle_id = result["vehicle_id"]

        # Вызов функции удаления из db_operations
        success = db.delete_repair(repair_id)

        if success:
            await callback_query.message.edit_text(
                "✅ Запись о ремонте успешно удалена!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📋 К списку ремонтов", callback_data=f"manage_repairs_{vehicle_id}")],
                    [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
                ])
            )
            logging.info(f"Запись о ремонте с ID={repair_id} для ТС ID={vehicle_id} успешно удалена")
        else:
            await callback_query.message.edit_text(
                "⚠️ Не удалось удалить запись о ремонте.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"manage_repairs_{vehicle_id}")]
                ])
            )
    except Exception as e:
        logging.error(f"Ошибка при удалении записи о ремонте: {e}", exc_info=True)
        await callback_query.answer("⚠️ Произошла ошибка при удалении", show_alert=True)


@dp.message(RefuelingState.liters)
async def refueling_liters_entered(message: types.Message, state: FSMContext):
    """Handler for fuel liters input"""
    # Validate liters
    is_valid, result = validate_float(message.text, "количество литров")

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Store liters in state
    await state.update_data(liters=result)

    # Ask for cost per liter
    await message.answer(
        "💰 Введите стоимость одного литра топлива (в рублях):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RefuelingState.cost_per_liter)

@dp.message(RefuelingState.cost_per_liter)
async def refueling_cost_entered(message: types.Message, state: FSMContext):
    """Handler for fuel cost input"""
    # Validate cost
    is_valid, result = validate_float(message.text, "стоимость")

    if not is_valid:
        await message.answer(
            f"❌ Ошибка: {result}\n\nПожалуйста, введите корректное значение:",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Get complete refueling data
    data = await state.get_data()
    vehicle_id = data["vehicle_id"]
    date = data["date"]
    mileage = data["mileage"]
    liters = data["liters"]
    cost_per_liter = result

    # Add refueling record
    success = db.add_refueling(
        vehicle_id=vehicle_id,
        date=date,
        mileage=mileage,
        liters=liters,
        cost_per_liter=cost_per_liter
    )

    if success:
        total_cost = liters * cost_per_liter
        await message.answer(
            f"✅ Заправка успешно добавлена!\n\n"
            f"📅 Дата: {date}\n"
            f"🚗 Пробег: {mileage} км\n"
            f"⛽ Топливо: {liters} л.\n"
            f"💰 Стоимость: {total_cost:.2f} руб. ({cost_per_liter:.2f} руб/л)"
        )

        # Return to vehicle card after a short delay
        await asyncio.sleep(1)
        await message.answer(
            format_vehicle_card(vehicle_id),
            parse_mode="Markdown",
            reply_markup=get_vehicle_keyboard(vehicle_id)
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении заправки.",
            reply_markup=get_back_keyboard(vehicle_id)
        )

    # Clear state
    await state.clear()

# Main entry point
async def main():
    # Initialize the database
    init_database()

    # Start the bot
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")