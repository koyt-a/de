"""
Интерактивный скрипт для создания и заполнения базы данных.
"""

import sys
import os
import warnings
import io

# Принудительно UTF-8 для вывода в консоль Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Добавляем корень проекта в путь поиска модулей
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

import pandas as pd
from database.db import (
    init_db, get_connection,
    insert_category, insert_supplier, insert_manufacturer,
    insert_product, insert_user, insert_pickup_point,
    insert_order, insert_order_item, count_table
)
from config import DB_NAME

# ╔══════════════════════════════════╗
# ║  НАСТРОЙКА ШАБЛОНА — МЕНЯЙ ЗДЕСЬ ║
# ╚══════════════════════════════════╝
# Названия колонок в Excel-файлах — если в твоём задании колонки называются
# иначе, поменяй значения здесь. Ключи не трогай.

# === КОЛОНКИ ДЛЯ ТАБЛИЦЫ ТОВАРОВ ===
COLUMNS_PRODUCT = {
    "article":      "Артикул",
    "name":         "Наименование товара",
    "unit":         "Единица измерения",
    "price":        "Цена",
    "supplier":     "Поставщик",
    "manufacturer": "Производитель",
    "category":     "Категория товара",
    "discount":     "Действующая скидка",
    "stock":        "Кол-во на складе",
    "description":  "Описание товара",
    "photo":        "Фото",
}

# === КОЛОНКИ ДЛЯ ТАБЛИЦЫ ПОЛЬЗОВАТЕЛЕЙ ===
COLUMNS_USER = {
    "role":         "Роль сотрудника",
    "full_name":    "ФИО",
    "login":        "Логин",
    "password":     "Пароль",
}

# === КОЛОНКИ ДЛЯ ТАБЛИЦЫ ЗАКАЗОВ ===
COLUMNS_ORDER = {
    "order_num":     "Номер заказа",
    "article":       "Артикул заказа",
    "order_date":    "Дата заказа",
    "delivery_date": "Дата доставки",
    "point":         "Адрес пункта выдачи",
    "client":        "ФИО авторизированного клиента",
    "pickup_code":   "Код для получения",
    "status":        "Статус заказа",
}
# (Пункты выдачи определяются автоматически по первому столбцу без заголовка)

DATA_DIR = os.path.join(BASE_DIR, "data")


def _read_excel(path: str) -> pd.DataFrame | None:
    try:
        return pd.read_excel(path, dtype=str)
    except Exception as e:
        print(f"  ⚠  Ошибка чтения {path}: {e}")
        return None

def import_products(path: str):
    df = _read_excel(path)
    if df is None:
        return
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():
        cat_id = insert_category(str(row.get(COLUMNS_PRODUCT["category"], "")).strip()) \
            if pd.notna(row.get(COLUMNS_PRODUCT["category"])) else None
        sup_id = insert_supplier(str(row.get(COLUMNS_PRODUCT["supplier"], "")).strip()) \
            if pd.notna(row.get(COLUMNS_PRODUCT["supplier"])) else None
        man_id = insert_manufacturer(str(row.get(COLUMNS_PRODUCT["manufacturer"], "")).strip()) \
            if pd.notna(row.get(COLUMNS_PRODUCT["manufacturer"])) else None

        try:
            price = float(str(row.get(COLUMNS_PRODUCT["price"], "0")).replace(",", ".").strip())
        except (ValueError, TypeError):
            price = 0.0

        try:
            discount = int(float(str(row.get(COLUMNS_PRODUCT["discount"], "0")).strip()))
        except (ValueError, TypeError):
            discount = 0

        try:
            stock = int(float(str(row.get(COLUMNS_PRODUCT["stock"], "0")).strip()))
        except (ValueError, TypeError):
            stock = 0

        article = str(row.get(COLUMNS_PRODUCT["article"], "")).strip()
        if not article or article == "nan":
            continue

        insert_product({
            "article":      article,
            "name":         str(row.get(COLUMNS_PRODUCT["name"], "")).strip(),
            "unit":         str(row.get(COLUMNS_PRODUCT["unit"], "шт.")).strip() or "шт.",
            "price":        price,
            "discount":     discount,
            "stock":        stock,
            "description":  str(row.get(COLUMNS_PRODUCT["description"], "")).strip() or None,
            "photo":        str(row.get(COLUMNS_PRODUCT["photo"], "")).strip() or None,
            "id_category":  cat_id,
            "id_supplier":  sup_id,
            "id_manufacturer": man_id,
        })

def import_users(path: str):
    df = _read_excel(path)
    if df is None:
        return
    df.columns = df.columns.str.strip()

    role_map = {
        "Администратор": "admin",
        "Менеджер": "manager",
        "Авторизированный клиент": "client",
        "Авторизованный клиент": "client",
    }

    for _, row in df.iterrows():
        raw_role = str(row.get(COLUMNS_USER["role"], "")).strip()
        role = role_map.get(raw_role, "client")
        full_name = str(row.get(COLUMNS_USER["full_name"], "")).strip()
        login = str(row.get(COLUMNS_USER["login"], "")).strip()
        password = str(row.get(COLUMNS_USER["password"], "")).strip()
        if login and login != "nan":
            insert_user(role, full_name, login, password)

def import_pickup_points(path: str):
    try:
        df = pd.read_excel(path, header=None, dtype=str)
    except Exception as e:
        print(f"  ⚠  Ошибка чтения пунктов выдачи: {e}")
        return

    for _, row in df.iterrows():
        address = str(row.iloc[0]).strip()
        if address and address.lower() != "nan":
            insert_pickup_point(address)

