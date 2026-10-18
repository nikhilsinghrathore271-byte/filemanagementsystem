import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from datetime import datetime


APP_TITLE = "File Management System"
DB_PATH = Path(__file__).with_name("file_activity.db")


class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1000x650")
        self.root.minsize(800, 500)
        self.current_dir = Path.home()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self._setup_database()
        self._build_ui()
        self.refresh_files()

    def _setup_database(self):
        """Create the SQLite activity table if it does not exist."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()

    def log_activity(self, action, item_name, location, details=""):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """INSERT INTO activity_log
                   (timestamp, action, item_name, location, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 action, item_name, str(location), details)
            )
            conn.commit()

    def _build_ui(self):
        # Top toolbar
        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Choose Folder", command=self.choose_folder).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Up One Level", command=self.go_up).pack(side="left", padx=3)
        ttk.Button(toolbar, text="New File", command=self.create_file).pack(side="left", padx=3)
        ttk.Button(toolbar, text="New Folder", command=self.create_folder).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Rename", command=self.rename_item).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Delete", command=self.delete_item).pack(side="left", padx=3)

        # Current directory
        path_frame = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        path_frame.pack(fill="x")
        ttk.Label(path_frame, text="Current folder:").pack(side="left")
        self.path_label = ttk.Label(path_frame, text="", foreground="#1b5eaa")
        self.path_label.pack(side="left", padx=(6, 0), fill="x", expand=True)

        # Search bar
        search_frame = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search name:").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=35)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_files())
        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side="left")

        # File list
        columns = ("name", "type", "size", "modified", "permissions")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Last Modified")
        self.tree.heading("permissions", text="Permissions")
        self.tree.column("name", width=340, anchor="w")
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("modified", width=170, anchor="center")
        self.tree.column("permissions", width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.tree.bind("<Double-1>", self.open_selected)

        # Bottom controls and status
        bottom = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Copy To…", command=self.copy_item).pack(side="left", padx=3)
        ttk.Button(bottom, text="Move To…", command=self.move_item).pack(side="left", padx=3)
        ttk.Button(bottom, text="Activity Log", command=self.show_activity_log).pack(side="left", padx=3)
        ttk.Label(bottom, textvariable=self.status_var).pack(side="right")

    def choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=str(self.current_dir), title="Choose a folder")
        if chosen:
            self.current_dir = Path(chosen)
            self.search_var.set("")
            self.refresh_files()

    def go_up(self):
        parent = self.current_dir.parent
        if parent != self.current_dir:
            self.current_dir = parent
            self.search_var.set("")
            self.refresh_files()

    def clear_search(self):
        self.search_var.set("")
        self.refresh_files()

    def refresh_files(self):
        self.path_label.config(text=str(self.current_dir))
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self.current_dir.exists() or not self.current_dir.is_dir():
            self.status_var.set("Folder is unavailable")
            return

        query = self.search_var.get().strip().casefold()
        try:
            entries = sorted(self.current_dir.iterdir(),
                             key=lambda p: (not p.is_dir(), p.name.casefold()))
            shown = 0
            for path in entries:
                if query and query not in path.name.casefold():
                    continue
                try:
                    stat = path.stat()
                    is_dir = path.is_dir()
                    kind = "Folder" if is_dir else (path.suffix.lower() or "File")
                    size = "—" if is_dir else self._format_size(stat.st_size)
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    permissions = self._permissions(path)
                    self.tree.insert("", "end", iid=str(path), values=(
                        path.name, kind, size, modified, permissions
                    ))
                    shown += 1
                except (OSError, PermissionError):
                    continue
            self.status_var.set(f"{shown} item(s)")
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Folder error", f"Could not read this folder:\n{exc}")
            self.status_var.set("Could not read folder")

    @staticmethod
    def _format_size(size):
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{size} B"

    @staticmethod
    def _permissions(path):
        try:
            mode = path.stat().st_mode
            return "".join([
                "r" if mode & 0o400 else "-",
                "w" if mode & 0o200 else "-",
                "x" if mode & 0o100 else "-"
            ])
        except OSError:
            return "Unknown"

    def _selected_path(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select an item", "Please select a file or folder first.")
            return None
        return Path(selection[0])

    def create_file(self):
        name = simpledialog.askstring("New File", "Enter a file name (example: notes.txt):", parent=self.root)
        if not name:
            return
        if Path(name).name != name or name in {".", ".."}:
            messagebox.showerror("Invalid name", "Enter a file name only, without a folder path.")
            return
        target = self.current_dir / name
        try:
            if target.exists():
                messagebox.showwarning("Already exists", "An item with this name already exists.")
                return
            target.touch(exist_ok=False)
            self.log_activity("CREATE FILE", target.name, target.parent)
            self.refresh_files()
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Could not create file", str(exc))

    def create_folder(self):
        name = simpledialog.askstring("New Folder", "Enter a folder name:", parent=self.root)
        if not name:
            return
        if Path(name).name != name or name in {".", ".."}:
            messagebox.showerror("Invalid name", "Enter a folder name only, without a folder path.")
            return
        target = self.current_dir / name
        try:
            target.mkdir(exist_ok=False)
            self.log_activity("CREATE FOLDER", target.name, target.parent)
            self.refresh_files()
        except FileExistsError:
            messagebox.showwarning("Already exists", "An item with this name already exists.")
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Could not create folder", str(exc))

    def rename_item(self):
        source = self._selected_path()
        if not source:
            return
        new_name = simpledialog.askstring("Rename", "Enter the new name:", initialvalue=source.name, parent=self.root)
        if not new_name or new_name == source.name:
            return
        if Path(new_name).name != new_name or new_name in {".", ".."}:
            messagebox.showerror("Invalid name", "Enter a name only, without a folder path.")
            return
        target = source.with_name(new_name)
        if target.exists():
            messagebox.showwarning("Already exists", "An item with this name already exists.")
            return
        try:
            source.rename(target)
            self.log_activity("RENAME", source.name, source.parent, f"New name: {new_name}")
            self.refresh_files()
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Could not rename item", str(exc))

    def delete_item(self):
        target = self._selected_path()
        if not target:
            return
        item_type = "folder and all its contents" if target.is_dir() else "file"
        confirm = messagebox.askyesno(
            "Confirm deletion",
            f"Are you sure you want to permanently delete this {item_type}?\n\n{target}\n\nThis cannot be undone."
        )
        if not confirm:
            return
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            self.log_activity("DELETE", target.name, target.parent)
            self.refresh_files()
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Could not delete item", str(exc))

    def copy_item(self):
        source = self._selected_path()
        if not source:
            return
        destination = filedialog.askdirectory(title="Choose destination folder", initialdir=str(self.current_dir))
        if not destination:
            return
        target_dir = Path(destination)
        target = target_dir / source.name
        if target.exists():
            messagebox.showwarning("Already exists", "The destination already contains an item with this name.")
            return
        try:
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
            self.log_activity("COPY", source.name, source.parent, f"Destination: {target}")
            self.status_var.set(f"Copied {source.name}")
            self.refresh_files()
        except (OSError, shutil.Error, PermissionError) as exc:
            messagebox.showerror("Could not copy item", str(exc))

    def move_item(self):
        source = self._selected_path()
        if not source:
            return
        destination = filedialog.askdirectory(title="Choose destination folder", initialdir=str(self.current_dir))
        if not destination:
            return
        target = Path(destination) / source.name
        if target.exists():
            messagebox.showwarning("Already exists", "The destination already contains an item with this name.")
            return
        try:
            shutil.move(str(source), str(target))
            self.log_activity("MOVE", source.name, source.parent, f"Destination: {target}")
            self.refresh_files()
        except (OSError, shutil.Error, PermissionError) as exc:
            messagebox.showerror("Could not move item", str(exc))

    def open_selected(self, _event=None):
        selected = self._selected_path()
        if not selected:
            return
        try:
            if selected.is_dir():
                self.current_dir = selected
                self.search_var.set("")
                self.refresh_files()
            else:
                # Use the operating system's default app, with platform-specific support.
                if os.name == "nt":
                    os.startfile(str(selected))
                elif os.uname().sysname == "Darwin":
                    import subprocess
                    subprocess.Popen(["open", str(selected)])
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", str(selected)])
                self.log_activity("OPEN", selected.name, selected.parent)
        except (OSError, AttributeError) as exc:
            messagebox.showerror("Could not open item", str(exc))

    def show_activity_log(self):
        window = tk.Toplevel(self.root)
        window.title("Activity Log")
        window.geometry("850x400")

        columns = ("time", "action", "name", "location", "details")
        log_tree = ttk.Treeview(window, columns=columns, show="headings")
        for col, heading, width in [
            ("time", "Timestamp", 145),
            ("action", "Action", 120),
            ("name", "Item", 140),
            ("location", "Location", 220),
            ("details", "Details", 200)
        ]:
            log_tree.heading(col, text=heading)
            log_tree.column(col, width=width, anchor="w")
        log_tree.pack(fill="both", expand=True, padx=10, pady=10)

        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                """SELECT timestamp, action, item_name, location, details
                   FROM activity_log ORDER BY id DESC LIMIT 500"""
            ).fetchall()
        for row in rows:
            log_tree.insert("", "end", values=row)


def main():
    root = tk.Tk()
    FileManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
