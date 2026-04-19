import tkinter as tk
from tkinter import messagebox
import random
import time
from collections import deque
import os

from PIL import Image, ImageTk   # ✅ FIX FOR IMAGE

from database import create_tables, get_connection
from ui_styles import *
from ui_screens import *

create_tables()

# ---------------- GLOBALS ---------------- #
PLAYER_ID = None
PLAYER_NAME = ""
BOARD_SIZE = 0

totalRounds = 5
currentRound = 1
score = 0

snakes = {}
ladders = {}
correct_answer = 0
bfs_time_global = 0
dfs_time_global = 0

# ---------------- ROOT ---------------- #
root = tk.Tk()
root.title("Snake & Ladder")

# ---------------- CENTER WINDOW ---------------- #
def center_window(win, width=700, height=700):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2) - 50)

    win.geometry(f"{width}x{height}+{x}+{y}")

center_window(root, 700, 700)

apply_theme(root)

main_frame = tk.Frame(root, bg=BG_COLOR)
main_frame.pack(fill="both", expand=True)

# ---------------- START SCREEN ---------------- #
def show_start():
    card = create_card(main_frame)

    tk.Label(card, text="Snake & Ladder",
             font=("Segoe UI", 22, "bold"),
             bg=CARD_COLOR, fg=TEXT).pack(pady=25)

    tk.Label(card, text="Enter Player Name",
             font=("Segoe UI", 12),
             bg=CARD_COLOR, fg=TEXT).pack(pady=10)

    global name_entry
    name_entry = tk.Entry(card,
        font=("Segoe UI", 14),
        width=25,
        justify="center"
    )
    name_entry.pack(pady=10)

    modern_button(card, "Start Game", start_game)

    # ---------------- IMAGE FIX (PIL) ---------------- #
    img_path = os.path.join("assets", "snake and ladder.png")

    try:
        image = Image.open(img_path)

        # resize for UI
        image = image.resize((450, 300))

        img = ImageTk.PhotoImage(image)

        img_label = tk.Label(card,
            image=img,
            bg=CARD_COLOR
        )
        img_label.image = img   # 🔥 KEEP REFERENCE
        img_label.pack(pady=20)

    except Exception as e:
        print("Image not loaded:", e)

# ---------------- BOARD SELECT ---------------- #
def show_board_select():
    card = create_card(main_frame)

    tk.Label(card, text=f"Welcome {PLAYER_NAME}",
             font=FONT_TITLE, bg=CARD_COLOR, fg=TEXT).pack(pady=20)

    for size in [6, 8, 10]:
        modern_button(card, f"{size} x {size}",
                      lambda s=size: select_board(s))

# ---------------- BOARD SCREEN ---------------- #
def show_board():
    card = create_card(main_frame)

    tk.Label(card,
        text=f"Round {currentRound}/5   Score: {score}",
        font=FONT_SUB,
        bg=CARD_COLOR,
        fg=TEXT
    ).pack(pady=10)

    frame = tk.Frame(card, bg=CARD_COLOR)
    frame.pack()

    draw_board(frame, BOARD_SIZE, snakes, ladders)

    modern_button(card, "Continue",
        lambda: show_question(correct_answer))

# ---------------- QUESTION SCREEN ---------------- #
def show_question(answer):
    card = create_card(main_frame)

    tk.Label(card, text="Minimum Dice Throws?",
             font=FONT_TITLE, bg=CARD_COLOR, fg=TEXT).pack(pady=20)

    opts = [answer - 1, answer, answer + 1]
    random.shuffle(opts)

    for o in opts:
        modern_button(card, str(o),
                      lambda x=o: check_answer(x, answer))

    tk.Button(card,
        text="Skip (+5 points)",
        bg="#4b5563",
        fg="white",
        relief="flat",
        command=skip
    ).pack(pady=10)

