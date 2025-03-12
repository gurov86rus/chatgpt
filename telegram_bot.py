import logging
import sqlite3
import asyncio
import os
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError
from config import TOKEN
from db_init import init_database
from db_operations import register_user, get_all_users, get_user_stats, is_user_admin, set_admin_status
import utils
from utils import days_until, format_days_remaining, get_to_interval_based_on_mileage, edit_fuel_info

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Изменено с INFO на DEBUG для большей детализации
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler("bot_debug.log")  # Дополнительный вывод в файл
    ]
)

# Ensure database is initialized
init_database()

# Admin list - add your Telegram ID here
ADMIN_IDS = [936544929]  # ID пользователя добавлен

# Function to check if user is admin
def is_admin(user_id):
    """Check if user is admin"""
    # Первоначальная проверка по статичному списку админов для доступа до инициализации базы
    if user_id in ADMIN_IDS:
        return True
    
    # Проверка через базу данных для динамического управления админами
    return is_user_admin(user_id)

# Decorator for admin-only functions
def admin_required(func):
    """Decorator to restrict function to admins only"""
    import inspect
    
    # Получаем информацию о параметрах оригинальной функции
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    
    async def wrapper(event, *args, **kwargs):
        # Проверка прав администратора
        user_id = event.from_user.id
        if not is_admin(user_id):
            if isinstance(event, types.CallbackQuery):
                await event.answer("⚠️ У вас нет прав администратора для выполнения этой операции", show_alert=True)
                return
            elif isinstance(event, types.Message):
                await event.answer("⚠️ У вас нет прав администратора для выполнения этой операции")
                return
        
        # Оставляем только те аргументы, которые функция может принять
        # Первый параметр всегда event, его оставляем
        filtered_kwargs = {}
        for key, value in kwargs.items():
            if key in param_names:
                filtered_kwargs[key] = value
        
        # Вызываем функцию только с теми аргументами, которые она принимает
        return await func(event, *args, **filtered_kwargs)
    
    return wrapper

# Initialize bot and dispatcher with enhanced error handling
try:
    # Импортируем DefaultBotProperties для новой версии aiogram 3.7.0+
    from aiogram.client.default import DefaultBotProperties
    
    # Проверка токена перед инициализацией
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден или пустой. Проверьте настройки окружения.")
    
    # Вывод информации о токене для диагностики (без самого токена)
    token_parts = TOKEN.split(':')
    if len(token_parts) >= 2:
        bot_id = token_parts[0]
        token_length = len(TOKEN)
        logging.info(f"Используется токен бота с ID: {bot_id}, длина токена: {token_length} символов")
    else:
        logging.warning("Формат токена выглядит некорректным, должен быть вида '123456789:ABC...XYZ'")
    
    # Create Bot instance with updated initialization for aiogram 3.7.0+
    bot = Bot(
        token=TOKEN, 
        default=DefaultBotProperties(parse_mode="Markdown")
    )
    
    # Проверка соединения с API Telegram
    logging.info("Проверка соединения с API Telegram...")
    
    # Initialize storage and dispatcher
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logging.info("Dispatcher successfully initialized")
except Exception as e:
    logging.error(f"Error initializing bot or dispatcher: {e}")
    import traceback
    logging.error(traceback.format_exc())
    raise

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
    
class FuelInfoState(StatesGroup):
    vehicle_id = State()
    fuel_type = State()
    fuel_tank_capacity = State()
    avg_fuel_consumption = State()
    
