import sqlite3
import os
import sys

# =================================================================
# НАСТРОЙКИ ФАЙЛОВ — МЕНЯЙТЕ ЗДЕСЬ
# =================================================================
# Укажите здесь точное название вашего .sql файла (с расширением)
SQL_FILE = "script.sql"  

# Название итогового файла базы данных (по умолчанию DataBase.db)
DB_FILE = "DataBase.db"
# =================================================================

def main():
    print("="*50)
    print("  КОНВЕРТЕР .SQL В .DB (SQLite)")
    print("="*50)

    # Ищем файл в текущей папке и в корне проекта
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    sql_path = SQL_FILE
    if not os.path.exists(sql_path):
        sql_path = os.path.join(base_dir, SQL_FILE)
        if not os.path.exists(sql_path):
            print(f"❌ Ошибка: Файл '{SQL_FILE}' не найден!")
            print("Убедитесь, что файл лежит в корне папки с проектом или рядом со скриптом.")
            return

    db_path = os.path.join(base_dir, DB_FILE)

    print(f"Читаем SQL-дамп из файла: {sql_path}")
    
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return

    # Удаляем старую БД, если она уже существует
    if os.path.exists(db_path):
        print(f"Удаление старой базы данных {DB_FILE}...")
        os.remove(db_path)

    print(f"Создание новой базы данных {DB_FILE}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Выполнение SQL-скрипта (создание таблиц и импорт данных)...")
        cursor.executescript(sql_script)
        
        conn.commit()
        conn.close()
        print(f"✅ Успешно! База данных сохранена как: {db_path}")
    except sqlite3.OperationalError as e:
        print(f"\n❌ Ошибка SQL-синтаксиса в файле:")
        print(f"{e}")
        print("Возможно, SQL-дамп содержит команды (например, из MySQL или SQL Server), которые SQLite не понимает.")
        print("Убедитесь, что дамп совместим со стандартом SQLite.")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()
