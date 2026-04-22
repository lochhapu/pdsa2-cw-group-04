import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
import time
import copy
import math

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS correct_answers (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name    TEXT NOT NULL,
            correct_answer INTEGER NOT NULL,
            round_number   INTEGER NOT NULL,
            recorded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_or_create_player(name: str) -> int:
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
        return
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

        if result == "win":
            c.execute("""
                INSERT INTO correct_answers (player_name, correct_answer, round_number)
                VALUES (?, ?, ?)
            """, (player_name, correct, round_no))

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
    if source == sink:
        return 0
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
    if source == sink:
        return 0
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
    "A": (65,  150),
    "B": (200,  70),
    "C": (200, 150),
    "D": (200, 230),
    "E": (360,  95),
    "F": (360, 200),
    "G": (510,  70),
    "H": (510, 175),
    "T": (650, 130),
}


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
BG       = "#0d0f14"
CARD     = "#141720"
CARD2    = "#1a1d27"
BORDER   = "#252836"
ACCENT   = "#1e2130"
FG       = "#e8eaf2"
FG2      = "#9498b0"
FG3      = "#5a5e78"

AMBER    = "#f0a500"
AMBER_DK = "#c98800"
GREEN    = "#22c97a"
RED      = "#e84855"
ORANGE   = "#f07830"

EDGE_LOW = "#e84855"
EDGE_MID = "#f0a500"
EDGE_HI  = "#22c97a"

BTN_PRI    = "#f0a500"
BTN_PRI_FG = "#0d0f14"
BTN_SEC    = "#1e2130"
BTN_HOV    = "#252836"

