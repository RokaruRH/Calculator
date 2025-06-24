import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Получаем токен из переменных окружения с проверкой
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Если токен не найден через .env, попробуем альтернативные способы
if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN не найден в .env файле")
    print("Попытка использования токена напрямую...")
    # Резервный токен (временное решение)
    BOT_TOKEN = "7427838862:AAET4yjpqH6k8OYr4xzOkshDbZvTBo6Zpbo"

    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        print("Создайте файл .env в корне проекта с содержимым:")
        print("BOT_TOKEN=7427838862:AAET4yjpqH6k8OYr4xzOkshDbZvTBo6Zpbo")
        exit(1)
    else:
        print("✅ Используется резервный токен")

# Дополнительная проверка типа и содержимого
if not isinstance(BOT_TOKEN, str) or not BOT_TOKEN.strip():
    print(f"❌ Ошибка: BOT_TOKEN должен быть непустой строкой, получен: {type(BOT_TOKEN)}")
    exit(1)

print(f"✅ Токен загружен успешно: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")

# Инициализация бота и диспетчера
try:
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("✅ Бот и диспетчер инициализированы успешно")
except Exception as e:
    print(f"❌ Ошибка при инициализации бота: {e}")
    exit(1)

# Таблица данных для рейда
raid_sulfur_table = {
    "Деревянная стенка": {"Количество": 3, "Тип": "Сачель", "Сера": 480*3},
    "Каменная стенка": {"Количество": 2, "Тип": "С4", "Сера": 2200*2},
    "Металл стена": {"Количество": 4, "Тип": "С4", "Сера": 2200*4},
    "Деревянная дверь": {"Количество": 2, "Тип": "Сачель", "Сера": 480*2},
    "Железная дверь": {"Количество": 3, "Тип": "Сачель", "Сера": 480*3},
    "Гаражка": {"Количество": 3, "Тип": "С4 + Ракеты", "Сера": 1400+2200},
    "МВК дверь": {"Количество": 3, "Тип": "С4", "Сера": 2200*3},
    "Турель": {"Количество": 4, "Тип": "Скоростные ракеты", "Сера": 100*4},
}

# Состояния для FSM
class RaidStates(StatesGroup):
    waiting_for_quantity = State()

# Функция для создания клавиатуры с целями
def create_targets_keyboard():
    builder = InlineKeyboardBuilder()
    for target in raid_sulfur_table.keys():
        builder.add(InlineKeyboardButton(
            text=target,
            callback_data=f"target_{target}"
        ))
    builder.adjust(2)  # По 2 кнопки в ряд
    return builder.as_markup()

# Функция для создания клавиатуры с количествами
def create_quantity_keyboard():
    builder = InlineKeyboardBuilder()
    quantities = [1, 2, 3, 4, 5, 10]
    for qty in quantities:
        builder.add(InlineKeyboardButton(
            text=str(qty),
            callback_data=f"qty_{qty}"
        ))
    builder.add(InlineKeyboardButton(
        text="Другое количество",
        callback_data="qty_custom"
    ))
    builder.adjust(3)  # По 3 кнопки в ряд
    return builder.as_markup()

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "💣 **Калькулятор рейда Rust по сере**\n\n"
        "Привет! Я помогу тебе рассчитать необходимое количество серы для рейда.\n\n"
        "Выбери цель для разрушения:",
        reply_markup=create_targets_keyboard(),
        parse_mode="Markdown"
    )

# Команда /help
@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        "🆘 **Помощь по боту**\n\n"
        "**Команды:**\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/targets - Показать все доступные цели\n\n"
        "**Как использовать:**\n"
        "1. Выберите цель для разрушения\n"
        "2. Укажите количество целей\n"
        "3. Получите расчет необходимых ресурсов\n\n"
        "Удачного рейда! 🎯"
    )
    await message.answer(help_text, parse_mode="Markdown")

# Команда /targets
@dp.message(Command("targets"))
async def targets_handler(message: types.Message):
    targets_text = "🎯 **Доступные цели для рейда:**\n\n"
    for i, (target, info) in enumerate(raid_sulfur_table.items(), 1):
        targets_text += f"{i}. **{target}**\n"
        targets_text += f"   • {info['Количество']} {info['Тип']}\n"
        targets_text += f"   • {info['Сера']} серы\n\n"

    await message.answer(targets_text, parse_mode="Markdown")

