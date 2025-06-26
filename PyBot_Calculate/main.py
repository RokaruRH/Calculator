import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
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

# Система монетизации - настройки
MONETIZATION_CONFIG = {
    "enabled": True,
    "show_ads_every": 3,  # Показывать рекламу каждые 3 расчета
    "donation_link": "https://example.com/donate",  # Замените на ваш сайт
    "crypto_wallets": {
        "bitcoin": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",  # Пример BTC адреса
        "ethereum": "0x742d35Cc6634C0532925a3b8D4fB00000000000",  # Пример ETH адреса
        "usdt_trc20": "TLrADxfy123456789abcdefghijklmnop",  # Пример USDT TRC20
        "ton": "EQD1234567890abcdef1234567890abcdef12345678"  # Пример TON адреса
    }
}

# Счетчик использований для рекламы
user_usage_count = {}

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

# Функция для создания клавиатуры донатов
def create_donation_keyboard():
    builder = InlineKeyboardBuilder()

    # Кнопка перехода на сайт
    builder.add(InlineKeyboardButton(
        text="💎 Поддержать проект",
        url=MONETIZATION_CONFIG["donation_link"]
    ))

    # Кнопки с криптокошельками
    builder.add(InlineKeyboardButton(
        text="₿ Bitcoin",
        callback_data="wallet_bitcoin"
    ))
    builder.add(InlineKeyboardButton(
        text="Ξ Ethereum",
        callback_data="wallet_ethereum"
    ))
    builder.add(InlineKeyboardButton(
        text="₮ USDT",
        callback_data="wallet_usdt_trc20"
    ))
    builder.add(InlineKeyboardButton(
        text="💎 TON",
        callback_data="wallet_ton"
    ))

    # Кнопка "Закрыть"
    builder.add(InlineKeyboardButton(
        text="❌ Закрыть",
        callback_data="close_donation"
    ))

    builder.adjust(1, 2, 2, 1)  # Расположение кнопок
    return builder.as_markup()

# Функция для создания рекламной клавиатуры
def create_ad_keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="💎 Поддержать разработчика",
        url=MONETIZATION_CONFIG["donation_link"]
    ))
    builder.add(InlineKeyboardButton(
        text="🎯 Продолжить расчет",
        callback_data="continue_calculation"
    ))

    builder.adjust(1)
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
    welcome_text = (
        "💣 **Калькулятор рейда Rust по сере**\n\n"
        "Привет! Я помогу тебе рассчитать необходимое количество серы для рейда.\n\n"
        "🎯 Выбери цель для разрушения:\n\n"
        "💡 *Если бот тебе помогает, можешь поддержать разработчика* /donate"
    )

    await message.answer(
        welcome_text,
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
        "/targets - Показать все доступные цели\n"
        "/donate - Поддержать разработчика\n\n"
        "**Как использовать:**\n"
        "1. Выберите цель для разрушения\n"
        "2. Укажите количество целей\n"
        "3. Получите расчет необходимых ресурсов\n\n"
        "💡 **Поддержка проекта:**\n"
        "Бот бесплатный, но разработка требует времени и ресурсов.\n"
        "Если он тебе помогает - можешь поддержать проект!\n\n"
        "Удачного рейда! 🎯"
    )
    await message.answer(help_text, parse_mode="Markdown")

# Команда /donate - монетизация
@dp.message(Command("donate"))
async def donate_handler(message: types.Message):
    donate_text = (
        "💝 **Поддержка проекта**\n\n"
        "Спасибо, что хочешь поддержать разработчика!\n\n"
        "🎯 **Этот бот помог тебе:**\n"
        "• Сэкономить время на расчетах\n"
        "• Спланировать успешные рейды\n"
        "• Избежать нехватки ресурсов\n\n"
        "💎 **Способы поддержки:**\n"
        "• Перейти на наш сайт для доната\n"
        "• Отправить криптовалюту\n"
        "• Рассказать друзьям о боте\n\n"
        "Любая поддержка поможет развивать проект дальше! 🚀"
    )

    await message.answer(
        donate_text,
        reply_markup=create_donation_keyboard(),
        parse_mode="Markdown"
    )

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

# Функция для проверки показа рекламы
def should_show_ad(user_id: int) -> bool:
    if not MONETIZATION_CONFIG["enabled"]:
        return False

    count = user_usage_count.get(user_id, 0)
    return count > 0 and count % MONETIZATION_CONFIG["show_ads_every"] == 0

# Функция для увеличения счетчика пользователя
def increment_user_count(user_id: int):
    user_usage_count[user_id] = user_usage_count.get(user_id, 0) + 1

