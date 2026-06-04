import tkinter as tk
from tkinter import ttk
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from database.db import authenticate
from config import (
    APP_NAME, APP_ICON, FONT_FAMILY,
    BG_PRIMARY, BG_SECONDARY, COLOR_ACCENT,
    TEXT_PRIMARY, TEXT_SECONDARY
)

ROLE_LABELS = {
    "admin":   "Администратор",
    "manager": "Менеджер",
    "client":  "Авторизованный клиент",
    "guest":   "Гость",
}

class LoginWindow(tk.Toplevel):

    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title(f"Авторизация — {APP_NAME}")

        try:
            self.iconbitmap(os.path.join(BASE_DIR, APP_ICON))
        except:
            pass

        self.resizable(False, False)
        self.configure(bg=BG_PRIMARY)
        self._build_ui()
        self._center()
        self.grab_set()
        self.focus_force()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_PRIMARY)
        container.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(container, bg="white", padx=40, pady=30,
                        highlightbackground=COLOR_ACCENT, highlightthickness=2)
        card.pack(fill="both", expand=True)

        logo_label = tk.Label(card, bg="white")
        logo_label.pack(pady=(0, 4))
        self._load_logo(logo_label)

        tk.Label(
            card, text=APP_NAME,
            font=(FONT_FAMILY, 20, "bold"),
            bg="white", fg=TEXT_PRIMARY
        ).pack()

        tk.Label(
            card, text="Вход в систему",
            font=(FONT_FAMILY, 11),
            bg="white", fg=TEXT_SECONDARY
        ).pack(pady=(0, 20))

        self._add_label(card, "Логин")
        self.entry_login = self._add_entry(card)
        self.entry_login.focus_set()

        self._add_label(card, "Пароль")
        self.entry_password = self._add_entry(card, show="●")

        self.lbl_error = tk.Label(
            card, text="", fg="red",
            font=(FONT_FAMILY, 9), bg="white"
        )
        self.lbl_error.pack(pady=(6, 0))

        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(fill="x", pady=(14, 0))

        self.btn_login = tk.Button(
            btn_frame, text="Войти",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_ACCENT, fg=TEXT_PRIMARY,
            activebackground=COLOR_ACCENT, activeforeground=TEXT_PRIMARY,
            relief="flat", cursor="hand2", pady=9,
            command=self._do_login
        )
        self.btn_login.pack(fill="x", pady=(0, 8))

        self.btn_guest = tk.Button(
            btn_frame, text="Войти как гость",
            font=(FONT_FAMILY, 10),
            bg=BG_PRIMARY, fg=TEXT_SECONDARY,
            activebackground=BG_PRIMARY, activeforeground=TEXT_PRIMARY,
            relief="flat", cursor="hand2", pady=7,
            command=self._do_guest
        )
        self.btn_guest.pack(fill="x")

        self._bind_hover(self.btn_login, COLOR_ACCENT, "#32CD32") # Слегка темнее салатового
        self._bind_hover(self.btn_guest, BG_PRIMARY, "#F0F0F0")

        self.bind("<Return>", lambda _: self._do_login())

    @staticmethod
    def _add_label(parent, text):
        tk.Label(
            parent, text=text,
            font=(FONT_FAMILY, 9, "bold"),
            bg=BG_SECONDARY, fg=TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", pady=(8, 2))

    @staticmethod
    def _add_entry(parent, show=None):
        frame = tk.Frame(parent, bg=COLOR_ACCENT, pady=1, padx=1)
        frame.pack(fill="x", pady=(0, 2))
        e = tk.Entry(
            frame, show=show,
            font=(FONT_FAMILY, 11),
            bg=BG_PRIMARY, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat", bd=0
        )
        e.pack(fill="x", ipady=7, padx=6, pady=4)
        return e

    @staticmethod
    def _bind_hover(widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda _: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda _: widget.config(bg=normal_bg))

    def _do_login(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()

        if not login or not password:
            self._show_error("Введите логин и пароль")
            return

        user = authenticate(login, password)
        if user is None:
            self._show_error("Неверный логин или пароль")
            self.entry_password.delete(0, "end")
            self.entry_password.focus_set()
            return

        self._show_error("")
        self.destroy()
        self.on_success(user)

    def _do_guest(self):
        self.destroy()
        self.on_success({"role": "guest", "full_name": "Гость", "id": None})

    def _show_error(self, msg: str):
        self.lbl_error.config(text=msg)

    def _load_logo(self, label):

        try:
            from PIL import Image, ImageTk
            icon_path = os.path.join(BASE_DIR, APP_ICON)
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img.thumbnail((64, 64))
                tk_img = ImageTk.PhotoImage(img)
                label.config(image=tk_img)
                label._img_ref = tk_img
            else:
                label.config(text="🏢", font=("Segoe UI Emoji", 36), fg=COLOR_ACCENT)
        except Exception:
            label.config(text="🏢", font=("Segoe UI Emoji", 36), fg=COLOR_ACCENT)

    def _center(self):
        self.update_idletasks()
        w, h = 380, 490
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
