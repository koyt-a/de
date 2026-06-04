

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import (
    get_all_products, get_all_categories, get_all_suppliers,
    get_all_manufacturers, get_product_by_article,
    insert_product, update_product, delete_product,
)
from config import (
    APP_NAME, APP_ICON, ITEM_NAME_SINGULAR, ITEM_NAME_PLURAL, PRODUCT_COLUMNS,
    FONT_FAMILY, BG_PRIMARY, BG_SECONDARY, COLOR_ACCENT,
    TEXT_PRIMARY, TEXT_SECONDARY, DISCOUNT_THRESHOLD, COLOR_DISCOUNT_HIGH
)

IMAGES_DIR = "images/"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_PATH = os.path.join(BASE_DIR, IMAGES_DIR)

BG_DARK   = BG_PRIMARY
BG_MID    = BG_PRIMARY
BG_CARD   = BG_PRIMARY
BG_ROW    = BG_PRIMARY
BG_ROW_ALT = "#F0F0F0"
ACCENT    = COLOR_ACCENT
ACCENT2   = COLOR_ACCENT
TEXT_MAIN = TEXT_PRIMARY
TEXT_SUB  = TEXT_SECONDARY
BTN_FG    = TEXT_PRIMARY
HEADER_BG = BG_SECONDARY
SEL_BG    = COLOR_ACCENT

