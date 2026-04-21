import tkinter as tk
from tkinter import messagebox
import time
from PIL import Image, ImageTk
from logic.knights_tour import knights_tour, knights_tour_backtracking
from logic.moves import MOVES
from utils.helpers import get_center
from ui.animation import KnightSprite

class ComparisonBoard:
    def __init__(self, root, size=8, start_pos=(0, 0), on_close=None):
        """
        Create a side-by-side comparison board showing Warnsdorff vs Backtracking
        
        Args:
            root: Tkinter root
            size: Board size (default 8)
            start_pos: Starting position as tuple (row, col)
            on_close: Callback when comparison is done
        """
        self.root = root
        self.size = size
        self.start_pos = start_pos
        self.on_close = on_close
        # Adaptive cell size: smaller for larger boards
        self.cell_size = max(30, min(50, 400 // size))
        
        self.execution_times = {"warnsdorff": None, "backtracking": None}
        self.paths = {"warnsdorff": None, "backtracking": None}
        
        # Create main container
        self.main_frame = tk.Frame(root, bg="#2c3e50")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            self.main_frame,
            text="Algorithm Comparison: Warnsdorff vs Backtracking",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=10)
        
        # Canvas container for both boards
        canvas_container = tk.Frame(self.main_frame, bg="#2c3e50")
        canvas_container.pack(pady=10)
        
        # Left side - Warnsdorff
        left_frame = tk.Frame(canvas_container, bg="#2c3e50")
        left_frame.pack(side=tk.LEFT, padx=20)
        
        warnsdorff_label = tk.Label(
            left_frame,
            text="Warnsdorff's Algorithm",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="#3498db"
        )
        warnsdorff_label.pack()
        
        self.canvas_left = tk.Canvas(left_frame, bg="gray20")
        self.canvas_left.pack()
        
        self.warnsdorff_time_label = tk.Label(
            left_frame,
            text="Running...",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white"
        )
        self.warnsdorff_time_label.pack(pady=5)
        
        # Right side - Backtracking
        right_frame = tk.Frame(canvas_container, bg="#2c3e50")
        right_frame.pack(side=tk.LEFT, padx=20)
        
        backtracking_label = tk.Label(
            right_frame,
            text="Backtracking Algorithm",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="#e74c3c"
        )
        backtracking_label.pack()
        
        self.canvas_right = tk.Canvas(right_frame, bg="gray20")
        self.canvas_right.pack()
        
        self.backtracking_time_label = tk.Label(
            right_frame,
            text="Running...",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white"
        )
        self.backtracking_time_label.pack(pady=5)
        
        # Results frame
        self.results_frame = tk.Frame(self.main_frame, bg="#2c3e50")
        self.results_frame.pack(pady=10, fill=tk.X)
        
        # Close button
        button_frame = tk.Frame(self.main_frame, bg="#2c3e50")
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Close",
            command=self.close_comparison,
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            width=15
        ).pack()
        
        # Initialize boards
        self.board_states_left = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        self.board_states_right = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        
        self.draw_empty_board(self.canvas_left)
        self.draw_empty_board(self.canvas_right)
        
        # Run algorithms
        self.root.after(500, self.run_algorithms)
    
    def draw_empty_board(self, canvas):
        """Draw an empty board"""
        canvas.delete("all")
        board_size = self.size * self.cell_size
        canvas.config(width=board_size, height=board_size)
        
        for r in range(self.size):
            for c in range(self.size):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = (c + 1) * self.cell_size, (r + 1) * self.cell_size
                
                color = "white" if (r + c) % 2 == 0 else "gray40"
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray60")
    
    def draw_solution_path(self, canvas, path):
        """Draw the solution path on canvas"""
        self.draw_empty_board(canvas)
        
        if not path:
            return
        
        # Draw path with numbers
        for step, (r, c) in enumerate(path):
            x1, y1 = c * self.cell_size, r * self.cell_size
            x2, y2 = (c + 1) * self.cell_size, (r + 1) * self.cell_size
            
            # Highlight the cell
            color = "white" if (r + c) % 2 == 0 else "gray40"
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray60")
            
            # Draw step number
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            canvas.create_text(center_x, center_y, text=str(step + 1), font=("Arial", 8), fill="black")
        
        # Draw path lines connecting the moves
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            x1 = c1 * self.cell_size + self.cell_size / 2
            y1 = r1 * self.cell_size + self.cell_size / 2
            x2 = c2 * self.cell_size + self.cell_size / 2
            y2 = r2 * self.cell_size + self.cell_size / 2
            canvas.create_line(x1, y1, x2, y2, fill="blue", width=2, dash=(2, 2))
    
    def run_algorithms(self):
        """Run both algorithms and display results"""
        # Run Warnsdorff
        start_time = time.time()
        warnsdorff_path = knights_tour(self.size, start=self.start_pos)
        warnsdorff_time = (time.time() - start_time) * 1000  # Convert to ms
        
        self.execution_times["warnsdorff"] = warnsdorff_time
        self.paths["warnsdorff"] = warnsdorff_path
        
        self.warnsdorff_time_label.config(
            text=f"Time: {warnsdorff_time:.2f} ms",
            fg="#2ecc71" if warnsdorff_path else "#e74c3c"
        )
        
        if warnsdorff_path:
            self.draw_solution_path(self.canvas_left, warnsdorff_path)
        else:
            self.warnsdorff_time_label.config(text="No solution found")
        
        # Run Backtracking
        start_time = time.time()
        backtracking_path = knights_tour_backtracking(self.size, start=self.start_pos)
        backtracking_time = (time.time() - start_time) * 1000  # Convert to ms
        
        self.execution_times["backtracking"] = backtracking_time
        self.paths["backtracking"] = backtracking_path
        
        self.backtracking_time_label.config(
            text=f"Time: {backtracking_time:.2f} ms",
            fg="#2ecc71" if backtracking_path else "#e74c3c"
        )
        
        if backtracking_path:
            self.draw_solution_path(self.canvas_right, backtracking_path)
        else:
            self.backtracking_time_label.config(text="No solution found")
        
        # Show results comparison
        self.display_results()
    
    def display_results(self):
        """Display comparison results"""
        self.results_frame.destroy()
        self.results_frame = tk.Frame(self.main_frame, bg="#2c3e50")
        self.results_frame.pack(pady=10, fill=tk.X)
        
        warnsdorff_time = self.execution_times["warnsdorff"]
        backtracking_time = self.execution_times["backtracking"]
        
        warnsdorff_path = self.paths["warnsdorff"]
        backtracking_path = self.paths["backtracking"]
        
        results_text = ""
        
        if warnsdorff_path and backtracking_path:
            results_text = f"✓ Both algorithms found a solution!\n"
            results_text += f"Warnsdorff: {warnsdorff_time:.2f} ms | Backtracking: {backtracking_time:.2f} ms\n"
            
            if warnsdorff_time < backtracking_time:
                faster_algo = "Warnsdorff"
                time_diff = backtracking_time - warnsdorff_time
                results_text += f"Winner: {faster_algo} ({time_diff:.2f} ms faster)"
            else:
                faster_algo = "Backtracking"
                time_diff = warnsdorff_time - backtracking_time
                results_text += f"Winner: {faster_algo} ({time_diff:.2f} ms faster)"
        elif warnsdorff_path:
            results_text = f"Warnsdorff found a solution ({warnsdorff_time:.2f} ms)\nBacktracking: No solution found"
        elif backtracking_path:
            results_text = f"Backtracking found a solution ({backtracking_time:.2f} ms)\nWarnsdorff: No solution found"
        else:
            results_text = "Neither algorithm found a solution"
        
        results_label = tk.Label(
            self.results_frame,
            text=results_text,
            font=("Arial", 11),
            bg="#2c3e50",
            fg="white",
            justify=tk.CENTER
        )
        results_label.pack()
    
    def close_comparison(self):
        """Close the comparison window"""
        self.main_frame.destroy()
        if self.on_close:
            self.on_close()