class AdminManageState(StatesGroup):
    user_id = State()
    action = State() # "add" или "remove"

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
    
    # Добавляем кнопку для перехода на веб-интерфейс
    web_url = "https://d933dc0e-c8d9-4501-bbd7-4bdac973738c-00-33heojbox43gm.picard.replit.dev"
    keyboard.append([
        InlineKeyboardButton(
            text="🌐 Открыть веб-интерфейс", 
            url=web_url
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
    
    # Get last maintenance record for interval calculation
    cursor.execute("""
        SELECT mileage FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC LIMIT 1
    """, (vehicle_id,))
    last_to_record = cursor.fetchone()
    last_to_mileage = last_to_record['mileage'] if last_to_record else None
    
    # Generate vehicle card with enhanced information
    card = (
        f"🚛 **{vehicle['model']} ({vehicle['reg_number']})**\n\n"
        f"📋 **Основная информация:**\n"
        f"📜 **VIN:** `{vehicle['vin'] or '-'}`\n"
        f"🔖 **Категория:** `{vehicle['category'] or '-'}`\n"
        f"🏷 **Квалификация:** `{vehicle['qualification'] or '-'}`\n"
        f"🔢 **Пробег:** `{vehicle['mileage'] or 0} км`\n"
        f"🛠 **Тахограф:** {'✅ Требуется' if vehicle['tachograph_required'] else '❌ Не требуется'}\n\n"
        
        f"📝 **Документы и сроки:**\n"
    )
    
    # Add document expiration with days remaining
    osago_days = days_until(vehicle['osago_valid'])
    tech_days = days_until(vehicle['tech_inspection_valid'])
    
    card += f"📅 **ОСАГО до:** `{vehicle['osago_valid'] or '-'}` {format_days_remaining(osago_days)}\n"
    card += f"🔧 **Техосмотр до:** `{vehicle['tech_inspection_valid'] or '-'}` {format_days_remaining(tech_days)}\n"
    
    # Add SKZI information if tachograph is required
    if vehicle['tachograph_required']:
        skzi_days = days_until(vehicle['skzi_valid_date'])
        card += (
            f"🔐 **СКЗИ установлен:** `{vehicle['skzi_install_date'] or '-'}`\n"
            f"🔐 **СКЗИ действует до:** `{vehicle['skzi_valid_date'] or '-'}` {format_days_remaining(skzi_days)}\n"
        )
    
    # Add maintenance information with TO interval calculation
    if last_to_mileage:
        # Calculate next TO based on 10,000 km interval
        remaining_km, next_to_mileage = get_to_interval_based_on_mileage(last_to_mileage, vehicle['mileage'])
        
        card += f"\n🔧 **Обслуживание:**\n"
        
        if vehicle['last_to_date']:
            card += f"📆 **Последнее ТО:** `{vehicle['last_to_date']}` при пробеге `{last_to_mileage} км`\n"
        
        # Display next TO based on mileage
        card += f"🔄 **Следующее ТО при:** `{next_to_mileage} км`\n"
        card += f"🔄 **Осталось до ТО:** `{remaining_km} км`\n"
        
        if remaining_km <= 0:
            card += "⚠️ **ВНИМАНИЕ! Необходимо пройти ТО!**\n"
        elif remaining_km <= 500:
            card += "⚠️ **ВНИМАНИЕ! ТО требуется в ближайшее время!**\n"
        elif remaining_km <= 1000:
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
            [InlineKeyboardButton(text="⛽ Информация о топливе", callback_data=f"edit_fuel_{vehicle_id}")],
            [InlineKeyboardButton(text="✏️ Редактировать ТС", callback_data=f"edit_{vehicle_id}")],
            [InlineKeyboardButton(text="📋 Управление ТО", callback_data=f"manage_to_{vehicle_id}")],
            [InlineKeyboardButton(text="🔧 Управление ремонтами", callback_data=f"manage_repairs_{vehicle_id}")],
            [InlineKeyboardButton(text="📊 Сгенерировать отчет", callback_data="generate_report")],
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
    
    # Регистрируем пользователя в системе
    register_user(user_id, message.from_user.username or "", user_name)
    
    # Show user ID
    user_id_info = f"🆔 Ваш Telegram ID: {user_id}"
    if is_admin(user_id):
        user_id_info += " (Вы администратор)"
    else:
        user_id_info += " (Обычный пользователь)"
    
    # Отправляем информацию без кнопки веб-интерфейса
    await message.answer(
        f"👋 *Добро пожаловать в Систему Управления Автопарком!*\n\n"
        f"🚚 *АвтоБот - Ваш интеллектуальный помощник в управлении транспортными средствами*\n\n"
        f"Привет, {user_name}! С помощью этого бота вы можете вести полный учет автопарка, отслеживать техническое обслуживание, ремонты и расход топлива.\n\n"
        f"🌐 *Также доступен веб-интерфейс* для более детального просмотра информации в браузере.\n\n"
        f"{user_id_info}\n\n"
        f"📊 *Основные функции:*\n"
        f"• Отслеживание пробега и технического состояния\n"
        f"• Управление плановыми ТО и внеплановыми ремонтами\n"
        f"• Учет расхода топлива и затрат\n"
        f"• Контроль сроков документов (ОСАГО, ТО, СКЗИ)\n"
        f"• Уведомления о приближающихся сроках обслуживания\n"
        f"• Автоматические резервные копии данных\n\n"
        f"🔍 *Команды бота:*\n"
        f"/start - Запуск бота и список автомобилей\n"
        f"/help - Подробная справка по использованию\n"
        f"/myid - Просмотр вашего Telegram ID",
        parse_mode="Markdown"
    )
    
    # Отправляем список автомобилей
    await message.answer(
        f"🚗 *Выберите автомобиль из списка для начала работы:*",
        reply_markup=get_vehicle_buttons(),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Handler for /help command"""
    # Получаем правильную ссылку на веб-интерфейс
    web_url = "https://d933dc0e-c8d9-4501-bbd7-4bdac973738c-00-33heojbox43gm.picard.replit.dev"
    
    # Базовая справка
    help_text = (
        "ℹ️ **Справка по использованию бота:**\n\n"
        "🚗 **Основные команды:**\n"
        "/start - Показать список автомобилей\n"
        "/help - Показать эту справку\n"
        "/myid - Показать ваш Telegram ID\n"
    )
    
    # Дополнительные команды для администраторов
    if is_admin(message.from_user.id):
        help_text += (
            "/backup - Создать резервную копию базы данных\n"
            "/users - Просмотр списка пользователей\n"
            "/admin - Управление статусом администратора\n"
        )
    
    # Общая справка
    help_text += (
        "\n⚙️ **Работа с автомобилем:**\n"
        "- Нажмите на автомобиль в списке, чтобы увидеть подробную информацию\n"
        "- Используйте кнопки под карточкой автомобиля для внесения новых данных\n\n"
        "📊 **Доступные функции:**\n"
        "- Обновление текущего пробега\n"
        "- Внесение данных о плановом ТО\n"
        "- Запись о внеплановом ремонте\n"
        "- Редактирование данных ТС\n\n"
        "🔔 **Уведомления:**\n"
        "Система автоматически предупредит об истечении сроков документов и необходимости ТО\n\n"
        "💾 **Резервное копирование:**\n"
        "Резервные копии создаются автоматически каждый день в 3:00\n\n"
        "🌐 **Веб-интерфейс:**\n"
        "Для расширенного просмотра и анализа данных используйте веб-интерфейс системы"
    )
    
    # Отправляем справку без кнопки веб-интерфейса
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("myid"))
async def show_my_id(message: types.Message):
    """Handler to show user's Telegram ID"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # Регистрируем пользователя при запросе ID
    register_user(user_id, message.from_user.username or "", user_name)
    
    # Проверяем статус администратора и выводим информацию
    admin_status = is_admin(user_id)
    help_text = ""
    if not admin_status and user_id in ADMIN_IDS:
        # Если пользователь в списке ADMIN_IDS, но не отмечен в БД как админ, исправляем
        set_admin_status(user_id, True)
        admin_status = True
        help_text = "✅ Ваш статус администратора восстановлен в базе данных!"
    
    await message.answer(
        f"👤 **Информация о пользователе**\n\n"
        f"🆔 Ваш Telegram ID: `{user_id}`\n"
        f"👤 Имя: {user_name}\n"
        f"🔑 Статус: {'Администратор' if admin_status else 'Обычный пользователь'}\n\n"
        f"{help_text}\n"
        f"ℹ️ Используйте команду /admin для управления статусами администраторов",
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
@admin_required
async def admin_command(message: types.Message, state: FSMContext):
    """Handler for admin command to manage admin status"""
    # Создаем клавиатуру с кнопками действий
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Добавить администратора", callback_data="admin_add")],
        [InlineKeyboardButton(text="🔄 Удалить администратора", callback_data="admin_remove")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ])
    
    await message.answer(
        "👑 **Управление администраторами**\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "admin_add")
@admin_required
async def admin_add(callback: types.CallbackQuery, state: FSMContext):
    """Start process of adding an admin"""
    # Сначала очищаем состояние, чтобы избежать конфликтов
    await state.clear()
    # Затем устанавливаем новое значение
    await state.update_data(action="add")
    logging.info(f"Начало процесса добавления администратора. Состояние: {await state.get_data()}")
    
    await callback.message.edit_text(
        "👑 **Добавление администратора**\n\n"
        "Введите Telegram ID пользователя, которого нужно сделать администратором:\n"
        "_(Пользователь должен быть зарегистрирован в системе)_",
        parse_mode="Markdown"
    )
    await state.set_state(AdminManageState.user_id)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_remove")
@admin_required
async def admin_remove(callback: types.CallbackQuery, state: FSMContext):
    """Start process of removing an admin"""
    # Сначала очищаем состояние, чтобы избежать конфликтов
    await state.clear()
    # Затем устанавливаем новое значение
    await state.update_data(action="remove")
    logging.info(f"Начало процесса удаления администратора. Состояние: {await state.get_data()}")
    
    await callback.message.edit_text(
        "🔄 **Удаление администратора**\n\n"
        "Введите Telegram ID пользователя, которого нужно лишить прав администратора:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminManageState.user_id)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_cancel")
@admin_required
async def admin_cancel(callback: types.CallbackQuery):
    """Cancel admin management process"""
    await callback.message.edit_text(
        "❌ Управление администраторами отменено.",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(AdminManageState.user_id)
@admin_required
async def process_admin_user_id(message: types.Message, state: FSMContext):
    """Process user ID input for admin management"""
    try:
        user_id = int(message.text)
        data = await state.get_data()
        logging.info(f"Обработка ID пользователя: {user_id}, текущее состояние: {data}")
        
        action = data.get("action")
        if not action:
            logging.error(f"Ошибка: отсутствует действие в состоянии. Текущие данные: {data}")
            await message.answer(
                "⚠️ Ошибка: Не указано действие. Пожалуйста, начните процесс заново."
            )
            await state.clear()
            return
        
        # Проверяем, существует ли пользователь
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            logging.warning(f"Пользователь с ID {user_id} не найден в базе данных")
            await message.answer(
                "⚠️ Ошибка: Пользователь с указанным ID не найден в системе.\n\n"
                "Пользователь должен быть зарегистрирован. Попросите его использовать бота и выполнить команду /start или /myid."
            )
            await state.clear()
            return
        
        # Извлекаем данные о пользователе
        user_name = user[1]
        is_admin = bool(user[2])
        logging.info(f"Найден пользователь: {user_name}, админ: {is_admin}")
        
        # Проверяем, что действие имеет смысл
        if action == "add" and is_admin:
            logging.info(f"Попытка добавить существующего администратора {user_name} (ID: {user_id})")
            await message.answer(
                f"ℹ️ Пользователь {user_name} (ID: {user_id}) уже является администратором."
            )
            await state.clear()
            return
        
        if action == "remove" and not is_admin:
            logging.info(f"Попытка удалить пользователя {user_name} (ID: {user_id}), который не является администратором")
            await message.answer(
                f"ℹ️ Пользователь {user_name} (ID: {user_id}) не является администратором."
            )
            await state.clear()
            return
        
        # Запрашиваем подтверждение
        await state.update_data(target_user_id=user_id, target_user_name=user_name)
        updated_data = await state.get_data()
        logging.info(f"Обновленное состояние перед подтверждением: {updated_data}")
        
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
        ])
        
        action_text = "добавить как администратора" if action == "add" else "удалить из администраторов"
        
        await message.answer(
            f"⚠️ **Подтвердите действие**\n\n"
            f"Вы собираетесь {action_text} пользователя:\n"
            f"👤 Имя: {user_name}\n"
            f"🆔 ID: {user_id}\n\n"
            f"Подтвердите или отмените действие:",
            reply_markup=confirm_keyboard,
            parse_mode="Markdown"
        )
        
        # Устанавливаем новое состояние и проверяем его
        await state.set_state(AdminManageState.action)
        logging.info(f"Установлено состояние AdminManageState.action")
        
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: ID пользователя должен быть числом.\n\n"
            "Попробуйте снова:"
        )

@dp.callback_query(lambda c: c.data.startswith("confirm_"))
@admin_required
async def confirm_admin_action(callback: types.CallbackQuery, state: FSMContext):
    """Confirm admin status change"""
    # Добавляем подробное логирование
    logging.info(f"Получен callback: {callback.data}")
    
    # Получаем действие из callback data
    callback_parts = callback.data.split("_")
    if len(callback_parts) > 1:
        callback_action = callback_parts[1]  # add или remove
        logging.info(f"Извлечено действие из callback: {callback_action}")
    else:
        logging.error(f"Неверный формат callback data: {callback.data}")
        callback_action = "unknown"
    
    # Выводим текущее состояние для диагностики
    data = await state.get_data()
    logging.info(f"Текущее состояние: {data}")
    
    # Извлекаем имя и ID пользователя из callback, если они отсутствуют в состоянии
    if "target_user_id" not in data or "target_user_name" not in data or "action" not in data:
        logging.info(f"Данных в состоянии нет, пытаемся извлечь из callback: {callback.data}")
        
        try:
            # Восстанавливаем данные из callback, если возможно
            if len(callback_parts) > 3 and callback_parts[0] == "confirm":
                user_id_str = callback_parts[3]
                user_id = int(user_id_str)
                
                # Получаем имя пользователя из базы данных
                conn = sqlite3.connect('vehicles.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Исправлено: column user_id -> id в таблице users
                cursor.execute("SELECT username, full_name FROM users WHERE id = ?", (user_id,))
                user_data = cursor.fetchone()
                conn.close()
                
                if user_data:
                    # Восстанавливаем данные в состоянии
                    action = "add" if "add" in callback.data else "remove"
                    await state.update_data(
                        target_user_id=user_id,
                        target_user_name=user_data['full_name'] or user_data['username'],
                        action=action
                    )
                    data = await state.get_data()
                    logging.info(f"Восстановили данные в состоянии: {data}")
                else:
                    # Проверяем, существует ли таблица users и есть ли в ней записи
                    conn = sqlite3.connect('vehicles.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                    table_exists = cursor.fetchone()
                    
                    if not table_exists:
                        logging.error("Таблица users не существует в базе данных")
                        message_text = "⚠️ Ошибка: Таблица пользователей не найдена. Необходимо инициализировать базу данных."
                    else:
                        # Проверяем, есть ли записи в таблице
                        cursor.execute("SELECT COUNT(*) FROM users")
                        count = cursor.fetchone()[0]
                        if count == 0:
                            logging.error("Таблица users пуста, нет зарегистрированных пользователей")
                            message_text = "⚠️ Ошибка: В системе нет зарегистрированных пользователей. Пользователь должен сначала использовать команду /start."
                        else:
                            logging.error(f"Пользователь {user_id} не найден в базе данных")
                            message_text = f"⚠️ Ошибка: Пользователь с ID {user_id} не найден. Попросите его выполнить команду /start или /myid."
                    
                    conn.close()
                    
                    await callback.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="⬅️ Вернуться", callback_data="admin")]
                        ])
                    )
                    await callback.answer()
                    await state.clear()
                    return
            else:
                logging.error(f"Невозможно восстановить данные пользователя из callback: {callback.data}")
                await callback.message.edit_text(
                    "⚠️ Ошибка: Данные пользователя не найдены. Пожалуйста, попробуйте снова.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Вернуться", callback_data="admin")]
                    ])
                )
                await callback.answer()
                await state.clear()
                return
        except (ValueError, IndexError, TypeError) as e:
            logging.error(f"Ошибка при извлечении данных из callback: {e}")
            await callback.message.edit_text(
                "⚠️ Ошибка: Некорректный формат данных. Пожалуйста, попробуйте снова.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Вернуться", callback_data="admin")]
                ])
            )
            await callback.answer()
            await state.clear()
            return
    
    user_id = data["target_user_id"]
    user_name = data["target_user_name"]
    action = data["action"]  # Используем сохраненное действие вместо извлеченного из callback
    
    logging.info(f"Обрабатываем изменение статуса администратора для пользователя {user_name} (ID: {user_id}), действие: {action}")
    
    # Проверяем соответствие действий
    if action != callback_action and callback_action != "unknown":
        logging.warning(f"Несоответствие действий: state={action}, callback={callback_action}")
    
    # Изменяем статус администратора
    new_status = (action == "add")
    logging.info(f"Устанавливаем статус администратора: {new_status}")
    result = set_admin_status(user_id, new_status)
    logging.info(f"Результат установки статуса: {result}")
    
    # Очищаем состояние до вывода сообщения
    await state.clear()
    
    if result:
        action_text = "добавлен в" if new_status else "удален из"
        await callback.message.edit_text(
            f"✅ Пользователь {user_name} (ID: {user_id}) успешно {action_text} списка администраторов.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Вернуться к управлению", callback_data="admin")]
            ])
        )
    else:
        await callback.message.edit_text(
            f"⚠️ Произошла ошибка при изменении статуса администратора для пользователя {user_name}.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Вернуться к управлению", callback_data="admin")]
            ])
        )
    
    await callback.answer()

