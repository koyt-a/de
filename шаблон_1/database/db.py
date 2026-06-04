import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config import DB_NAME

DB_PATH = os.path.join(BASE_DIR, DB_NAME)

def get_connection():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.executescript()

    conn.commit()
    conn.close()

def get_user_by_login(login: str):

    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM user WHERE login = ?", (login,)
    ).fetchone()
    conn.close()
    return row

def authenticate(login: str, password: str):

    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM user WHERE login = ? AND password = ?",
        (login, password)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, role, full_name, login FROM user ORDER BY full_name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM category ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_category(name: str) -> int:
    conn = get_connection()
    cur = conn.execute("INSERT OR IGNORE INTO category (name) VALUES (?)", (name,))
    conn.commit()
    row = conn.execute("SELECT id FROM category WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row["id"]

def get_all_suppliers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM supplier ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_supplier(name: str) -> int:
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO supplier (name) VALUES (?)", (name,))
    conn.commit()
    row = conn.execute("SELECT id FROM supplier WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row["id"]

def get_all_manufacturers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM manufacturer ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_manufacturer(name: str) -> int:
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO manufacturer (name) VALUES (?)", (name,))
    conn.commit()
    row = conn.execute("SELECT id FROM manufacturer WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row["id"]

def get_all_products(search: str = "", category_id: int = None,
                     sort_col: str = "name", sort_dir: str = "ASC"):

    allowed_cols = {"name": "p.name", "price": "p.price", "stock": "p.stock",
                    "article": "p.article", "discount": "p.discount"}
    allowed_dir = {"ASC", "DESC"}
    col = allowed_cols.get(sort_col, "p.name")
    direction = sort_dir if sort_dir in allowed_dir else "ASC"

    query = 
    params = [f"%{search}%", f"%{search}%"]

    if category_id:
        query += " AND p.id_category = ?"
        params.append(category_id)

    query += f" ORDER BY {col} {direction}"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product_by_article(article: str):
    conn = get_connection()
    row = conn.execute(, (article,)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_product(data: dict):
    conn = get_connection()
    conn.execute(, (
        data["article"], data["name"], data.get("unit", "шт."),
        data["price"], data.get("discount", 0), data.get("stock", 0),
        data.get("description"), data.get("photo"),
        data.get("id_category"), data.get("id_supplier"), data.get("id_manufacturer")
    ))
    conn.commit()
    conn.close()

def update_product(article: str, data: dict):
    conn = get_connection()
    conn.execute(, (
        data["name"], data.get("unit", "шт."), data["price"],
        data.get("discount", 0), data.get("stock", 0),
        data.get("description"), data.get("photo"),
        data.get("id_category"), data.get("id_supplier"), data.get("id_manufacturer"),
        article
    ))
    conn.commit()
    conn.close()

def delete_product(article: str):
    conn = get_connection()
    conn.execute("DELETE FROM product WHERE article = ?", (article,))
    conn.commit()
    conn.close()

def get_all_pickup_points():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM pickup_point ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_pickup_point(address: str) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO pickup_point (address) VALUES (?)", (address,)
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def get_all_orders():
    conn = get_connection()
    rows = conn.execute().fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_order_items(order_id: int):
    conn = get_connection()
    rows = conn.execute(, (order_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_order(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute(, (
        data.get("order_date"), data.get("delivery_date"),
        data.get("pickup_code"), data.get("status", "Новый"),
        data.get("id_user"), data.get("id_point")
    ))
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return oid

def update_order(order_id: int, data: dict):
    conn = get_connection()
    conn.execute(, (
        data.get("order_date"), data.get("delivery_date"),
        data.get("pickup_code"), data.get("status", "Новый"),
        data.get("id_user"), data.get("id_point"),
        order_id
    ))
    conn.commit()
    conn.close()

def delete_order(order_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM order_item WHERE id_order = ?", (order_id,))
    conn.execute("DELETE FROM order_t WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def insert_order_item(order_id: int, article: str, quantity: int):
    conn = get_connection()
    conn.execute(, (order_id, article, quantity))
    conn.commit()
    conn.close()

def delete_order_items(order_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM order_item WHERE id_order = ?", (order_id,))
    conn.commit()
    conn.close()

def insert_user(role: str, full_name: str, login: str, password: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO user (role, full_name, login, password) VALUES (?, ?, ?, ?)",
        (role, full_name, login, password)
    )
    conn.commit()
    conn.close()

def count_table(table: str) -> int:

    conn = get_connection()
    row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
    conn.close()
    return row["cnt"]
