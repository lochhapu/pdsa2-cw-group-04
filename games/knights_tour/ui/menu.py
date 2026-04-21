import tkinter as tk
from ui.board import Board
from ui.controls import Controls
from db.db_helper import DatabaseHelper
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Knight's Tour Problem")
        # Initialize menu size
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c3e50")  # background color

        self.menu_frame = None
        self.board = None
        self.controls = None

        # Container frame (for better alignment)
        frame = tk.Frame(root, bg="#2c3e50")
        frame.pack(expand=True)
        self.menu_frame = frame

        # Title
        title = tk.Label(
            frame,
            text="Knight's Tour Problem",
            font=("Arial", 22, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=30)

        # Buttons
        self.create_button(frame, "Start Game", self.start_game)
        self.create_button(frame, "View Scores", self.view_scores)
        self.create_button(frame, "Exit", root.quit)

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

    def start_game(self):
        # Prompt for player name and optionally cheat code
        dialog_result = self._show_player_name_dialog()
        if not dialog_result or not dialog_result.get("name"):
            return  # User cancelled
        
        player_name = dialog_result["name"]
        cheat_code = dialog_result.get("cheat_code")
        
        # Get or create player in database
        try:
            db = DatabaseHelper()
            player_id = db.create_or_get_player(player_name, cheat_code)
            db.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to create player: {e}")
            return
        
        # Hide menu
        self.menu_frame.pack_forget()
        
        # Un-constrain geometry so board and HUD can fit properly
        self.root.geometry("") 
        self.root.resizable(True, True)
        self.root.configure(bg="SystemButtonFace") # Reset to default OS bg
        
        # Create board and controls HUD with player_id and callback
        self.board = Board(self.root, player_id=player_id, on_exit_menu=self.return_to_menu, cheat_code=cheat_code)
        self.controls = Controls(self.root, self.board)

    def _show_player_name_dialog(self):
        """Show custom player name input dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter Your Name")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center dialog on parent window
        dialog.transient(self.root)
        
        # Title label
        title_label = tk.Label(
            dialog,
            text="What's your name, brave knight?",
            font=("Arial", 14, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=10)
        
        # Input field
        name_entry = tk.Entry(
            dialog,
            font=("Arial", 12),
            width=25,
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            bd=2
        )
        name_entry.pack(pady=10)
        name_entry.focus()
        
        # Cheat code Title label
        cheat_label = tk.Label(
            dialog,
            text="(Optional) Enter cheat code:",
            font=("Arial", 12),
            fg="#2c3e50"
        )
        cheat_label.pack(pady=5)
        
        # Cheat code Input field
        cheat_entry = tk.Entry(
            dialog,
            font=("Arial", 12),
            width=25,
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            bd=2
        )
        cheat_entry.pack(pady=5)
        
        # Result variable
        result = {"name": None, "cheat_code": None}
        
        def on_submit():
            name = name_entry.get().strip()
            cheat_code = cheat_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Empty Name", "Please enter a valid name!")
                return
            if len(name) > 50:
                messagebox.showwarning("Name Too Long", "Name must be 50 characters or less!")
                return
            result["name"] = name
            
            if cheat_code:
                result["cheat_code"] = cheat_code
                
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Buttons frame
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        submit_btn = tk.Button(
            button_frame,
            text="Start Adventure",
            command=on_submit,
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
            command=on_cancel,
            font=("Arial", 11),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            width=15,
            bd=0,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Allow Enter key to submit
        name_entry.bind("<Return>", lambda e: on_submit())
        cheat_entry.bind("<Return>", lambda e: on_submit())
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return result

    def return_to_menu(self):
        """Return from game to main menu."""
        # Destroy board and controls
        if self.board:
            self.board.canvas.destroy()
            self.board = None
        if self.controls:
            self.controls = None
        
        # Clean up any remaining widgets except menu_frame
        for widget in self.root.winfo_children():
            if widget != self.menu_frame:
                widget.destroy()
        
        # Reset window geometry and resizability
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c3e50")
        
        # Show menu frame again
        self.menu_frame.pack(expand=True)

    def view_scores(self):
        try:
            db = DatabaseHelper()
            leaderboard = db.get_leaderboard(limit=10, order_by="wins")
            
            top = tk.Toplevel(self.root)
            top.title("Leaderboard")
            top.geometry("550x350")
            top.configure(bg="#2c3e50")
            top.resizable(False, False)
            
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
            
            # Make the window modal
            top.transient(self.root)
            top.grab_set()
            self.root.wait_window(top)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load leaderboard: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()

    