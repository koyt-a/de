import tkinter as tk
from tkinter import ttk
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db import init_db
from ui.login import LoginWindow
from ui.products import ProductsWindow
from ui.orders import OrdersWindow
from config import (
    APP_NAME, APP_ICON, ITEM_NAME_PLURAL, ROLE_DISPLAY,
    FONT_FAMILY, BG_PRIMARY, BG_SECONDARY, COLOR_ACCENT,
    TEXT_PRIMARY, TEXT_SECONDARY
)

SIDEBAR_W  = 180

ROLE_LABELS = {
    "admin":   "Администратор",
    "manager": "Менеджер",
    "client":  "Авторизованный клиент",
    "guest":   "Гость",
}

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.withdraw()          # Скрываем до авторизации
        self.title(f"{APP_NAME} — Система управления")
        self.minsize(900, 560)
        self.configure(bg=BG_PRIMARY)

        icon_path = os.path.join(BASE_DIR, APP_ICON)
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        init_db()
        self._current_user: dict | None = None
        self._active_frame: tk.Frame | None = None

        LoginWindow(self, on_success=self._on_login)

    def _on_login(self, user: dict):
        self._current_user = user
        self._build_main_ui()
        self._center()
        self.deiconify()
        self._show_products()

    def _build_main_ui(self):
        for w in self.winfo_children():
            w.destroy()

        role = self._current_user.get("role", "guest")

        topbar = tk.Frame(self, bg=BG_PRIMARY)
        topbar.pack(side="top", fill="x")

        top_inner = tk.Frame(topbar, bg=BG_PRIMARY, pady=8)
        top_inner.pack(fill="x")

        self.logo_label = tk.Label(top_inner, bg=BG_PRIMARY)
        self.logo_label.pack(side="left", padx=(16, 8))
        self._load_logo(self.logo_label)

        tk.Label(top_inner, text=APP_NAME,
                 font=(FONT_FAMILY, 14, "bold"),
                 bg=BG_PRIMARY, fg=TEXT_PRIMARY).pack(side="left")

        user_name = self._current_user.get("full_name", "")
        role_label = ROLE_DISPLAY.get(role, role)
        info_frame = tk.Frame(top_inner, bg=BG_PRIMARY)
        info_frame.pack(side="right", padx=16)
        tk.Label(info_frame,
                 text=f"{role_label}: {user_name}",
                 font=(FONT_FAMILY, 10, "italic"),
                 bg=BG_PRIMARY, fg=TEXT_SECONDARY).pack(side="left", padx=(0, 16))

        btn_logout = tk.Button(info_frame, text="Выйти",
                               font=(FONT_FAMILY, 9, "bold"),
                               bg=COLOR_ACCENT, fg=TEXT_PRIMARY,
                               activebackground="#32CD32", activeforeground=TEXT_PRIMARY,
                               relief="flat", cursor="hand2", command=self._logout)
        btn_logout.pack(side="right")

        main_area = tk.Frame(self, bg=BG_PRIMARY)
        main_area.pack(fill="both", expand=True)

        self._sidebar = tk.Frame(main_area, bg=BG_SECONDARY, width=220)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        self._content = tk.Frame(main_area, bg=BG_PRIMARY)
        self._content.pack(side="left", fill="both", expand=True)

        nav_items = [(f"🛍  {ITEM_NAME_PLURAL}", self._show_products)]
        if role in ("manager", "admin"):
            nav_items.append(("📦  Заказы", self._show_orders))

        tk.Label(self._sidebar, text="Навигация",
                 font=(FONT_FAMILY, 8),
                 bg=BG_SECONDARY, fg=TEXT_SECONDARY).pack(pady=(16, 8), padx=12, anchor="w")

        self.nav_btns = []
        for text, cmd in nav_items:
            b = tk.Button(
                self._sidebar, text=text,
                font=(FONT_FAMILY, 10),
                bg=BG_SECONDARY, fg=TEXT_SECONDARY,
                activebackground=BG_PRIMARY,
                activeforeground=TEXT_PRIMARY,
                relief="flat", anchor="w",
                cursor="hand2", padx=16, pady=10,
                command=cmd
            )
            b.pack(fill="x")
            self.nav_btns.append(b)

    def _clear_content(self):
        if self._active_frame:
            self._active_frame.destroy()
            self._active_frame = None

    def _show_products(self):
        self._clear_content()
        role = self._current_user.get("role", "guest")
        frame = ProductsWindow(self._content, role=role)
        frame.pack(fill="both", expand=True)
        self._active_frame = frame
        self._mark_nav(0)

    def _show_orders(self):
        self._clear_content()
        role = self._current_user.get("role", "guest")
        frame = OrdersWindow(self._content, role=role)
        frame.pack(fill="both", expand=True)
        self._active_frame = frame
        self._mark_nav(1)

    def _mark_nav(self, active_idx: int):
        for i, btn in enumerate(self.nav_btns):
            if i == active_idx:
                btn.config(bg=BG_PRIMARY, fg=TEXT_PRIMARY)
            else:
                btn.config(bg=BG_SECONDARY, fg=TEXT_SECONDARY)

    def _logout(self):
        self._clear_content()
        self._current_user = None
        for w in self.winfo_children():
            w.destroy()
        self.withdraw()
        LoginWindow(self, on_success=self._on_login)

    def _load_logo(self, label):

        try:
            from PIL import Image, ImageTk
            icon_path = os.path.join(BASE_DIR, APP_ICON)
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img.thumbnail((32, 32))
                tk_img = ImageTk.PhotoImage(img)
                label.config(image=tk_img)
                label._img_ref = tk_img
            else:
                label.config(text="🏢", font=("Segoe UI Emoji", 24), fg=COLOR_ACCENT)
        except Exception:
            label.config(text="🏢", font=("Segoe UI Emoji", 24), fg=COLOR_ACCENT)

    def _center(self):
        self.update_idletasks()
        w, h = 1100, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
