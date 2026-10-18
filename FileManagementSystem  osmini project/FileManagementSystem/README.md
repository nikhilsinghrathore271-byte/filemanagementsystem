# File Management System — OS Mini Project

A desktop file manager built with Python, Tkinter, and SQLite.

## Features
- Browse folders and display files
- Search items by name
- Create files and folders
- Rename and permanently delete selected items
- Copy and move files/folders
- Show file size, last modified time, and basic permissions
- Record operations in a SQLite activity log
- Double-click folders to open them; double-click files to open with the default app

## Requirements
- Python 3.10 or later recommended
- Tkinter (included with most standard Python installations)
- SQLite (included with Python)

No third-party Python packages are required.

## Run in VS Code
1. Extract the project ZIP.
2. Open the `FileManagementSystem` folder in VS Code.
3. Open the terminal in VS Code.
4. Run:

   ```bash
   python main.py
   ```

   On some systems, use `python3 main.py`.

The app creates `file_activity.db` beside `main.py` the first time it runs.

## Important safety note
Deletion is permanent. The application asks for confirmation first. Test with a sample folder containing non-important files before using it on real data. File permissions and the ability to open files vary by operating system.
