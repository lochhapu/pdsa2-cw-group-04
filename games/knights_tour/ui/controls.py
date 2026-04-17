import tkinter as tk
from tkinter import ttk

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

        # Reset button
        ttk.Button(control_frame, text="Reset", command=self.board.reset_board).grid(row=0, column=4, padx=5)

    def apply_size(self):
        size = self.size_var.get()
        self.board.set_size(size)