@dp.message(Command("users"))
@admin_required
async def show_users(message: types.Message):
    """Handler for showing registered users (admin only)"""
    users = get_all_users()
    stats = get_user_stats()
    
    if not users:
        await message.answer("⚠️ Список пользователей пуст.")
        return
    
    # Статистика пользователей
    stats_text = (
        f"📊 **Статистика пользователей:**\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"👤 Активных за 7 дней: {stats['active_users']}\n"
        f"🆕 Новых за 30 дней: {stats['new_users']}\n"
        f"🔑 Администраторов: {stats['admin_count']}\n\n"
    )
    
    # Список пользователей
    users_text = "👥 **Список пользователей:**\n\n"
    
    for user in users:
        admin_status = "👑 Администратор" if user.get('is_admin') else "👤 Пользователь"
        username = f"@{user.get('username')}" if user.get('username') else "нет"
        
        users_text += (
            f"🆔 `{user.get('id')}`\n"
            f"👤 Имя: {user.get('full_name')}\n"
            f"🔖 Username: {username}\n"
            f"🔑 Статус: {admin_status}\n"
            f"📅 Первый вход: {user.get('first_seen')}\n"
            f"🕒 Последняя активность: {user.get('last_activity')}\n"
            f"🔄 Действий: {user.get('interaction_count', 0)}\n\n"
        )
    
    # Отправляем несколько сообщений, если список слишком длинный
    max_message_length = 4000
    
    if len(stats_text + users_text) <= max_message_length:
        await message.answer(stats_text + users_text, parse_mode="Markdown")
    else:
        await message.answer(stats_text, parse_mode="Markdown")
        
        # Разделяем список пользователей на части
        remaining_text = users_text
        while remaining_text:
            # Находим безопасную точку разделения (между записями пользователей)
            split_point = remaining_text[:max_message_length].rfind("\n\n")
            if split_point == -1:  # Если не нашли двойной перенос, разделяем по одинарному
                split_point = remaining_text[:max_message_length].rfind("\n")
            if split_point == -1:  # Если и это не помогло, просто отрезаем максимальную длину
                split_point = max_message_length - 1
            
            # Отправляем часть текста
            await message.answer(remaining_text[:split_point+1], parse_mode="Markdown")
            
            # Обновляем оставшийся текст
            remaining_text = remaining_text[split_point+1:]

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
@dp.callback_query(lambda c: c.data.startswith("edit_") and not c.data.startswith("edit_field_") and not c.data.startswith("edit_repair_") and not c.data.startswith("edit_maintenance_") and not c.data.startswith("edit_fuel_"))
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
@admin_required
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

