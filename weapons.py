
# Калькулятор рейда Rust по сере

# --- Встроенная рейд-таблица (по сере и количеству взрывов) ---
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

# --- Основная программа ---
print("💣 Калькулятор рейда Rust по сере")
print("=" * 40)

# Показываем доступные цели
print("Доступные цели:")
for i, target in enumerate(raid_sulfur_table.keys(), 1):
    print(f"{i}. {target}")

print("\n" + "=" * 40)

while True:
    target = input("Что ты хочешь разрушить? (введи название или номер): ").strip()

    # Проверяем, введен ли номер
    if target.isdigit():
        target_num = int(target)
        if 1 <= target_num <= len(raid_sulfur_table):
            target = list(raid_sulfur_table.keys())[target_num - 1]
        else:
            print("❌ Неверный номер цели.")
            continue

    # Ищем цель (с учетом регистра)
    found_target = None
    for key in raid_sulfur_table.keys():
        if key.lower() == target.lower():
            found_target = key
            break

    if found_target:
        info = raid_sulfur_table[found_target]
        print(f"\n🔎 Информация по цели: {found_target}")
        print(f" - Количество зарядов: {info['Количество']} ({info['Тип']})")
        print(f" - Требуемая сера: {info['Сера']} единиц")

        # Запрашиваем количество целей
        while True:
            multiplier_input = input("\nСколько таких целей ты хочешь разрушить? (число, Enter = 1): ").strip()

            if multiplier_input == "":
                multiplier = 1
                break
            else:
                try:
                    multiplier = int(multiplier_input)
                    if multiplier <= 0:
                        print("⚠️ Количество должно быть больше 0.")
                        continue
                    break
                except ValueError:
                    print("⚠️ Введено неверное число. Попробуй еще раз.")
                    continue

        # Вычисляем итоговые значения
        total_charges = info['Количество'] * multiplier
        total_sulfur = info['Сера'] * multiplier

        print(f"\n🧮 Итого для {multiplier}x {found_target}:")
        print(f" - Зарядов ({info['Тип']}): {total_charges}")
        print(f" - Серы: {total_sulfur} единиц")

        # Дополнительная информация о ресурсах
        print(f"\n Дополнительная информация:")
        if "С4" in info['Тип']:
            print(f" - Нужно металлических фрагментов: {total_charges * 20}")
            print(f" - Нужно низкосортного топлива: {total_charges * 30}")
        elif "Сачель" in info['Тип']:
            print(f" - Нужно ткани: {total_charges * 10}")
            print(f" - Нужно бобовых банок: {total_charges * 4}")

        break
    else:
        print("❌ Такой цели нет в таблице. Проверь написание или выбери из списка выше.")
        print("Доступные варианты:", ", ".join(raid_sulfur_table.keys()))

print("\n🎯 Удачного рейда!")
