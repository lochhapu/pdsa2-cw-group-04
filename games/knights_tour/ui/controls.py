import tkinter as tk
from ui.comparison import ComparisonBoard

class Controls:
    def __init__(self, root, board):
        self.root = root
        self.board = board
        
        # Set root window background to match the theme
        root.configure(bg="#2c3e50")

        # Frame for controls with dark background and padding - centered below board
        control_frame = tk.Frame(root, bg="#2c3e50")
        control_frame.pack(pady=15)

        # Left section: Board size control
        size_frame = tk.Frame(control_frame, bg="#2c3e50")
        size_frame.pack(side=tk.LEFT, padx=10)
        
        size_label = tk.Label(
            size_frame,
            text="Board Size:",
            font=("Arial", 11),
            bg="#2c3e50",
            fg="white"
        )
        size_label.pack(side=tk.LEFT, padx=5)
        
        self.size_var = tk.IntVar(value=8)
        size_spinbox = tk.Spinbox(
            size_frame,
            from_=4,
            to=12,
            textvariable=self.size_var,
            width=5,
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.FLAT,
            bd=2
        )
        size_spinbox.pack(side=tk.LEFT, padx=5)

        # Right section: Action buttons
        button_frame = tk.Frame(control_frame, bg="#2c3e50")
        button_frame.pack(side=tk.LEFT, padx=10)

        # Apply size button
        self._create_button(button_frame, "Apply Size", self.apply_size).pack(side=tk.LEFT, padx=5)

        # Compare Algorithms button
        self._create_button(button_frame, "Compare", self.compare_algorithms).pack(side=tk.LEFT, padx=5)

        # Reset button
        self._create_button(button_frame, "Reset", self.board.reset_board).pack(side=tk.LEFT, padx=5)

        # Back to Menu button
        self._create_button(button_frame, "Back to Menu", self.back_to_menu, bg="#e74c3c", hover_bg="#c0392b").pack(side=tk.LEFT, padx=5)

    def _create_button(self, parent, text, command, bg="#3498db", hover_bg="#2980b9"):
        """Create a styled button that matches the menu theme."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 10),
            bg=bg,
            fg="white",
            activebackground=hover_bg,
            activeforeground="white",
            width=12,
            height=1,
            bd=0,
            cursor="hand2",
            padx=5,
            pady=3
        )
        
        # Add hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        
        return btn

    def apply_size(self):
        size = self.size_var.get()
        self.board.set_size(size)

    def compare_algorithms(self):
        """Open algorithm comparison window"""
        # Get current board size and starting position
        size = self.size_var.get()
        start_pos = self.board.player_path[0] if self.board.player_path else (0, 0)
        
        # Calculate cell size and window dimensions
        cell_size = max(30, min(50, 400 // size))
        board_pixel_size = size * cell_size
        window_width = board_pixel_size * 2 + 150  # Two boards + padding
        window_height = board_pixel_size + 250  # Board + title + labels + results
        
        # Create a new window for comparison
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title("Algorithm Comparison")
        comparison_window.geometry(f"{window_width}x{window_height}")
        comparison_window.resizable(True, True)
        comparison_window.configure(bg="#2c3e50")
        
        def on_comparison_close():
            """Callback when comparison is done"""
            comparison_window.destroy()
        
        # Create the comparison board
        ComparisonBoard(comparison_window, size=size, start_pos=start_pos, on_close=on_comparison_close)

    def back_to_menu(self):
        """Return to main menu"""
        if self.board.on_exit_menu:
            self.board.on_exit_menu()