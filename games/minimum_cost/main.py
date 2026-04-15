import tkinter as tk
from tkinter import messagebox
import random
import time
import sqlite3

# ---------------- DATABASE SETUP ---------------- #
conn = sqlite3.connect("min_cost_game.db")
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS results (
    round_id INTEGER PRIMARY KEY AUTOINCREMENT,
    num_tasks INTEGER,
    greedy_cost INTEGER,
    greedy_time REAL,
    hungarian_cost INTEGER,
    hungarian_time REAL
)""")
conn.commit()

# ---------------- COLORS / STYLING ---------------- #
BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
ACCENT_COLOR = "#38bdf8"
BUTTON_COLOR = "#2563eb"
BUTTON_HOVER = "#1d4ed8"
TEXT_COLOR = "#f8fafc"
SECONDARY_TEXT = "#cbd5e1"
RESULT_BG = "#111827"
SUCCESS_COLOR = "#22c55e"

TITLE_FONT = ("Arial", 24, "bold")
SUBTITLE_FONT = ("Arial", 14)
LABEL_FONT = ("Arial", 13)
BUTTON_FONT = ("Arial", 13, "bold")
RESULT_FONT = ("Consolas", 13)

# ---------------- ALGORITHMS ---------------- #

def greedy_assignment(cost_matrix):
    n = len(cost_matrix)
    assigned = [-1] * n
    total_cost = 0
    used_rows = set()
    used_cols = set()
    start_time = time.time()

    flat_list = [(i, j, cost_matrix[i][j]) for i in range(n) for j in range(n)]
    flat_list.sort(key=lambda x: x[2])

    for i, j, cost in flat_list:
        if i not in used_rows and j not in used_cols:
            assigned[i] = j
            used_rows.add(i)
            used_cols.add(j)
            total_cost += cost

    end_time = time.time()
    return total_cost, end_time - start_time

def hungarian_algorithm(cost_matrix):
    # TODO: Implement hungarian_algorithm
    pass

# ---------------- GAME FUNCTIONS ---------------- #

def generate_cost_matrix(n):
    return [[random.randint(20, 200) for _ in range(n)] for _ in range(n)]

def play_round():
    try:
        n = int(num_tasks_entry.get())
        if n < 50 or n > 100:
            raise ValueError("Number of tasks must be between 50 and 100.")
    except ValueError as e:
        messagebox.showerror("Invalid Input", str(e))
        return

    cost_matrix = generate_cost_matrix(n)

    greedy_cost, greedy_time = greedy_assignment(cost_matrix)
    hungarian_cost, hungarian_time = hungarian_algorithm(cost_matrix)

    c.execute(
        "INSERT INTO results (num_tasks, greedy_cost, greedy_time, hungarian_cost, hungarian_time) VALUES (?, ?, ?, ?, ?)",
        (n, greedy_cost, greedy_time, hungarian_cost, hungarian_time)
    )
    conn.commit()

    # Compare costs
    if greedy_cost < hungarian_cost:
        cheaper = "Greedy"
        cost_difference = hungarian_cost - greedy_cost
        cheaper_text = f"Greedy was cheaper by ${cost_difference}"
    elif hungarian_cost < greedy_cost:
        cheaper = "Hungarian"
        cost_difference = greedy_cost - hungarian_cost
        cheaper_text = f"Hungarian was cheaper by ${cost_difference}"
    else:
        cheaper = "Tie"
        cheaper_text = "Both algorithms had the same total cost"

    # Compare speed
    if greedy_time < hungarian_time:
        faster = "Greedy"
        time_difference = hungarian_time - greedy_time
        faster_text = f"Greedy was faster by {time_difference:.6f} seconds"
    elif hungarian_time < greedy_time:
        faster = "Hungarian"
        time_difference = greedy_time - hungarian_time
        faster_text = f"Hungarian was faster by {time_difference:.6f} seconds"
    else:
        faster = "Tie"
        faster_text = "Both algorithms took the same time"

    result_text = f"""
╔══════════════════════════════════════════════════════════════════════╗
                            ROUND COMPLETED
╚══════════════════════════════════════════════════════════════════════╝

Tasks / Employees : {n}

GREEDY ALGORITHM
   Total Cost : ${greedy_cost}
   Time Taken : {greedy_time:.6f} seconds

HUNGARIAN ALGORITHM
   Total Cost : ${hungarian_cost}
   Time Taken : {hungarian_time:.6f} seconds

COMPARISON
   {cheaper_text}
   {faster_text}

RESULT SUMMARY
   Cheapest Solution : {cheaper}
   Fastest Algorithm : {faster}