# Функция для показа рекламы
async def show_advertisement(message, user_id: int):
    ads = [
        "🎯 **Нравится бот?**\n\nПоддержи разработчика и получи еще больше крутых функций в будущем!",
        "💎 **Этот бот бесплатный!**\n\nНо разработка требует времени. Твоя поддержка поможет добавить новые фичи!",
        "🚀 **Помог с рейдом?**\n\nПоблагодари разработчика символической суммой - это очень мотивирует!",
        "⚡ **Сэкономил серу?**\n\nПотрать немного на поддержку проекта - будет еще больше полезных ботов!"
    ]

    ad_text = random.choice(ads)

    await message.answer(
        ad_text,
        reply_markup=create_ad_keyboard(),
        parse_mode="Markdown"
    )
# Функция для обработки расчета
async def process_calculation(message, state: FSMContext, quantity: int, callback: CallbackQuery = None):
    data = await state.get_data()
    target_name = data.get('selected_target')
    user_id = message.chat.id if hasattr(message, 'chat') else callback.from_user.id

    if not target_name:
        await message.answer("❌ Ошибка: цель не выбрана. Начни заново с /start")
        return

    # Увеличиваем счетчик использований
    increment_user_count(user_id)

    # Проверяем, нужно ли показать рекламу
    if should_show_ad(user_id):
        if callback:
            await show_advertisement(callback.message, user_id)
        else:
            await show_advertisement(message, user_id)
        # Задержка перед основным результатом
        await asyncio.sleep(2)

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

    # Добавляем призыв к действию в некоторых случаях
    if user_usage_count.get(user_id, 0) % 5 == 0:
        result_text += "\n\n💡 *Бот помогает? Поддержи разработчика* /donate"

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

# Обработчики для монетизации

# Обработчик кнопок криптокошельков
@dp.callback_query(F.data.startswith("wallet_"))
async def wallet_handler(callback: CallbackQuery):
    wallet_type = callback.data.replace("wallet_", "")
    wallet_address = MONETIZATION_CONFIG["crypto_wallets"].get(wallet_type)

    if not wallet_address:
        await callback.answer("❌ Адрес не найден")
        return

    wallet_names = {
        "bitcoin": "Bitcoin (BTC)",
        "ethereum": "Ethereum (ETH)",
        "usdt_trc20": "USDT TRC20",
        "ton": "TON"
    }

    wallet_text = (
        f"💰 **{wallet_names.get(wallet_type, wallet_type.upper())}**\n\n"
        f"**Адрес для перевода:**\n"
        f"`{wallet_address}`\n\n"
        f"**Как отправить:**\n"
        f"1. Скопируйте адрес выше\n"
        f"2. Откройте свой кошелек\n"
        f"3. Отправьте любую сумму\n"
        f"4. Напишите @username_bot что отправили\n\n"
        f"Спасибо за поддержку! 🙏"
    )

    # Кнопка для копирования адреса
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать адрес", callback_data=f"copy_{wallet_type}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="show_donation_menu")]
    ])

    await callback.message.edit_text(wallet_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Обработчик копирования адреса
@dp.callback_query(F.data.startswith("copy_"))
async def copy_wallet_handler(callback: CallbackQuery):
    wallet_type = callback.data.replace("copy_", "")
    wallet_address = MONETIZATION_CONFIG["crypto_wallets"].get(wallet_type)

    if wallet_address:
        await callback.answer(f"Адрес скопирован: {wallet_address}", show_alert=True)
    else:
        await callback.answer("❌ Ошибка копирования")

# Показать меню доната
@dp.callback_query(F.data == "show_donation_menu")
async def show_donation_menu(callback: CallbackQuery):
    donate_text = (
        "💝 **Поддержка проекта**\n\n"
        "Спасибо, что хочешь поддержать разработчика!\n\n"
        "💎 **Способы поддержки:**\n"
        "• Перейти на наш сайт для доната\n"
        "• Отправить криптовалюту\n"
        "• Рассказать друзьям о боте\n\n"
        "Любая поддержка поможет развивать проект дальше! 🚀"
    )

    await callback.message.edit_text(
        donate_text,
        reply_markup=create_donation_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Закрыть меню доната
@dp.callback_query(F.data == "close_donation")
async def close_donation_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "💣 **Калькулятор рейда Rust**\n\n"
        "Выбери цель для разрушения:",
        reply_markup=create_targets_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Продолжить после рекламы
@dp.callback_query(F.data == "continue_calculation")
async def continue_calculation_handler(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Продолжаем! 🎯")
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