@dp.callback_query(lambda c: c.data.startswith("maintenance_") and not c.data.startswith("maintenance_delete_"))
async def show_maintenance_record(callback: types.CallbackQuery):
    """Handler for showing maintenance record details"""
    # Проверяем формат callback data
    callback_parts = callback.data.split("_")
    if len(callback_parts) < 2 or callback_parts[0] != "maintenance":
        await callback.answer("⚠️ Неверный формат данных", show_alert=True)
        return
        
    try:
        maintenance_id = int(callback_parts[1])
    except ValueError:
        await callback.answer("⚠️ Неверный формат ID записи", show_alert=True)
        return
    
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
    try:
        # Получаем ID записи ТО из callback data
        callback_parts = callback.data.split("_")
        if len(callback_parts) >= 3:
            maintenance_id = int(callback_parts[2])
        else:
            await callback.answer("⚠️ Ошибка в формате данных", show_alert=True)
            return
        
        logging.info(f"Запрос на удаление записи ТО с ID={maintenance_id}")
        
        # Очищаем предыдущее состояние
        await state.clear()
        
        # Получаем данные о записи ТО
        conn = sqlite3.connect('vehicles.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT date, mileage, vehicle_id FROM maintenance WHERE id = ?", (maintenance_id,))
        record = cursor.fetchone()
        conn.close()
        
        if not record:
            await callback.answer("⚠️ Запись о ТО не найдена", show_alert=True)
            return
        
        vehicle_id = record['vehicle_id']
        date = record['date']
        mileage = record['mileage']
        
        # Создаем клавиатуру для подтверждения удаления
        keyboard = [
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"maintenance_delete_confirm_{maintenance_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"manage_to_{vehicle_id}")]
        ]
        
        await callback.message.edit_text(
            f"⚠️ **Подтверждение удаления**\n\n"
            f"Вы действительно хотите удалить запись о ТО от {date} (пробег: {mileage} км)?\n\n"
            f"Это действие нельзя отменить.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка при подготовке удаления записи ТО: {e}")
        await callback.answer("⚠️ Произошла ошибка", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("maintenance_delete_confirm_"))
@admin_required
async def maintenance_delete_execute(callback: types.CallbackQuery, state: FSMContext):
    """Handler for executing maintenance record deletion"""
    try:
        # Получаем ID записи ТО из callback data
        maintenance_id = int(callback.data.split("_")[3])
        logging.info(f"Выполнение удаления записи ТО с ID={maintenance_id}")
        
        # Получаем ID транспортного средства
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id FROM maintenance WHERE id = ?", (maintenance_id,))
        result = cursor.fetchone()
        
        if not result:
            await callback.answer("⚠️ Запись уже удалена", show_alert=True)
            conn.close()
            return
            
        vehicle_id = result[0]
        
        # Удаляем запись
        cursor.execute("DELETE FROM maintenance WHERE id = ?", (maintenance_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text(
            "✅ Запись о техническом обслуживании успешно удалена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 К списку ТО", callback_data=f"manage_to_{vehicle_id}")],
                [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
            ])
        )
        logging.info(f"Запись ТО с ID={maintenance_id} для ТС ID={vehicle_id} успешно удалена")
    except Exception as e:
        logging.error(f"Ошибка при удалении записи ТО: {e}")
        await callback.message.edit_text(
            "⚠️ Произошла ошибка при удалении записи.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку автомобилей", callback_data="back")]
            ])
        )
    
    await callback.answer()
    await state.clear()
    


