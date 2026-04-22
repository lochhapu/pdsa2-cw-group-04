import tkinter as tk
import random
from PIL import Image, ImageTk
from logic.knights_tour import knights_tour, knights_tour_backtracking
from logic.moves import MOVES
from utils.helpers import get_center
from ui.animation import KnightSprite
from db.db_helper import DatabaseHelper
import time

class Board:
    def __init__(self, root, player_id=None, on_exit_menu=None, cheat_code=None):
        self.root = root
        self.size = 8
        self.player_id = player_id
        self.cheat_code = cheat_code
        self.on_exit_menu = on_exit_menu
        self.game_start_time = None
        self.game_recorded = False
        self.overlay_panel = None
        self.notification_label = None
        self.notification_timer = None
        self.streak_count = 0

        # Streak label above the board
        self.streak_label = tk.Label(root, text=f"Streak: {self.streak_count}", font=("Arial", 14, "bold"), bg="#2c3e50", fg="#f1c40f")
        self.streak_label.pack(pady=5)

        # Container frame for canvas and overlays with dark background
        self.container = tk.Frame(root, bg="#2c3e50")
        self.container.pack(fill=tk.BOTH, expand=True)

        # Board frame to center the canvas
        self.board_frame = tk.Frame(self.container, bg="#2c3e50")
        self.board_frame.pack(expand=True, pady=10)

        self.canvas = tk.Canvas(self.board_frame, bg="#2c3e50", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        self.cell_size = 60
        self.squares = []
        self.highlighted_items = []
        self.blue_highlights = []
        
        self.player_path = []
        self.valid_moves = []
        
        self.solution_path = None
        self.current_step = 0
        self.is_playing = False
        self.animating = False
        
        # Load base textures
        try:
            self.grass_img = Image.open("assets/tiles/TX Tileset Grass.png")
            self.stone_img = Image.open("assets/tiles/TX Tileset Stone Ground.png")
        except Exception as e:
            print(f"Error loading tiles: {e}")
            self.grass_img = None
            self.stone_img = None
            
        self.photo_grass = None
        self.photo_stone = None

        self.reset_board()

    def generate_path(self):
        # We don't need generate_path inside the board anymore because 
        # the player makes their own path dynamically.
        pass

    def draw_board(self):
        self.canvas.delete("all")
        self.squares = []
        self.highlighted_items = []
        self.blue_highlights = []
        
        self.animating = False
        self.is_playing = False
        self.player_path = []
        self.valid_moves = []

        self.cell_size = 480 // self.size
        self.canvas.config(width=480, height=480, bg="#2c3e50")

        # Resize textures for the current cell size
        if self.grass_img and self.stone_img:
            # We crop the top-left 32x32 area from the tileset first, assuming it's a grid of tiles
            # If not a tileset, cropping will still give us a consistent texture portion
            grass_crop = self.grass_img.crop((0, 0, min(64, self.grass_img.width), min(64, self.grass_img.height)))
            stone_crop = self.stone_img.crop((0, 0, min(64, self.stone_img.width), min(64, self.stone_img.height)))
            
            self.photo_grass = ImageTk.PhotoImage(grass_crop.resize((self.cell_size, self.cell_size), getattr(Image, 'LANCZOS', 1)))
            self.photo_stone = ImageTk.PhotoImage(stone_crop.resize((self.cell_size, self.cell_size), getattr(Image, 'LANCZOS', 1)))

        for r in range(self.size):
            row = []
            for c in range(self.size):
                is_grass = (r + c) % 2 == 0
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = (c + 1) * self.cell_size, (r + 1) * self.cell_size
                
                if self.photo_grass and self.photo_stone:
                    img_to_draw = self.photo_grass if is_grass else self.photo_stone
                    rect = self.canvas.create_image(x1, y1, image=img_to_draw, anchor="nw")
                else:
                    color = "white" if is_grass else "gray"
                    rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)
                    
                row.append(rect)
            self.squares.append(row)

        self.knight = KnightSprite(self.canvas, {
            "idle": {"path": "assets/knight/IDLE.png", "frames": 7},
            "jump": {"path": "assets/knight/JUMP.png", "frames": 5},
            "death": {"path": "assets/knight/DEATH.png", "frames": 12}
        })

    def set_size(self, size):
        self.size = size
        self.reset_board(reset_streak=True)

    def reset_board(self, reset_streak=False):
        if reset_streak or (self.is_playing and len(self.player_path) > 1):
            self.streak_count = 0
            self.streak_label.config(text=f"Streak: {self.streak_count}")
            
        self.draw_board()
        
        # Pick a random starting point
        sr = random.randint(0, self.size - 1)
        sc = random.randint(0, self.size - 1)
        
        self.player_path = [(sr, sc)]
        self.is_playing = True
        self.game_start_time = time.time()
        self.game_recorded = False
        
        start_coord = get_center(sr, sc, self.cell_size)
        self.knight.move_to(*start_coord)
        self.highlight_tile(sr, sc)
        self.update_valid_moves()
        
        if self.cheat_code and self.cheat_code.lower() == "nutter tools":
            self.root.after(100, self.start_animation)

    def update_valid_moves(self):
        # Clear existing blue highlights
        for item in self.blue_highlights:
            self.canvas.delete(item)
        self.blue_highlights.clear()
        
        if len(self.player_path) == self.size * self.size:
            self.is_playing = False
            self.streak_count += 1
            self.streak_label.config(text=f"Streak: {self.streak_count}")
            self._record_game_result("won")
            self._show_win_dialog()
            return
            
        r, c = self.player_path[-1]
        self.valid_moves = []
        
        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                if (nr, nc) not in self.player_path:
                    self.valid_moves.append((nr, nc))
                    
        if not self.valid_moves:
            self.is_playing = False
            self.animating = True
            
            def on_death_done():
                self.animating = False
                self.streak_count = 0
                self.streak_label.config(text=f"Streak: {self.streak_count}")
                self._show_stuck_dialog()
                
            self.knight.animate_death(callback=on_death_done)
        else:
            # Highlight valid moves in light blue
            for (vr, vc) in self.valid_moves:
                x1, y1 = vc * self.cell_size, vr * self.cell_size
                x2, y2 = (vc + 1) * self.cell_size, (vr + 1) * self.cell_size
                hl = self.canvas.create_rectangle(x1, y1, x2, y2, outline="lightblue", width=4, stipple="gray25", fill="lightblue")
                self.canvas.tag_lower(hl, self.knight.image) # Place below knight
                self.blue_highlights.append(hl)

    def _show_stuck_dialog(self):
        """Show inline overlay panel when player gets stuck."""
        self._show_overlay_dialog(
            title="You Got Stuck!",
            message="You got stuck! What would you like to do?",
            buttons=[
                ("God take the wheel", lambda: self._on_stuck_algorithm()),
                ("Exit to Menu", lambda: self._on_stuck_exit())
            ]
        )

    def _on_stuck_algorithm(self):
        """Handle algorithm selection when stuck."""
        self._clear_overlay()
        self._record_game_result("died")
        self._start_algorithm_from_beginning()

    def _on_stuck_exit(self):
        """Handle exit to menu when stuck."""
        self._clear_overlay()
        self._record_game_result("quit")
        if self.on_exit_menu:
            self.on_exit_menu()

    def _show_win_dialog(self):
        """Show inline overlay panel when player wins the game."""
        self._show_overlay_dialog(
            title="You Won!",
            message="Congratulations, you completed the Knight's Tour!\nWhat would you like to do?",
            buttons=[
                ("Play Again", lambda: self._on_win_play_again()),
                ("Return to Main Menu", lambda: self._on_win_exit())
            ]
        )

    def _on_win_play_again(self):
        """Handle play again selection."""
        self._clear_overlay()
        self.reset_board()

    def _on_win_exit(self):
        """Handle exit to menu after win."""
        self._clear_overlay()
        if self.on_exit_menu:
            self.on_exit_menu()

    def highlight_tile(self, r, c):
        x1, y1 = c * self.cell_size, r * self.cell_size
        x2, y2 = (c + 1) * self.cell_size, (r + 1) * self.cell_size
        hl = self.canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=4, stipple="gray25", fill="yellow")
        self.canvas.tag_raise(self.knight.image) # Ensure knight is above highlight
        self.highlighted_items.append(hl)

    def on_click(self, event):
        if not self.is_playing or self.animating:
            return

        c = event.x // self.cell_size
        r = event.y // self.cell_size

        if (r, c) in self.valid_moves:
            self.animating = True
            
            # Get start and end coordinates
            pr, pc = self.player_path[-1]
            start = get_center(pr, pc, self.cell_size)
            end = get_center(r, c, self.cell_size)
            
            self.player_path.append((r, c))
            
            def on_done():
                self.animating = False
                self.highlight_tile(r, c)
                self.update_valid_moves()
                
            self.knight.animate_jump(start, end, callback=on_done)

    def start_animation(self):
        # Force auto-complete from the beginning
        if self.is_playing and not self.animating:
            self.is_playing = False
            self._start_algorithm_from_beginning()
            
    def _start_algorithm_from_beginning(self):
        # Find starting position
        start_r, start_c = self.player_path[0]
        
        # Clear previous highlights
        for item in self.highlighted_items:
            self.canvas.delete(item)
        self.highlighted_items.clear()
        
        for item in self.blue_highlights:
            self.canvas.delete(item)
        self.blue_highlights.clear()

        # Reset knight to starting point
        start_coord = get_center(start_r, start_c, self.cell_size)
        self.knight.move_to(*start_coord)
        
        # Determine path from the original start using the algorithm
        start_time = time.time()
        
        path = knights_tour(self.size, start=(start_r, start_c))
        exec_time_ms = (time.time() - start_time) * 1000
        
        # Also run backtracking algorithm in background to compare and save data
        bt_start_time = time.time()
        bt_path = knights_tour_backtracking(self.size, start=(start_r, start_c))
        bt_exec_time_ms = (time.time() - bt_start_time) * 1000
        
        # Save algorithm result
        db = None
        try:
            db = DatabaseHelper()
            db.save_algorithm_result(
                board_size=self.size,
                start_r=start_r,
                start_c=start_c,
                algo_name="Warnsdorff",
                execution_time_ms=exec_time_ms,
                solution_found=bool(path)
            )
            
            db.save_algorithm_result(
                board_size=self.size,
                start_r=start_r,
                start_c=start_c,
                algo_name="Backtracking",
                execution_time_ms=bt_exec_time_ms,
                solution_found=bool(bt_path)
            )
        except Exception as e:
            print(f"Error saving algorithm result: {e}")
        finally:
            if db:
                db.close()
        
        if path:
            self.player_path = path
            self.game_recorded = False
            self.game_start_time = time.time()
            self.animate_path(self.player_path, 0)
        else:
            self._show_notification("No solution could be found from the starting position!", error=True)

    def _record_game_result(self, status):
        """Record the game result to the database."""
        if not self.player_id or self.game_recorded:
            print(f"Cannot record game: player_id={self.player_id}, game_recorded={self.game_recorded}")
            return
        
        db = None
        try:
            # Create a fresh database connection for this save
            db = DatabaseHelper()
            
            # Calculate game duration
            time_taken = int(time.time() - self.game_start_time) if self.game_start_time else 0
            
            # Get start position as string
            start_pos = f"{self.player_path[0][0]},{self.player_path[0][1]}"
            
            # Save game result (only save the move sequence if the game was won)
            path_to_save = str(self.player_path) if status == "won" else None
            
            game_id = db.save_game_result(
                player_id=self.player_id,
                board_size=self.size,
                start_position=start_pos,
                completion_status=status,
                moves_count=len(self.player_path),
                total_squares=self.size * self.size,
                time_taken=time_taken,
                path=path_to_save
            )
            
            print(f"Game recorded successfully! Game ID: {game_id}, Status: {status}")
            self.game_recorded = True
        except Exception as e:
            print(f"Error recording game result: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always close the database connection
            if db:
                db.close()

    def animate_path(self, path, index):
        if index >= len(path) - 1:
            self.animating = False
            # Record the completion when algorithm finishes
            if not self.game_recorded:
                status = "won" if (self.cheat_code and self.cheat_code.lower() == "nutter tools") else "completed"
                self._record_game_result(status)
                if status == "won" or status == "completed":
                    self.streak_count += 1
                    self.streak_label.config(text=f"Streak: {self.streak_count}")
                    self._show_win_dialog()
            return
            
        self.animating = True
        r1, c1 = path[index]
        r2, c2 = path[index + 1]

        start = get_center(r1, c1, self.cell_size)
        end = get_center(r2, c2, self.cell_size)

        if index == 0 and not self.highlighted_items: # If it hasn't started
            self.knight.move_to(*start)
            self.highlight_tile(r1, c1)
            
        def on_step_done():
            self.highlight_tile(r2, c2)
            self.animate_path(path, index + 1)

        self.knight.animate_jump(start, end, callback=on_step_done)

    def _show_overlay_dialog(self, title, message, buttons):
        """Show an inline overlay dialog with buttons."""
        self._clear_overlay()
        
        # Create a centered dialog frame without full-screen overlay
        self.overlay_panel = tk.Frame(self.container, bg="#34495e", relief=tk.RAISED, bd=3)
        self.overlay_panel.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.6, relheight=0.5)
        
        # Title
        title_label = tk.Label(
            self.overlay_panel,
            text=title,
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#34495e"
        )
        title_label.pack(pady=15)
        
        # Message
        msg_label = tk.Label(
            self.overlay_panel,
            text=message,
            font=("Arial", 12),
            fg="white",
            bg="#34495e",
            wraplength=400,
            justify=tk.CENTER
        )
        msg_label.pack(pady=10, padx=10)
        
        # Buttons frame
        button_frame = tk.Frame(self.overlay_panel, bg="#34495e")
        button_frame.pack(pady=20)
        
        for btn_text, btn_command in buttons:
            btn = tk.Button(
                button_frame,
                text=btn_text,
                command=btn_command,
                font=("Arial", 11),
                bg="#3498db",
                fg="white",
                activebackground="#2980b9",
                width=15,
                bd=0,
                cursor="hand2",
                padx=10,
                pady=8
            )
            btn.pack(side=tk.LEFT, padx=5)

    def _clear_overlay(self):
        """Clear the overlay dialog if it exists."""
        if self.overlay_panel:
            self.overlay_panel.destroy()
            self.overlay_panel = None

    def _show_notification(self, message, error=False):
        """Show a temporary inline notification at the top of the board."""
        if self.notification_label:
            self.notification_label.destroy()
        
        fg_color = "#e74c3c" if error else "#27ae60"
        bg_color = "#2c3e50"
        
        self.notification_label = tk.Label(
            self.container,
            text=message,
            font=("Arial", 11),
            fg=fg_color,
            bg=bg_color,
            wraplength=400,
            justify=tk.CENTER,
            padx=10,
            pady=8
        )
        self.notification_label.pack(pady=5)
        
        if self.notification_timer:
            self.root.after_cancel(self.notification_timer)
        
        self.notification_timer = self.root.after(4000, self._clear_notification)

    def _clear_notification(self):
        """Clear the notification label."""
        if self.notification_label:
            self.notification_label.destroy()
            self.notification_label = None
        self.notification_timer = None