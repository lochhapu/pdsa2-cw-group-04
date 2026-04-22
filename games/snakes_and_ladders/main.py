import tkinter as tk
from tkinter import messagebox
import random
import time
from collections import deque
import os

from PIL import Image, ImageTk
from chart_analysis import add_round_data, round_data

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

board_timer = 20
timer_running = False

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

    # ---------------- TITLE ---------------- #
    tk.Label(card, text="Snakes & Ladders",
             font=("Segoe UI", 46, "bold"),
             bg=CARD_COLOR, fg=TEXT).pack(pady=(20, 5))

    # ---------------- SUBTITLE ---------------- #
    tk.Label(card,
        text="Welcome! Let's start your adventure",
        font=("Segoe UI", 16),
        bg=CARD_COLOR,
        fg="#86efac"   # light green
    ).pack(pady=(0, 20))

    # ---------------- INPUT FRAME (for border effect) ---------------- #
    input_frame = tk.Frame(card,
        bg="#10b981",   # border color (green)
        padx=2,
        pady=2
    )
    input_frame.pack(pady=10)

    # ---------------- ENTRY ---------------- #
    global name_entry
    name_entry = tk.Entry(input_frame,
        font=("Segoe UI", 14),
        width=28,
        justify="center",
        bd=0,
        bg="#ecfdf5",   # light green background
        fg="black"
    )
    name_entry.pack(ipady=8)   # increase height

    # ---------------- PLACEHOLDER ---------------- #
    def on_focus_in(e):
        if name_entry.get() == "Enter your name here...":
            name_entry.delete(0, tk.END)
            name_entry.config(fg="black")

    def on_focus_out(e):
        if name_entry.get() == "":
            name_entry.insert(0, "Enter your name here...")
            name_entry.config(fg="gray")

    name_entry.insert(0, "Enter your name here...")
    name_entry.config(fg="gray")

    name_entry.bind("<FocusIn>", on_focus_in)
    name_entry.bind("<FocusOut>", on_focus_out)

    # ---------------- BUTTON (ROUNDED STYLE SIMULATION) ---------------- #
    btn_frame = tk.Frame(card,
        bg="#059669",   # darker green border
        padx=1,
        pady=1
    )
    btn_frame.pack(pady=15)

    tk.Button(btn_frame,
        text="Start Game",
        font=("Segoe UI", 13, "bold"),
        bg=PRIMARY,
        fg="white",
        activebackground="#059669",
        relief="flat",
        width=18,
        height=2,
        cursor="hand2",
        command=start_game
    ).pack()

    # ---------------- IMAGE ---------------- #
    img_path = os.path.join("assets", "snake and ladder.png")

    try:
        image = Image.open(img_path)
        image = image.resize((380, 260))

        img = ImageTk.PhotoImage(image)

        img_label = tk.Label(card,
            image=img,
            bg=CARD_COLOR
        )
        img_label.image = img
        img_label.pack(pady=20)

    except Exception as e:
        print("Image not loaded:", e)

