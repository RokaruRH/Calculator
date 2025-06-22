import requests
from bs4 import BeautifulSoup
import re
#TODO нужно сделать так чтобы программа считывакала данные с Hashmap и отправил запросы по ссылке и отправила данные чтобы калькулировать
def search_web_data(title, keyword):
    url = f"https://rust.fandom.com/wiki/Items {title.replace(' ','_')}"
    print(f" Opening web: {url}")
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")


    matches = []
    for tag in soup.find_all(['p', 'li', 'td']):
        text = tag.get_text(strip=True).lower()
        if keyword.lower() in text:
            matches.append(tag.get_text(strip=True))

    numbers = []
    for m in matches:
        match = re.search(r'(\d+[\s.,]?\d*)', m)
        if match:
            number = match.group(1)
            number = number.replace(" ", "").replace(",", ".")
            try:
                numbers.append(float(number))
            except:
                continue

    if numbers:
        return numbers[0]
    else:
        return None

# 🧑 Ввод от пользователя
title = "Items"
keyword = input("Что искать?: ")
value = search_web_data(title, keyword)

if value:
    print(f"✅ Найдено значение: {value}")
    action = input("Хочешь умножить/поделить/ничего? (пример: * 2): ")
    if action:
        try:
            operator, operand = action.strip().split()
            operand = float(operand)
            if operator == "*":
                result = value * operand
            elif operator == "/":
                result = value / operand
            else:
                result = value
            print(f"📊 Результат: {result}")
        except:
            print("⚠️ Неверный ввод.")
else:
    print("❌ Не удалось найти данные.")