# Repair Management Handlers
@dp.callback_query(lambda c: c.data.startswith("manage_repairs_"))
@admin_required
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
    
    # Очищаем старое состояние перед началом нового действия
    await state.clear()
    
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
    
    # Save repair_id and vehicle_id to state с четкими названиями
    await state.update_data(
        repair_delete_id=repair_id,
        repair_vehicle_id=record['vehicle_id'],
        repair_date=record['date'],
        repair_mileage=record['mileage']
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
    try:
        # Получаем ID записи ремонта из callback data
        repair_id = int(callback.data.split("_")[3])
        logging.info(f"Выполнение удаления записи ремонта с ID={repair_id}")
        
        # Получаем ID транспортного средства
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id FROM repairs WHERE id = ?", (repair_id,))
        result = cursor.fetchone()
        
        if not result:
            await callback.answer("⚠️ Запись уже удалена", show_alert=True)
            conn.close()
            return
            
        vehicle_id = result[0]
        
        # Удаляем запись
        cursor.execute("DELETE FROM repairs WHERE id = ?", (repair_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text(
            "✅ Запись о ремонте успешно удалена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔧 К списку ремонтов", callback_data=f"manage_repairs_{vehicle_id}")],
                [InlineKeyboardButton(text="🔙 К карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
            ])
        )
        logging.info(f"Запись ремонта с ID={repair_id} для ТС ID={vehicle_id} успешно удалена")
    except Exception as e:
        logging.error(f"Ошибка при удалении записи ремонта: {e}")
        await callback.message.edit_text(
            "⚠️ Произошла ошибка при удалении записи.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку автомобилей", callback_data="back")]
            ])
        )
    
    await callback.answer()
    await state.clear()