NODE_SRC  = "#f0a500"
NODE_SINK = "#f0a500"
NODE_INT  = "#1e2130"


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class TrafficGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Traffic Flow  ·  Maximum Flow Challenge")
        self.root.geometry("820x700")
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

    def divider(self, parent, padx=0, pady=6):
        f = tk.Frame(parent, bg=BORDER, height=1)
        f.pack(fill="x", padx=padx, pady=pady)

    def label(self, parent, text, size=11, bold=False, color=FG, **kw):
        weight = "bold" if bold else "normal"
        return tk.Label(parent, text=text,
                        font=("Consolas", size, weight),
                        bg=parent.cget("bg"), fg=color, **kw)

    def header(self, parent):
        bar = tk.Frame(parent, bg=CARD, pady=0, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=CARD)
        left.pack(side="left", padx=18, fill="y")
        tk.Label(left, text="●", font=("Consolas", 9), bg=CARD,
                 fg=AMBER).pack(side="left", padx=(0, 6))
        tk.Label(left, text=self.player_name,
                 font=("Consolas", 12, "bold"), bg=CARD, fg=FG).pack(side="left")

        right = tk.Frame(bar, bg=CARD)
        right.pack(side="right", padx=18, fill="y")
        tk.Label(right, text=f"Round {self.round_no}",
                 font=("Consolas", 11), bg=CARD, fg=FG2).pack(side="left", padx=(0, 18))
        tk.Label(right, text="Score",
                 font=("Consolas", 10), bg=CARD, fg=FG3).pack(side="left", padx=(0, 6))
        tk.Label(right, text=str(self.score),
                 font=("Consolas", 13, "bold"), bg=CARD, fg=AMBER).pack(side="left")

        sep = tk.Frame(parent, bg=BORDER, height=1)
        sep.pack(fill="x")

    def _make_btn(self, parent, text, cmd, primary=False, side=None, **kw):
        bg_c  = BTN_PRI  if primary else BTN_SEC
        fg_c  = BTN_PRI_FG if primary else FG
        hov_c = AMBER_DK if primary else BTN_HOV
        b = tk.Button(parent, text=text, command=cmd,
                      font=("Consolas", 10, "bold"),
                      bg=bg_c, fg=fg_c,
                      activebackground=hov_c, activeforeground=fg_c,
                      relief="flat", padx=20, pady=10,
                      cursor="hand2", **kw)
        if side:
            b.pack(side=side, padx=5)
        else:
            b.pack(pady=5)
        return b

    # ── HOME ─────────────────────────────────
    def show_home(self):
        self.clear()

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True, fill="both", padx=30, pady=30)

        card = tk.Frame(outer, bg=CARD, bd=0, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(expand=True, fill="both")

        accent_bar = tk.Frame(card, bg=AMBER, height=3)
        accent_bar.pack(fill="x")

        inner = tk.Frame(card, bg=CARD, padx=60, pady=36)
        inner.pack(expand=True, fill="both")

        icon_frame = tk.Frame(inner, bg=CARD)
        icon_frame.pack(pady=(0, 6))
        tk.Label(icon_frame, text="🚦", font=("Segoe UI Emoji", 46),
                 bg=CARD).pack()

        tk.Label(inner, text="Traffic Flow",
                 font=("Consolas", 28, "bold"), bg=CARD, fg=FG).pack()
        tk.Label(inner, text="M A X I M U M   F L O W   C H A L L E N G E",
                 font=("Consolas", 9), bg=CARD, fg=FG3).pack(pady=(3, 0))

        self.divider(inner, padx=80, pady=20)

        tk.Label(inner,
                 text="Analyze a live road network and estimate the maximum\n"
                      "number of vehicles that can travel from  A  →  T.",
                 font=("Consolas", 10), bg=CARD, fg=FG2,
                 justify="center").pack(pady=(0, 24))

        form = tk.Frame(inner, bg=CARD)
        form.pack(fill="x", padx=40)

        tk.Label(form, text="PLAYER NAME",
                 font=("Consolas", 9, "bold"), bg=CARD, fg=FG3).pack(anchor="w", pady=(0, 5))

        entry_frame = tk.Frame(form, bg=AMBER, bd=0)
        entry_frame.pack(fill="x")
        entry_inner = tk.Frame(entry_frame, bg=ACCENT, bd=0)
        entry_inner.pack(fill="x", padx=1, pady=1)

        self.name_var = tk.StringVar()
        e = tk.Entry(entry_inner, textvariable=self.name_var,
                     font=("Consolas", 13),
                     bg=ACCENT, fg=FG, insertbackground=AMBER,
                     relief="flat", bd=0)
        e.pack(fill="x", ipady=10, padx=12)
        e.focus()
        e.bind("<Return>", lambda _: self.start_game())

        tk.Frame(inner, bg=CARD, height=16).pack()

        btn_frame = tk.Frame(inner, bg=CARD, padx=40)
        btn_frame.pack(fill="x", padx=40)
        start_btn = tk.Button(btn_frame, text="Start Game  →",
                              command=self.start_game,
                              font=("Consolas", 12, "bold"),
                              bg=AMBER, fg=BTN_PRI_FG,
                              activebackground=AMBER_DK, activeforeground=BTN_PRI_FG,
                              relief="flat", pady=12, cursor="hand2")
        start_btn.pack(fill="x")

        tk.Frame(inner, bg=CARD, height=12).pack()
        tk.Label(inner, text="∞  unlimited rounds",
                 font=("Consolas", 9), bg=CARD, fg=FG3).pack()

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
        self._render_round()

    def _render_round(self):
        self.clear()
        self.header(self.root)

        g_outer = tk.Frame(self.root, bg=BG)
        g_outer.pack(fill="x", padx=12, pady=(10, 4))

        g_card = tk.Frame(g_outer, bg=CARD, highlightthickness=1,
                          highlightbackground=BORDER)
        g_card.pack(fill="x")

        g_title_row = tk.Frame(g_card, bg=CARD)
        g_title_row.pack(fill="x", padx=16, pady=(12, 4))

        tk.Label(g_title_row, text="Road Network",
                 font=("Consolas", 12, "bold"), bg=CARD, fg=FG).pack(side="left")
        tk.Label(g_title_row, text="A  →  T",
                 font=("Consolas", 11), bg=CARD, fg=AMBER).pack(side="left", padx=12)

        self.canvas = tk.Canvas(g_card, width=790, height=280,
                                bg=CARD2, highlightthickness=0)
        self.canvas.pack(padx=12, pady=(0, 6))
        self._draw_graph()

        leg = tk.Frame(g_card, bg=CARD)
        leg.pack(fill="x", padx=16, pady=(0, 10))
        for dot, label in [("●", "Source / Sink"), ("●", "Intersection"),
                            ("●", "Low  5–8"), ("●", "Med  9–11"), ("●", "High  12–15")]:
            colors = [AMBER, FG3, EDGE_LOW, EDGE_MID, EDGE_HI]
            idx    = [("●", "Source / Sink"), ("●", "Intersection"),
                      ("●", "Low  5–8"), ("●", "Med  9–11"), ("●", "High  12–15")].index((dot, label))
            f = tk.Frame(leg, bg=CARD)
            f.pack(side="left", padx=(0, 16))
            tk.Label(f, text="●", font=("Consolas", 8), bg=CARD,
                     fg=colors[idx]).pack(side="left")
            tk.Label(f, text=" " + label, font=("Consolas", 8), bg=CARD,
                     fg=FG3).pack(side="left")

        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        a_outer = tk.Frame(row, bg=BG)
        a_outer.pack(side="left", fill="both", expand=True, padx=(0, 5))
        a_card = tk.Frame(a_outer, bg=CARD, highlightthickness=1,
                          highlightbackground=BORDER)
        a_card.pack(fill="both", expand=True)

        a_inner = tk.Frame(a_card, bg=CARD, padx=18, pady=16)
        a_inner.pack(fill="both", expand=True)

        tk.Label(a_inner, text="YOUR ANSWER",
                 font=("Consolas", 9, "bold"), bg=CARD, fg=FG3).pack(anchor="w")
        tk.Label(a_inner, text="Max vehicles from A → T",
                 font=("Consolas", 11, "bold"), bg=CARD, fg=FG).pack(anchor="w", pady=(2, 14))

        ef = tk.Frame(a_inner, bg=AMBER)
        ef.pack(fill="x")
        ei = tk.Frame(ef, bg=ACCENT)
        ei.pack(fill="x", padx=1, pady=1)

        self.ans_var = tk.StringVar()
        e = tk.Entry(ei, textvariable=self.ans_var,
                     font=("Consolas", 16, "bold"),
                     bg=ACCENT, fg=AMBER, insertbackground=AMBER,
                     relief="flat", bd=0, justify="center")
        e.pack(fill="x", ipady=12)
        e.bind("<Return>", lambda _: self.submit())
        e.focus()

        tk.Frame(a_inner, bg=CARD, height=12).pack()

        sb = tk.Button(a_inner, text="Submit Answer",
                       command=self.submit,
                       font=("Consolas", 11, "bold"),
                       bg=AMBER, fg=BTN_PRI_FG,
                       activebackground=AMBER_DK, activeforeground=BTN_PRI_FG,
                       relief="flat", pady=10, cursor="hand2")
        sb.pack(fill="x")

        al_outer = tk.Frame(row, bg=BG)
        al_outer.pack(side="right", fill="both", expand=True, padx=(5, 0))
        al_card = tk.Frame(al_outer, bg=CARD, highlightthickness=1,
                           highlightbackground=BORDER)
        al_card.pack(fill="both", expand=True)

        al_inner = tk.Frame(al_card, bg=CARD, padx=18, pady=16)
        al_inner.pack(fill="both", expand=True)

        tk.Label(al_inner, text="ALGORITHM TIMING",
                 font=("Consolas", 9, "bold"), bg=CARD, fg=FG3).pack(anchor="w")
        tk.Label(al_inner, text="Execution performance",
                 font=("Consolas", 11, "bold"), bg=CARD, fg=FG).pack(anchor="w", pady=(2, 14))

        for algo_name, ms in [("Ford-Fulkerson", self.ff_ms), ("Edmonds-Karp", self.ek_ms)]:
            row2 = tk.Frame(al_inner, bg=CARD2, highlightthickness=1,
                            highlightbackground=BORDER)
            row2.pack(fill="x", pady=4)
            row2_inner = tk.Frame(row2, bg=CARD2, pady=10, padx=14)
            row2_inner.pack(fill="x")
            tk.Label(row2_inner, text=algo_name,
                     font=("Consolas", 10), bg=CARD2, fg=FG2).pack(side="left")
            ms_frame = tk.Frame(row2_inner, bg=CARD2)
            ms_frame.pack(side="right")
            tk.Label(ms_frame, text=f"{ms:.3f}",
                     font=("Consolas", 13, "bold"), bg=CARD2, fg=GREEN).pack(side="left")
            tk.Label(ms_frame, text=" ms",
                     font=("Consolas", 9), bg=CARD2, fg=FG3).pack(side="left")

    # ── DRAW GRAPH ───────────────────────────
    def _draw_graph(self):
        c = self.canvas
        R = 23

        def edge_color(cap):
            if cap <= 8:    return EDGE_LOW
            elif cap <= 11: return EDGE_MID
            else:           return EDGE_HI

        def perp_offset(x1, y1, x2, y2, dist=14):
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            if length == 0:
                return 0, -dist
            px, py = -dy / length, dx / length
            return px * dist, py * dist

        MANUAL_POS = {
            ("B", "E"): (290,  68),
            ("B", "F"): (218, 102),
            ("C", "E"): (326, 116),
            ("C", "F"): (296, 192),
        }

        for gx in range(20, 790, 40):
            for gy in range(10, 280, 40):
                c.create_oval(gx-1, gy-1, gx+1, gy+1, fill=BORDER, outline="")

        def arrow(u, v, cap):
            x1, y1 = NODE_POS[u]
            x2, y2 = NODE_POS[v]
            color = edge_color(cap)

            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            sx, sy = dx / length * R, dy / length * R
            ex, ey = dx / length * (R + 4), dy / length * (R + 4)

            c.create_line(x1 + sx, y1 + sy, x2 - ex, y2 - ey,
                          fill=color, width=4, smooth=True, capstyle="round")
            c.create_line(x1 + sx, y1 + sy, x2 - ex, y2 - ey,
                          fill=color, width=2,
                          arrow=tk.LAST, arrowshape=(11, 14, 4),
                          smooth=True, capstyle="round")

            if (u, v) in MANUAL_POS:
                mx, my = MANUAL_POS[(u, v)]
            else:
                ox, oy = perp_offset(x1, y1, x2, y2, dist=14)
                mx = (x1 + x2) / 2 + ox
                my = (y1 + y2) / 2 + oy

            pad = 5
            c.create_rectangle(mx - pad - 7, my - pad - 1,
                                mx + pad + 7, my + pad + 1,
                                fill=CARD, outline=color, width=1)
            c.create_text(mx, my, text=str(cap), fill=color,
                          font=("Consolas", 9, "bold"))

        for u, v in EDGES:
            arrow(u, v, self.caps[(u, v)])

        for node, (x, y) in NODE_POS.items():
            is_terminal = node in ("A", "T")

            if is_terminal:
                c.create_oval(x - R - 5, y - R - 5, x + R + 5, y + R + 5,
                              fill="", outline=AMBER, width=1)

            fill_c   = "#1a1500" if is_terminal else "#141720"
            border_c = AMBER    if is_terminal else BORDER
            c.create_oval(x - R, y - R, x + R, y + R,
                          fill=fill_c, outline=border_c, width=2)

            label_c = AMBER if is_terminal else FG
            c.create_text(x, y, text=node, fill=label_c,
                          font=("Consolas", 11, "bold"))

    # ── SUBMIT ───────────────────────────────
    def submit(self):
        raw = self.ans_var.get().strip()
        if not raw:
            messagebox.showwarning("No answer", "Please enter a number first.")
            return
        try:
            player_ans = int(raw)
        except ValueError:
            messagebox.showerror("Invalid input",
                                 f'"{raw}" is not a whole number.\n'
                                 "Please enter a positive integer.")
            return
        if player_ans < 0:
            messagebox.showerror("Invalid input",
                                 "Max flow cannot be negative.")
            return
        MAX_POSSIBLE = 15 * len(EDGES)
        if player_ans > MAX_POSSIBLE:
            if not messagebox.askyesno("Unusual answer",
                                       f"{player_ans} seems very high.\n"
                                       "Submit anyway?"):
                return

        result = "win" if player_ans == self.correct else "lose"
        if result == "win":
            self.score += 1

        try:
            save_round(self.player_name, self.round_no, self.correct,
                       player_ans, result, self.ff_ms, self.ek_ms)
        except Exception as e:
            messagebox.showwarning("Save failed",
                                   f"Result couldn't be saved:\n{e}\n"
                                   "The game will continue.")

        self.show_result(player_ans, result)

    # ── RESULT ───────────────────────────────
    def show_result(self, player_ans, result):
        self.clear()
        self.header(self.root)

        win = result == "win"

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=12, pady=10)

        card = tk.Frame(outer, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        accent_color = GREEN if win else RED
        tk.Frame(card, bg=accent_color, height=3).pack(fill="x")

        inner = tk.Frame(card, bg=CARD, padx=40, pady=28)
        inner.pack(fill="both", expand=True)

        banner_bg = "#0c2018" if win else "#200c0f"
        banner = tk.Frame(inner, bg=banner_bg, highlightthickness=1,
                          highlightbackground=accent_color)
        banner.pack(fill="x", pady=(0, 20))
        b_inner = tk.Frame(banner, bg=banner_bg, padx=24, pady=22)
        b_inner.pack()

        icon_txt  = "✓" if win else "✗"
        title_txt = "You got it!" if win else "Not quite"
        sub_txt   = (f"Correct answer: {self.correct} vehicles / min" if win
                     else f"The correct answer was: {self.correct} vehicles / min")

        tk.Label(b_inner, text=icon_txt,
                 font=("Consolas", 30, "bold"),
                 bg=banner_bg, fg=accent_color).pack()
        tk.Label(b_inner, text=title_txt,
                 font=("Consolas", 22, "bold"), bg=banner_bg, fg=FG).pack(pady=(4, 2))
        tk.Label(b_inner, text=sub_txt,
                 font=("Consolas", 10), bg=banner_bg, fg=FG2).pack()

        cmp = tk.Frame(inner, bg=CARD)
        cmp.pack(fill="x", pady=(0, 18))

        for label_txt, val, hl in [("Your Answer", player_ans, not win),
                                    ("Correct Answer", self.correct, True)]:
            f = tk.Frame(cmp, bg=CARD2, highlightthickness=1,
                         highlightbackground=BORDER)
            f.pack(side="left", expand=True, fill="both", padx=5)
            fi = tk.Frame(f, bg=CARD2, padx=20, pady=18)
            fi.pack()
            val_color = GREEN if (label_txt == "Correct Answer") else (
                GREEN if win else RED)
            tk.Label(fi, text=str(val),
                     font=("Consolas", 36, "bold"), bg=CARD2,
                     fg=val_color).pack()
            tk.Label(fi, text=label_txt,
                     font=("Consolas", 9), bg=CARD2, fg=FG3).pack()

        self.divider(inner, pady=8)

        algo = tk.Frame(inner, bg=CARD)
        algo.pack(fill="x", pady=(0, 20))

        for algo_name, ms in [("Ford-Fulkerson", self.ff_ms), ("Edmonds-Karp", self.ek_ms)]:
            f = tk.Frame(algo, bg=CARD2, highlightthickness=1,
                         highlightbackground=BORDER)
            f.pack(side="left", expand=True, fill="both", padx=5)
            fi = tk.Frame(f, bg=CARD2, padx=20, pady=16)
            fi.pack()
            ms_row = tk.Frame(fi, bg=CARD2)
            ms_row.pack()
            tk.Label(ms_row, text=f"{ms:.3f}",
                     font=("Consolas", 26, "bold"), bg=CARD2, fg=FG).pack(side="left")
            tk.Label(ms_row, text=" ms",
                     font=("Consolas", 11), bg=CARD2, fg=FG3).pack(side="left", anchor="s")
            tk.Label(fi, text=algo_name,
                     font=("Consolas", 9), bg=CARD2, fg=FG3).pack()

        btn_row = tk.Frame(inner, bg=CARD)
        btn_row.pack()

        if not win:
            self._make_btn(btn_row, "Try Again", self.retry_round,
                           primary=False, side="left")

        def next_round():
            self.round_no += 1
            self.show_round()

        self._make_btn(btn_row, "Next Round  →", next_round,
                       primary=True, side="left")
        self._make_btn(btn_row, "Main Menu", self.show_home,
                       primary=False, side="left")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    TrafficGame(root)
    root.mainloop()
