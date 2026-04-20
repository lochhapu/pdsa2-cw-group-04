import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
import time
import copy

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("traffic_game.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_rounds (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id         INTEGER NOT NULL REFERENCES players(id),
            round_number      INTEGER NOT NULL,
            correct_answer    INTEGER NOT NULL,
            player_answer     INTEGER NOT NULL,
            result            TEXT    NOT NULL,
            ford_fulkerson_ms REAL    NOT NULL,
            edmonds_karp_ms   REAL    NOT NULL,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_or_create_player(name: str) -> int:
    """Return the player's id, inserting a new row only if the name is new."""
    conn = sqlite3.connect("traffic_game.db")
    try:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
        conn.commit()
        c.execute("SELECT id FROM players WHERE name = ?", (name,))
        row = c.fetchone()
        return row[0]
    except sqlite3.Error as e:
        messagebox.showerror("Database error", f"Could not look up player:\n{e}")
        return None
    finally:
        conn.close()


def save_round(player_name, round_no, correct, player, result, ff_ms, ek_ms):
    player_id = get_or_create_player(player_name)
    if player_id is None:
        return  # DB error already shown to the user
    conn = sqlite3.connect("traffic_game.db")
    try:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("""
            INSERT INTO game_rounds
                (player_id, round_number, correct_answer, player_answer,
                 result, ford_fulkerson_ms, edmonds_karp_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (player_id, round_no, correct, player, result, ff_ms, ek_ms))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Database error", f"Could not save round:\n{e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  GRAPH GENERATION
# ─────────────────────────────────────────────
EDGES = [
    ("A","B"), ("A","C"), ("A","D"),
    ("B","E"), ("B","F"),
    ("C","E"), ("C","F"),
    ("D","F"),
    ("E","G"), ("E","H"),
    ("F","H"),
    ("G","T"),
    ("H","T"),
]

def generate_graph():
    graph = {}
    caps  = {}
    for u, v in EDGES:
        w = random.randint(5, 15)
        caps[(u, v)] = w
        graph.setdefault(u, {})[v] = w
    return graph, caps


# ─────────────────────────────────────────────
#  FORD-FULKERSON
# ─────────────────────────────────────────────
def _dfs(res, u, sink, visited, bottleneck):
    if u == sink:
        return bottleneck
    visited.add(u)
    for v, cap in res.get(u, {}).items():
        if v not in visited and cap > 0:
            pushed = _dfs(res, v, sink, visited, min(bottleneck, cap))
            if pushed > 0:
                res[u][v] -= pushed
                res.setdefault(v, {})[u] = res.get(v, {}).get(u, 0) + pushed
                return pushed
    return 0

def ford_fulkerson(graph, source="A", sink="T"):
    res = copy.deepcopy(graph)
    max_flow = 0
    while True:
        f = _dfs(res, source, sink, set(), float("inf"))
        if f == 0:
            break
        max_flow += f
    return max_flow


# ─────────────────────────────────────────────
#  EDMONDS-KARP
# ─────────────────────────────────────────────
def edmonds_karp(graph, source="A", sink="T"):
    from collections import deque
    res = copy.deepcopy(graph)
    max_flow = 0

    while True:
        parent = {source: None}
        queue  = deque([source])
        while queue and sink not in parent:
            u = queue.popleft()
            for v, cap in res.get(u, {}).items():
                if v not in parent and cap > 0:
                    parent[v] = u
                    queue.append(v)

        if sink not in parent:
            break

        path_flow = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, res[u][v])
            v = u

        v = sink
        while v != source:
            u = parent[v]
            res[u][v] -= path_flow
            res.setdefault(v, {})[u] = res.get(v, {}).get(u, 0) + path_flow
            v = u

        max_flow += path_flow

    return max_flow


# ─────────────────────────────────────────────
#  NODE POSITIONS
# ─────────────────────────────────────────────
NODE_POS = {
    "A": (60,  140),
    "B": (190,  65),
    "C": (190, 140),
    "D": (190, 215),
    "E": (340,  90),
    "F": (340, 180),
    "G": (480,  65),
    "H": (480, 160),
    "T": (620, 120),
}


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
BG      = "#1e1e1e"
CARD    = "#2b2b2b"
ACCENT  = "#3d3d3d"
FG      = "#ffffff"
MUTED   = "#888888"
GREEN   = "#4caf50"
RED     = "#f44336"
BTN     = "#444444"
BTN_HOV = "#555555"


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class TrafficGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Traffic Flow – Maximum Flow Challenge")
        self.root.geometry("780x680")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.player_name = ""
        self.round_no    = 1
        self.score       = 0
        self.graph       = {}
        self.caps        = {}
        self.correct     = 0
        self.ff_ms       = 0.0
        self.ek_ms       = 0.0

        init_db()
        self.show_home()

    # ── helpers ──────────────────────────────
    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def header(self, parent):
        bar = tk.Frame(parent, bg=CARD, pady=8)
        bar.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(bar, text=f"Name: {self.player_name}",
                 font=("Segoe UI", 11), bg=CARD, fg=FG).pack(side="left",  padx=12)
        tk.Label(bar, text=f"Round {self.round_no}   Score: {self.score}",
                 font=("Segoe UI", 11), bg=CARD, fg=FG).pack(side="right", padx=12)

    def btn(self, parent, text, cmd, side=None, **kw):
        b = tk.Button(parent, text=text, command=cmd,
                      font=("Segoe UI", 11, "bold"),
                      bg=BTN, fg=FG, activebackground=BTN_HOV,
                      relief="flat", padx=16, pady=8, cursor="hand2", **kw)
        if side:
            b.pack(side=side, padx=6)
        else:
            b.pack(pady=6)
        return b

    # ── HOME ─────────────────────────────────
    def show_home(self):
        self.clear()

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True, fill="both")

        card = tk.Frame(outer, bg=CARD, padx=60, pady=44)
        card.pack(padx=36, pady=48, expand=True, fill="both")

        tk.Label(card, text="🚦", font=("Segoe UI", 52), bg=CARD).pack()

        tk.Label(card, text="Traffic Flow",
                 font=("Segoe UI", 26, "bold"), bg=CARD, fg=FG).pack(pady=(6, 0))

        tk.Label(card, text="Maximum flow challenge",
                 font=("Segoe UI", 12), bg=CARD, fg=MUTED).pack()

        tk.Label(card,
                 text="Analyze a live road network and guess the maximum\nnumber of vehicles that can travel from A to T.",
                 font=("Segoe UI", 11), bg=CARD, fg="#cccccc",
                 justify="center").pack(pady=22)

        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x", pady=(0, 4))

        tk.Label(form, text="Your Name:",
                 font=("Segoe UI", 11), bg=CARD, fg=FG).pack(anchor="w")

        self.name_var = tk.StringVar()
        e = tk.Entry(form, textvariable=self.name_var,
                     font=("Segoe UI", 13),
                     bg=ACCENT, fg=FG, insertbackground=FG, relief="flat")
        e.pack(fill="x", pady=(6, 0), ipady=6)
        e.focus()
        e.bind("<Return>", lambda _: self.start_game())

        tk.Button(card, text="Start Game →", command=self.start_game,
                  font=("Segoe UI", 11, "bold"),
                  bg=BTN, fg=FG, activebackground=BTN_HOV,
                  relief="solid", bd=1, padx=20, pady=8,
                  cursor="hand2").pack(pady=(18, 6))

        tk.Label(card, text="Round 1 of unlimited",
                 font=("Segoe UI", 10), bg=CARD, fg=MUTED,
                 relief="solid", bd=1, padx=10, pady=4).pack()

    def start_game(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter your name before starting.")
            return
        self.player_name = name
        self.round_no    = 1
        self.score       = 0
        self.show_round()

    # ── GAME ROUND ───────────────────────────
    def show_round(self):
        """Generate a brand-new graph then render it."""
        self.graph, self.caps = generate_graph()

        t0 = time.perf_counter()
        ff = ford_fulkerson(self.graph)
        self.ff_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        edmonds_karp(self.graph)
        self.ek_ms = (time.perf_counter() - t0) * 1000

        self.correct = ff
        self._render_round()

    def retry_round(self):
        """Re-show the SAME graph — round number stays unchanged."""
        self._render_round()

    def _render_round(self):
        """Draw the round UI using whatever is already in self.graph/caps/correct."""
        self.clear()
        self.header(self.root)

        g_card = tk.Frame(self.root, bg=CARD)
        g_card.pack(fill="x", padx=8, pady=4)
        tk.Label(g_card, text="Road network — A → T",
                 font=("Segoe UI", 11, "bold"), bg=CARD, fg=FG).pack(anchor="w", padx=12, pady=(8, 0))

        self.canvas = tk.Canvas(g_card, width=746, height=265, bg=CARD, highlightthickness=0)
        self.canvas.pack(padx=12, pady=6)
        self._draw_graph()

        tk.Label(g_card,
                 text="● Source (A)   ● Sink (T)   ● Intersection"
                      "     🔴 Low (5–8)   🟠 Medium (9–11)   🟢 High (12–15)",
                 font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(anchor="w", padx=12, pady=(0, 8))

        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=8, pady=4)

        a_card = tk.Frame(row, bg=CARD, padx=16, pady=14)
        a_card.pack(side="left", fill="both", expand=True, padx=(0, 4))

        tk.Label(a_card, text="Your answer",
                 font=("Segoe UI", 12, "bold"), bg=CARD, fg=FG).pack(anchor="w")
        tk.Label(a_card, text="Max vehicles from A → T",
                 font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(anchor="w")

        self.ans_var = tk.StringVar()
        e = tk.Entry(a_card, textvariable=self.ans_var,
                     font=("Segoe UI", 14),
                     bg=ACCENT, fg=FG, insertbackground=FG, relief="flat")
        e.pack(fill="x", pady=8, ipady=4)
        e.bind("<Return>", lambda _: self.submit())
        e.focus()

        self.btn(a_card, "Submit Answer", self.submit)

        al_card = tk.Frame(row, bg=CARD, padx=16, pady=14)
        al_card.pack(side="right", fill="both", expand=True, padx=(4, 0))

        tk.Label(al_card, text="Algorithms",
                 font=("Segoe UI", 12, "bold"), bg=CARD, fg=FG).pack(anchor="w")

        for name, ms in [("Ford-Fulkerson", self.ff_ms), ("Edmonds-Karp", self.ek_ms)]:
            r = tk.Frame(al_card, bg=CARD)
            r.pack(fill="x", pady=4)
            tk.Label(r, text=name, font=("Segoe UI", 11), bg=CARD, fg=FG).pack(side="left")
            tk.Label(r, text=f"● {ms:.3f} ms",
                     font=("Segoe UI", 11), bg=CARD, fg=GREEN).pack(side="right")
            ttk.Separator(al_card).pack(fill="x")

    # ── DRAW GRAPH ───────────────────────────
    def _draw_graph(self):
        c = self.canvas
        R = 22

        def edge_color(cap):
            if cap <= 8:
                return "#f44336"    # red = low / bottleneck
            elif cap <= 11:
                return "#ff9800"    # orange = medium
            else:
                return "#4caf50"    # green = high

        def arrow(u, v, cap):
            x1, y1 = NODE_POS[u]
            x2, y2 = NODE_POS[v]
            color = edge_color(cap)
            c.create_line(x1, y1, x2, y2, fill=color, width=2,
                          arrow=tk.LAST, arrowshape=(10, 12, 4))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 12
            c.create_text(mx, my, text=str(cap), fill=color,
                          font=("Segoe UI", 9, "bold"))

        for u, v in EDGES:
            arrow(u, v, self.caps[(u, v)])

        for node, (x, y) in NODE_POS.items():
            color = "#111111" if node in ("A", "T") else "#555555"
            c.create_oval(x - R, y - R, x + R, y + R,
                          fill=color, outline="#999", width=2)
            c.create_text(x, y, text=node, fill=FG,
                          font=("Segoe UI", 11, "bold"))

    # ── SUBMIT ───────────────────────────────
    def submit(self):
        raw = self.ans_var.get().strip()

        # ── Validation 1: empty input ──
        if not raw:
            messagebox.showwarning("No answer", "Please enter a number first.")
            return

        # ── Validation 2: must be a whole number ──
        try:
            player_ans = int(raw)
        except ValueError:
            messagebox.showerror(
                "Invalid input",
                f'"{raw}" is not a whole number.\nPlease enter a positive integer (e.g. 24).'
            )
            return

        # ── Validation 3: must be non-negative ──
        if player_ans < 0:
            messagebox.showerror(
                "Invalid input",
                "Max flow cannot be negative.\nPlease enter a positive integer."
            )
            return

        # ── Validation 4: sanity upper-bound ──
        MAX_POSSIBLE = 15 * len(EDGES)
        if player_ans > MAX_POSSIBLE:
            if not messagebox.askyesno(
                "Unusual answer",
                f"{player_ans} seems very high for this network.\nDo you want to submit it anyway?"
            ):
                return

        result = "win" if player_ans == self.correct else "lose"
        if result == "win":
            self.score += 1

        # ── DB save ──
        try:
            save_round(self.player_name, self.round_no, self.correct,
                       player_ans, result, self.ff_ms, self.ek_ms)
        except Exception as e:
            messagebox.showwarning(
                "Save failed",
                f"Your result couldn't be saved to the database:\n{e}\nThe game will continue."
            )

        self.show_result(player_ans, result)

    # ── RESULT ───────────────────────────────
    def show_result(self, player_ans, result):
        self.clear()
        self.header(self.root)

        card = tk.Frame(self.root, bg=CARD, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=8, pady=4)

        win = result == "win"
        banner_bg = "#1e3a1e" if win else "#3a1e1e"
        icon_txt  = "✓" if win else "✗"
        title_txt = "You got it!" if win else "Not quite"
        sub_txt   = (f"Correct answer: {self.correct} vehicles/min" if win
                     else f"Correct answer was: {self.correct} vehicles/min")

        banner = tk.Frame(card, bg=banner_bg, pady=20)
        banner.pack(fill="x", pady=(0, 16))

        tk.Label(banner, text=icon_txt,
                 font=("Segoe UI", 28, "bold"),
                 bg="#333", fg=FG, width=2, height=1).pack()
        tk.Label(banner, text=title_txt,
                 font=("Segoe UI", 22, "bold"), bg=banner_bg, fg=FG).pack(pady=4)
        tk.Label(banner, text=sub_txt,
                 font=("Segoe UI", 11), bg=banner_bg, fg=MUTED).pack()

        cmp = tk.Frame(card, bg=CARD)
        cmp.pack(fill="x", pady=10)
        for label, val in [("Your Answer", player_ans), ("Correct Answer", self.correct)]:
            f = tk.Frame(cmp, bg=CARD)
            f.pack(side="left", expand=True)
            tk.Label(f, text=str(val),
                     font=("Segoe UI", 30, "bold"), bg=CARD, fg=FG).pack()
            tk.Label(f, text=label,
                     font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack()

        ttk.Separator(card).pack(fill="x", pady=10)

        algo = tk.Frame(card, bg=CARD)
        algo.pack(fill="x", pady=6)
        for label, ms in [("Ford-Fulkerson", self.ff_ms), ("Edmonds-Karp", self.ek_ms)]:
            f = tk.Frame(algo, bg=CARD)
            f.pack(side="left", expand=True)
            tk.Label(f, text=f"{ms:.3f} ms",
                     font=("Segoe UI", 22, "bold"), bg=CARD, fg=FG).pack()
            tk.Label(f, text=label,
                     font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack()

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(pady=20)

        if not win:
            self.btn(btn_row, "Try Again", self.retry_round, side="left")

        def next_round():
            self.round_no += 1
            self.show_round()

        self.btn(btn_row, "Next Round →", next_round, side="left")
        self.btn(btn_row, "Main Menu", self.show_home, side="left")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    TrafficGame(root)
    root.mainloop()