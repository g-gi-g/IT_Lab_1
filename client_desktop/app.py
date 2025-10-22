import io
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

from .sync import FolderSync

class PythonSyntaxHighlighter:
    """Improved Python syntax highlighter for tkinter Text widget"""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()
    
    def setup_tags(self):
        """Configure text tags for syntax highlighting"""
        # Keywords
        self.text_widget.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 10, "bold"))
        # Strings
        self.text_widget.tag_configure("string", foreground="#008000", font=("Consolas", 10))
        # Comments
        self.text_widget.tag_configure("comment", foreground="#808080", font=("Consolas", 10, "italic"))
        # Numbers
        self.text_widget.tag_configure("number", foreground="#FF8000", font=("Consolas", 10))
        # Functions
        self.text_widget.tag_configure("function", foreground="#800080", font=("Consolas", 10, "bold"))
        # Operators
        self.text_widget.tag_configure("operator", foreground="#FF0000", font=("Consolas", 10))
        # Built-ins
        self.text_widget.tag_configure("builtin", foreground="#000080", font=("Consolas", 10, "bold"))
    
    def highlight_python(self, content):
        """Apply syntax highlighting to Python code"""
        # Clear existing tags
        for tag in ["keyword", "string", "comment", "number", "function", "operator", "builtin"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)
        
        # Get all text content
        text_content = self.text_widget.get("1.0", tk.END)
        if not text_content.strip():
            return
        
        # Process line by line for better accuracy
        lines = text_content.split('\n')
        current_line = 1
        
        for line in lines:
            if not line.strip():
                current_line += 1
                continue
                
            # Highlight comments first (they have priority)
            self._highlight_line_comments(line, current_line)
            
            # Highlight strings (both single and multi-line)
            self._highlight_line_strings(line, current_line)
            
            # Highlight keywords
            self._highlight_line_keywords(line, current_line)
            
            # Highlight numbers
            self._highlight_line_numbers(line, current_line)
            
            # Highlight function definitions
            self._highlight_line_functions(line, current_line)
            
            # Highlight operators
            self._highlight_line_operators(line, current_line)
            
            # Highlight built-ins
            self._highlight_line_builtins(line, current_line)
            
            current_line += 1
    
    def _highlight_line_comments(self, line, line_num):
        """Highlight comments in a line"""
        comment_start = line.find('#')
        if comment_start != -1:
            start_pos = f"{line_num}.{comment_start}"
            end_pos = f"{line_num}.{len(line)}"
            self.text_widget.tag_add("comment", start_pos, end_pos)
    
    def _highlight_line_strings(self, line, line_num):
        """Highlight strings in a line"""
        # Single quotes
        self._highlight_quoted_strings(line, line_num, "'", "'")
        # Double quotes
        self._highlight_quoted_strings(line, line_num, '"', '"')
        # Triple quotes
        self._highlight_quoted_strings(line, line_num, '"""', '"""')
        self._highlight_quoted_strings(line, line_num, "'''", "'''")
    
    def _highlight_quoted_strings(self, line, line_num, start_char, end_char):
        """Highlight quoted strings"""
        start_idx = 0
        while True:
            start_pos = line.find(start_char, start_idx)
            if start_pos == -1:
                break
            
            # Find matching end quote
            end_pos = line.find(end_char, start_pos + len(start_char))
            if end_pos == -1:
                # String continues to end of line
                end_pos = len(line)
            else:
                end_pos += len(end_char)
            
            # Apply highlighting
            start_tag = f"{line_num}.{start_pos}"
            end_tag = f"{line_num}.{end_pos}"
            self.text_widget.tag_add("string", start_tag, end_tag)
            
            start_idx = end_pos
    
    def _highlight_line_keywords(self, line, line_num):
        """Highlight Python keywords"""
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
            'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global',
            'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print',
            'raise', 'return', 'try', 'while', 'with', 'yield', 'True', 'False', 'None'
        ]
        
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            start = 0
            while True:
                match = re.search(pattern, line[start:])
                if not match:
                    break
                
                start_pos = start + match.start()
                end_pos = start + match.end()
                
                # Check if this is inside a string or comment
                if not self._is_inside_string_or_comment(line, start_pos):
                    start_tag = f"{line_num}.{start_pos}"
                    end_tag = f"{line_num}.{end_pos}"
                    self.text_widget.tag_add("keyword", start_tag, end_tag)
                
                start = start_pos + 1
    
    def _highlight_line_numbers(self, line, line_num):
        """Highlight numbers"""
        # Find all numbers (integers and floats)
        for match in re.finditer(r'\b\d+\.?\d*\b', line):
            start_pos = match.start()
            end_pos = match.end()
            
            # Check if this is inside a string or comment
            if not self._is_inside_string_or_comment(line, start_pos):
                start_tag = f"{line_num}.{start_pos}"
                end_tag = f"{line_num}.{end_pos}"
                self.text_widget.tag_add("number", start_tag, end_tag)
    
    def _highlight_line_functions(self, line, line_num):
        """Highlight function definitions"""
        # Look for 'def function_name(' pattern
        for match in re.finditer(r'\bdef\s+(\w+)', line):
            start_pos = match.start()
            end_pos = match.end()
            
            # Check if this is inside a string or comment
            if not self._is_inside_string_or_comment(line, start_pos):
                start_tag = f"{line_num}.{start_pos}"
                end_tag = f"{line_num}.{end_pos}"
                self.text_widget.tag_add("function", start_tag, end_tag)
    
    def _highlight_line_operators(self, line, line_num):
        """Highlight operators"""
        operators = ['+', '-', '*', '/', '%', '=', '<', '>', '!', '&', '|', '^', '~', '==', '!=', '<=', '>=', '+=', '-=', '*=', '/=']
        
        for op in operators:
            start_idx = 0
            while True:
                pos = line.find(op, start_idx)
                if pos == -1:
                    break
                
                # Check if this is inside a string or comment
                if not self._is_inside_string_or_comment(line, pos):
                    start_tag = f"{line_num}.{pos}"
                    end_tag = f"{line_num}.{pos + len(op)}"
                    self.text_widget.tag_add("operator", start_tag, end_tag)
                
                start_idx = pos + 1
    
    def _highlight_line_builtins(self, line, line_num):
        """Highlight built-in functions"""
        builtins = ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set', 'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed']
        
        for builtin in builtins:
            pattern = r'\b' + re.escape(builtin) + r'\b'
            start = 0
            while True:
                match = re.search(pattern, line[start:])
                if not match:
                    break
                
                start_pos = start + match.start()
                end_pos = start + match.end()
                
                # Check if this is inside a string or comment
                if not self._is_inside_string_or_comment(line, start_pos):
                    start_tag = f"{line_num}.{start_pos}"
                    end_tag = f"{line_num}.{end_pos}"
                    self.text_widget.tag_add("builtin", start_tag, end_tag)
                
                start = start_pos + 1
    
    def _is_inside_string_or_comment(self, line, pos):
        """Check if position is inside a string or comment"""
        # Check for comment
        comment_pos = line.find('#')
        if comment_pos != -1 and pos >= comment_pos:
            return True
        
        # Check for strings
        in_string = False
        string_char = None
        i = 0
        while i < pos:
            if line[i] in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = line[i]
                elif line[i] == string_char:
                    in_string = False
                    string_char = None
            i += 1
        
        return in_string

