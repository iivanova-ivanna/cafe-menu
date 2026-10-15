"""Общее меню кофейни.

Каждый ученик добавляет своё блюдо отдельным файлом в папку menu/.
Программа сама находит все файлы menu/*.json и собирает из них меню.

Запуск:
    python main.py          окно с таблицей меню
    python main.py --text   то же самое, но текстом в консоли (и проверка файлов)
"""
import json
import sys
from pathlib import Path

MENU_DIR = Path(__file__).parent / "menu"
MAX_PRICE = 100


def read_dish(path):
    """Читает один файл блюда. Возвращает (блюдо, None) или (None, текст ошибки)."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, (f"{path.name}: ошибка в JSON около строки {e.lineno}. "
                      "Частые причины: пропущена запятая в конце строки, "
                      "запятая вместо точки в цене (7,5 вместо 7.5), "
                      "нет кавычек у текста или не закрыта скобка.")
    except OSError as e:
        return None, f"{path.name}: не удалось открыть файл ({e})"

    if not isinstance(data, dict):
        return None, f"{path.name}: внутри файла должны быть фигурные скобки {{ ... }}"

    for field in ("name", "author"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f'{path.name}: поле "{field}" должно быть непустым текстом в кавычках'

    price = data.get("price")
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return None, (f'{path.name}: поле "price" должно быть числом без кавычек, '
                      'с точкой, а не запятой (например 7.5)')
    if not 0 < price <= MAX_PRICE:
        return None, f'{path.name}: цена должна быть больше 0 и не больше {MAX_PRICE}'

    category = data.get("category", "Другое")
    if not isinstance(category, str) or not category.strip():
        category = "Другое"

    dish = {
        "name": data["name"].strip(),
        "price": float(price),
        "author": data["author"].strip(),
        "category": category.strip(),
        "file": path.name,
    }
    return dish, None


def load_menu(menu_dir=MENU_DIR):
    """Читает все menu/*.json (кроме файлов, чьё имя начинается с _)."""
    dishes, errors = [], []
    for path in sorted(Path(menu_dir).glob("*.json")):
        if path.name.startswith("_"):
            continue
        dish, error = read_dish(path)
        if error:
            errors.append(error)
        else:
            dishes.append(dish)
    return dishes, errors


def summary(dishes):
    if not dishes:
        return "В меню пока нет блюд"
    average = sum(d["price"] for d in dishes) / len(dishes)
    top = max(dishes, key=lambda d: d["price"])
    return (f"Блюд: {len(dishes)}   |   Средняя цена: {average:.2f} BYN   |   "
            f"Самое дорогое: {top['name']} ({top['price']:.2f} BYN)")


def print_menu(dishes, errors):
    print("=== МЕНЮ КОФЕЙНИ ===")
    for d in sorted(dishes, key=lambda d: (d["category"], d["name"])):
        print(f"[{d['category']}] {d['name']} — {d['price']:.2f} BYN (автор: {d['author']})")
    print()
    print(summary(dishes))
    if errors:
        print()
        print(f"Файлы с ошибками ({len(errors)}), эти блюда в меню не попали:")
        for e in errors:
            print("  !", e)


def show_window(dishes, errors):
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Меню кофейни")

    columns = ("name", "category", "price", "author")
    titles = {"name": "Блюдо", "category": "Категория", "price": "Цена, BYN", "author": "Автор"}
    table = ttk.Treeview(root, columns=columns, show="headings", height=14)
    for col in columns:
        table.heading(col, text=titles[col], command=lambda c=col: sort_by(c))
        table.column(col, width=130 if col != "name" else 200)
    table.pack(padx=10, pady=10, fill="both", expand=True)

    state = {"column": "category", "reverse": False}

    def fill():
        table.delete(*table.get_children())
        key = state["column"]
        rows = sorted(dishes, key=lambda d: (d[key], d["name"]), reverse=state["reverse"])
        for d in rows:
            table.insert("", "end", values=(d["name"], d["category"], f"{d['price']:.2f}", d["author"]))

    def sort_by(column):
        state["reverse"] = (state["column"] == column) and not state["reverse"]
        state["column"] = column
        fill()

    fill()
    tk.Label(root, text=summary(dishes), font=("Arial", 11)).pack(pady=5)
    if errors:
        tk.Label(root, text="Файлы с ошибками:\n" + "\n".join(errors),
                 fg="red", justify="left", wraplength=620).pack(padx=10, pady=5)
    tk.Label(root, text="Нажмите на заголовок столбца, чтобы отсортировать",
             fg="gray").pack(pady=(0, 10))
    root.mainloop()


def main():
    dishes, errors = load_menu()
    if "--text" in sys.argv:
        print_menu(dishes, errors)
        return 1 if errors else 0
    try:
        show_window(dishes, errors)
    except ImportError:
        print("Окно недоступно (нет tkinter), показываю меню текстом.\n")
        print_menu(dishes, errors)
    return 0


if __name__ == "__main__":
    sys.exit(main())
