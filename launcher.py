import tkinter as tk
from tkinter import ttk
import subprocess
import os
import sys

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("PDSA2 Game Launcher")
        self.root.geometry("400x400")
        
        # Dictionary of apps (name: path to main file)
        self.apps = {
            "Minimum Cost Assignment": os.path.join("games", "minimum_cost", "main.py"),
            "Knights Tour": os.path.join("games", "knights_tour", "main.py"),
            "Snakes & Ladders": os.path.join("games", "snakes_and_ladders", "main.py"),
            "Traffic Simulation": os.path.join("games", "traffic_sim", "main.py"),
            "16 Queens": os.path.join("games", "queens", "main.py"),
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="Select Game to Launch", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=20)
        
        # Buttons for each app
        for app_name, app_path in self.apps.items():
            btn = tk.Button(self.root, text=app_name, 
                          command=lambda path=app_path: self.launch_app(path),
                          width=30, height=2)
            btn.pack(pady=5)
        
        # Exit button
        exit_btn = tk.Button(self.root, text="Exit", command=self.root.quit,
                           bg="red", fg="white")
        exit_btn.pack(pady=20)
    
    def launch_app(self, app_path):
        """Launch an app in a separate process"""
        try:
            # Get the directory containing the app
            app_dir = os.path.dirname(app_path)
            app_file = os.path.basename(app_path)
            
            # Change to app's directory and run it
            subprocess.Popen(
                [sys.executable, app_file],
                cwd=app_dir,  # Important: runs in app's own folder
                stdout=None,
                stderr=None
            )
        except Exception as e:
            # Show error if app fails to launch
            error_window = tk.Toplevel(self.root)
            error_window.title("Launch Error")
            tk.Label(error_window, text=f"Failed to launch {app_path}\n{str(e)}").pack(pady=20)
            tk.Button(error_window, text="OK", command=error_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()