import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
# Custom filter for callback data
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from states import RepairFSM, MileageFSM, RefuelingFSM
from keyboards import (
    get_main_keyboard, 
    get_cancel_keyboard, 
    get_back_keyboard, 
    get_confirm_mileage_keyboard
)
from vehicle_data import (
    get_vehicle_card, 
    get_maintenance_history, 
    get_refueling_history,
    add_refueling
)
from services import (
    validate_date, 
    validate_mileage, 
    process_repair_data, 
    process_mileage_update
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define custom Text filter for callback data
class TextFilter:
    def __init__(self, text):
        self.text = text
        
    async def __call__(self, callback_query: types.CallbackQuery):
        return callback_query.data == self.text

# Create Text filter constructor for decorator usage
def Text(text):
    return TextFilter(text)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handler for /start command"""
    await message.answer(
        get_vehicle_card() + get_maintenance_history(),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handler for /help command"""
    help_text = (
        "🔹 Это бот для учёта обслуживания автомобиля.\n\n"
        "Доступные команды:\n"
        "/start - Показать информацию о машине\n"
        "/help - Показать эту справку\n\n"
        "Вы также можете использовать кнопки под сообщениями для:\n"
        "🔄 Обновления пробега\n"
        "📜 Просмотра истории ТО\n"
        "🛠 Добавления внепланового ремонта\n"
        "⛽ Добавления записи о заправке\n"
        "📊 Просмотра статистики расхода топлива"
    )
    await message.answer(help_text)

# Callback query handlers
@dp.callback_query(Text("back_to_main"))
@dp.callback_query(Text("cancel"))
async def back_to_main(callback_query: types.CallbackQuery, state: FSMContext = None):
    """Handler for back/cancel buttons"""
    # Clear state if it exists
    if state:
        await state.clear()
    
    # Answer callback to remove loading indicator
    await callback_query.answer()
    
    try:
        # Edit or send new message with main menu
        await callback_query.message.edit_text(
            get_vehicle_card() + get_maintenance_history(),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        # Handle the case when message content is the same
        if "message is not modified" in str(e):
            # Just log it, no need to take action
            logging.info("Message content is the same, no changes needed")
        else:
            # For other errors, log and potentially handle
            logging.error(f"Error in back_to_main: {e}")

@dp.callback_query(Text("show_history"))
async def show_history(callback_query: types.CallbackQuery):
    """Handler for showing maintenance history"""
    await callback_query.answer()
    await callback_query.message.edit_text(
        "📜 **История обслуживания автомобиля**\n" + get_maintenance_history(),
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

# Mileage update handlers
@dp.callback_query(Text("update_mileage"))
async def update_mileage_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for starting mileage update"""
    await callback_query.answer()
    await callback_query.message.edit_text(
        "🔄 **Обновление пробега**\n\n"
        "Введите текущий пробег автомобиля (в километрах):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(MileageFSM.input_mileage)

@dp.message(MileageFSM.input_mileage)
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
    
    # Store mileage in state
    await state.update_data(mileage=result)
    
    # Ask for confirmation
    await message.answer(
        f"🔄 Вы хотите установить пробег: **{result} км**?",
        parse_mode="Markdown",
        reply_markup=get_confirm_mileage_keyboard(result)
    )

@dp.callback_query(lambda c: c.data.startswith("confirm_mileage_"))
async def confirm_mileage(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for mileage confirmation"""
    await callback_query.answer()
    
    # Get mileage from callback data
    new_mileage = int(callback_query.data.split("_")[-1])
    
    # Process mileage update
    success = await process_mileage_update(new_mileage)
    
    if success:
        await callback_query.message.edit_text(
            "✅ Пробег успешно обновлен!",
            parse_mode="Markdown"
        )
        
        # Return to main menu after a short delay
        await asyncio.sleep(2)
        await callback_query.message.edit_text(
            get_vehicle_card() + get_maintenance_history(),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback_query.message.edit_text(
            "❌ Ошибка обновления пробега. Введенное значение меньше текущего пробега.",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
    
    # Clear state
    await state.clear()

# Repair handlers
@dp.callback_query(Text("add_repair"))
async def add_repair_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for starting repair addition"""
    await callback_query.answer()
    await callback_query.message.edit_text(
        "🛠 **Добавление внепланового ремонта**\n\n"
        "Введите дату ремонта (в формате ДД.ММ.ГГГГ):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RepairFSM.date)

@dp.message(RepairFSM.date)
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
    await state.set_state(RepairFSM.mileage)

@dp.message(RepairFSM.mileage)
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
    await state.set_state(RepairFSM.issues)

@dp.message(RepairFSM.issues)
async def repair_issues_entered(message: types.Message, state: FSMContext):
    """Handler for repair issues input"""
    # Store repair details in state
    await state.update_data(issues=message.text.strip())
    
    # Ask for repair cost
    await message.answer(
        "💰 Введите стоимость ремонта (в рублях, только цифры):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RepairFSM.cost)

@dp.message(RepairFSM.cost)
async def repair_cost_entered(message: types.Message, state: FSMContext):
    """Handler for repair cost input"""
    try:
        # Try to convert cost to integer
        cost = int(message.text)
        
        if cost < 0:
            raise ValueError("Cost must be positive")
        
        # Store cost in state
        await state.update_data(cost=cost)
        
        # Process repair data
        repair_data = await state.get_data()
        success = await process_repair_data(repair_data)
        
        if success:
            await message.answer("✅ Ремонт успешно добавлен!")
            
            # Return to main menu after a short delay
            await asyncio.sleep(2)
            await message.answer(
                get_vehicle_card() + get_maintenance_history(),
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при добавлении ремонта.",
                reply_markup=get_back_keyboard()
            )
        
        # Clear state
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Ошибка! Стоимость должна быть положительным числом. Пожалуйста, введите корректную сумму:",
            reply_markup=get_cancel_keyboard()
        )

# Fuel tracking handlers
@dp.callback_query(Text("show_fuel_stats"))
async def show_fuel_stats(callback_query: types.CallbackQuery):
    """Handler for showing fuel statistics"""
    await callback_query.answer()
    await callback_query.message.edit_text(
        "⛽ **Статистика расхода топлива**\n" + get_refueling_history(),
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

@dp.callback_query(Text("add_refueling"))
async def add_refueling_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler for starting refueling addition"""
    await callback_query.answer()
    await callback_query.message.edit_text(
        "⛽ **Добавление заправки**\n\n"
        "Введите дату заправки (в формате ДД.ММ.ГГГГ):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RefuelingFSM.date)

@dp.message(RefuelingFSM.date)
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
    await state.set_state(RefuelingFSM.mileage)

@dp.message(RefuelingFSM.mileage)
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
    await state.set_state(RefuelingFSM.liters)

@dp.message(RefuelingFSM.liters)
async def refueling_liters_entered(message: types.Message, state: FSMContext):
    """Handler for fuel liters input"""
    try:
        # Try to convert liters to float
        liters = float(message.text.replace(',', '.'))
        
        if liters <= 0:
            raise ValueError("Liters must be positive")
        
        # Store liters in state
        await state.update_data(liters=liters)
        
        # Ask for cost per liter
        await message.answer(
            "💰 Введите стоимость одного литра топлива (в рублях):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(RefuelingFSM.cost_per_liter)
        
    except ValueError:
        await message.answer(
            "❌ Ошибка! Количество литров должно быть положительным числом. Пожалуйста, введите корректное значение:",
            reply_markup=get_cancel_keyboard()
        )

@dp.message(RefuelingFSM.cost_per_liter)
async def refueling_cost_entered(message: types.Message, state: FSMContext):
    """Handler for fuel cost input"""
    try:
        # Try to convert cost to float
        cost_per_liter = float(message.text.replace(',', '.'))
        
        if cost_per_liter <= 0:
            raise ValueError("Cost must be positive")
        
        # Get complete refueling data
        state_data = await state.get_data()
        date = state_data["date"]
        mileage = state_data["mileage"]
        liters = state_data["liters"]
        
        # Add refueling record
        success = add_refueling(date, mileage, liters, cost_per_liter)
        
        if success:
            total_cost = liters * cost_per_liter
            await message.answer(
                f"✅ Заправка успешно добавлена!\n\n"
                f"📅 Дата: {date}\n"
                f"🚗 Пробег: {mileage} км\n"
                f"⛽ Топливо: {liters} л.\n"
                f"💰 Стоимость: {total_cost:.2f} руб. ({cost_per_liter:.2f} руб/л)"
            )
            
            # Return to main menu after a short delay
            await asyncio.sleep(2)
            await message.answer(
                get_vehicle_card(),
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при добавлении заправки.",
                reply_markup=get_back_keyboard()
            )
        
        # Clear state
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Ошибка! Стоимость должна быть положительным числом. Пожалуйста, введите корректную сумму:",
            reply_markup=get_cancel_keyboard()
        )

# Main entry point
async def main():
    # Remove webhook and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")