# Try to import tkinterdnd2 for better drag-n-drop support
try:
    import tkinterdnd2 as tkdnd
    HAS_TKINTERDND2 = True
except ImportError:
    HAS_TKINTERDND2 = False


API_URL = os.environ.get("API_URL", "http://127.0.0.1:5000")


@dataclass
class Session:
    token: Optional[str] = None
    username: Optional[str] = None


class DriveClientApp(tkdnd.Tk if HAS_TKINTERDND2 else tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Mini Drive Client")
        self.geometry("1000x650")
        self.session = Session()

        self.columns_visibility: Dict[str, bool] = {
            "name": True,
            "extension": True,
            "created_at": True,
            "updated_at": True,
            "uploader": True,
            "editor": True,
        }

        self.preview_image_tk: Optional[ImageTk.PhotoImage] = None
        
        # Sync variables
        self.sync_folder: Optional[Path] = None
        self.sync_thread: Optional[threading.Thread] = None
        self.sync_running = False

        self._build_ui()

    # UI
    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(top, text="Користувач:").pack(side=tk.LEFT)
        self.username_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.username_var, width=16).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="Пароль:").pack(side=tk.LEFT)
        self.password_var = tk.StringVar()
        ttk.Entry(top, show="*", textvariable=self.password_var, width=16).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Увійти", command=self.login).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Реєстрація", command=self.register).pack(side=tk.LEFT, padx=4)

        self.filter_var = tk.StringVar(value="all")
        ttk.Label(top, text="Фільтр:").pack(side=tk.LEFT, padx=(16, 4))
        ttk.Combobox(top, state="readonly", values=["all", "py", "jpg"], textvariable=self.filter_var, width=6,
                     postcommand=self.refresh_files).pack(side=tk.LEFT)

        self.sort_var = tk.StringVar(value="uploader")
        self.order_var = tk.StringVar(value="asc")
        ttk.Label(top, text="Сортування:").pack(side=tk.LEFT, padx=(16, 4))
        ttk.Combobox(top, state="readonly", values=["uploader"], textvariable=self.sort_var, width=9,
                     postcommand=self.refresh_files).pack(side=tk.LEFT)
        ttk.Combobox(top, state="readonly", values=["asc", "desc"], textvariable=self.order_var, width=6,
                     postcommand=self.refresh_files).pack(side=tk.LEFT, padx=(4, 0))

        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Button(actions, text="Завантажити файл", command=self.upload_file_dialog).pack(side=tk.LEFT)
        ttk.Button(actions, text="Вивантажити", command=self.download_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Видалити", command=self.delete_selected).pack(side=tk.LEFT)
        
        # Sync buttons
        ttk.Separator(actions, orient='vertical').pack(side=tk.LEFT, padx=6, fill=tk.Y)
        ttk.Button(actions, text="📁 Вибрати папку", command=self.select_sync_folder).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="⬆️ Завантажити у", command=self.sync_upload_only).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions, text="⬇️ Завантажити з", command=self.sync_download_only).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions, text="🔄 Синхронізувати", command=self.sync_bidirectional).pack(side=tk.LEFT, padx=2)

        # columns toggle
        columns_toggle = ttk.Menubutton(actions, text="Стовпці")
        self.columns_menu = tk.Menu(columns_toggle, tearoff=0)
        columns_toggle["menu"] = self.columns_menu
        columns_toggle.pack(side=tk.LEFT, padx=12)
        for col in ["extension", "created_at", "updated_at", "uploader", "editor"]:
            self.columns_menu.add_checkbutton(
                label=col,
                onvalue=True,
                offvalue=False,
                variable=tk.BooleanVar(value=True),
                command=lambda c=col: self.toggle_column(c),
            )

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(expand=True, fill=tk.BOTH, padx=8, pady=6)

        # table
        self.tree = ttk.Treeview(body, columns=("name", "extension", "created_at", "updated_at", "uploader", "editor"), show="headings")
        for c, w in [("name", 220), ("extension", 70), ("created_at", 160), ("updated_at", 160), ("uploader", 120), ("editor", 120)]:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, stretch=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_preview())
        body.add(self.tree, weight=3)

        # preview area
        right = ttk.Frame(body)
        body.add(right, weight=2)
        self.preview_text = scrolledtext.ScrolledText(right, height=10, font=("Consolas", 10))
        self.preview_text.pack(expand=True, fill=tk.BOTH)
        self.preview_label = ttk.Label(right)
        self.preview_label.pack()
        
        # Initialize syntax highlighter
        self.syntax_highlighter = PythonSyntaxHighlighter(self.preview_text)

        # drag-n-drop support
        self.setup_drag_drop()

    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        if HAS_TKINTERDND2:
            try:
                self.drop_target_register('DND_Files')
                self.dnd_bind('<<Drop>>', self._on_drop_files)
                return
            except Exception as e:
                print(f"Failed to setup drag-n-drop: {e}")
        
        # If no drag-n-drop available, add a button for multiple file selection
        self.add_multiple_file_button()

    def add_multiple_file_button(self):
        """Add button for selecting multiple files if drag-n-drop is not available"""
        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Button(actions, text="Завантажити кілька файлів", command=self.upload_multiple_files_dialog).pack(side=tk.LEFT, padx=6)

    # actions
    def auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.session.token}"} if self.session.token else {}

    def register(self) -> None:
        try:
            r = requests.post(f"{API_URL}/auth/register", json={
                "username": self.username_var.get().strip(),
                "password": self.password_var.get(),
            }, timeout=10)
            if r.status_code == 201:
                messagebox.showinfo("OK", "Реєстрація успішна. Тепер увійдіть.")
            else:
                messagebox.showerror("Помилка", r.json().get("message", "Помилка реєстрації"))
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def login(self) -> None:
        try:
            r = requests.post(f"{API_URL}/auth/login", json={
                "username": self.username_var.get().strip(),
                "password": self.password_var.get(),
            }, timeout=10)
            if r.ok:
                data = r.json()
                self.session.token = data["access_token"]
                self.session.username = data["user"]["username"]
                self.refresh_files()
            else:
                messagebox.showerror("Помилка", r.json().get("message", "Невірні облікові дані"))
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def refresh_files(self) -> None:
        if not self.session.token:
            return
        params = {
            "type": self.filter_var.get(),
            "sort_by": self.sort_var.get(),
            "order": self.order_var.get(),
        }
        try:
            r = requests.get(f"{API_URL}/files", headers=self.auth_headers(), params=params, timeout=10)
            r.raise_for_status()
            items = r.json()
            for i in self.tree.get_children():
                self.tree.delete(i)
            for it in items:
                values = (it["name"], it["extension"], it["created_at"], it["updated_at"], it.get("uploader"), it.get("editor"))
                node = self.tree.insert('', tk.END, values=values)
                # Store id in tags instead of trying to set non-existent column
                self.tree.item(node, tags=(str(it["id"]),))
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def _get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        # recover id from tag
        tags = self.tree.item(sel[0], 'tags')
        try:
            return int(tags[0]) if tags else None
        except Exception:
            return None

    def upload_file_dialog(self) -> None:
        path = filedialog.askopenfilename(title="Виберіть файл")
        if not path:
            return
        self._upload_file(Path(path))

    def upload_multiple_files_dialog(self) -> None:
        paths = filedialog.askopenfilenames(title="Виберіть файли")
        if not paths:
            return
        for path in paths:
            self._upload_file(Path(path))

    def _on_drop_files(self, event):  # type: ignore[no-redef]
        files = self.tk.splitlist(event.data)  # type: ignore[attr-defined]
        for f in files:
            p = Path(f)
            if p.exists():
                self._upload_file(p)

    def _upload_file(self, path: Path) -> None:
        if not self.session.token:
            return
        try:
            with open(path, 'rb') as fh:
                r = requests.post(f"{API_URL}/files", headers=self.auth_headers(), files={"file": (path.name, fh)})
            if r.status_code in (200, 201):
                self.refresh_files()
            else:
                messagebox.showerror("Помилка", r.text)
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def download_selected(self) -> None:
        fid = self._get_selected_id()
        if fid is None:
            return
        save_to = filedialog.asksaveasfilename(title="Зберегти як")
        if not save_to:
            return
        try:
            r = requests.get(f"{API_URL}/files/{fid}/download", headers=self.auth_headers(), stream=True)
            r.raise_for_status()
            with open(save_to, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def delete_selected(self) -> None:
        fid = self._get_selected_id()
        if fid is None:
            return
        if not messagebox.askyesno("Підтвердження", "Видалити файл?"):
            return
        try:
            r = requests.delete(f"{API_URL}/files/{fid}", headers=self.auth_headers())
            r.raise_for_status()
            self.refresh_files()
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def toggle_column(self, column: str) -> None:
        self.columns_visibility[column] = not self.columns_visibility.get(column, True)
        display = [c for c, v in self.columns_visibility.items() if v]
        display = ["name"] + [c for c in ["extension", "created_at", "updated_at", "uploader", "editor"] if self.columns_visibility.get(c, True)]
        self.tree["displaycolumns"] = display

    def show_preview(self) -> None:
        fid = self._get_selected_id()
        if fid is None:
            return
        try:
            # First, get selected row to know extension
            item = self.tree.item(self.tree.selection()[0])
            vals = item.get('values', [])
            extension = vals[1] if len(vals) > 1 else ''
            if extension == '.py':
                r = requests.get(f"{API_URL}/files/{fid}/preview", headers=self.auth_headers(), timeout=10)
                r.raise_for_status()
                data = r.json()
                self.preview_label.configure(image='')
                self.preview_text.configure(state=tk.NORMAL)
                self.preview_text.delete('1.0', tk.END)
                content = data.get('content', '')
                self.preview_text.insert('1.0', content)
                # Apply syntax highlighting
                self.syntax_highlighter.highlight_python(content)
                self.preview_text.configure(state=tk.NORMAL)
            elif extension == '.jpg':
                r = requests.get(f"{API_URL}/files/{fid}/preview", headers=self.auth_headers(), timeout=10)
                r.raise_for_status()
                self.preview_text.delete('1.0', tk.END)
                img = Image.open(io.BytesIO(r.content))
                img.thumbnail((400, 400))
                self.preview_image_tk = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=self.preview_image_tk)
            else:
                self.preview_text.delete('1.0', tk.END)
                self.preview_label.configure(image='')
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    # Sync methods
    def select_sync_folder(self):
        """Select folder for synchronization"""
        folder = filedialog.askdirectory(title="Виберіть папку для синхронізації")
        if folder:
            self.sync_folder = Path(folder)
            messagebox.showinfo("Папка вибрана", f"Папка для синхронізації: {self.sync_folder}")

    def sync_upload_only(self):
        """Upload local files to server"""
        if not self.sync_folder:
            messagebox.showwarning("Помилка", "Спочатку виберіть папку для синхронізації")
            return
        
        if not self.session.token:
            messagebox.showerror("Помилка", "Потрібно увійти в систему")
            return

        def sync_thread():
            try:
                sync = FolderSync(API_URL, self.session.token, self.sync_folder)
                results = sync.sync_upload_only()
                
                # Show results in UI thread
                self.after(0, lambda: self._show_sync_results("Завантаження", results))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Помилка синхронізації", str(e)))

        threading.Thread(target=sync_thread, daemon=True).start()

    def sync_download_only(self):
        """Download files from server to local folder"""
        if not self.sync_folder:
            messagebox.showwarning("Помилка", "Спочатку виберіть папку для синхронізації")
            return
        
        if not self.session.token:
            messagebox.showerror("Помилка", "Потрібно увійти в систему")
            return

        def sync_thread():
            try:
                sync = FolderSync(API_URL, self.session.token, self.sync_folder)
                results = sync.sync_download_only()
                
                # Show results in UI thread
                self.after(0, lambda: self._show_sync_results("Завантаження з сервера", results))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Помилка синхронізації", str(e)))

        threading.Thread(target=sync_thread, daemon=True).start()

    def sync_bidirectional(self):
        """Bidirectional sync: upload and download"""
        if not self.sync_folder:
            messagebox.showwarning("Помилка", "Спочатку виберіть папку для синхронізації")
            return
        
        if not self.session.token:
            messagebox.showerror("Помилка", "Потрібно увійти в систему")
            return

        def sync_thread():
            try:
                sync = FolderSync(API_URL, self.session.token, self.sync_folder)
                results = sync.sync_bidirectional()
                
                # Show results in UI thread
                self.after(0, lambda: self._show_sync_results("Двостороння синхронізація", results))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Помилка синхронізації", str(e)))

        threading.Thread(target=sync_thread, daemon=True).start()

    def _show_sync_results(self, operation: str, results: Dict):
        """Show sync results in a dialog"""
        total_ops = results.get('uploaded', 0) + results.get('downloaded', 0)
        total_errors = results.get('errors', 0)
        total_skipped = results.get('skipped', 0)
        
        message = f"{operation} завершено:\n\n"
        message += f"✅ Оброблено: {total_ops} файлів\n"
        message += f"⏭️ Пропущено: {total_skipped} файлів\n"
        message += f"❌ Помилок: {total_errors}\n\n"
        
        if results.get('files'):
            message += "Деталі:\n"
            for file_info in results['files'][:10]:  # Show first 10 files
                message += f"• {file_info}\n"
            if len(results['files']) > 10:
                message += f"... та ще {len(results['files']) - 10} файлів"
        
        if total_errors > 0:
            messagebox.showwarning("Синхронізація з помилками", message)
        else:
            messagebox.showinfo("Синхронізація завершена", message)
        
        # Refresh file list
        self.refresh_files()


if __name__ == "__main__":
    app = DriveClientApp()
    app.mainloop()