# ---------------- BOARD SELECT ---------------- #
def show_board_select():
    card = create_card(main_frame)

    # ---------------- TITLE ---------------- #
    tk.Label(card, text="Choose Board Size",
             font=("Segoe UI", 46, "bold"),
             bg=CARD_COLOR, fg=TEXT).pack(pady=(20, 5))

    # ---------------- SUBTITLE ---------------- #
    tk.Label(card,
        text="Select your difficulty level",
        font=("Segoe UI", 16),
        bg=CARD_COLOR,
        fg="#86efac"
    ).pack(pady=(0, 25))

    # ---------------- CONTAINER ---------------- #
    container = tk.Frame(card, bg=CARD_COLOR)
    container.pack()

    # ---------------- BUTTON CREATOR ---------------- #
    def create_option(parent, text_main, text_sub, size):

        outer = tk.Frame(parent,
            bg="#10b981",   # border color
            width=260,
            height=100
        )
        outer.pack(pady=12)
        outer.pack_propagate(False)  # 🔥 FORCE SAME SIZE

        btn = tk.Frame(outer,
            bg="white",
            cursor="hand2"
        )
        btn.pack(fill="both", expand=True, padx=2, pady=2)

        # main text
        tk.Label(btn,
            text=text_main,
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="black"
        ).pack(pady=(15, 0))

        # sub text
        tk.Label(btn,
            text=text_sub,
            font=("Segoe UI", 14),
            bg="white",
            fg="#10b981"
        ).pack()

        # click event (applies to whole card)
        btn.bind("<Button-1>", lambda e: select_board(size))
        for child in btn.winfo_children():
            child.bind("<Button-1>", lambda e: select_board(size))

        # hover effect
        def on_enter(e):
            btn.config(bg="#ecfdf5")

        def on_leave(e):
            btn.config(bg="white")

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # ---------------- OPTIONS ---------------- #
    create_option(container, "Easy", "6 x 6 Board", 6)
    create_option(container, "Medium", "8 x 8 Board", 8)
    create_option(container, "Hard", "10 x 10 Board", 10)

# ---------------- BOARD SCREEN ---------------- #
def show_board():
    global board_timer, timer_running

    card = create_card(main_frame)

    # ---------------- TOP CHIPS ---------------- #
    top_frame = tk.Frame(card, bg=CARD_COLOR)
    top_frame.pack(pady=10)

    def create_chip(parent, text):
        outer = tk.Frame(parent, bg="#10b981", padx=2, pady=2)
        outer.pack(side="left", padx=8)

        inner = tk.Label(outer,
            text=text,
            bg="#ecfdf5",
            fg="#065f46",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=6
        )
        inner.pack()

    create_chip(top_frame, f"Round {currentRound}/5")
    create_chip(top_frame, f"Score {score}")

    # ---------------- TIMER DISPLAY ---------------- #
    timer_label = tk.Label(card,
        text=f"Time Left: {board_timer}s",
        font=("Segoe UI", 16, "bold"),
        bg=CARD_COLOR,
        fg="#f59e0b"
    )
    timer_label.pack(pady=5)

    # ---------------- BOARD ---------------- #
    frame = tk.Frame(card, bg=CARD_COLOR)
    frame.pack()

    draw_board(frame, BOARD_SIZE, snakes, ladders)

    # ---------------- CONTINUE BUTTON ---------------- #
    def go_next():
        global timer_running
        timer_running = False
        show_question(correct_answer)

    modern_button(card, "Continue", go_next)

    # ---------------- COUNTDOWN FUNCTION ---------------- #
    def countdown():
        global board_timer, timer_running

        if not timer_running:
            timer_running = True

        if board_timer > 0:
            timer_label.config(text=f"Time Left: {board_timer}s")
            board_timer -= 1
            card.after(1000, countdown)
        else:
            # reset timer for next round
            board_timer = 20
            timer_running = False
            show_question(correct_answer)

    # start countdown
    countdown()

