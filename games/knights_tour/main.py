import tkinter as tk
from ui.menu import MainMenu

root = tk.Tk()
root.geometry("800x900")  # Set initial resizable size
root.minsize(600, 600)    # Set minimum size for usability
root.resizable(True, True)  # Make window resizable from the start
app = MainMenu(root)

root.mainloop()