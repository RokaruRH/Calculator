import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "7427838862:AAET4yjpqH6k8OYr4xzOkshDbZvTBo6Zpbo"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

raid_sulfur_table = {
    "Деревянная стенка": {"Количество": 3, "Тип": "Сачель", "Сера": 1440},
    "Каменная стенка": {"Количество": 2, "Тип": "С4", "Сера": 4400},
    "Металл стена": {"Количество": 4, "Тип": "С4", "Сера": 8800},
    "Деревянная дверь": {"Количество": 2, "Тип": "Сачель", "Сера": 960},
    "Железная дверь": {"Количество": 3, "Тип": "Сачель", "Сера": 1440},
    "Гаражка": {"Количество": 3, "Тип": "С4 + Ракеты", "Сера": 3600},
    "МВК дверь": {"Количество": 3, "Тип": "С4", "Сера": 6600},
    "Турель": {"Количество": 4, "Тип": "Скоростные ракеты", "Сера": 400},
}

class RaidStates(StatesGroup):
    waiting_for_quantity = State()

def create_targets_keyboard():
    builder = InlineKeyboardBuilder()
    for target in raid_sulfur_table.keys():
        builder.add(InlineKeyboardButton(text=target, callback_data=f"target_{target}"))
    builder.adjust(2)
    return builder.as_markup()

def create_quantity_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Введите количество", callback_data="qty_custom")
    ]])

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Выбери цель для разрушения:", reply_markup=create_targets_keyboard())

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer("Команды:\n/start - Начать\n/targets - Показать цели\n\nВыберите цель → укажите количество → получите расчет")

@dp.message(Command("targets"))
async def targets_handler(message: types.Message):
    text = "Доступные цели:\n\n" + "\n".join([f"{target}: {info['Количество']} {info['Тип']} ({info['Сера']} серы)"
                                               for target, info in raid_sulfur_table.items()])
    await message.answer(text)

@dp.callback_query(F.data.startswith("target_"))
async def target_selected(callback: CallbackQuery, state: FSMContext):
    target_name = callback.data.replace("target_", "")
    if target_name not in raid_sulfur_table:
        return await callback.answer("Неизвестная цель!")

    await state.update_data(selected_target=target_name)
    info = raid_sulfur_table[target_name]
    text = f"Цель: {target_name}\n{info['Количество']} {info['Тип']} = {info['Сера']} серы\n\nУкажите количество целей:"
    await callback.message.edit_text(text, reply_markup=create_quantity_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "qty_custom")
async def quantity_custom(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите количество:")
    await state.set_state(RaidStates.waiting_for_quantity)
    await callback.answer()

@dp.callback_query(F.data == "new_calculation")
async def new_calculation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Выбери цель для разрушения:", reply_markup=create_targets_keyboard())
    await callback.answer()

@dp.message(RaidStates.waiting_for_quantity)
async def custom_quantity_handler(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            return await message.answer("Количество должно быть больше 0")
        await process_calculation(message, state, quantity)
    except ValueError:
        await message.answer("Введите корректное число")

async def process_calculation(message, state: FSMContext, quantity: int):
    data = await state.get_data()
    target_name = data.get('selected_target')

    if not target_name:
        return await message.answer("Ошибка: цель не выбрана. Начните заново /start")

    info = raid_sulfur_table[target_name]
    total_charges = info['Количество'] * quantity
    total_sulfur = info['Сера'] * quantity

    result = f"Расчет для {quantity}x {target_name}:\n\n"
    result += f"Зарядов ({info['Тип']}): {total_charges}\n"
    result += f"Серы: {total_sulfur}\n\n"

    # Добавляем материалы в зависимости от типа
    materials = {
        "С4": f"Металл фрагментов: {total_charges * 20}\nНизкосортное топливо: {total_charges * 30}",
        "Сачель": f"Ткань: {total_charges * 10}\nБобовые банки: {total_charges * 4}",
        "Скоростные ракеты": f"Металл трубы: {total_charges * 2}\nВзрывчатка: {total_charges * 10}"
    }

    for material_type, material_info in materials.items():
        if material_type in info['Тип']:
            result += material_info + "\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Новый расчет", callback_data="new_calculation")
    ]])

    await message.answer(result, reply_markup=keyboard)
    await state.clear()

@dp.message()
async def unknown_message(message: types.Message):
    await message.answer("Используй /start")

async def main():
    print("🤖 Rust Raid Calculator Bot запущен!")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("Бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