# ---------------- QUESTION SCREEN ---------------- #
def show_question(answer):
    card = create_card(main_frame)

    # ---------------- DICE IMAGE ---------------- #
    img_path = os.path.join("assets", "dice.png")

    try:
        dice_img = Image.open(img_path)
        dice_img = dice_img.resize((80, 80))

        dice = ImageTk.PhotoImage(dice_img)

        dice_label = tk.Label(card,
            image=dice,
            bg=CARD_COLOR
        )
        dice_label.image = dice  # keep reference
        dice_label.pack(pady=(10, 5))

    except Exception as e:
        print("Dice image not loaded:", e)

    # ---------------- TITLE ---------------- #
    tk.Label(card,
        text="Minimum Dice Throws?",
        font=("Segoe UI", 30, "bold"),
        bg=CARD_COLOR,
        fg=TEXT
    ).pack(pady=10)

    # ---------------- SMART OPTIONS ---------------- #
    options = set()
    options.add(answer)

    while len(options) < 3:
        offset = random.choice([-4, -3, -2, 2, 3, 4])
        wrong = answer + offset

        if wrong > 0:
            options.add(wrong)

    opts = list(options)
    random.shuffle(opts)

    # ---------------- OPTION BUTTONS ---------------- #
    for o in opts:
        outer = tk.Frame(card, bg="#10b981", padx=2, pady=2)
        outer.pack(pady=8)

        btn = tk.Button(outer,
            text=str(o),
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="black",
            width=12,
            height=2,
            relief="flat",
            cursor="hand2",
            command=lambda x=o: check_answer(x, answer)
        )
        btn.pack()

        # hover effect
        def on_enter(e, b=btn):
            b.config(bg="#ecfdf5")

        def on_leave(e, b=btn):
            b.config(bg="white")

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # ---------------- SKIP BUTTON ---------------- #
    tk.Button(card,
        text="Skip (+5 points)",
        font=("Segoe UI", 11),
        bg="#4b5563",
        fg="white",
        relief="flat",
        cursor="hand2",
        command=skip
    ).pack(pady=15)

# ---------------- DETAILED RESULTS ---------------- #
def show_detailed_results():
    card = create_card(main_frame)

    tk.Label(card,
        text="Detailed Round Results",
        font=("Segoe UI", 28, "bold"),
        bg=CARD_COLOR,
        fg=TEXT
    ).pack(pady=20)

    table_frame = tk.Frame(card, bg=CARD_COLOR)
    table_frame.pack(pady=10)

    headers = ["Round", "BFS Time (s)", "DFS Time (s)"]

    for col, h in enumerate(headers):
        tk.Label(table_frame,
            text=h,
            font=("Segoe UI", 12, "bold"),
            bg="#10b981",
            fg="white",
            width=18,
            pady=8
        ).grid(row=0, column=col, padx=2, pady=2)

    from chart_analysis import round_data

    total_bfs = 0
    total_dfs = 0

    for i, (round_no, bfs_t, dfs_t) in enumerate(round_data, start=1):

        total_bfs += bfs_t
        total_dfs += dfs_t

        values = [
            round_no,
            f"{bfs_t:.6f}",
            f"{dfs_t:.6f}"
        ]

        for col, val in enumerate(values):
            tk.Label(table_frame,
                text=val,
                font=("Segoe UI", 11),
                bg="#ecfdf5" if i % 2 == 0 else "white",
                fg="black",
                width=18,
                pady=6
            ).grid(row=i, column=col, padx=2, pady=2)

    # ---------------- TOTAL ROW ---------------- #
    row_index = len(round_data) + 1

    tk.Label(table_frame,
        text="TOTAL",
        font=("Segoe UI", 11, "bold"),
        bg="#10b981",
        fg="white",
        width=18,
        pady=8
    ).grid(row=row_index, column=0, padx=2, pady=2)

    tk.Label(table_frame,
        text=f"{total_bfs:.6f}",
        font=("Segoe UI", 11, "bold"),
        bg="#10b981",
        fg="white",
        width=18,
        pady=8
    ).grid(row=row_index, column=1, padx=2, pady=2)

    tk.Label(table_frame,
        text=f"{total_dfs:.6f}",
        font=("Segoe UI", 11, "bold"),
        bg="#10b981",
        fg="white",
        width=18,
        pady=8
    ).grid(row=row_index, column=2, padx=2, pady=2)

    tk.Button(card,
        text="Back",
        font=("Segoe UI", 11, "bold"),
        bg="#4b5563",
        fg="white",
        relief="flat",
        command=show_result
    ).pack(pady=20)

