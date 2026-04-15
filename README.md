# Application Launcher Menu – Setup & Run Guide

This guide explains how to set up a Python virtual environment, install dependencies, and use the launcher to run multiple independent Tkinter applications – each in its own folder with its own SQL database – without modifying their original code.

---

## 1. Prerequisites

- **Python 3.6 or higher** — check with `python --version` or `python3 --version`
- **pip** — usually comes bundled with Python
- **tkinter** — usually included, but may need a separate install on Linux

---

## 2. Set Up a Virtual Environment

A virtual environment keeps dependencies isolated from your system Python.

### Windows

Open Command Prompt or PowerShell inside the launcher folder:

```cmd
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

Open a terminal inside the launcher folder:

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` appear at the beginning of your command prompt in both cases.

---

## 3. Install Dependencies

With the virtual environment activated, run:

```bash
pip install -r requirements.txt
```

> If your `requirements.txt` is empty, you can skip this step.

---

## 4. Run the Launcher

Make sure your virtual environment is still activated (`(venv)` is visible in the prompt), then run:

```bash
python launcher.py
```

A window will appear with a button for each app. Click a button to open that app in its own independent window.

---

## 5. How Database Isolation Works

The launcher uses `subprocess.Popen` with `cwd` set to each app's folder. This means:

- `sqlite3.connect('data.db')` looks for `data.db` **inside the app's own folder**, not the launcher's folder.
- SQLAlchemy with a relative path like `sqlite:///myapp.db` also resolves relative to the app's folder.
- Each app runs in its own process and memory space, so database connections and locks never interfere with each other.

**Result:** Ten apps, each with their own `database.db` — zero conflicts.

---

## 6. Apps That Use Absolute Database Paths

If an app uses an absolute path (e.g. `C:\data\app.db` or `/home/user/app.db`), the `cwd` setting has no effect on that path. The app still runs correctly, but its database won't be folder-isolated.

To maintain isolation, use relative paths in your apps, or build the path dynamically:

```python
import os
db_path = os.path.join(os.path.dirname(__file__), 'myapp.db')
engine = create_engine(f'sqlite:///{db_path}')
```

---

## 7. Stopping Apps

- Close each app window normally — the launcher is unaffected.
- Closing the launcher does **not** close any running apps; they continue independently.
- To kill all apps on launcher exit, add process tracking (advanced — not covered here).

---

## 8. Troubleshooting

### `tkinter` not found (Linux)

```bash
sudo apt-get install python3-tk   # Debian / Ubuntu
```

### `No module named 'sqlalchemy'`

Activate your virtual environment, then install:

```bash
pip install sqlalchemy
```

### App launches but can't find its database

Make sure the app uses relative paths or `os.path.dirname(__file__)`:

```python
# ❌ Avoid:
conn = sqlite3.connect('data.db')

# ✅ Use instead:
import os
db_file = os.path.join(os.path.dirname(__file__), 'data.db')
conn = sqlite3.connect(db_file)
```

### Launcher button is disabled (shows MISSING)

Check that the path in `self.apps` matches the actual folder and filename. For example, if your app is at `my_tool/start.py`:

```python
"Tool": os.path.join("my_tool", "start.py")
```

---

## 9. Next Steps

- Add more apps by extending the `self.apps` dictionary.
- Customise the launcher's appearance (colours, fonts, icons).
- Add a **"Kill all apps"** button if workflow requires it.
- Use `.env` files to manage database credentials via environment variables.

---

## Quick Reference: Commands

| Step                 | Windows                           | macOS / Linux              |
| -------------------- | --------------------------------- | -------------------------- |
| Create venv          | `python -m venv venv`             | `python3 -m venv venv`     |
| Activate venv        | `venv\Scripts\activate`           | `source venv/bin/activate` |
| Install dependencies | `pip install -r requirements.txt` | same                       |
| Run launcher         | `python launcher.py`              | same                       |

> Once the virtual environment is set up, you only need to **activate it** and run `python launcher.py` each time.
