import tkinter as tk
from tkinter import messagebox
import random
import time
from collections import deque

from database import create_tables, get_connection

create_tables()

PLAYER_ID = None
bfs_time_global = 0
dfs_time_global = 0

# ---------------- GLOBALS ---------------- #
PLAYER_NAME = ""
BOARD_SIZE = 0

totalRounds = 5
currentRound = 1
score = 0

snakes = {}
ladders = {}
correct_answer = 0

# ---------------- START ---------------- #
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

    root.withdraw()
    open_board_selection()


# ---------------- BOARD SELECT ---------------- #
def open_board_selection():
    window = tk.Toplevel(root)
    window.title("Select Board")
    window.geometry("400x350")

    tk.Label(window, text=f"Welcome {PLAYER_NAME}", font=("Arial", 14)).pack(pady=20)

    def select(size):
        global BOARD_SIZE
        BOARD_SIZE = size
        window.destroy()
        initialize_game()

    for size in [6, 8, 10]:
        tk.Button(window, text=f"{size} x {size}", width=15,
                  command=lambda s=size: select(s)).pack(pady=10)


# ---------------- INIT ---------------- #
def initialize_game():
    global currentRound, score
    currentRound = 1
    score = 0
    start_round()


# ---------------- ROUND ---------------- #
def start_round():
    global snakes, ladders, correct_answer
    global bfs_time_global, dfs_time_global

    snakes, ladders = generate_board(BOARD_SIZE)

    correct_answer, dfs_ans, bfs_time, dfs_time = run_algorithms(BOARD_SIZE)

    bfs_time_global = bfs_time
    dfs_time_global = dfs_time

    show_board()


# ---------------- BOARD GEN ---------------- #
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


# ---------------- BFS ---------------- #
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

            if nxt in snakes:
                nxt = snakes[nxt]
            if nxt in ladders:
                nxt = ladders[nxt]

            q.append((nxt, dist + 1))

    return float("inf")


# ---------------- SAFE DFS (ITERATIVE) ---------------- #
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

            if nxt in snakes:
                nxt = snakes[nxt]
            if nxt in ladders:
                nxt = ladders[nxt]

            stack.append((nxt, depth + 1))

    return float("inf")


# ---------------- RUN ALGOS ---------------- #
def run_algorithms(n):
    start = 1
    end = n * n

    t1 = time.time()
    bfs_ans = bfs(start, end)
    bfs_time = time.time() - t1

    t2 = time.time()
    dfs_ans = dfs_limited(start, end, 15)
    dfs_time = time.time() - t2

    print("BFS:", bfs_ans, "DFS:", dfs_ans)

    return bfs_ans, dfs_ans, bfs_time, dfs_time


# ---------------- BOARD UI ---------------- #
def show_board():
    window = tk.Toplevel(root)
    window.title("Board")
    window.geometry("600x650")

    tk.Label(window, text=f"Round {currentRound}/5   Score: {score}",
             font=("Arial", 12)).pack()

    frame = tk.Frame(window)
    frame.pack()

    draw_board(frame, BOARD_SIZE)

    tk.Button(window, text="Continue",
              command=lambda: [window.destroy(), show_question(correct_answer)]
              ).pack(pady=20)


# ---------------- DRAW BOARD ---------------- #
def draw_board(frame, n):
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
            txt = str(val)
            color = "#333"

            if val in ladders:
                txt += " 🪜"
                color = "green"
            elif val in snakes:
                txt += " 🐍"
                color = "red"

            tk.Label(frame, text=txt, width=6, height=3,
                     bg=color, fg="white").grid(row=r, column=c)


# ---------------- QUESTION ---------------- #
def show_question(answer):
    window = tk.Toplevel(root)
    window.title("Question")
    window.geometry("400x300")

    opts = [answer - 1, answer, answer + 1]
    random.shuffle(opts)

    tk.Label(window, text="Minimum dice throws?",
             font=("Arial", 12)).pack(pady=20)

    def check(ans):
        global score

        is_correct = 1 if ans == answer else 0

        if is_correct:
            score += 10
            msg = "Correct!"
        else:
            msg = f"Wrong! Answer: {answer}"

        # SAVE TO DATABASE
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
            answer,
            bfs_time_global,
            dfs_time_global,
            is_correct
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo("Result", msg)
        window.destroy()
        next_round()

    # buttons MUST be outside check()
    for o in opts:
        tk.Button(window, text=str(o),
                  command=lambda x=o: check(x)).pack(pady=5)

    tk.Button(window, text="Skip",
              command=lambda: skip(window)).pack(pady=10)


# ---------------- SKIP ---------------- #
def skip(window):
    global score
    score += 5
    window.destroy()
    next_round()


# ---------------- NEXT ROUND ---------------- #
def next_round():
    global currentRound
    currentRound += 1

    if currentRound > totalRounds:
        show_result()
    else:
        start_round()


# ---------------- FINAL ---------------- #
def show_result():
    window = tk.Toplevel(root)
    window.title("Result")
    window.geometry("400x300")

    tk.Label(window, text=f"Final Score: {score}/50",
             font=("Arial", 14)).pack(pady=30)

    if score >= 40:
        res = "WIN"
    elif score >= 20:
        res = "DRAW"
    else:
        res = "LOSE"

    tk.Label(window, text=res, font=("Arial", 16)).pack()

    tk.Button(window, text="Exit", command=root.destroy).pack(pady=20)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO game_results (player_id, final_score, result)
    VALUES (?, ?, ?)
    """, (PLAYER_ID, score, res))

    conn.commit()
    conn.close()


def dump_data():
    conn = get_connection()
    cursor = conn.cursor()

    print("\n--- PLAYERS ---")
    for row in cursor.execute("SELECT * FROM players"):
        print(row)

    print("\n--- ROUNDS ---")
    for row in cursor.execute("SELECT * FROM game_rounds"):
        print(row)

    print("\n--- RESULTS ---")
    for row in cursor.execute("SELECT * FROM game_results"):
        print(row)

    conn.close()


# ---------------- MAIN ---------------- #
root = tk.Tk()
root.title("Snake & Ladder")
root.geometry("400x300")

tk.Label(root, text="Snake & Ladder", font=("Arial", 16)).pack(pady=20)

name_entry = tk.Entry(root)
name_entry.pack()

tk.Button(root, text="Start", command=start_game).pack(pady=20)

root.mainloop()