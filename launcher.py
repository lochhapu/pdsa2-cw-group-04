import tkinter as tk
from tkinter import ttk
import subprocess
import os
import sys

# ---------------- STYLING ---------------- #
BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
BUTTON_COLOR = "#2563eb"
BUTTON_HOVER = "#1d4ed8"
TEXT_COLOR = "#f8fafc"
SECONDARY_TEXT = "#cbd5e1"
ACCENT_COLOR = "#38bdf8"

TITLE_FONT = ("Segoe UI", 20, "bold")
BUTTON_FONT = ("Segoe UI", 11, "bold")

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("PDSA2 Game Launcher")
        self.root.geometry("500x520")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        
        self.apps = {
            "Minimum Cost Assignment": os.path.join("games", "minimum_cost", "main.py"),
            "Knights Tour": os.path.join("games", "knights_tour", "main.py"),
            "Snakes & Ladders": os.path.join("games", "snakes_and_ladders", "main.py"),
            "Traffic Simulation": os.path.join("games", "traffic_sim", "main.py"),
            "16 Queens": os.path.join("games", "queens", "main.py"),
        }
        
        self.create_widgets()

    # ---------------- BUTTON STYLE ---------------- #
    def style_button(self, btn):
        btn.config(
            bg=BUTTON_COLOR,
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
            bd=0,
            padx=15,
            pady=10,
            cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=BUTTON_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=BUTTON_COLOR))

    # ---------------- UI ---------------- #
    def create_widgets(self):
        # Shadow
        shadow = tk.Frame(self.root, bg="#020617")
        shadow.place(relx=0.5, rely=0.5, anchor="center", width=420, height=460)

        # Card
        card = tk.Frame(self.root, bg=CARD_COLOR)
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=440)

        # Title
        tk.Label(card, text="Game Launcher", font=TITLE_FONT,
                 bg=CARD_COLOR, fg=TEXT_COLOR).pack(pady=(25, 5))

        # Accent line
        tk.Frame(card, bg=ACCENT_COLOR, height=3, width=100).pack(pady=5)

        tk.Label(card, text="Select a game to start",
                 font=("Segoe UI", 11),
                 bg=CARD_COLOR, fg=SECONDARY_TEXT).pack(pady=(0, 20))

        # Buttons
        for app_name, app_path in self.apps.items():
            btn = tk.Button(
                card,
                text=app_name,
                command=lambda path=app_path: self.launch_app(path),
                width=28
            )
            self.style_button(btn)
            btn.pack(pady=6)

        # Exit Button
        exit_btn = tk.Button(card, text="Exit", command=self.root.quit,
                             bg="#dc2626", fg="white")
        self.style_button(exit_btn)
        exit_btn.pack(pady=20)

    # ---------------- LAUNCH APP ---------------- #
    def launch_app(self, app_path):
        try:
            app_dir = os.path.dirname(app_path)
            app_file = os.path.basename(app_path)

            subprocess.Popen(
                [sys.executable, app_file],
                cwd=app_dir,
                stdout=None,
                stderr=None
            )

        except Exception as e:
            self.show_error(app_path, str(e))

    # ---------------- ERROR POPUP ---------------- #
    def show_error(self, app_path, error_msg):
        error_win = tk.Toplevel(self.root)
        error_win.title("Error")
        error_win.geometry("350x180")
        error_win.configure(bg=BG_COLOR)

        card = tk.Frame(error_win, bg=CARD_COLOR)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        tk.Label(card, text="Launch Failed",
                 font=("Segoe UI", 14, "bold"),
                 bg=CARD_COLOR, fg="red").pack(pady=10)

        tk.Label(card,
                 text=f"{app_path}\n{error_msg}",
                 bg=CARD_COLOR,
                 fg=SECONDARY_TEXT,
                 wraplength=300,
                 justify="center").pack(pady=5)

        btn = tk.Button(card, text="OK", command=error_win.destroy)
        self.style_button(btn)
        btn.pack(pady=10)

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()