# ---------------- RESULT ---------------- #
def show_result():
    card = create_card(main_frame)

    # ---------------- RESULT STATE ---------------- #
    if score >= 40:
        result_text = "YOU WIN!"
        color = "#22c55e"
        emoji = "🏆"
    elif score >= 20:
        result_text = "IT'S A DRAW!"
        color = "#f59e0b"
        emoji = "🤝"
    else:
        result_text = "YOU LOSE!"
        color = "#ef4444"
        emoji = "💀"

    # ---------------- GAME OVER ---------------- #
    tk.Label(card,
        text="Game Over",
        font=("Segoe UI", 36, "bold"),
        bg=CARD_COLOR,
        fg=TEXT
    ).pack(pady=(25, 10))

    # ---------------- ICON ---------------- #
    tk.Label(card,
    text=emoji,
    font=("Segoe UI Emoji", 60),
    bg=CARD_COLOR,
    fg=color   # 🔥 match result color
    ).pack(pady=(0, 10))

    # ---------------- RESULT TEXT ---------------- #
    tk.Label(card,
        text=result_text,
        font=("Segoe UI", 24, "bold"),
        bg=CARD_COLOR,
        fg=color
    ).pack(pady=(0, 15))

    # ---------------- PLAYER INFO ---------------- #
    tk.Label(card,
        text=f"Player: {PLAYER_NAME}",
        font=("Segoe UI", 16),
        bg=CARD_COLOR,
        fg=TEXT
    ).pack(pady=(5, 5))

    tk.Label(card,
        text=f"Score: {score}/50",
        font=("Segoe UI", 16, "bold"),
        bg=CARD_COLOR,
        fg="#86efac"
    ).pack(pady=(0, 25))

    # ---------------- CHART ---------------- #
    #show_time_chart()

    # ---------------- BUTTON CONTAINER ---------------- #
    btn_container = tk.Frame(card, bg=CARD_COLOR)
    btn_container.pack(pady=15)

    # ---------------- SHOW TABLE BUTTON ---------------- #
    tk.Button(btn_container,
        text="Show Detailed Results",
        font=("Segoe UI", 12, "bold"),
        bg="#3b82f6",
        fg="white",
        relief="flat",
        cursor="hand2",
        width=18,
        height=2,
        command=show_detailed_results
    ).pack(pady=6)

    # ---------------- PLAY AGAIN BUTTON ---------------- #
    tk.Button(btn_container,
        text="Play Again",
        font=("Segoe UI", 12, "bold"),
        bg="#10b981",
        fg="white",
        activebackground="#059669",
        relief="flat",
        cursor="hand2",
        width=18,
        height=2,
        command=show_board_select
    ).pack(pady=6)

    # ---------------- EXIT BUTTON ---------------- #
    tk.Button(btn_container,
        text="Exit Game",
        font=("Segoe UI", 12, "bold"),
        bg="#ef4444",
        fg="white",
        activebackground="#b91c1c",
        relief="flat",
        cursor="hand2",
        width=18,
        height=2,
        command=root.destroy
    ).pack(pady=6)

# ---------------- GAME LOGIC ---------------- #
def start_game():
    global PLAYER_NAME, PLAYER_ID

    PLAYER_NAME = name_entry.get().strip()

    # ---------------- VALIDATION FIX ---------------- #
    if PLAYER_NAME == "" or PLAYER_NAME == "Enter your name here...":
        messagebox.showerror("Error", "Please enter your name!")
        return

    # extra safety (spaces only)
    if PLAYER_NAME.strip() == "":
        messagebox.showerror("Error", "Please enter a valid name!")
        return

    # ---------------- DATABASE INSERT ---------------- #
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO players (name) VALUES (?)", (PLAYER_NAME,))
    conn.commit()

    PLAYER_ID = cursor.lastrowid

    conn.close()

    # ---------------- NEXT SCREEN ---------------- #
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

    add_round_data(currentRound, bfs_time, dfs_time)

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