# Fuel information handling
@dp.callback_query(lambda c: c.data.startswith("edit_fuel_"))
@admin_required
async def edit_fuel_start(callback: types.CallbackQuery, state: FSMContext):
    """Start fuel information editing process"""
    # Correctly parse id from edit_fuel_{id} pattern
    vehicle_id = int(callback.data.split("_")[2])
    await state.update_data(vehicle_id=vehicle_id)
    
    # Get current fuel information
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fuel_type, fuel_tank_capacity, avg_fuel_consumption 
        FROM vehicles 
        WHERE id = ?
    """, (vehicle_id,))
    fuel_data = cursor.fetchone()
    conn.close()
    
    # Create a message with the current values
    message_text = (
        f"⛽ **Редактирование информации о топливе**\n\n"
        f"Текущие значения:\n"
        f"🛢 **Тип топлива:** `{fuel_data['fuel_type'] or '-'}`\n"
        f"🛢 **Объем бака:** `{fuel_data['fuel_tank_capacity'] or '-'} л`\n"
        f"🛢 **Средний расход:** `{fuel_data['avg_fuel_consumption'] or '-'} л/100км`\n\n"
        f"Введите тип топлива (например, 'Дизель', 'АИ-95' и т.д.):"
    )
    
    await callback.message.edit_text(
        message_text,
        parse_mode="Markdown"
    )
    await state.set_state(FuelInfoState.fuel_type)
    await callback.answer()

@dp.message(FuelInfoState.fuel_type)
async def process_fuel_type(message: types.Message, state: FSMContext):
    """Process fuel type input"""
    await state.update_data(fuel_type=message.text.strip())
    await message.answer(
        "🛢 Введите объем топливного бака в литрах (например, 60):"
    )
    await state.set_state(FuelInfoState.fuel_tank_capacity)

@dp.message(FuelInfoState.fuel_tank_capacity)
async def process_fuel_tank_capacity(message: types.Message, state: FSMContext):
    """Process fuel tank capacity input"""
    try:
        if message.text.strip():
            capacity = float(message.text.strip())
            await state.update_data(fuel_tank_capacity=capacity)
        else:
            await state.update_data(fuel_tank_capacity=None)
            
        await message.answer(
            "🛢 Введите средний расход топлива в л/100км (например, 8.5):"
        )
        await state.set_state(FuelInfoState.avg_fuel_consumption)
    except ValueError:
        await message.answer(
            "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
            "Попробуйте снова или оставьте поле пустым:"
        )

@dp.message(FuelInfoState.avg_fuel_consumption)
async def process_fuel_consumption(message: types.Message, state: FSMContext):
    """Process fuel consumption input and save all fuel data"""
    data = await state.get_data()
    vehicle_id = data["vehicle_id"]
    
    # Prepare fuel consumption value
    avg_fuel_consumption = None
    if message.text.strip():
        try:
            avg_fuel_consumption = float(message.text.strip())
        except ValueError:
            await message.answer(
                "⚠️ Ошибка: Введите число без дополнительных символов.\n\n"
                "Попробуйте снова или оставьте поле пустым:"
            )
            return
    
    # Update fuel information in the database
    success = edit_fuel_info(
        vehicle_id=vehicle_id,
        fuel_type=data.get("fuel_type"),
        fuel_tank_capacity=data.get("fuel_tank_capacity"),
        avg_fuel_consumption=avg_fuel_consumption
    )
    
    if success:
        await state.clear()
        await message.answer(
            "✅ Информация о топливе успешно обновлена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться к карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
            ])
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении информации о топливе.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться к карточке ТС", callback_data=f"vehicle_{vehicle_id}")]
            ])
        )

# Report generation handler
@dp.callback_query(lambda c: c.data == "generate_report")
@admin_required
async def generate_pdf_report(callback: types.CallbackQuery):
    """Generate and send PDF report"""
    try:
        # Generate the report
        report_path = utils.generate_expiration_report()
        
        # Send the report
        with open(report_path, 'rb') as pdf:
            await callback.message.answer_document(
                types.BufferedInputFile(
                    pdf.read(),
                    filename=f"report_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
                ),
                caption="📊 Отчет о сроках действия документов для всех транспортных средств"
            )
        
        # Cleanup the file
        os.remove(report_path)
        
        await callback.answer("✅ Отчет успешно сгенерирован!")
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        await callback.message.answer(f"❌ Ошибка при генерации отчета: {str(e)}")
        await callback.answer("❌ Ошибка при генерации отчета")

# Обработчик команды резервного копирования
@dp.message(Command("backup"))
@admin_required
async def backup_command(message: types.Message):
    """Handler for backup command - creates backup and sends to admin"""
    await message.answer("🔄 Создание резервной копии базы данных...")
    
    # Импортируем функцию резервного копирования
    from backup import manual_backup
    
    # Создаем резервную копию
    success = await manual_backup(message.from_user.id)
    
    if success:
        await message.answer("✅ Резервная копия создана и отправлена!")
    else:
        await message.answer("❌ Ошибка при создании резервной копии!")

# Main function to run the bot
async def main():
    # Initialize database
    init_database()
    
    # Запуск планировщика резервного копирования в отдельной задаче
    try:
        from backup import scheduled_backup
        asyncio.create_task(scheduled_backup(hour=3, minute=0))
        logging.info("Планировщик резервного копирования запущен")
    except Exception as e:
        logging.error(f"Ошибка при запуске планировщика резервного копирования: {e}")
    
    # Reset webhook before starting polling to avoid conflicts
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Start polling with aggressive settings to prevent conflicts
    logging.info("Starting vehicle maintenance bot...")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
        polling_timeout=30
    )

if __name__ == "__main__":
    asyncio.run(main())