# ---------------- RESULT ---------------- #
def show_result():
    card = create_card(main_frame)

    tk.Label(card, text=f"Final Score: {score}/50",
             font=FONT_TITLE, bg=CARD_COLOR, fg=TEXT).pack(pady=30)

    res = "WIN" if score >= 40 else "DRAW" if score >= 20 else "LOSE"

    tk.Label(card, text=res,
             font=FONT_TITLE, bg=CARD_COLOR, fg=TEXT).pack()

    modern_button(card, "Exit", root.destroy)

# ---------------- GAME LOGIC ---------------- #
def start_game():
    global PLAYER_NAME, PLAYER_ID

    PLAYER_NAME = name_entry.get().strip()

    if PLAYER_NAME == "":
        messagebox.showerror("Error", "Enter your name!")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO players (name) VALUES (?)", (PLAYER_NAME,))
    conn.commit()
    PLAYER_ID = cursor.lastrowid
    conn.close()

    show_board_select()


def select_board(size):
    global BOARD_SIZE
    BOARD_SIZE = size
    initialize_game()


def initialize_game():
    global currentRound, score
    currentRound = 1
    score = 0
    start_round()


def start_round():
    global snakes, ladders, correct_answer
    global bfs_time_global, dfs_time_global

    snakes, ladders = generate_board(BOARD_SIZE)
    correct_answer, dfs_ans, bfs_time, dfs_time = run_algorithms(BOARD_SIZE)

    bfs_time_global = bfs_time
    dfs_time_global = dfs_time

    show_board()


def check_answer(ans, correct):
    global score

    is_correct = 1 if ans == correct else 0

    if is_correct:
        score += 10
        msg = "Correct!"
    else:
        msg = f"Wrong! Answer: {correct}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO game_rounds 
    (player_id, round_number, board_size, correct_answer, bfs_time, dfs_time, is_correct)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        PLAYER_ID,
        currentRound,
        BOARD_SIZE,
        correct,
        bfs_time_global,
        dfs_time_global,
        is_correct
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo("Result", msg)
    next_round()


def skip():
    global score
    score += 5
    next_round()


def next_round():
    global currentRound
    currentRound += 1

    if currentRound > totalRounds:
        show_result()
    else:
        start_round()

# ---------------- ALGORITHMS ---------------- #
def generate_board(n):
    total = n * n
    count = n - 2

    s, l = {}, {}
    used = set()

    while len(l) < count:
        a = random.randint(2, total - 1)
        b = random.randint(2, total - 1)
        if a < b and a not in used and b not in used:
            l[a] = b
            used.add(a); used.add(b)

    while len(s) < count:
        a = random.randint(2, total - 1)
        b = random.randint(2, total - 1)
        if a > b and a not in used and b not in used:
            s[a] = b
            used.add(a); used.add(b)

    return s, l


def bfs(start, end):
    q = deque([(start, 0)])
    visited = set()

    while q:
        node, dist = q.popleft()
        if node == end:
            return dist

        if node in visited:
            continue

        visited.add(node)

        for d in range(1, 7):
            nxt = node + d
            if nxt > end:
                continue

            if nxt in snakes: nxt = snakes[nxt]
            if nxt in ladders: nxt = ladders[nxt]

            q.append((nxt, dist + 1))

    return float("inf")


def dfs_limited(start, end, max_depth=15):
    stack = [(start, 0)]
    visited = set()

    while stack:
        node, depth = stack.pop()

        if node == end:
            return depth

        if depth >= max_depth:
            continue

        if node in visited:
            continue

        visited.add(node)

        for d in range(1, 7):
            nxt = node + d
            if nxt > end:
                continue

            if nxt in snakes: nxt = snakes[nxt]
            if nxt in ladders: nxt = ladders[nxt]

            stack.append((nxt, depth + 1))

    return float("inf")


def run_algorithms(n):
    start = 1
    end = n * n

    t1 = time.time()
    bfs_ans = bfs(start, end)
    bfs_time = time.time() - t1

    t2 = time.time()
    dfs_ans = dfs_limited(start, end)
    dfs_time = time.time() - t2

    return bfs_ans, dfs_ans, bfs_time, dfs_time

# ---------------- START APP ---------------- #
show_start()
root.mainloop()