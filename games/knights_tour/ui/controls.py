import tkinter as tk
from tkinter import ttk
from ui.comparison import ComparisonBoard

class Controls:
    def __init__(self, root, board):
        self.root = root
        self.board = board

        # Frame for controls
        control_frame = ttk.Frame(root)
        control_frame.pack(pady=10)

        # Board size control
        ttk.Label(control_frame, text="Board Size:").grid(row=0, column=0, padx=5)
        self.size_var = tk.IntVar(value=8)
        size_spinbox = ttk.Spinbox(control_frame, from_=4, to=12, textvariable=self.size_var, width=5)
        size_spinbox.grid(row=0, column=1, padx=5)

        # Apply size button
        ttk.Button(control_frame, text="Apply Size", command=self.apply_size).grid(row=0, column=2, padx=5)

        # Start button
        ttk.Button(control_frame, text="Start Tour", command=self.board.start_animation).grid(row=0, column=3, padx=5)

        # Compare Algorithms button
        ttk.Button(control_frame, text="Compare Algorithms", command=self.compare_algorithms).grid(row=0, column=4, padx=5)

        # Reset button
        ttk.Button(control_frame, text="Reset", command=self.board.reset_board).grid(row=0, column=5, padx=5)

        # Back to Menu button
        ttk.Button(control_frame, text="Back to Menu", command=self.back_to_menu).grid(row=0, column=6, padx=5)

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
        
        def on_comparison_close():
            """Callback when comparison is done"""
            comparison_window.destroy()
        
        # Create the comparison board
        ComparisonBoard(comparison_window, size=size, start_pos=start_pos, on_close=on_comparison_close)

    def back_to_menu(self):
        """Return to main menu"""
        if self.board.on_exit_menu:
            self.board.on_exit_menu()