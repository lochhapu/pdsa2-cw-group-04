import tkinter as tk
import tkinter.ttk as ttk
from ui.board import Board
from ui.controls import Controls
from db.db_helper import DatabaseHelper
try:
    from chart_algo import display_algorithm_chart
except ImportError:
    display_algorithm_chart = None
import os
from PIL import Image, ImageTk, ImageOps

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Knight's Tour")
        self.root.configure(bg="#2c3e50")  # background color

        self.menu_frame = None
        self.profile_panel = None
        self.board = None
        self.controls = None
        self.notification_label = None
        self.notification_timer = None

        # Container frame (for better alignment)
        frame = tk.Frame(root, bg="#2c3e50")
        frame.pack(expand=True, fill=tk.BOTH)
        self.menu_frame = frame

        # Title
        title = tk.Label(
            frame,
            text="Knight's Tour",
            font=("Arial", 22, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=10)

        # Animation
        self.idle_frames_right = []
        self.idle_frames_left = []
        self.attack_frames_right = []
        self.attack_frames_left = []
        self.facing_right = True
        self.current_action = "idle"
        self.attack_frame_idx = 0
        self.pending_command = None
        self.action_in_progress = False

        self.idle_frame_idx = 0
        self.animation_job = None
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            idle_path = os.path.join(base_dir, "assets", "knight", "IDLE.png")
            attack_path = os.path.join(base_dir, "assets", "knight", "ATTACK 1.png")
            
            sheet = Image.open(idle_path)
            num_frames = 7
            frame_width = sheet.width // num_frames
            scale_factor = 2 
            
            for i in range(num_frames):
                frame_img = sheet.crop((i * frame_width, 0, (i + 1) * frame_width, sheet.height))
                frame_img = frame_img.resize((frame_width * scale_factor, sheet.height * scale_factor), Image.NEAREST)
                self.idle_frames_right.append(ImageTk.PhotoImage(frame_img))
                self.idle_frames_left.append(ImageTk.PhotoImage(ImageOps.mirror(frame_img)))
                
            try:
                sheet_atk = Image.open(attack_path)
                num_frames_atk = sheet_atk.width // frame_width
                for i in range(num_frames_atk):
                    frame_img = sheet_atk.crop((i * frame_width, 0, (i + 1) * frame_width, sheet_atk.height))
                    frame_img = frame_img.resize((frame_width * scale_factor, sheet_atk.height * scale_factor), Image.NEAREST)
                    self.attack_frames_right.append(ImageTk.PhotoImage(frame_img))
                    self.attack_frames_left.append(ImageTk.PhotoImage(ImageOps.mirror(frame_img)))
            except Exception as e:
                print("Failed to load ATTACK animation:", e)
                
            self.anim_label = tk.Label(frame, bg="#2c3e50")
            self.anim_label.pack(pady=10)
            self._animate_knight()
        except Exception as e:
            print("Failed to load animations:", e)

        # Mouse tracking for mirroring
        self.root.bind('<Motion>', self._on_mouse_motion)

        # Buttons
        self.create_button(frame, "Start Game", self.wrap_command(self.start_game))
        self.create_button(frame, "View Scores", self.wrap_command(self.view_scores))
        self.create_button(frame, "View Chart", self.wrap_command(self.view_chart))
        self.create_button(frame, "Exit", self.wrap_command(root.quit))

    def _on_mouse_motion(self, event):
        if self.current_action != "attack":
            screen_width = self.root.winfo_width()
            if screen_width > 0:
                self.facing_right = (event.x > screen_width / 2)

    def wrap_command(self, cmd):
        def wrapped(*args, **kwargs):
            if self.action_in_progress:
                return
            self.action_in_progress = True
            
            if self.attack_frames_right:
                self.current_action = "attack"
                self.attack_frame_idx = 0
                self.pending_command = cmd
            else:
                self.action_in_progress = False
                cmd()
        return wrapped

    def create_button(self, parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 14),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            width=20,
            height=2,
            bd=0,
            cursor="hand2"
        )
        btn.pack(pady=10)

        # Hover effect (because we have standards now)
        btn.bind("<Enter>", lambda e: btn.config(bg="#2980b9"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#3498db"))

    def _animate_knight(self):
        if not hasattr(self, 'anim_label') or not self.anim_label.winfo_exists():
            return
            
        if self.current_action == "idle":
            frames = self.idle_frames_right if self.facing_right else self.idle_frames_left
            if frames:
                self.anim_label.config(image=frames[self.idle_frame_idx])
                self.idle_frame_idx = (self.idle_frame_idx + 1) % len(frames)
        elif self.current_action == "attack":
            frames = self.attack_frames_right if self.facing_right else self.attack_frames_left
            if frames:
                if self.attack_frame_idx < len(frames):
                    self.anim_label.config(image=frames[self.attack_frame_idx])
                    self.attack_frame_idx += 1
                else:
                    # Attack finished
                    self.current_action = "idle"
                    self.attack_frame_idx = 0
                    if self.pending_command:
                        cmd = self.pending_command
                        self.pending_command = None
                        self.root.after(50, lambda: self._execute_delayed_command(cmd))
        
        self.animation_job = self.root.after(100, self._animate_knight)

    def _execute_delayed_command(self, cmd):
        self.action_in_progress = False
        cmd()

    def start_game(self):
        """Show profile selection panel instead of dialog."""
        # Hide main menu buttons
        for widget in self.menu_frame.winfo_children():
            if widget not in [self.anim_label]:
                widget.pack_forget()
        
        # Show profile selection panel
        self._show_profile_selection_panel()

    def _show_profile_selection_panel(self):
        """Show inline profile selection panel."""
        if self.profile_panel:
            self.profile_panel.destroy()
        
        self.profile_panel = tk.Frame(self.menu_frame, bg="#34495e", relief=tk.RAISED, bd=2)
        self.profile_panel.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            self.profile_panel,
            text="Choose your profile, brave knight!",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#34495e"
        )
        title_label.pack(pady=10)
        
        # Get profiles
        try:
            db = DatabaseHelper()
            players = db.get_all_players()
            db.close()
        except:
            players = []
        
        profiles = [p[1] for p in players[:15]]
        options = profiles + ["+ Create New Profile"]
        
        # Profile dropdown
        profile_var = tk.StringVar()
        profile_var.set(profiles[0] if profiles else "+ Create New Profile")
        
        profile_dropdown = ttk.Combobox(
            self.profile_panel,
            textvariable=profile_var,
            values=options,
            state="readonly",
            font=("Arial", 12),
            width=25
        )
        profile_dropdown.pack(pady=5)
        
        # New name entry frame (hidden by default)
        new_name_frame = tk.Frame(self.profile_panel, bg="#34495e")
        
        name_label = tk.Label(
            new_name_frame,
            text="New Profile Name:",
            font=("Arial", 10),
            fg="white",
            bg="#34495e"
        )
        name_label.pack()
        
        name_entry = tk.Entry(
            new_name_frame,
            font=("Arial", 12),
            width=25,
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            bd=2
        )
        name_entry.pack(pady=5)
        new_name_frame.pack_forget()
        
        if not profiles:
            new_name_frame.pack(pady=5, after=profile_dropdown)
            name_entry.focus()
        
        def on_profile_change(*args):
            if profile_var.get() == "+ Create New Profile":
                new_name_frame.pack(pady=5, after=profile_dropdown)
                name_entry.focus()
            else:
                new_name_frame.pack_forget()
        
        profile_var.trace_add("write", on_profile_change)
        
        # Cheat code
        cheat_label = tk.Label(
            self.profile_panel,
            text="(Optional) Enter cheat code:",
            font=("Arial", 10),
            fg="white",
            bg="#34495e"
        )
        cheat_label.pack(pady=5)
        
        cheat_entry = tk.Entry(
            self.profile_panel,
            font=("Arial", 12),
            width=25,
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            bd=2
        )
        cheat_entry.pack(pady=5)
        
        # Notification label for validation errors
        error_label = tk.Label(
            self.profile_panel,
            text="",
            font=("Arial", 10),
            fg="#e74c3c",
            bg="#34495e"
        )
        error_label.pack(pady=5)
        
        def on_submit():
            is_new = (profile_var.get() == "+ Create New Profile")
            
            # Validation
            if is_new:
                if len(profiles) >= 15:
                    error_label.config(text="⚠ Maximum of 15 profiles reached!")
                    return
                name = name_entry.get().strip()
                if not name:
                    error_label.config(text="⚠ Please enter a valid name!")
                    return
                if len(name) > 50:
                    error_label.config(text="⚠ Name must be 50 characters or less!")
                    return
                if name in profiles:
                    error_label.config(text="⚠ Profile already exists!")
                    return
            else:
                name = profile_var.get()
            
            cheat_code = cheat_entry.get().strip() or None
            
            # Create player
            try:
                db = DatabaseHelper()
                player_id = db.create_or_get_player(name, cheat_code)
                db.close()
            except Exception as e:
                error_label.config(text=f"⚠ Database error: {str(e)[:40]}")
                return
            
            # Start game
            self._start_game_with_player(player_id, cheat_code)
        
        def on_cancel():
            # Hide profile panel and show menu again
            self.profile_panel.destroy()
            self.profile_panel = None
            for widget in self.menu_frame.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.profile_panel, bg="#34495e")
        button_frame.pack(pady=15)
        
        submit_btn = tk.Button(
            button_frame,
            text="Start Adventure",
            command=self.wrap_command(on_submit),
            font=("Arial", 11),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            width=15,
            bd=0,
            cursor="hand2"
        )
        submit_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.wrap_command(on_cancel),
            font=("Arial", 11),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            width=15,
            bd=0,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        name_entry.bind("<Return>", lambda e: self.wrap_command(on_submit)())
        cheat_entry.bind("<Return>", lambda e: self.wrap_command(on_submit)())

    def _start_game_with_player(self, player_id, cheat_code):
        """Start the game with the given player."""
        # Hide menu
        self.menu_frame.pack_forget()
        
        # Reset window background
        self.root.configure(bg="SystemButtonFace")
        
        # Create board and controls HUD with player_id and callback
        self.board = Board(self.root, player_id=player_id, on_exit_menu=self.return_to_menu, cheat_code=cheat_code)
        self.controls = Controls(self.root, self.board)

    def return_to_menu(self):
        """Return from game to main menu."""
        # Destroy board and controls
        if self.board:
            if hasattr(self.board, 'container'):
                self.board.container.destroy()
            else:
                self.board.canvas.destroy()
            self.board = None
        if self.controls:
            self.controls = None
        if self.profile_panel:
            self.profile_panel.destroy()
            self.profile_panel = None
        
        # Clean up any remaining widgets except menu_frame
        for widget in self.root.winfo_children():
            if widget != self.menu_frame:
                widget.destroy()
        
        # Reset window background
        self.root.configure(bg="#2c3e50")
        
        # Show menu frame again
        self.menu_frame.pack(expand=True, fill=tk.BOTH)
        
        # Show all buttons (recreate them if needed)
        for widget in self.menu_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.pack(pady=10)

    def view_scores(self):
        try:
            db = DatabaseHelper()
            leaderboard = db.get_leaderboard(limit=10, order_by="wins")
            
            top = tk.Toplevel(self.root)
            top.title("Leaderboard")
            top.geometry("550x350")
            top.configure(bg="#2c3e50")
            top.resizable(True, True)
            
            title = tk.Label(top, text="Leaderboard", font=("Arial", 18, "bold"), bg="#2c3e50", fg="white")
            title.pack(pady=15)
            
            if not leaderboard:
                empty = tk.Label(top, text="No scores available yet.", font=("Arial", 12), bg="#2c3e50", fg="white")
                empty.pack(pady=20)
            else:
                header_frame = tk.Frame(top, bg="#34495e")
                header_frame.pack(fill=tk.X, padx=20, pady=5)
                
                headers = ["Rank", "Name", "Total Games", "Wins", "Win Rate %"]
                widths = [6, 15, 10, 10, 10]
                
                for i, (h, w) in enumerate(zip(headers, widths)):
                    lbl = tk.Label(header_frame, text=h, font=("Arial", 11, "bold"), bg="#34495e", fg="white", width=w)
                    lbl.grid(row=0, column=i, padx=2, pady=5)
                
                for idx, (player_name, total_games, total_wins, win_rate) in enumerate(leaderboard):
                    row_frame = tk.Frame(top, bg="#2c3e50")
                    row_frame.pack(fill=tk.X, padx=20, pady=2)
                    
                    data = [str(idx+1), player_name, str(total_games), str(total_wins), f"{win_rate}%"]
                    for i, (val, w) in enumerate(zip(data, widths)):
                        lbl = tk.Label(row_frame, text=val, font=("Arial", 11), bg="#2c3e50", fg="white", width=w)
                        lbl.grid(row=0, column=i, padx=2)
            
            close_btn = tk.Button(top, text="Close", command=top.destroy, font=("Arial", 12),
                                  bg="#e74c3c", fg="white", activebackground="#c0392b", activeforeground="white", bd=0, padx=20, pady=5)
            close_btn.pack(pady=20)
            
        except Exception as e:
            self._show_notification(f"Error loading leaderboard: {str(e)[:50]}", error=True)

    def view_chart(self):
        """Display the algorithm comparison chart."""
        if display_algorithm_chart is None:
            self._show_notification("Chart module not available. Install matplotlib.", error=True)
            return

        try:
            display_algorithm_chart()
        except Exception as e:
            self._show_notification(f"Failed to display chart: {str(e)[:50]}", error=True)

    def _show_notification(self, message, error=False):
        """Show a temporary inline notification."""
        if self.notification_label:
            self.notification_label.destroy()
        
        fg_color = "#e74c3c" if error else "#27ae60"
        
        self.notification_label = tk.Label(
            self.root,
            text=message,
            font=("Arial", 10),
            fg=fg_color,
            bg="#2c3e50"
        )
        self.notification_label.pack(pady=5)
        
        if self.notification_timer:
            self.root.after_cancel(self.notification_timer)
        
        self.notification_timer = self.root.after(4000, lambda: self._clear_notification())

    def _clear_notification(self):
        """Clear the notification label."""
        if self.notification_label:
            self.notification_label.destroy()
            self.notification_label = None
        self.notification_timer = None


if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()

    