class ProductsWindow(tk.Frame):

    def __init__(self, master, role: str, **kwargs):
        super().__init__(master, bg=BG_DARK, **kwargs)
        self.role = role

        self.COLUMNS = [c[0] for c in PRODUCT_COLUMNS]
        self.COL_HEADERS = {c[0]: c[1] for c in PRODUCT_COLUMNS}
        self.COL_WIDTHS = {c[0]: c[2] for c in PRODUCT_COLUMNS}

        self._sort_col = "name"
        self._sort_dir = "ASC"
        self._search_var = tk.StringVar()
        self._cat_var = tk.StringVar(value="Все категории")
        self._categories: list[dict] = []
        self._build_ui()
        self.load_products()

    def _build_ui(self):
        if self.role in ("manager", "admin"):
            self._build_toolbar()

        if self.role == "admin":
            self._build_admin_bar()

        self._build_table()

        self._build_statusbar()

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=BG_MID, pady=8)
        toolbar.pack(fill="x", padx=0)

        tk.Label(toolbar, text="🔍", bg=BG_MID, fg=TEXT_SUB,
                 font=(FONT_FAMILY, 12)).pack(side="left", padx=(12, 4))
        search_frame = tk.Frame(toolbar, bg=ACCENT2, pady=1, padx=1)
        search_frame.pack(side="left")
        self._entry_search = tk.Entry(
            search_frame, textvariable=self._search_var,
            font=(FONT_FAMILY, 10), bg=BG_ROW, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN, relief="flat", width=22
        )
        self._entry_search.pack(ipady=5, padx=4, pady=2)
        self._search_var.trace_add("write", lambda *_: self.load_products())

        tk.Label(toolbar, text="Категория:", bg=BG_MID, fg=TEXT_SUB,
                 font=(FONT_FAMILY, 9)).pack(side="left", padx=(16, 4))

        self._cat_combo = ttk.Combobox(
            toolbar, textvariable=self._cat_var,
            state="readonly", width=18, font=(FONT_FAMILY, 9)
        )
        self._cat_combo.pack(side="left")
        self._cat_combo.bind("<<ComboboxSelected>>", lambda _: self.load_products())

        tk.Label(toolbar, text="Сортировка:", bg=BG_MID, fg=TEXT_SUB,
                 font=(FONT_FAMILY, 9)).pack(side="left", padx=(16, 4))

        self._sort_var = tk.StringVar(value="По названию ↑")
        sort_options = [
            "По названию ↑", "По названию ↓",
            "По цене ↑", "По цене ↓",
            "По остатку ↑", "По остатку ↓",
        ]
        sort_combo = ttk.Combobox(
            toolbar, textvariable=self._sort_var,
            values=sort_options, state="readonly", width=16,
            font=(FONT_FAMILY, 9)
        )
        sort_combo.pack(side="left")
        sort_combo.bind("<<ComboboxSelected>>", self._on_sort_changed)

        btn_reset = tk.Button(
            toolbar, text="✕ Сбросить фильтры",
            bg=BG_ROW, fg=TEXT_SUB,
            font=(FONT_FAMILY, 9), relief="flat",
            cursor="hand2", padx=10, pady=5,
            command=self._reset_filters
        )
        btn_reset.pack(side="left", padx=(16, 0))
        btn_reset.bind("<Enter>", lambda _: btn_reset.config(fg=TEXT_MAIN))
        btn_reset.bind("<Leave>", lambda _: btn_reset.config(fg=TEXT_SUB))

    def _build_admin_bar(self):
        bar = tk.Frame(self, bg=BG_DARK, pady=6)
        bar.pack(fill="x", padx=12)

        for text, cmd, color in [
            ("＋ Добавить", self._on_add, "#27ae60"),
            ("✎  Редактировать", self._on_edit, "#2980b9"),
            ("✕  Удалить", self._on_delete, ACCENT),
        ]:
            b = tk.Button(
                bar, text=text, bg=color, fg=BTN_FG,
                font=(FONT_FAMILY, 9, "bold"), relief="flat",
                cursor="hand2", padx=12, pady=5, command=cmd
            )
            b.pack(side="left", padx=(0, 8))

    def _build_table(self):
        tbl_frame = tk.Frame(self, bg=BG_DARK)
        tbl_frame.pack(fill="both", expand=True, padx=12, pady=(6, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Products.Treeview",
                         font=(FONT_FAMILY, 10),
                         rowheight=64,
                         background=BG_CARD,
                         fieldbackground=BG_CARD,
                         foreground=TEXT_PRIMARY)
        style.configure("Products.Treeview.Heading",
                         background=HEADER_BG,
                         foreground=TEXT_MAIN,
                         font=(FONT_FAMILY, 9, "bold"),
                         relief="flat")
        style.map("Products.Treeview",
                  background=[("selected", SEL_BG)],
                  foreground=[("selected", "#ffffff")])
        style.map("Products.Treeview.Heading",
                  background=[("active", BG_CARD)])

        self.tree = ttk.Treeview(
            tbl_frame,
            columns=self.COLUMNS,
            show="tree headings",
            style="Products.Treeview",
            selectmode="browse",
        )

        self.tree.heading("#0", text="Фото")
        self.tree.column("#0", width=80, anchor="center")

        for col in self.COLUMNS:
            self.tree.heading(
                col, text=self.COL_HEADERS[col],
                command=lambda c=col: self._header_sort(c)
            )
            self.tree.column(col, width=self.COL_WIDTHS[col], anchor="w", minwidth=50)

        vsb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbl_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tbl_frame.rowconfigure(0, weight=1)
        tbl_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.tag_configure("even", background=BG_ROW_ALT)
        self.tree.tag_configure("odd",  background=BG_ROW)
        self.tree.tag_configure("discount_high", background=COLOR_DISCOUNT_HIGH, foreground="#FFFFFF")

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Показано товаров: 0")
        status = tk.Label(
            self, textvariable=self._status_var,
            bg=BG_MID, fg=TEXT_SUB,
            font=(FONT_FAMILY, 9), anchor="w", padx=14, pady=5
        )
        status.pack(fill="x", side="bottom")

    def load_products(self):
        search = ""
        cat_id = None

        if self.role in ("manager", "admin"):
            search = self._search_var.get().strip()
            cat_name = self._cat_var.get()
            if cat_name != "Все категории":
                for c in self._categories:
                    if c["name"] == cat_name:
                        cat_id = c["id"]
                        break

        self._refresh_categories()
        products = get_all_products(
            search=search, category_id=cat_id,
            sort_col=self._sort_col, sort_dir=self._sort_dir
        )

        for item in self.tree.get_children():
            self.tree.delete(item)

        self._image_cache = {}

        for i, p in enumerate(products):
            values = []
            for col in self.COLUMNS:
                val = p.get(col, "")
                if col == "price":
                    val = f"{val:.2f} ₽"
                elif col == "discount" and val:
                    val = f"{val}%"
                elif col == "discount":
                    val = "—"
                elif not val:
                    val = "—"
                values.append(val)

            tag = "even" if i % 2 == 0 else "odd"
            discount_val = p.get("discount")
            if discount_val and discount_val > DISCOUNT_THRESHOLD:
                tag = "discount_high"

            img_ref = self._get_thumbnail(p.get("photo"))
            self._image_cache[p["article"]] = img_ref

            self.tree.insert("", "end", iid=p["article"], image=img_ref, values=values, tags=(tag,))

        self._status_var.set(f"Показано {ITEM_NAME_PLURAL.lower()}: {len(products)}")

    def _refresh_categories(self):

        if self.role not in ("manager", "admin"):
            return
        self._categories = get_all_categories()
        values = ["Все категории"] + [c["name"] for c in self._categories]
        self._cat_combo["values"] = values
        if self._cat_var.get() not in values:
            self._cat_var.set("Все категории")

    _SORT_MAP = {
        "По названию ↑": ("name", "ASC"),
        "По названию ↓": ("name", "DESC"),
        "По цене ↑": ("price", "ASC"),
        "По цене ↓": ("price", "DESC"),
        "По остатку ↑": ("stock", "ASC"),
        "По остатку ↓": ("stock", "DESC"),
    }

    def _on_sort_changed(self, _event=None):
        col, direction = self._SORT_MAP.get(
            self._sort_var.get(), ("name", "ASC")
        )
        self._sort_col = col
        self._sort_dir = direction
        self.load_products()

    def _header_sort(self, col: str):

        if self.role not in ("manager", "admin"):
            return
        if self._sort_col == col:
            self._sort_dir = "DESC" if self._sort_dir == "ASC" else "ASC"
        else:
            self._sort_col = col
            self._sort_dir = "ASC"
        self.load_products()

    def _reset_filters(self):
        self._search_var.set("")
        self._cat_var.set("Все категории")
        self._sort_var.set("По названию ↑")
        self._sort_col = "name"
        self._sort_dir = "ASC"
        self.load_products()

    def _get_selected_article(self) -> str | None:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _on_double_click(self, _event=None):
        article = self._get_selected_article()
        if article:
            self._show_detail(article)

    def _on_add(self):
        ProductDialog(self.winfo_toplevel(), mode="add",
                      on_save=self._after_save)

    def _on_edit(self):
        article = self._get_selected_article()
        if not article:
            messagebox.showwarning("Внимание", "Выберите товар для редактирования",
                                   parent=self.winfo_toplevel())
            return
        ProductDialog(self.winfo_toplevel(), mode="edit",
                      article=article, on_save=self._after_save)

    def _on_delete(self):
        article = self._get_selected_article()
        if not article:
            messagebox.showwarning("Внимание", "Выберите товар для удаления",
                                   parent=self.winfo_toplevel())
            return
        product = get_product_by_article(article)
        name = product["name"] if product else article
        if messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить {ITEM_NAME_SINGULAR.lower()} «{name}» (арт. {article})?\nЭто действие необратимо.",
            parent=self.winfo_toplevel()
        ):
            delete_product(article)
            self.load_products()

    def _after_save(self):
        self.load_products()

    def _get_thumbnail(self, filename: str):
        if not filename:
            return ""

        path = os.path.join(BASE_DIR, "images", filename)
        if not os.path.exists(path):
            path = os.path.join(BASE_DIR, "images", "picture.png")
            if not os.path.exists(path):
                return ""

        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((60, 60))
            return ImageTk.PhotoImage(img)
        except ImportError:
            print(f"Установите Pillow для отображения миниатюр")
            return ""
        except Exception as e:
            print(f"Ошибка загрузки миниатюры {filename}: {e}")
            return ""

    def _show_detail(self, article: str):
        product = get_product_by_article(article)
        if not product:
            return
        DetailWindow(self.winfo_toplevel(), product)