# Обработчик выбора цели
@dp.callback_query(F.data.startswith("target_"))
async def target_selected(callback: CallbackQuery, state: FSMContext):
    target_name = callback.data.replace("target_", "")

    # Сохраняем выбранную цель в состоянии
    await state.update_data(selected_target=target_name)

    info = raid_sulfur_table[target_name]

    message_text = (
        f"🔎 **Выбрана цель: {target_name}**\n\n"
        f"**Базовая информация:**\n"
        f"• Количество зарядов: {info['Количество']} ({info['Тип']})\n"
        f"• Требуемая сера: {info['Сера']} единиц\n\n"
        f"**Сколько таких целей хочешь разрушить?**"
    )

    await callback.message.edit_text(
        message_text,
        reply_markup=create_quantity_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик выбора количества
@dp.callback_query(F.data.startswith("qty_"))
async def quantity_selected(callback: CallbackQuery, state: FSMContext):
    if callback.data == "qty_custom":
        await callback.message.edit_text(
            "Введите количество целей (число больше 0):",
            reply_markup=None
        )
        await state.set_state(RaidStates.waiting_for_quantity)
        await callback.answer()
        return

    quantity = int(callback.data.replace("qty_", ""))
    await process_calculation(callback.message, state, quantity, callback)

# Обработчик ввода пользовательского количества
@dp.message(RaidStates.waiting_for_quantity)
async def custom_quantity_handler(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            await message.answer("⚠️ Количество должно быть больше 0. Попробуй еще раз:")
            return

        await process_calculation(message, state, quantity)

    except ValueError:
        await message.answer("⚠️ Введи корректное число. Попробуй еще раз:")

# Функция для обработки расчета
async def process_calculation(message, state: FSMContext, quantity: int, callback: CallbackQuery = None):
    data = await state.get_data()
    target_name = data.get('selected_target')

    if not target_name:
        await message.answer("❌ Ошибка: цель не выбрана. Начни заново с /start")
        return

    info = raid_sulfur_table[target_name]

    # Вычисляем итоговые значения
    total_charges = info['Количество'] * quantity
    total_sulfur = info['Сера'] * quantity

    # Формируем результат
    result_text = (
        f"🧮 **Расчет для {quantity}x {target_name}:**\n\n"
        f"**Основные ресурсы:**\n"
        f"• Зарядов ({info['Тип']}): {total_charges}\n"
        f"• Серы: {total_sulfur} единиц\n\n"
    )

    # Дополнительная информация о ресурсах
    result_text += "**Дополнительные ресурсы:**\n"
    if "С4" in info['Тип']:
        result_text += f"• Металлических фрагментов: {total_charges * 20}\n"
        result_text += f"• Низкосортного топлива: {total_charges * 30}\n"
    elif "Сачель" in info['Тип']:
        result_text += f"• Ткани: {total_charges * 10}\n"
        result_text += f"• Бобовых банок: {total_charges * 4}\n"
    elif "Скоростные ракеты" in info['Тип']:
        result_text += f"• Металлических труб: {total_charges * 2}\n"
        result_text += f"• Взрывчатки: {total_charges * 10}\n"

    result_text += "\n🎯 Удачного рейда!"

    # Создаем кнопку для нового расчета
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Новый расчет", callback_data="new_calculation")]
    ])

    if callback:
        await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    else:
        await message.answer(result_text, reply_markup=keyboard, parse_mode="Markdown")

    # Очищаем состояние
    await state.clear()

# Обработчик кнопки "Новый расчет"
@dp.callback_query(F.data == "new_calculation")
async def new_calculation(callback: CallbackQuery):
    await callback.message.edit_text(
        "💣 **Калькулятор рейда Rust по сере**\n\n"
        "Выбери цель для разрушения:",
        reply_markup=create_targets_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик неизвестных сообщений
@dp.message()
async def unknown_message(message: types.Message):
    await message.answer(
        "❓ Не понимаю эту команду.\n\n"
        "Используй /start для начала работы или /help для получения справки."
    )

# Главная функция
async def main():
    print("🤖 Rust Raid Calculator Bot запускается...")
    print(f"🔑 Токен: {'✅ Найден' if BOT_TOKEN else '❌ Не найден'}")

    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"👤 Бот @{bot_info.username} готов к работе!")
        print("📱 Пользователи могут найти бота и отправить /start")
        print("🔄 Для остановки нажмите Ctrl+C")

        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка запуска бота: {e}")
        print(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()
        print("🛑 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
