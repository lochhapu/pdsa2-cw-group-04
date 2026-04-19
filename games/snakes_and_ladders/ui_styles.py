# ui_styles.py

from tkinter import ttk

BG_COLOR = "#022c22"
CARD_COLOR = "#064e3b"
PRIMARY = "#10b981"
SUCCESS = "#22c55e"
DANGER = "#ef4444"
TEXT = "#ecfdf5"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUB = ("Segoe UI", 12)
FONT_BTN = ("Segoe UI", 12, "bold")

def apply_theme(root):
    style = ttk.Style()
    style.theme_use("clam")
    root.configure(bg=BG_COLOR)