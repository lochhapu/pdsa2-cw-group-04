import tkinter as tk
from tkinter import ttk
from datetime import datetime
from db_setup import get_session, Solution, PlayerAnswer, SolverRun, init_db
import threading

N    = 16
CELL = 28

# Colors
BG_DEEP_PURPLE = "#1a0b2e"
BG_GRADIENT_START = "#2c003e"
BG_GRADIENT_END = "#000000"
ACCENT_PURPLE = "#8e24aa"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#b39ddb"
BOARD_LIGHT = "#e1bee7"
BOARD_DARK = "#7b1fa2"
CONFLICT_RED = "#ff5252"
BTN_BG = "#9c27b0"
ROW_EVEN = "#2a1b40"
ROW_ODD = "#33224f"

class NameScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("16 Queens Puzzle")
        self.root.geometry("640x500")
        self.root.resizable(False, False)
        self._build()

    def _build(self):
        self.canvas = tk.Canvas(self.root, width=640, height=500, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._draw_gradient(BG_GRADIENT_START, BG_GRADIENT_END)

        self.canvas.create_text(320, 80, text="♛", font=("Arial", 90), fill="#d896ff")
        self.canvas.create_text(320, 180, text="16 Queens Puzzle", font=("Georgia", 32, "bold"), fill="white")
        self.canvas.create_text(320, 220, text="Place 16 queens so none can attack another.", font=("Georgia", 12, "italic"), fill="#b39ddb")
        self.canvas.create_text(320, 310, text="Enter your name to begin:", font=("Georgia", 14), fill="white")

        self.name_var = tk.StringVar()
        self.entry = tk.Entry(self.root, textvariable=self.name_var, font=("Courier", 16), bd=0, justify="center")
        self.canvas.create_window(320, 350, window=self.entry, width=280, height=40)

        self.start_btn = tk.Button(self.root, text="Start Playing  ►", font=("Courier", 14, "bold"),
                                   bg=BTN_BG, fg="white", activebackground="#aa00ff", activeforeground="white",
                                   bd=0, cursor="hand2", command=self._start)
        self.canvas.create_window(320, 420, window=self.start_btn, width=220, height=50)

        self.entry.bind("<Return>", lambda e: self._start())
        self.entry.focus_set()

    def _draw_gradient(self, color1, color2):
        r1, g1, b1 = self.canvas.winfo_rgb(color1)
        r2, g2, b2 = self.canvas.winfo_rgb(color2)
        r_ratio = (r2 - r1) / 500
        g_ratio = (g2 - g1) / 500
        b_ratio = (b2 - b1) / 500
        for i in range(500):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f"#{nr>>8:02x}{ng>>8:02x}{nb>>8:02x}"
            self.canvas.create_line(0, i, 640, i, fill=color)

    def _start(self):
        name = self.name_var.get().strip()
        if not name:
            return
        for w in self.root.winfo_children():
            w.destroy()
        GameScreen(self.root, name)


class GameScreen:
    def __init__(self, root, player_name):
        self.root = root
        self.player_name = player_name
        self.root.configure(bg=BG_DEEP_PURPLE)
        self.root.title(f"16 Queens — {player_name}")
        self.root.geometry("800x820")
        self.board = [-1] * N
        self.conflicts = set()
        self.timer_running = False   # timer only starts when player clicks START
        self.game_started = False
        self._build()

    def _build(self):
        # ── Top Bar ───────────────────────────────────────────
        top = tk.Frame(self.root, bg=BG_DEEP_PURPLE, pady=10, padx=20)
        top.pack(fill=tk.X)

        tk.Label(top, text="♛ 16 Queens", font=("Georgia", 16, "bold"),
                 bg=BG_DEEP_PURPLE, fg="#d896ff").pack(side=tk.LEFT)

        self.timer_var = tk.StringVar(value="Time: 00:00")
        tk.Label(top, textvariable=self.timer_var, font=("Courier", 16, "bold"),
                 bg=BG_DEEP_PURPLE, fg="#00e676").pack(side=tk.LEFT, padx=50)

        tk.Label(top, text=f"Player: {self.player_name}", font=("Courier", 12),
                 bg=BG_DEEP_PURPLE, fg="white").pack(side=tk.RIGHT)

        # ── Info Bar ──────────────────────────────────────────
        info_frame = tk.Frame(self.root, bg=BG_DEEP_PURPLE, pady=5)
        info_frame.pack(fill=tk.X)

        self.counter_label = tk.Label(info_frame, text="Queens Remaining: 16",
                                      font=("Courier", 12), bg=BG_DEEP_PURPLE, fg="#b39ddb")
        self.counter_label.pack(side=tk.TOP)
        self.conflict_label = tk.Label(info_frame, text="", font=("Courier", 11),
                                       bg=BG_DEEP_PURPLE, fg=CONFLICT_RED)
        self.conflict_label.pack(side=tk.TOP)

        # ── Board + overlay wrapper ───────────────────────────
        board_outer = tk.Frame(self.root, bg="#d896ff", padx=2, pady=2)
        board_outer.pack(padx=16, pady=10)

        # Use a Frame as a container so we can overlay canvas items
        board_container = tk.Frame(board_outer, width=N * CELL, height=N * CELL)
        board_container.pack()
        board_container.pack_propagate(False)

        self.canvas = tk.Canvas(board_container, width=N * CELL, height=N * CELL,
                                highlightthickness=0, bg=BG_DEEP_PURPLE)
        self.canvas.place(x=0, y=0)
        self.canvas.bind("<Button-1>", self._on_click)
        self._draw_board()

        # START overlay button — centered on the board
        board_w = N * CELL  # 448px
        board_h = N * CELL
        self.start_overlay = tk.Button(
            board_container,
            text="▶  START",
            font=("Courier", 18, "bold"),
            bg="#aa00ff", fg="white",
            activebackground="#d896ff", activeforeground="#1a0b2e",
            bd=0, cursor="hand2",
            relief=tk.FLAT,
            command=self._start_game
        )
        # Place it centered
        btn_w, btn_h = 160, 60
        self.start_overlay.place(
            x=(board_w - btn_w) // 2,
            y=(board_h - btn_h) // 2,
            width=btn_w, height=btn_h
        )

        # ── Action Buttons ────────────────────────────────────
        # FIX: centre the grid inside a centred frame so it has equal margins
        btn_outer = tk.Frame(self.root, bg=BG_DEEP_PURPLE, pady=15)
        btn_outer.pack()   # no fill=tk.X → centres automatically

        btn_frame = tk.Frame(btn_outer, bg=BG_DEEP_PURPLE)
        btn_frame.pack()

        self._btn(btn_frame, "Submit Solution",    BTN_BG,    "white",   self._submit      ).grid(row=0, column=0, padx=8, pady=5)
        self._btn(btn_frame, "Clear Board",        "#5c0e70", "white",   self._clear       ).grid(row=0, column=1, padx=8, pady=5)
        self._btn(btn_frame, "Algorithms Analysis","#4a148c", "white",   self._solver_window).grid(row=0, column=2, padx=8, pady=5)
        self._btn(btn_frame, "Leaderboard",        "#311b92", "white",   self._progress_window).grid(row=0, column=3, padx=8, pady=5)
        self._btn(btn_frame, "My Solutions",       "#4527a0", "white",   self._my_solutions_window).grid(row=0, column=4, padx=8, pady=5)
        self._btn(btn_frame, "Logout",             "#631EBF", "#b39ddb", self._back_to_name).grid(row=1, column=2, padx=8, pady=5)

    # ── Start Game (overlay btn) ──────────────────────────────
    def _start_game(self):
        self.game_started = True
        self.timer_running = True
        self.start_time = datetime.now()
        self.start_overlay.place_forget()   # hide the overlay button
        self._update_timer()

    # ── Board ─────────────────────────────────────────────────
    def _draw_board(self):
        self.canvas.delete("all")
        self.conflicts = self._find_conflicts()
        for row in range(N):
            for col in range(N):
                x1, y1 = col * CELL, row * CELL
                x2, y2 = x1 + CELL, y1 + CELL
                base = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
                fill = CONFLICT_RED if (row in self.conflicts and self.board[row] == col) else base
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#6a0572", width=0.5)
                if self.board[row] == col:
                    self.canvas.create_text(x1 + CELL // 2, y1 + CELL // 2,
                                            text="♛", font=("Arial", int(CELL * 0.6)),
                                            fill="white" if fill == CONFLICT_RED else BG_DEEP_PURPLE)
                    
            # Row numbers left side
            for row in range(N):
                self.canvas.create_text(
                    4, row * CELL + CELL // 2,
                    text=str(row + 1),
                    font=("Courier", 7, "bold"),
                    fill="#d896ff", anchor="w"
                )

            # Column numbers top
            for col in range(N):
                self.canvas.create_text(
                    col * CELL + CELL // 2, 6,
                    text=str(col + 1),
                    font=("Courier", 7, "bold"),
                    fill="#d896ff"
                )

    def _find_conflicts(self):
        conflict_rows = set()
        for r1 in range(N):
            if self.board[r1] == -1:
                continue
            for r2 in range(r1 + 1, N):
                if self.board[r2] == -1:
                    continue
                c1, c2 = self.board[r1], self.board[r2]
                if c1 == c2 or abs(r1 - r2) == abs(c1 - c2):
                    conflict_rows.add(r1)
                    conflict_rows.add(r2)
        return conflict_rows

    def _on_click(self, event):
        if not self.game_started:
            return   # board is locked until START is pressed
        col = event.x // CELL
        row = event.y // CELL
        if not (0 <= row < N and 0 <= col < N):
            return
        self.board[row] = -1 if self.board[row] == col else col
        self._draw_board()
        self._update_counter()

    def _update_counter(self):
        placed = sum(1 for c in self.board if c != -1)
        self.counter_label.config(text=f"Queens Remaining: {16 - placed}")
        if self.conflicts:
            self.conflict_label.config(text=f"{len(self.conflicts)} queens in conflict!")
        else:
            self.conflict_label.config(text="")

    def _clear(self):
        self.board = [-1] * N
        self._draw_board()
        self._update_counter()

    def _submit(self):
        if not self.game_started:
            return
        placed = sum(1 for c in self.board if c != -1)
        if placed < 16:
            self._show_result_popup("Incomplete", f"Please place all 16 queens. You have placed {placed}.", False, color="#ffb300")
            return
        if self.conflicts:
            self._show_result_popup("Conflicts", "There are queens attacking each other! Fix the red squares.", False, color=CONFLICT_RED)
            return

        elapsed = datetime.now() - self.start_time
        time_str = f"{elapsed.total_seconds():.1f} seconds"

        board_str = ",".join([str(int(x)) for x in self.board])
        session = get_session()

        try:
            sol = session.query(Solution).filter_by(board=board_str).first()

            if sol is None:
                sol = Solution(board=board_str, is_claimed=True, claimed_by=self.player_name, claimed_at=datetime.now())
                session.add(sol)
                is_new = True
                owner = self.player_name
            else:
                if sol.is_claimed:
                    is_new = False
                    owner = sol.claimed_by
                else:
                    sol.is_claimed = True
                    sol.claimed_by = self.player_name
                    sol.claimed_at = datetime.now()
                    is_new = True
                    owner = self.player_name

            session.add(PlayerAnswer(
                player_name=self.player_name,
                solution=board_str,
                time_taken=elapsed.total_seconds()
            ))
            session.commit()

            if is_new:
                msg = f"Congratulations!\n\nYou've discovered a new solution.\nTime taken: {time_str} - incredible speed!"
                self._show_result_popup("New Solution Found", msg, True, color="#00e676")
            else:
                msg = f"This person \"{owner}\" already recognized this solution.\n\nPlease find a different arrangement."
                self._show_result_popup("Already Claimed", msg, True, color="#29b6f6")

            total = session.query(Solution).count()
            claimed = session.query(Solution).filter_by(is_claimed=True).count()
            if not is_new:
                total = session.query(Solution).count()
                claimed = session.query(Solution).filter_by(is_claimed=True).count()

                if total > 0 and claimed == total:
                    session.query(Solution).update({
                        "is_claimed": False,
                        "claimed_by": None,
                        "claimed_at": None
                    })
                    session.commit()

                    self._show_result_popup(
                        "All Found!",
                        "All solutions were claimed! Flags have been reset.",
                        False,
                        color="#d896ff"
                    )

        except Exception as e:
            session.rollback()
            self._show_result_popup("Error", str(e), False, color=CONFLICT_RED)
        finally:
            session.close()

    def _show_result_popup(self, title, message, restart_after, color="white"):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=BG_DEEP_PURPLE)
        # win.geometry("450x250")

        win.update_idletasks()

        # Get main window position and size
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        # Popup size
        popup_width = 450
        popup_height = 250

      # Calculate center position
        x = main_x + (main_width // 2) - (popup_width // 2)
        y = main_y + (main_height // 2) - (popup_height // 2)

        win.geometry(f"{popup_width}x{popup_height}+{x}+{y}")



        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="♛", font=("Arial", 36), bg=BG_DEEP_PURPLE, fg=color).pack(pady=(15, 0))
        tk.Label(win, text=message, font=("Georgia", 11), bg=BG_DEEP_PURPLE, fg="white", justify="center").pack(pady=10, padx=20)

        def on_close():
            if restart_after:
                self._clear()
                self.start_time = datetime.now()
            win.destroy()

        tk.Button(win, text="Try Again", font=("Courier", 11, "bold"), bg=BTN_BG, fg="white",
                  activebackground="#aa00ff", activeforeground="white", bd=0, padx=20, pady=8,
                  cursor="hand2", command=on_close).pack(pady=10)
        win.protocol("WM_DELETE_WINDOW", on_close)

    # ── My Solutions ──────────────────────────────────────────
    def _my_solutions_window(self):
        session = get_session()
        my_answers = session.query(PlayerAnswer).filter(
            PlayerAnswer.player_name == self.player_name
        ).order_by(PlayerAnswer.submitted_at.desc()).all()
        session.close()

        win = tk.Toplevel(self.root)
        win.title(f"My Solutions — {self.player_name}")
        win.configure(bg=BG_DEEP_PURPLE)
        win.geometry("700x500")
        win.grab_set()

        tk.Label(win, text=f"♛ Solutions by {self.player_name}", font=("Georgia", 16, "bold"),
                 bg=BG_DEEP_PURPLE, fg="#d896ff").pack(pady=(20, 5))
        tk.Label(win, text=f"Total discovered: {len(my_answers)}", font=("Courier", 11),
                 bg=BG_DEEP_PURPLE, fg="#b39ddb").pack(pady=(0, 10))

        if not my_answers:
            tk.Label(win, text="You haven't found any solutions yet.", font=("Georgia", 12),
                     bg=BG_DEEP_PURPLE, fg="white").pack(expand=True)
        else:
            container = tk.Frame(win, bg=BG_DEEP_PURPLE)
            container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            canvas = tk.Canvas(container, bg=BG_DEEP_PURPLE, highlightthickness=0)
            scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            inner = tk.Frame(canvas, bg=BG_DEEP_PURPLE)

            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            hdr = tk.Frame(inner, bg="#311b92")
            hdr.pack(fill=tk.X, pady=(0, 5))
            for txt, w in [("Date & Time", 25), ("Name", 15), ("Solution Layout", 35)]:
                tk.Label(hdr, text=txt, font=("Courier", 10, "bold"), bg="#311b92", fg="white",
                         width=w, anchor="w", padx=5, pady=5).pack(side=tk.LEFT)

            for i, ans in enumerate(my_answers):
                row_bg = ROW_EVEN if i % 2 == 0 else ROW_ODD
                row_f = tk.Frame(inner, bg=row_bg)
                row_f.pack(fill=tk.X, pady=1)
                time_str = ans.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ans.submitted_at, datetime) else str(ans.submitted_at)[:19]
                for txt, w in [(time_str, 25), (ans.player_name, 15), (ans.solution, 35)]:
                    tk.Label(row_f, text=txt, font=("Courier", 9), bg=row_bg, fg="white",
                             width=w, anchor="w", padx=5, pady=8).pack(side=tk.LEFT)

        tk.Button(win, text="Close", font=("Courier", 10), bg="#4a148c", fg="white",
                  bd=0, padx=15, pady=5, cursor="hand2", command=win.destroy).pack(pady=15)

    # ── Leaderboard (FIXED) ───────────────────────────────────
    def _progress_window(self):
        session = get_session()
        all_answers = session.query(PlayerAnswer).order_by(PlayerAnswer.submitted_at.asc()).all()
        session.close()

        player_stats = {}
        for a in all_answers:
            t = a.time_taken if a.time_taken is not None else float("inf")
            if a.player_name not in player_stats:
                player_stats[a.player_name] = {"count": 1, "best_time": t}
            else:
                player_stats[a.player_name]["count"] += 1
                if t < player_stats[a.player_name]["best_time"]:
                    player_stats[a.player_name]["best_time"] = t

        # Sort by best (lowest) time
        sorted_players = sorted(player_stats.items(), key=lambda x: x[1]["best_time"])

        win = tk.Toplevel(self.root)
        win.title("Leaderboard")
        win.configure(bg=BG_DEEP_PURPLE)
        win.geometry("600x480")
        win.grab_set()

        tk.Label(win, text="♛ Leaderboard ♛", font=("Georgia", 16, "bold"),
                 bg=BG_DEEP_PURPLE, fg="#d896ff").pack(pady=(20, 10))
        tk.Label(win, text="Ranked by fastest solve time", font=("Courier", 10, "italic"),
                 bg=BG_DEEP_PURPLE, fg="#b39ddb").pack(pady=(0, 10))

        if not sorted_players:
            tk.Label(win, text="No users on the leaderboard yet.", font=("Georgia", 12),
                     bg=BG_DEEP_PURPLE, fg="white").pack(expand=True)
        else:
            container = tk.Frame(win, bg=BG_DEEP_PURPLE)
            container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            hdr = tk.Frame(container, bg="#311b92")
            hdr.pack(fill=tk.X, pady=(0, 5))
            for txt, w in [("Rank", 7), ("Player Name", 15), ("Total Solved", 15), ("Best Time", 20)]:
                tk.Label(hdr, text=txt, font=("Courier", 10, "bold"), bg="#311b92", fg="white",
                         width=w, anchor="w", padx=5, pady=5).pack(side=tk.LEFT)

            for i, (p_name, stats) in enumerate(sorted_players):
                row_bg = ROW_EVEN if i % 2 == 0 else ROW_ODD
                if p_name == self.player_name:
                    row_bg = "#4a148c"

                row_f = tk.Frame(container, bg=row_bg)
                row_f.pack(fill=tk.X, pady=1)

                bt = stats["best_time"]
                t_str = f"{bt:.1f}s" if bt != float("inf") else "N/A"
                rank_str = f"#{i+1}"

                for txt, w in [(rank_str, 8), (p_name, 20), (str(stats["count"]), 15), (t_str, 20)]:
                    tk.Label(row_f, text=txt, font=("Courier", 9), bg=row_bg, fg="white",
                             width=w, anchor="w", padx=5, pady=8).pack(side=tk.LEFT)

        tk.Button(win, text="Close", font=("Courier", 10), bg="#4a148c", fg="white",
                  bd=0, padx=15, pady=5, cursor="hand2", command=win.destroy).pack(pady=15)

    # ── Solver Window ─────────────────────────────────────────
    def _solver_window(self):
        win = tk.Toplevel(self.root)
        win.title("Algorithm Analysis")
        win.configure(bg=BG_DEEP_PURPLE)
        win.geometry("600x400")
        win.grab_set()

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG_DEEP_PURPLE, borderwidth=0)
        style.configure("TNotebook.Tab", background="#311b92", foreground="white",
                        font=("Courier", 10, "bold"), padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", BTN_BG)], foreground=[("selected", "white")])
        style.configure("TFrame", background=BG_DEEP_PURPLE)

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tab_seq = ttk.Frame(notebook)
        tab_thr = ttk.Frame(notebook)
        tab_cmp = ttk.Frame(notebook)

        notebook.add(tab_seq, text=" Sequential Algorithm ")
        notebook.add(tab_thr, text=" Threaded Algorithm ")
        notebook.add(tab_cmp, text=" Comparing ")

        def run_algo_bg(algo_type, label_widget, btn_widget, pb_widget):
            btn_widget.config(state=tk.DISABLED)
            label_widget.config(text=f"Analyzing with {algo_type} technique...\nPlease wait.", fg="#d896ff")
            pb_widget.start(15)

            def task():
                try:
                    if algo_type == "Threading":
                        from threaded import run_threaded_solver
                        count, t = run_threaded_solver()
                    else:
                        from sequential import run_sequential_solver
                        count, t = run_sequential_solver()
                    msg = f"Analysis Complete!\n\nTechnique:   {algo_type}\nTotal Found: {count}\nTime Taken:  {t:.4f} seconds"
                    color = "#00e676"
                except Exception as e:
                    msg = f"Error during analysis:\n{e}"
                    color = CONFLICT_RED

                def on_done():
                    pb_widget.stop()
                    label_widget.config(text=msg, fg=color)
                    btn_widget.config(state=tk.NORMAL)
                win.after(0, on_done)

            threading.Thread(target=task, daemon=True).start()

        def compare_algos(text_widget):
            session = get_session()
            runs = session.query(SolverRun).order_by(SolverRun.run_at.desc()).limit(10).all()
            session.close()
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            if not runs:
                text_widget.insert(tk.END, "No database run history available.\nPlease run the algorithms first.")
            else:
                text_widget.insert(tk.END, f"{'Technique':<15} | {'Time Taken':<12} | {'Solutions':<10}\n")
                text_widget.insert(tk.END, "-" * 42 + "\n")
                for r in runs:
                    text_widget.insert(tk.END, f"{r.solver_type.capitalize():<15} | {r.time_taken:<10.4f} s | {r.solutions_found:<10}\n")
            text_widget.config(state=tk.DISABLED)

        tk.Label(tab_seq, text="Sequential Programming Analysis", font=("Georgia", 14),
                 bg=BG_DEEP_PURPLE, fg="white").pack(pady=(20, 10))
        lbl_seq = tk.Label(tab_seq, text="Ready to analyze.", font=("Courier", 11),
                           bg=BG_DEEP_PURPLE, fg="#b39ddb")
        lbl_seq.pack(pady=15)
        pb_seq = ttk.Progressbar(tab_seq, mode="indeterminate", length=250)
        pb_seq.pack(pady=10)
        btn_seq = tk.Button(tab_seq, text="Start Sequential Analysis", font=("Courier", 10, "bold"),
                            bg=BTN_BG, fg="white", bd=0, padx=15, pady=8, cursor="hand2")
        btn_seq.config(command=lambda: run_algo_bg("Sequential", lbl_seq, btn_seq, pb_seq))
        btn_seq.pack(pady=15)

        tk.Label(tab_thr, text="Threaded Programming Analysis", font=("Georgia", 14),
                 bg=BG_DEEP_PURPLE, fg="white").pack(pady=(20, 10))
        lbl_thr = tk.Label(tab_thr, text="Ready to analyze.", font=("Courier", 11),
                           bg=BG_DEEP_PURPLE, fg="#b39ddb")
        lbl_thr.pack(pady=15)
        pb_thr = ttk.Progressbar(tab_thr, mode="indeterminate", length=250)
        pb_thr.pack(pady=10)
        btn_thr = tk.Button(tab_thr, text="Start Threaded Analysis", font=("Courier", 10, "bold"),
                            bg=BTN_BG, fg="white", bd=0, padx=15, pady=8, cursor="hand2")
        btn_thr.config(command=lambda: run_algo_bg("Threading", lbl_thr, btn_thr, pb_thr))
        btn_thr.pack(pady=15)

        tk.Label(tab_cmp, text="Comparison History (Recent 10)", font=("Georgia", 14),
                 bg=BG_DEEP_PURPLE, fg="white").pack(pady=(15, 5))
        txt_cmp = tk.Text(tab_cmp, height=8, width=45, font=("Courier", 10),
                          bg="#2a1b40", fg="white", bd=0, padx=10, pady=10)
        txt_cmp.pack(pady=5)
        compare_algos(txt_cmp)
        tk.Button(tab_cmp, text="Refresh History", font=("Courier", 10, "bold"), bg="#4a148c",
                  fg="white", bd=0, padx=15, pady=5, cursor="hand2",
                  command=lambda: compare_algos(txt_cmp)).pack(pady=5)

        tk.Button(win, text="Close Window", font=("Courier", 10), bg="#1a0b2e", fg="#b39ddb",
                  bd=0, padx=15, pady=5, cursor="hand2", command=win.destroy).pack(pady=(0, 10))

    def _back_to_name(self):
        self.timer_running = False
        for w in self.root.winfo_children():
            w.destroy()
        NameScreen(self.root)

    def _update_timer(self):
        if not self.timer_running:
            return
        elapsed = datetime.now() - self.start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        self.timer_var.set(f"Time: {minutes:02d}:{seconds:02d}")
        self.root.after(1000, self._update_timer)

    def _btn(self, parent, text, bg, fg, cmd):
        return tk.Button(parent, text=text, font=("Courier", 10, "bold"), bg=bg, fg=fg,
                         activebackground="#d896ff", activeforeground="#1a0b2e", bd=0,
                         padx=15, pady=8, cursor="hand2", command=cmd)


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    root.resizable(False, False)
    app = NameScreen(root)
    root.mainloop()