class ProductDialog(tk.Toplevel):

    def __init__(self, master, mode: str, on_save,
                 article: str = None):
        super().__init__(master)
        self.mode = mode          # "add" | "edit"
        self.on_save = on_save
        self.article = article
        self.product = get_product_by_article(article) if article else None

        title = f"Добавить {ITEM_NAME_SINGULAR.lower()}" if mode == "add" else f"Редактировать {ITEM_NAME_SINGULAR.lower()}"
        self.title(title)

        try:
            self.iconbitmap(os.path.join(BASE_DIR, APP_ICON))
        except:
            pass

        self.resizable(False, False)
        self.configure(bg=BG_MID)
        self.grab_set()
        self._build_ui()
        self._center()
        if self.product:
            self._fill_data()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_CARD, pady=12, padx=20)
        header.pack(fill="x")
        tk.Label(header,
                 text=f"Добавить {ITEM_NAME_SINGULAR.lower()}" if self.mode == "add" else f"Редактировать {ITEM_NAME_SINGULAR.lower()}",
                 font=(FONT_FAMILY, 13, "bold"),
                 bg=BG_CARD, fg=TEXT_MAIN).pack(anchor="w")

        body = tk.Frame(self, bg=BG_MID, padx=24, pady=18)
        body.pack(fill="both", expand=True)

        self._vars = {}
        fields = [
            ("article",     "Артикул *",           False),
            ("name",        "Наименование *",      False),
            ("unit",        "Единица измерения",   False),
            ("price",       "Цена *",              False),
            ("discount",    "Скидка (%)",          False),
            ("stock",       "Остаток",             False),
            ("description", "Описание",            True),
            ("photo",       "Фото (имя файла)",    False),
        ]

        self._desc_text = None

        for i, (key, label, is_text) in enumerate(fields):
            row = i // 2
            col_base = (i % 2) * 2

            tk.Label(body, text=label, font=(FONT_FAMILY, 8, "bold"),
                     bg=BG_MID, fg=TEXT_SUB).grid(
                row=row * 2, column=col_base, sticky="w",
                padx=(0, 20), pady=(6, 1)
            )
            if is_text:
                t = tk.Text(body, height=3, width=30,
                            bg=BG_ROW, fg=TEXT_MAIN,
                            insertbackground=TEXT_MAIN,
                            font=(FONT_FAMILY, 9), relief="flat", bd=4)
                t.grid(row=row * 2 + 1, column=col_base, sticky="ew",
                       padx=(0, 20), pady=(0, 4))
                self._desc_text = t
            else:
                var = tk.StringVar()
                self._vars[key] = var
                e = tk.Entry(body, textvariable=var,
                             bg=BG_ROW, fg=TEXT_MAIN,
                             insertbackground=TEXT_MAIN,
                             font=(FONT_FAMILY, 9), relief="flat", bd=4)
                e.grid(row=row * 2 + 1, column=col_base, sticky="ew",
                       padx=(0, 20), pady=(0, 4))

                if key == "article" and self.mode == "edit":
                    e.config(state="disabled")

        body.columnconfigure(0, weight=1)
        body.columnconfigure(2, weight=1)

        dropdown_row = len(fields)
        self._cat_var = tk.StringVar()
        self._sup_var = tk.StringVar()
        self._man_var = tk.StringVar()

        self._categories  = get_all_categories()
        self._suppliers   = get_all_suppliers()
        self._manufacturers = get_all_manufacturers()

        for dr_idx, (label, var, items) in enumerate([
            ("Категория", self._cat_var,
             ["—"] + [c["name"] for c in self._categories]),
            ("Поставщик", self._sup_var,
             ["—"] + [s["name"] for s in self._suppliers]),
            ("Производитель", self._man_var,
             ["—"] + [m["name"] for m in self._manufacturers]),
        ]):
            col_base = dr_idx * 2 if dr_idx < 2 else 0
            extra_row = dropdown_row + (dr_idx // 2) * 2
            if dr_idx == 2:
                col_base = 0
                extra_row = dropdown_row + 2

            tk.Label(body, text=label, font=(FONT_FAMILY, 8, "bold"),
                     bg=BG_MID, fg=TEXT_SUB).grid(
                row=extra_row, column=col_base, sticky="w",
                padx=(0, 20), pady=(6, 1)
            )
            combo = ttk.Combobox(body, textvariable=var, values=items,
                                 state="readonly", width=26)
            combo.grid(row=extra_row + 1, column=col_base, sticky="ew",
                       padx=(0, 20), pady=(0, 4))

        self._err_var = tk.StringVar()
        tk.Label(body, textvariable=self._err_var,
                 fg="#ff4d6d", bg=BG_MID,
                 font=(FONT_FAMILY, 9)).grid(
            row=dropdown_row + 4, column=0, columnspan=4,
            sticky="w", pady=(6, 0)
        )

        btn_frame = tk.Frame(self, bg=BG_MID, pady=12, padx=24)
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame, text="Сохранить",
            bg="#27ae60", fg=BTN_FG,
            font=(FONT_FAMILY, 10, "bold"), relief="flat",
            cursor="hand2", padx=16, pady=7,
            command=self._save
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_frame, text="Отмена",
            bg=BG_ROW, fg=TEXT_SUB,
            font=(FONT_FAMILY, 10), relief="flat",
            cursor="hand2", padx=16, pady=7,
            command=self.destroy
        ).pack(side="left")

    def _fill_data(self):
        p = self.product
        field_map = {
            "article": str(p.get("article", "")),
            "name":    str(p.get("name", "")),
            "unit":    str(p.get("unit", "шт.")),
            "price":   str(p.get("price", "")),
            "discount": str(p.get("discount", "0")),
            "stock":   str(p.get("stock", "0")),
            "photo":   str(p.get("photo", "") or ""),
        }
        for key, val in field_map.items():
            if key in self._vars:
                self._vars[key].set(val)

        if self._desc_text and p.get("description"):
            self._desc_text.insert("1.0", p["description"])

        if p.get("category"):
            self._cat_var.set(p["category"])
        if p.get("supplier"):
            self._sup_var.set(p["supplier"])
        if p.get("manufacturer"):
            self._man_var.set(p["manufacturer"])

    def _save(self):
        article = self._vars.get("article", tk.StringVar()).get().strip()
        name    = self._vars.get("name", tk.StringVar()).get().strip()
        price_s = self._vars.get("price", tk.StringVar()).get().strip()

        errors = []
        if not article:
            errors.append("Артикул обязателен")
        if not name:
            errors.append("Наименование обязательно")
        try:
            price = float(price_s.replace(",", "."))
            if price <= 0:
                raise ValueError
        except ValueError:
            errors.append("Цена должна быть положительным числом")
            price = 0

        if errors:
            self._err_var.set(" | ".join(errors))
            return

        try:
            discount = int(self._vars.get("discount", tk.StringVar()).get() or "0")
        except ValueError:
            discount = 0
        try:
            stock = int(self._vars.get("stock", tk.StringVar()).get() or "0")
        except ValueError:
            stock = 0

        description = self._desc_text.get("1.0", "end-1c") \
            if self._desc_text else ""

        def _find_id(lst, name_val):
            for item in lst:
                if item["name"] == name_val:
                    return item["id"]
            return None

        cat_id = _find_id(self._categories,    self._cat_var.get())
        sup_id = _find_id(self._suppliers,     self._sup_var.get())
        man_id = _find_id(self._manufacturers, self._man_var.get())

        data = {
            "article":      article,
            "name":         name,
            "unit":         self._vars.get("unit", tk.StringVar()).get().strip() or "шт.",
            "price":        price,
            "discount":     discount,
            "stock":        stock,
            "description":  description or None,
            "photo":        self._vars.get("photo", tk.StringVar()).get().strip() or None,
            "id_category":  cat_id,
            "id_supplier":  sup_id,
            "id_manufacturer": man_id,
        }

        try:
            if self.mode == "add":
                insert_product(data)
            else:
                update_product(self.article, data)
        except Exception as e:
            self._err_var.set(f"Ошибка сохранения: {e}")
            return

        self.on_save()
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = 680, 560
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