"""

    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, result_text)
    result_box.config(state="disabled")

# ---- View History Function ----
def view_history():
    history_window = tk.Toplevel(window)
    history_window.title("Game History")
    history_window.geometry("850x450")
    history_window.configure(bg=BG_COLOR)

    tk.Label(history_window, text="Last 10 Rounds", font=("Arial", 16), bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=10)

    # Scrollable Text box
    text_frame = tk.Frame(history_window, bg=BG_COLOR)
    text_frame.pack(fill="both", expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_box = tk.Text(
        text_frame,
        width=95,
        height=20,
        bg=RESULT_BG,
        fg=SUCCESS_COLOR,
        font=RESULT_FONT,
        bd=0,
        relief="flat",
        yscrollcommand=scrollbar.set,
        padx=10,
        pady=10,
        wrap="word"
    )
    text_box.pack(fill="both", expand=True)
    scrollbar.config(command=text_box.yview)

    # Fetch last 10 rounds from DB
    c.execute("SELECT * FROM results ORDER BY round_id DESC LIMIT 10")
    rows = c.fetchall()
    
    if not rows:
        text_box.insert(tk.END, "No history yet.\n")
    else:
        for row in rows:
            round_id, n, g_cost, g_time, h_cost, h_time = row
            diff_time = abs(g_time - h_time)
            cheaper_algo = "Greedy" if g_cost < h_cost else "Hungarian" if h_cost < g_cost else "Tie"
            diff_cost = abs(g_cost - h_cost)
            text_box.insert(tk.END, f"Round {round_id} | Tasks: {n}\n")
            text_box.insert(tk.END, f"  Greedy → ${g_cost} | {g_time:.4f}s\n")
            text_box.insert(tk.END, f"  Hungarian → ${h_cost} | {h_time:.4f}s\n")
            text_box.insert(tk.END, f"  Faster by: {diff_time:.4f}s, Cheaper: {cheaper_algo} by ${diff_cost}\n")
            text_box.insert(tk.END, "-"*80 + "\n")

    text_box.config(state="disabled")
    tk.Button(history_window, text="Close", font=("Arial", 12), command=history_window.destroy).pack(pady=5)

# ---------------- GUI ---------------- #

window = tk.Tk()
window.title("Minimum Cost Game")
window.geometry("1050x760")
window.configure(bg=BG_COLOR)
window.resizable(False, False)

menu_frame = tk.Frame(window, bg=BG_COLOR)
game_frame = tk.Frame(window, bg=BG_COLOR)

# ---------------- BUTTON HOVER EFFECT ---------------- #
def on_enter(e):
    e.widget["background"] = BUTTON_HOVER

def on_leave(e):
    e.widget["background"] = BUTTON_COLOR

def style_button(btn):
    btn.config(
        bg=BUTTON_COLOR,
        fg="white",
        activebackground=BUTTON_HOVER,
        activeforeground="white",
        font=BUTTON_FONT,
        relief="flat",
        bd=0,
        padx=20,
        pady=10,
        cursor="hand2"
    )
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# ---------------- MENU SCREEN ---------------- #

menu_card = tk.Frame(menu_frame, bg=CARD_COLOR, bd=0, highlightthickness=0)
menu_card.place(relx=0.5, rely=0.5, anchor="center", width=650, height=420)

tk.Label(menu_card, text="Minimum Cost Game", font=TITLE_FONT, bg=CARD_COLOR, fg=TEXT_COLOR).pack(pady=(45, 10))
tk.Label(menu_card, text="Compare Greedy and Hungarian Algorithms\nfor optimal task assignment", font=SUBTITLE_FONT, bg=CARD_COLOR, fg=SECONDARY_TEXT, justify="center").pack(pady=(0, 35))

start_btn = tk.Button(menu_card, text="Start Game", command=lambda: [menu_frame.pack_forget(), game_frame.pack(fill="both", expand=True)])
style_button(start_btn)
start_btn.pack(pady=10)

exit_btn = tk.Button(menu_card, text="Exit", command=window.destroy)
style_button(exit_btn)
exit_btn.pack(pady=10)

menu_frame.pack(fill="both", expand=True)

# ---------------- GAME SCREEN ---------------- #

# Top bar with Back button
top_bar = tk.Frame(game_frame, bg=BG_COLOR)
top_bar.pack(fill="x", pady=(15, 5), padx=20)

back_btn_top = tk.Button(top_bar, text="← Back to Menu", command=lambda: [game_frame.pack_forget(), menu_frame.pack(fill="both", expand=True)])
style_button(back_btn_top)
back_btn_top.pack(anchor="w")

# Header
header_frame = tk.Frame(game_frame, bg=BG_COLOR)
header_frame.pack(pady=(5, 10))

tk.Label(header_frame, text="Minimum Cost Challenge", font=TITLE_FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack()
tk.Label(header_frame, text="Enter a task count and compare the two algorithms", font=SUBTITLE_FONT, bg=BG_COLOR, fg=SECONDARY_TEXT).pack(pady=(5, 0))

# Input Card
input_card = tk.Frame(game_frame, bg=CARD_COLOR)
input_card.pack(pady=15, padx=20, fill="x", ipadx=10, ipady=20)

tk.Label(input_card, text="Number of Tasks / Employees (50 - 100)", font=LABEL_FONT, bg=CARD_COLOR, fg=TEXT_COLOR).pack(pady=(0, 10))

num_tasks_entry = tk.Entry(input_card, font=("Arial", 16), justify="center", width=12, bd=0, relief="flat")
num_tasks_entry.pack(pady=5, ipady=6)

play_btn = tk.Button(input_card, text="Play Round", command=play_round)
style_button(play_btn)
play_btn.pack(pady=15)

# ---- View History Button ----
history_btn = tk.Button(input_card, text="View History", command=view_history)
style_button(history_btn)
history_btn.pack(pady=5)

# Results Card
results_card = tk.Frame(game_frame, bg=CARD_COLOR)
results_card.pack(padx=20, pady=10, fill="both", expand=True)

tk.Label(results_card, text="Results", font=("Arial", 18, "bold"), bg=CARD_COLOR, fg=ACCENT_COLOR).pack(pady=(15, 10))

# Bigger results area
result_box = tk.Text(results_card, width=100, height=24, bg=RESULT_BG, fg=SUCCESS_COLOR, font=RESULT_FONT, bd=0, relief="flat", insertbackground="white", wrap="word", padx=20, pady=20)
result_box.pack(padx=20, pady=(0, 20), fill="both", expand=True)

result_box.insert(tk.END, "Results will appear here after you play a round...")
result_box.config(state="disabled")

window.mainloop()