def import_orders(path: str):
    df = _read_excel(path)
    if df is None:
        return
    df.columns = df.columns.str.strip()

    conn = get_connection()
    user_cache: dict[str, int] = {}
    rows_users = conn.execute("SELECT id, full_name FROM user").fetchall()
    for u in rows_users:
        user_cache[u["full_name"].strip()] = u["id"]
    conn.close()

    imported_orders: dict[str, int] = {}

    def _parse_date(val) -> str | None:
        if pd.isna(val) or str(val).strip() in ("", "nan", "NaT"):
            return None
        s = str(val).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%Y-%m-%d"):
            try:
                from datetime import datetime
                return datetime.strptime(s.split(" ")[0] if " " in s else s, fmt.split(" ")[0]).strftime("%d.%m.%Y")
            except ValueError:
                continue
        return s

    for idx, row in df.iterrows():
        order_num = str(row.get(COLUMNS_ORDER["order_num"], "")).strip()
        article_raw = str(row.get(COLUMNS_ORDER["article"], "")).strip()
        order_date = _parse_date(row.get(COLUMNS_ORDER["order_date"]))
        delivery_date = _parse_date(row.get(COLUMNS_ORDER["delivery_date"]))
        point_raw = str(row.get(COLUMNS_ORDER["point"], "")).strip()
        client_name = str(row.get(COLUMNS_ORDER["client"], "")).strip()
        try:
            pickup_code = int(float(str(row.get(COLUMNS_ORDER["pickup_code"], "0")).strip()))
        except (ValueError, TypeError):
            pickup_code = None
        status = str(row.get(COLUMNS_ORDER["status"], "Новый")).strip() or "Новый"

        try:
            point_id = int(float(point_raw)) if point_raw and point_raw != "nan" else None
        except (ValueError, TypeError):
            point_id = None

        user_id = user_cache.get(client_name)

        if order_num not in imported_orders:
            oid = insert_order({
                "order_date":    order_date,
                "delivery_date": delivery_date,
                "pickup_code":   pickup_code,
                "status":        status,
                "id_user":       user_id,
                "id_point":      point_id,
            })
            imported_orders[order_num] = oid
        else:
            oid = imported_orders[order_num]

        if article_raw and article_raw.lower() != "nan":
            parts = [p.strip() for p in article_raw.split(",")]
            i = 0
            while i < len(parts):
                art = parts[i]
                qty = 1
                if i + 1 < len(parts):
                    try:
                        qty = int(parts[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
                if art:
                    try:
                        insert_order_item(oid, art, qty)
                    except Exception as e:
                        print(f"    ⚠  Позиция заказа {order_num}: {e}")

def main():
    print("=" * 50)
    print(f"  Сборка базы данных: {DB_NAME}")
    print("=" * 50)

    # Ищем файлы в data/
    excel_files = []
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith('.xlsx'):
                excel_files.append(f)

    if not excel_files:
        print(f"В папке data/ не найдено ни одного .xlsx файла.")
        return

    print(f"Найдены файлы в папке data/:")
    for i, f in enumerate(excel_files):
        print(f"{i + 1}. {f}")
    print()

    def ask_file(prompt):
        while True:
            choice = input(prompt).strip()
            if not choice:
                return None
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(excel_files):
                    return os.path.join(DATA_DIR, excel_files[idx])
            except ValueError:
                pass
            print("Неверный номер. Попробуйте еще раз или нажмите Enter для пропуска.")

    products_file = ask_file("Введите номер файла с ТОВАРАМИ: ")
    users_file = ask_file("Введите номер файла с ПОЛЬЗОВАТЕЛЯМИ: ")
    points_file = ask_file("Введите номер файла с ПУНКТАМИ ВЫДАЧИ: ")
    orders_file = ask_file("Введите номер файла с ЗАКАЗАМИ: ")

    # Удаляем старую БД если она есть
    db_path = os.path.join(BASE_DIR, DB_NAME)
    if os.path.exists(db_path):
        os.remove(db_path)

    print("\n[1/5] Инициализация базы данных...")
    init_db()
    print("  [OK] Таблицы созданы")

    if products_file:
        print(f"\n[2/5] Импорт товаров ({os.path.basename(products_file)})...")
        import_products(products_file)
    else:
        print("\n[2/5] Пропуск импорта товаров")

    if users_file:
        print(f"\n[3/5] Импорт пользователей ({os.path.basename(users_file)})...")
        import_users(users_file)
    else:
        print("\n[3/5] Пропуск импорта пользователей")

    if points_file:
        print(f"\n[4/5] Импорт пунктов выдачи ({os.path.basename(points_file)})...")
        import_pickup_points(points_file)
    else:
        print("\n[4/5] Пропуск импорта пунктов выдачи")

    if orders_file:
        print(f"\n[5/5] Импорт заказов ({os.path.basename(orders_file)})...")
        import_orders(orders_file)
    else:
        print("\n[5/5] Пропуск импорта заказов")

    print("\n" + "=" * 50)
    print("  Результат импорта:")
    print("=" * 50)
    print(f"✓ База данных создана: {DB_NAME}")
    print(f"✓ Категории:       {count_table('category')}")
    print(f"✓ Поставщики:      {count_table('supplier')}")
    print(f"✓ Производители:   {count_table('manufacturer')}")
    print(f"✓ Товары:          {count_table('product')}")
    print(f"✓ Пользователи:    {count_table('user')}")
    print(f"✓ Пункты выдачи:   {count_table('pickup_point')}")
    print(f"✓ Заказы:          {count_table('order_t')}")
    print(f"✓ Позиции заказов: {count_table('order_item')}")
    print("=" * 50)
    print("  Импорт завершён успешно!")
    print("=" * 50)

if __name__ == "__main__":
    main()