class DetailWindow(tk.Toplevel):

    def __init__(self, master, product: dict):
        super().__init__(master)
        self.title(f"{ITEM_NAME_SINGULAR}: {product['name']}")

        try:
            self.iconbitmap(os.path.join(BASE_DIR, APP_ICON))
        except:
            pass

        self.resizable(False, False)
        self.configure(bg=BG_MID)
        self.grab_set()
        self._build(product)
        self._center()

    def _build(self, p):
        left = tk.Frame(self, bg=BG_MID, padx=16, pady=16)
        left.pack(side="left", fill="y")

        photo_label = tk.Label(left, bg=BG_CARD, width=18, height=12)
        photo_label.pack()

        self._load_photo(photo_label, p.get("photo"))

        right = tk.Frame(self, bg=BG_MID, padx=16, pady=16)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text=p["name"],
                 font=(FONT_FAMILY, 14, "bold"),
                 bg=BG_MID, fg=TEXT_MAIN,
                 wraplength=360, justify="left").pack(anchor="w")

        tk.Label(right, text=f"Артикул: {p['article']}",
                 font=(FONT_FAMILY, 9), bg=BG_MID, fg=TEXT_SUB).pack(anchor="w", pady=(4, 8))

        price = p.get("price", 0)
        discount = p.get("discount", 0) or 0
        if discount > 0:
            final_price = price * (1 - discount / 100)
            price_text = f"{final_price:.2f} ₽  (скидка {discount}%,\nбез скидки: {price:.2f} ₽)"
            price_color = "#27ae60"
        else:
            price_text = f"{price:.2f} ₽"
            price_color = TEXT_MAIN

        tk.Label(right, text=price_text,
                 font=(FONT_FAMILY, 13, "bold"),
                 bg=BG_MID, fg=price_color).pack(anchor="w", pady=(0, 10))

        sep = tk.Frame(right, bg=BG_CARD, height=1)
        sep.pack(fill="x", pady=(0, 10))

        fields = [
            ("Категория",    p.get("category") or "—"),
            ("Поставщик",   p.get("supplier") or "—"),
            ("Производитель", p.get("manufacturer") or "—"),
            ("Ед. изм.",    p.get("unit") or "шт."),
            ("Остаток",     str(p.get("stock", 0)) + " шт."),
        ]
        for label, value in fields:
            row = tk.Frame(right, bg=BG_MID)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", width=14, anchor="w",
                     font=(FONT_FAMILY, 9), bg=BG_MID, fg=TEXT_SUB).pack(side="left")
            tk.Label(row, text=value, anchor="w",
                     font=(FONT_FAMILY, 9, "bold"), bg=BG_MID, fg=TEXT_MAIN).pack(side="left")

        if p.get("description"):
            sep2 = tk.Frame(right, bg=BG_CARD, height=1)
            sep2.pack(fill="x", pady=(10, 6))
            tk.Label(right, text="Описание:", font=(FONT_FAMILY, 9, "bold"),
                     bg=BG_MID, fg=TEXT_SUB).pack(anchor="w")
            tk.Label(right, text=p["description"],
                     font=(FONT_FAMILY, 9), bg=BG_MID, fg=TEXT_MAIN,
                     wraplength=360, justify="left").pack(anchor="w", pady=(2, 0))

        tk.Button(self, text="Закрыть",
                  bg=BG_CARD, fg=TEXT_MAIN,
                  font=(FONT_FAMILY, 9), relief="flat",
                  cursor="hand2", padx=20, pady=6,
                  command=self.destroy).pack(pady=(0, 14))

    def _load_photo(self, label, photo_name):

        if not photo_name:
            self._set_placeholder(label, "Фото отсутствует")
            return
        try:
            from PIL import Image, ImageTk
            img_path = os.path.join(IMAGES_PATH, photo_name)
            if not os.path.exists(img_path):
                self._set_placeholder(label, f"Фото отсутствует\n{photo_name}")
                return
            img = Image.open(img_path)
            img.thumbnail((300, 300))  # Max size 300x300 while maintaining aspect ratio
            tk_img = ImageTk.PhotoImage(img)
            label.config(image=tk_img, width=img.width, height=img.height, text="", bg=BG_MID)
            label._img_ref = tk_img  # сохраняем ссылку
        except ImportError:
            self._set_placeholder(label, f"Установите Pillow\n{photo_name}")
        except Exception:
            self._set_placeholder(label, f"Ошибка загрузки\n{photo_name}")

    def _set_placeholder(self, label, text):
        label.config(text=text, fg=TEXT_SUB, bg="#2a2a40",
                     font=(FONT_FAMILY, 10), width=30, height=15, image="")

    def _center(self):
        self.update_idletasks()
        w, h = 580, 380
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
