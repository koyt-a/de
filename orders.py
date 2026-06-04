import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import (
    get_all_orders, get_order_items,
    insert_order, update_order, delete_order,
    insert_order_item, delete_order_items,
    get_all_users, get_all_pickup_points, get_all_products,
)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from config import (
    APP_NAME, APP_ICON, ORDER_STATUSES,
    FONT_FAMILY, BG_PRIMARY, BG_SECONDARY, COLOR_ACCENT,
    TEXT_PRIMARY, TEXT_SECONDARY
)

BG_DARK    = BG_PRIMARY
BG_MID     = BG_PRIMARY
BG_CARD    = BG_PRIMARY
BG_ROW     = BG_PRIMARY
BG_ROW_ALT = "#F0F0F0"
ACCENT     = COLOR_ACCENT
ACCENT2    = COLOR_ACCENT
TEXT_MAIN  = TEXT_PRIMARY
TEXT_SUB   = TEXT_SECONDARY
BTN_FG     = TEXT_PRIMARY
HEADER_BG  = BG_SECONDARY
SEL_BG     = COLOR_ACCENT

class OrdersWindow(tk.Frame):

    O_COLS = ("id", "order_date", "delivery_date", "status",
              "client", "point_address", "pickup_code")
    O_HEADS = {
        "id":           "№",
        "order_date":   "Дата заказа",
        "delivery_date":"Дата доставки",
        "status":       "Статус",
        "client":       "Клиент",
        "point_address":"Пункт выдачи",
        "pickup_code":  "Код получения",
    }
    O_WIDTHS = {
        "id": 45, "order_date": 100, "delivery_date": 100,
        "status": 90, "client": 160, "point_address": 220, "pickup_code": 100,
    }

    I_COLS = ("product_article", "product_name", "quantity", "price")
    I_HEADS = {
        "product_article": "Артикул",
        "product_name":    "Наименование",
        "quantity":        "Кол-во",
        "price":           "Цена",
    }
    I_WIDTHS = {"product_article": 90, "product_name": 240,
                "quantity": 70, "price": 90}

    def __init__(self, master, role: str, **kwargs):
        super().__init__(master, bg=BG_DARK, **kwargs)
        self.role = role
        self._build_ui()
        self.load_orders()

    def _build_ui(self):
        if self.role == "admin":
            self._build_admin_bar()
        self._build_orders_table()
        self._build_items_table()
        self._build_statusbar()

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

    def _build_orders_table(self):
        lbl = tk.Label(self, text="Заказы",
                       font=(FONT_FAMILY, 10, "bold"),
                       bg=BG_DARK, fg=TEXT_SUB, anchor="w")
        lbl.pack(fill="x", padx=14, pady=(4, 2))

        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True, padx=12)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Orders.Treeview",
                         background=BG_ROW, foreground=TEXT_MAIN,
                         fieldbackground=BG_ROW, rowheight=24,
                         font=(FONT_FAMILY, 9))
        style.configure("Orders.Treeview.Heading",
                         background=HEADER_BG, foreground=TEXT_MAIN,
                         font=(FONT_FAMILY, 9, "bold"), relief="flat")
        style.map("Orders.Treeview",
                  background=[("selected", SEL_BG)],
                  foreground=[("selected", "#ffffff")])

        self.order_tree = ttk.Treeview(
            frame, columns=self.O_COLS, show="headings",
            style="Orders.Treeview", selectmode="browse", height=10
        )
        for col in self.O_COLS:
            self.order_tree.heading(col, text=self.O_HEADS[col])
            self.order_tree.column(col, width=self.O_WIDTHS[col], anchor="w", minwidth=40)

        vsb = ttk.Scrollbar(frame, orient="vertical",
                             command=self.order_tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal",
                             command=self.order_tree.xview)
        self.order_tree.configure(yscrollcommand=vsb.set,
                                   xscrollcommand=hsb.set)

        self.order_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.order_tree.tag_configure("even", background=BG_ROW_ALT)
        self.order_tree.tag_configure("odd",  background=BG_ROW)

        self.order_tree.tag_configure("new",       foreground="#4fc3f7")
        self.order_tree.tag_configure("transit",   foreground="#ffcc02")
        self.order_tree.tag_configure("done",      foreground="#81c784")
        self.order_tree.tag_configure("cancelled", foreground="#e57373")

        self.order_tree.bind("<<TreeviewSelect>>", self._on_order_select)

    def _build_items_table(self):
        sep = tk.Frame(self, bg=BG_CARD, height=2)
        sep.pack(fill="x", padx=12, pady=(8, 0))

        lbl = tk.Label(self, text="Состав заказа",
                       font=(FONT_FAMILY, 10, "bold"),
                       bg=BG_DARK, fg=TEXT_SUB, anchor="w")
        lbl.pack(fill="x", padx=14, pady=(6, 2))

        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True, padx=12)

        style = ttk.Style()
        style.configure("Items.Treeview",
                         background=BG_ROW_ALT, foreground=TEXT_MAIN,
                         fieldbackground=BG_ROW_ALT, rowheight=22,
                         font=(FONT_FAMILY, 9))
        style.configure("Items.Treeview.Heading",
                         background=HEADER_BG, foreground=TEXT_MAIN,
                         font=(FONT_FAMILY, 9, "bold"), relief="flat")
        style.map("Items.Treeview",
                  background=[("selected", SEL_BG)],
                  foreground=[("selected", "#ffffff")])

        self.items_tree = ttk.Treeview(
            frame, columns=self.I_COLS, show="headings",
            style="Items.Treeview", selectmode="browse", height=6
        )
        for col in self.I_COLS:
            self.items_tree.heading(col, text=self.I_HEADS[col])
            self.items_tree.column(col, width=self.I_WIDTHS[col],
                                    anchor="w", minwidth=40)

        vsb2 = ttk.Scrollbar(frame, orient="vertical",
                              command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=vsb2.set)
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Показано заказов: 0")
        tk.Label(self, textvariable=self._status_var,
                 bg=BG_MID, fg=TEXT_SUB,
                 font=(FONT_FAMILY, 9), anchor="w",
                 padx=14, pady=5).pack(fill="x", side="bottom")

    def load_orders(self):
        orders = get_all_orders()
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        for i, o in enumerate(orders):
            tag_row = "even" if i % 2 == 0 else "odd"
            tag_status = {
                "Новый":   "new",
                "В пути":  "transit",
                "Завершён": "done",
                "Отменён": "cancelled",
            }.get(o.get("status", ""), "")
            self.order_tree.insert("", "end", iid=str(o["id"]), values=(
                o["id"],
                o.get("order_date") or "—",
                o.get("delivery_date") or "—",
                o.get("status") or "—",
                o.get("client") or "—",
                o.get("point_address") or "—",
                o.get("pickup_code") or "—",
            ), tags=(tag_row, tag_status))
        self._status_var.set(f"Показано заказов: {len(orders)}")
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

    def _on_order_select(self, _event=None):
        sel = self.order_tree.selection()
        if not sel:
            return
        order_id = int(sel[0])
        items = get_order_items(order_id)
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        for oi in items:
            self.items_tree.insert("", "end", values=(
                oi.get("product_article") or "—",
                oi.get("product_name") or "—",
                oi.get("quantity") or 0,
                f"{oi.get('price', 0):.2f} ₽" if oi.get("price") else "—",
            ))

    def _get_selected_id(self):
        sel = self.order_tree.selection()
        return int(sel[0]) if sel else None

    def _on_add(self):
        OrderDialog(self.winfo_toplevel(), mode="add",
                    on_save=self.load_orders)

    def _on_edit(self):
        oid = self._get_selected_id()
        if not oid:
            messagebox.showwarning("Внимание",
                                   "Выберите заказ для редактирования",
                                   parent=self.winfo_toplevel())
            return
        orders = get_all_orders()
        order = next((o for o in orders if o["id"] == oid), None)
        if not order:
            return
        OrderDialog(self.winfo_toplevel(), mode="edit",
                    order=order, on_save=self.load_orders)

    def _on_delete(self):
        oid = self._get_selected_id()
        if not oid:
            messagebox.showwarning("Внимание",
                                   "Выберите заказ для удаления",
                                   parent=self.winfo_toplevel())
            return
        if messagebox.askyesno(
            "Подтверждение",
            f"Удалить заказ №{oid}?\nВсе позиции заказа также будут удалены.",
            parent=self.winfo_toplevel()
        ):
            delete_order(oid)
            self.load_orders()

