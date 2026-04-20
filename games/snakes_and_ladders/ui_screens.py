# ui_screens.py

import tkinter as tk
from ui_styles import *

def create_card(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    card = tk.Frame(parent, bg=CARD_COLOR)
    card.pack(fill="both", expand=True, padx=20, pady=20)
    return card


def modern_button(parent, text, command):
    btn = tk.Button(parent,
        text=text,
        font=FONT_BTN,
        bg=PRIMARY,
        fg="white",
        activebackground="#059669",
        relief="flat",
        width=18,
        height=2,
        cursor="hand2",
        command=command
    )
    btn.pack(pady=10)

    def on_enter(e): btn.config(bg="#059669")
    def on_leave(e): btn.config(bg=PRIMARY)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    return btn


def draw_board(frame, n, snakes, ladders):
    num = n * n

    for r in range(n):
        row = []
        for c in range(n):
            row.append(num)
            num -= 1

        if r % 2 == 1:
            row.reverse()

        for c in range(n):
            val = row[c]

            # ---------------- DEFAULT ---------------- #
            bg_color = "#1f2937"   # dark
            text = str(val)

            # ---------------- LADDER ---------------- #
            if val in ladders:
                bg_color = "#10b981"   # green
                text = f"{val}\n🪜"

            # ---------------- SNAKE ---------------- #
            elif val in snakes:
                bg_color = "#ef4444"   # red
                text = f"{val}\n🐍"

            # ---------------- TILE ---------------- #
            tile = tk.Label(frame,
                text=text,
                width=6,
                height=3,
                bg=bg_color,
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                justify="center"
            )
            tile.grid(row=r, column=c, padx=2, pady=2)