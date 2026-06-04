import os
import sys
from PIL import Image

# Добавляем корень проекта в путь поиска модулей
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def main():
    print("=" * 50)
    print("  Установка иконки приложения")
    print("=" * 50)

    # Ищем все .ico и .png файлы в папке проекта
    icon_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        # Исключаем папку .venv и .git
        if '.venv' in dirs:
            dirs.remove('.venv')
        if '.git' in dirs:
            dirs.remove('.git')
        
        for file in files:
            if file.lower().endswith('.ico') or file.lower().endswith('.png'):
                # Пропускаем уже установленную иконку
                if "assets" in root and "icon.ico" in file:
                    continue
                icon_files.append(os.path.join(root, file))

    if not icon_files:
        print("\nСкопируйте файл .ico или .png в папку проекта и запустите скрипт снова")
        return

    print("\nНайдены файлы:")
    for i, file in enumerate(icon_files):
        # Показываем путь относительно корня проекта для краткости
        rel_path = os.path.relpath(file, BASE_DIR)
        print(f"{i + 1}. {rel_path}")

    try:
        choice = input("\nВведите номер файла: ").strip()
        idx = int(choice) - 1
        if idx < 0 or idx >= len(icon_files):
            print("Неверный номер.")
            return
        
        chosen_file = icon_files[idx]
        
        # Конвертируем и сохраняем в assets/icon.ico
        assets_dir = os.path.join(BASE_DIR, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        dest_file = os.path.join(assets_dir, "icon.ico")
        
        try:
            img = Image.open(chosen_file)
            img.save(dest_file, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"\n✓ Иконка установлена: assets/icon.ico")
        except Exception as e:
            print(f"\n⚠ Ошибка при конвертации изображения: {e}")
            return
        
    except ValueError:
        print("Неверный ввод. Введите число.")
    except Exception as e:
        print(f"Ошибка при установке иконки: {e}")

if __name__ == "__main__":
    main()