class OrderDialog(tk.Toplevel):

    def __init__(self, master, mode: str, on_save, order: dict = None):
        super().__init__(master)
        self.mode = mode
        self.on_save = on_save
        self.order = order or {}
        self._items: list[dict] = []  # [{article, qty}, ...]

        title = "Новый заказ" if mode == "add" else f"Редактировать заказ №{order['id']}"
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
        if mode == "edit":
            self._fill_data()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_CARD, pady=10, padx=20)
        header.pack(fill="x")
        title_text = "Новый заказ" if self.mode == "add" \
            else f"Заказ №{self.order.get('id', '')}"
        tk.Label(header, text=title_text,
                 font=(FONT_FAMILY, 13, "bold"),
                 bg=BG_CARD, fg=TEXT_MAIN).pack(anchor="w")

        body = tk.Frame(self, bg=BG_MID, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        self._date_var     = self._field(body, "Дата заказа (ДД.ММ.ГГГГ)", 0, 0)
        self._deldate_var  = self._field(body, "Дата доставки (ДД.ММ.ГГГГ)", 0, 2)
        self._code_var     = self._field(body, "Код получения", 1, 0)

        tk.Label(body, text="Статус", font=(FONT_FAMILY, 8, "bold"),
                 bg=BG_MID, fg=TEXT_SUB).grid(row=2, column=0, sticky="w",
                                               padx=(0, 20), pady=(6, 1))
        self._status_var = tk.StringVar(value="Новый")
        ttk.Combobox(body, textvariable=self._status_var,
                     values=ORDER_STATUSES, state="readonly",
                     width=20).grid(row=3, column=0, sticky="ew",
                                    padx=(0, 20), pady=(0, 4))

        users = get_all_users()
        self._users = users
        user_names = ["—"] + [u["full_name"] for u in users]
        tk.Label(body, text="Клиент", font=(FONT_FAMILY, 8, "bold"),
                 bg=BG_MID, fg=TEXT_SUB).grid(row=2, column=2, sticky="w",
                                               padx=(0, 0), pady=(6, 1))
        self._client_var = tk.StringVar(value="—")
        ttk.Combobox(body, textvariable=self._client_var,
                     values=user_names, state="readonly",
                     width=24).grid(row=3, column=2, sticky="ew",
                                    padx=(0, 0), pady=(0, 4))

        points = get_all_pickup_points()
        self._points = points
        point_opts = ["—"] + [f"{p['id']} — {p['address']}" for p in points]
        tk.Label(body, text="Пункт выдачи", font=(FONT_FAMILY, 8, "bold"),
                 bg=BG_MID, fg=TEXT_SUB).grid(row=4, column=0, columnspan=3,
                                               sticky="w", padx=(0, 0), pady=(6, 1))
        self._point_var = tk.StringVar(value="—")
        ttk.Combobox(body, textvariable=self._point_var,
                     values=point_opts, state="readonly",
                     width=50).grid(row=5, column=0, columnspan=3, sticky="ew",
                                    padx=(0, 0), pady=(0, 4))

        body.columnconfigure(0, weight=1)
        body.columnconfigure(2, weight=1)

        sep = tk.Frame(body, bg=BG_CARD, height=1)
        sep.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(10, 6))

        tk.Label(body, text="Позиции заказа",
                 font=(FONT_FAMILY, 10, "bold"),
                 bg=BG_MID, fg=TEXT_MAIN).grid(
            row=7, column=0, columnspan=4, sticky="w", pady=(0, 4))

        item_frame = tk.Frame(body, bg=BG_DARK)
        item_frame.grid(row=8, column=0, columnspan=4, sticky="ew", pady=(0, 4))

        self.items_tree = ttk.Treeview(
            item_frame, columns=("article", "qty"), show="headings",
            height=4, selectmode="browse"
        )
        self.items_tree.heading("article", text="Артикул")
        self.items_tree.heading("qty", text="Кол-во")
        self.items_tree.column("article", width=140)
        self.items_tree.column("qty", width=80)
        self.items_tree.pack(side="left", fill="both", expand=True)

        item_btns = tk.Frame(body, bg=BG_MID)
        item_btns.grid(row=9, column=0, columnspan=4, sticky="w", pady=(0, 6))

        products = get_all_products()
        self._products = products
        art_opts = [p["article"] for p in products]

        self._art_var = tk.StringVar()
        self._qty_var = tk.StringVar(value="1")

        ttk.Combobox(item_btns, textvariable=self._art_var,
                     values=art_opts, width=16).pack(side="left", padx=(0, 4))

        tk.Entry(item_btns, textvariable=self._qty_var, width=5,
                 bg=BG_ROW, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                 relief="flat", font=(FONT_FAMILY, 9)).pack(side="left", padx=(0, 4))

        tk.Button(item_btns, text="+ Добавить позицию",
                  bg="#27ae60", fg=BTN_FG,
                  font=(FONT_FAMILY, 8), relief="flat",
                  cursor="hand2", padx=8, pady=4,
                  command=self._add_item).pack(side="left", padx=(0, 8))

        tk.Button(item_btns, text="✕ Удалить позицию",
                  bg=ACCENT, fg=BTN_FG,
                  font=(FONT_FAMILY, 8), relief="flat",
                  cursor="hand2", padx=8, pady=4,
                  command=self._del_item).pack(side="left")

        self._err_var = tk.StringVar()
        tk.Label(body, textvariable=self._err_var,
                 fg="#ff4d6d", bg=BG_MID,
                 font=(FONT_FAMILY, 9)).grid(
            row=10, column=0, columnspan=4, sticky="w", pady=(4, 0))

        btn_frame = tk.Frame(self, bg=BG_MID, pady=12, padx=24)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="Сохранить",
                  bg="#27ae60", fg=BTN_FG,
                  font=(FONT_FAMILY, 10, "bold"), relief="flat",
                  cursor="hand2", padx=16, pady=7,
                  command=self._save).pack(side="left", padx=(0, 10))

        tk.Button(btn_frame, text="Отмена",
                  bg=BG_ROW, fg=TEXT_SUB,
                  font=(FONT_FAMILY, 10), relief="flat",
                  cursor="hand2", padx=16, pady=7,
                  command=self.destroy).pack(side="left")

    def _field(self, parent, label, row, col):
        tk.Label(parent, text=label, font=(FONT_FAMILY, 8, "bold"),
                 bg=BG_MID, fg=TEXT_SUB).grid(
            row=row * 2, column=col, sticky="w",
            padx=(0, 20), pady=(6, 1)
        )
        var = tk.StringVar()
        tk.Entry(parent, textvariable=var,
                 bg=BG_ROW, fg=TEXT_MAIN,
                 insertbackground=TEXT_MAIN,
                 font=(FONT_FAMILY, 9), relief="flat", bd=4, width=18).grid(
            row=row * 2 + 1, column=col, sticky="ew",
            padx=(0, 20), pady=(0, 4)
        )
        return var

    def _fill_data(self):
        o = self.order
        self._date_var.set(o.get("order_date") or "")
        self._deldate_var.set(o.get("delivery_date") or "")
        self._code_var.set(str(o.get("pickup_code") or ""))
        self._status_var.set(o.get("status") or "Новый")

        if o.get("client"):
            self._client_var.set(o["client"])
        if o.get("id_point"):
            for pt in self._points:
                if pt["id"] == o["id_point"]:
                    self._point_var.set(f"{pt['id']} — {pt['address']}")
                    break

        items = get_order_items(o["id"])
        for oi in items:
            self._items.append({
                "article": oi["product_article"],
                "qty": oi["quantity"]
            })
            self.items_tree.insert("", "end", values=(
                oi["product_article"], oi["quantity"]
            ))

    def _add_item(self):
        art = self._art_var.get().strip()
        if not art:
            return
        try:
            qty = int(self._qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            qty = 1
        self._items.append({"article": art, "qty": qty})
        self.items_tree.insert("", "end", values=(art, qty))
        self._art_var.set("")
        self._qty_var.set("1")

    def _del_item(self):
        sel = self.items_tree.selection()
        if sel:
            idx = self.items_tree.index(sel[0])
            self.items_tree.delete(sel[0])
            if 0 <= idx < len(self._items):
                self._items.pop(idx)

    def _save(self):
        try:
            code = int(self._code_var.get()) if self._code_var.get() else None
        except ValueError:
            code = None

        client_name = self._client_var.get()
        user_id = None
        for u in self._users:
            if u["full_name"] == client_name:
                user_id = u["id"]
                break

        point_raw = self._point_var.get()
        point_id = None
        if point_raw and point_raw != "—":
            try:
                point_id = int(point_raw.split("—")[0].strip())
            except (ValueError, IndexError):
                pass

        data = {
            "order_date":    self._date_var.get().strip() or None,
            "delivery_date": self._deldate_var.get().strip() or None,
            "pickup_code":   code,
            "status":        self._status_var.get(),
            "id_user":       user_id,
            "id_point":      point_id,
        }

        try:
            if self.mode == "add":
                oid = insert_order(data)
                for item in self._items:
                    insert_order_item(oid, item["article"], item["qty"])
            else:
                oid = self.order["id"]
                update_order(oid, data)
                delete_order_items(oid)
                for item in self._items:
                    insert_order_item(oid, item["article"], item["qty"])
        except Exception as e:
            self._err_var.set(f"Ошибка: {e}")
            return

        self.on_save()
        self.destroy()

    def _center(self):
        self.update_idletasks()
        w, h = 660, 580
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
