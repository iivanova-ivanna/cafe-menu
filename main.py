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
    import flet as ft

    def mainGUI(page: ft.Page):
        page.title = "Меню кофейни"
        page.window.width = 700
        page.window.height = 500
        page.theme_mode = ft.ThemeMode.DARK

        def updateTable():
            nonlocal dishes
            for dish in dishes:
                table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(dish["name"])),
                            ft.DataCell(ft.Text(dish["category"])),
                            ft.DataCell(ft.Text(dish["price"])),
                            ft.DataCell(ft.Text(dish["author"])),
                        ]
                    )
                )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Блюдо", size=18, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Категория", size=18, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Цена, BYN", size=18, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Автор", size=18, weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        scrollTable = ft.ListView(
            controls=[table],
            expand=True,
        )

        field = ft.Container(
            expand=True,
            content=scrollTable,
            padding=5,
            bgcolor="#111315",
            border_radius=8,
            border=ft.Border(
                top=ft.BorderSide(1.5, "black"),
                bottom=ft.BorderSide(1.5, "black"),
                left=ft.BorderSide(1.5, "black"),
                right=ft.BorderSide(1.5, "black")
            )
        )

        updateTable()


        page.add(field,
                 ft.Text(summary(dishes), size=20),
                 ft.Container(height=10),
                 )

    ft.run(mainGUI)


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
