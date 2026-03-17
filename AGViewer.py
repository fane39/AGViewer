import codecs
import re
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

class AGViewer:
    """A Tkinter-based viewer for Amiga Guide files."""
    
    # Class-level regex patterns for parsing
    NODE_PATTERN = re.compile(
        r'@node\s+(?P<name>"[^"]*"|[\w\.]+)(?:\s+(?P<title>"[^"]*"|[^\s\n]+))?.*?\n(?P<body>.*?)(?=\n@endnode|@endnode|\n@node|$)',
        re.DOTALL | re.IGNORECASE
    )
    TAG_PATTERN = re.compile(
        r'@\{\s*(?:(?P<label>"[^"]*"|[^\s}]+)\s+(?P<type>\w+)\s+(?P<target>"[^"]*"|[^\s}]+)(?:\s+(?P<line>\d+))?|(?P<cmd>\w+)(?:\s+(?P<arg>\w+))?)\s*\}',
        re.IGNORECASE
    )

    def __init__(self, root):
        self.root = root
        self.root.title("AGViewer")
        self.nodes = {}
        self.node_list = []
        self.history = [] # Stores (abs_file_path, node_name)
        self.current_node_name = None
        self.current_file_path = None
        self.raw_mode = False
        self.link_counter = 0

        # --- UI Setup ---
        self.btn_frame = tk.Frame(root, bg="#f0f0f0", pady=5)
        self.btn_frame.pack(side="top", fill="x")
        
        # Left-aligned Navigation
        tk.Button(self.btn_frame, text="Open", command=self.open_file, relief="flat", bg="#ddd").pack(side="left", padx=2)
        self.contents_btn = tk.Button(self.btn_frame, text="Contents", command=self.go_home, state="disabled", relief="flat", bg="#ddd")
        self.contents_btn.pack(side="left", padx=2)
        self.index_btn = tk.Button(self.btn_frame, text="Index", command=self.go_index, state="disabled", relief="flat", bg="#ddd")
        self.index_btn.pack(side="left", padx=2)
        self.help_btn = tk.Button(self.btn_frame, text="Help", command=self.go_help, relief="flat", bg="#ddd")
        self.help_btn.pack(side="left", padx=2)
        self.retrace_btn = tk.Button(self.btn_frame, text="Retrace", command=self.go_back, state="disabled", relief="flat", bg="#ddd")
        self.retrace_btn.pack(side="left", padx=2)
        self.prev_btn = tk.Button(self.btn_frame, text="Browse <", command=self.go_prev, state="disabled", relief="flat", bg="#ddd")
        self.prev_btn.pack(side="left", padx=2)
        self.next_btn = tk.Button(self.btn_frame, text="Browse >", command=self.go_next, state="disabled", relief="flat", bg="#ddd")
        self.next_btn.pack(side="left", padx=2)
        
        # Right-aligned Utility
        tk.Button(self.btn_frame, text="Copy", command=self.copy_text, relief="flat", bg="#ddd").pack(side="right", padx=5)
        tk.Button(self.btn_frame, text="Find", command=self.find_text, relief="flat", bg="#ddd").pack(side="right", padx=5)
        self.raw_btn = tk.Button(self.btn_frame, text="Raw", command=self.toggle_raw, relief="flat", bg="#ddd")
        self.raw_btn.pack(side="right", padx=5)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w", font=("Segoe UI", 9)).pack(side="bottom", fill="x")

        text_frame = tk.Frame(root)
        text_frame.pack(expand=True, fill="both")
        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side="right", fill="y")
        self.text_widget = tk.Text(text_frame, wrap="word", width=95, height=35, padx=20, pady=20, 
                                   font=("Consolas", 11), yscrollcommand=self.scrollbar.set,
                                   bg="#fff", fg="#333", insertbackground="black")
        self.text_widget.pack(side="left", expand=True, fill="both")
        self.scrollbar.config(command=self.text_widget.yview)
        
        # Tag configuration
        self.text_widget.tag_config("link", foreground="black", background="#e1e1e1", relief="raised", borderwidth=1)
        self.text_widget.tag_config("btn_line", spacing1=10, spacing3=10)
        self.text_widget.tag_config("bold", font=("Consolas", 11, "bold"))
        self.text_widget.tag_config("italic", font=("Consolas", 11, "italic"))
        self.text_widget.tag_config("bold_italic", font=("Consolas", 11, "bold italic"))
        self.text_widget.tag_config("underline", underline=True)
        self.text_widget.tag_config("jcenter", justify="center")
        self.text_widget.tag_config("jright", justify="right")
        self.text_widget.tag_config("jleft", justify="left")
        self.text_widget.tag_config("search", background="yellow")
        
        self.colors = {"text": "#333", "highlight": "#d9534f", "shadow": "#777", "shine": "#bbb", "fill": "#337ab7", "filltext": "white", "background": "white", "back": "white"}
        for name, color in self.colors.items():
            self.text_widget.tag_config(f"fg_{name}", foreground=color)
            self.text_widget.tag_config(f"bg_{name}", background=color)

        self.text_widget.tag_raise("link")
        self.text_widget.tag_raise("search")
        self.text_widget.tag_bind("link", "<Button-1>", self.on_link_click)
        self.text_widget.tag_bind("link", "<Enter>", self.on_link_enter)
        self.text_widget.tag_bind("link", "<Leave>", self.on_link_leave)
        self.root.bind("<Control-f>", lambda e: self.find_text())

    def resolve_tags(self, styles, extra=None):
        s = set(styles)
        if extra: s.update(extra)
        tags = list(s)
        if "bold" in s and "italic" in s:
            if "bold" in tags: tags.remove("bold")
            if "italic" in tags: tags.remove("italic")
            tags.append("bold_italic")
        return tuple(tags)

    def on_link_enter(self, event):
        self.text_widget.config(cursor="hand2")
        idx = self.text_widget.index(f"@{event.x},{event.y}")
        for tag in self.text_widget.tag_names(idx):
            if tag.startswith("inst_"): self.text_widget.tag_config(tag, background="#d0d0d0")

    def on_link_leave(self, event):
        self.text_widget.config(cursor="arrow")
        for tag in self.text_widget.tag_names():
            if tag.startswith("inst_"): self.text_widget.tag_config(tag, background="#e1e1e1")

    def toggle_raw(self):
        self.raw_mode = not self.raw_mode
        self.raw_btn.config(text="Formatted" if self.raw_mode else "Raw")
        if self.current_node_name: self.show_node(self.current_node_name, add_to_history=False)

    def find_text(self):
        query = simpledialog.askstring("Find", "Enter text to find:")
        if not query: return
        self.text_widget.tag_remove("search", "1.0", tk.END)
        start_pos = "1.0"
        while True:
            start_pos = self.text_widget.search(query, start_pos, stopindex=tk.END, nocase=True)
            if not start_pos: break
            end_pos = f"{start_pos}+{len(query)}c"
            self.text_widget.tag_add("search", start_pos, end_pos)
            start_pos = end_pos

    def copy_text(self):
        try: text_to_copy = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: text_to_copy = self.text_widget.get(1.0, tk.END)
        self.root.clipboard_clear(); self.root.clipboard_append(text_to_copy.rstrip('\n'))
        self.status_var.set("Text copied to clipboard")

    def open_file(self, file_path=None, clear_history=True, auto_show=True):
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("AmigaGuide Files", "*.guide"), ("All Files", "*.*")])
        if file_path:
            self.root.config(cursor="watch"); self.root.update()
            try:
                with codecs.open(file_path, 'r', 'iso-8859-1') as file:
                    content = file.read().replace('\r\n', '\n')
                    self.parse_guide(content)
                    self.current_file_path = os.path.abspath(file_path)
                    if clear_history:
                        self.history = []
                        self.retrace_btn.config(state="disabled")
                    
                    self.current_node_name = None
                    if auto_show:
                        for sn in ['main', 'index', 'toc']:
                            if sn in self.nodes: self.show_node(sn, False); break
                        else:
                            if self.node_list: self.show_node(self.node_list[0], False)
                    
                    self.contents_btn.config(state="normal")
                    self.index_btn.config(state="normal" if "index" in self.nodes else "disabled")
                    self.next_btn.config(state="normal" if len(self.node_list) > 1 else "disabled")
                    self.prev_btn.config(state="normal" if len(self.node_list) > 1 else "disabled")
                    self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e: messagebox.showerror("Error", f"Could not read file: {e}")
            finally: self.root.config(cursor="arrow")

    def parse_guide(self, content):
        self.nodes, self.node_list = {}, []
        for match in self.NODE_PATTERN.finditer(content):
            name = match.group('name').strip('"').lower().strip()
            title = match.group('title').strip('"') if match.group('title') else name
            body = "\n".join([l for l in match.group('body').strip().splitlines() if not l.strip().upper().startswith(('@TOC', '@INDEX', '@DATABASE', '@$VER', '@REMARK', '@AUTHOR', '@(C)', '@FONT'))])
            self.nodes[name] = {"title": title, "body": body}
            self.node_list.append(name)
        if not self.nodes: self.nodes["main"], self.node_list = {"title": "Raw File", "body": content}, ["main"]

    def show_node(self, node_name, add_to_history=True):
        node_name = node_name.strip().lower()
        if node_name == self.current_node_name and add_to_history: return
        if node_name not in self.nodes:
            messagebox.showwarning("Missing Node", f"Node '{node_name}' not found.")
            return
        
        if add_to_history and self.current_node_name:
            self.history.append((self.current_file_path, self.current_node_name))
            self.retrace_btn.config(state="normal")
            
        self.current_node_name, node = node_name, self.nodes[node_name]
        self.root.title(f"AGViewer - {node['title']}")
        self.text_widget.config(state="normal"); self.text_widget.delete(1.0, tk.END)
        
        if self.raw_mode: self.text_widget.insert(tk.END, node['body'])
        else:
            current_styles, known_cmds = set(), {"b", "ub", "i", "ui", "u", "uu", "plain", "body", "pard", "fg", "bg", "jleft", "jcenter", "jright"}
            for line in node['body'].splitlines():
                if line.strip().startswith("@") and not "@{" in line: continue
                line_extra = ["btn_line"] if "@{" in line else []
                last_pos = 0
                for match in self.TAG_PATTERN.finditer(line):
                    segment = line[last_pos:match.start()].replace(r'\@', '@').replace(r'\\', '\\')
                    self.text_widget.insert(tk.END, segment, self.resolve_tags(current_styles, line_extra))
                    if match.group('label'):
                        label = match.group('label').strip('"').replace(r'\@', '@').replace(r'\\', '\\')
                        ltype, target = match.group('type').lower(), match.group('target').strip('"').strip()
                        inst_tag, action_tag = f"inst_{self.link_counter}", f"action_{ltype}:{target}"
                        self.link_counter += 1; self.text_widget.tag_config(inst_tag, background="#e1e1e1")
                        self.text_widget.insert(tk.END, f" {label} ", self.resolve_tags(current_styles, ["link", inst_tag, action_tag]))
                    elif match.group('cmd'):
                        cmd, arg = match.group('cmd').lower(), (match.group('arg').lower() if match.group('arg') else None)
                        if cmd in known_cmds:
                            if cmd == "b": current_styles.add("bold")
                            elif cmd == "ub": current_styles.discard("bold")
                            elif cmd == "i": current_styles.add("italic")
                            elif cmd == "ui": current_styles.discard("italic")
                            elif cmd == "u": current_styles.add("underline")
                            elif cmd == "uu": current_styles.discard("underline")
                            elif cmd in ["jleft", "jcenter", "jright"]: current_styles = {s for s in current_styles if not s.startswith("j")}; current_styles.add(cmd)
                            elif cmd == "fg" and arg in self.colors: current_styles = {s for s in current_styles if not s.startswith("fg_")}; current_styles.add(f"fg_{arg}")
                            elif cmd == "bg" and arg in self.colors: current_styles = {s for s in current_styles if not s.startswith("bg_")}; current_styles.add(f"bg_{arg}")
                            elif cmd == "plain": current_styles -= {"bold", "italic", "underline"}
                            elif cmd == "body": current_styles = {s for s in current_styles if s.startswith("j")}
                            elif cmd == "pard": current_styles = {s for s in current_styles if not s.startswith("j")}
                        else:
                            target = "amigaguide.guide/main" if cmd == "amigaguide" else cmd
                            label = "AmigaGuide" if cmd == "amigaguide" else match.group('cmd').replace(r'\@', '@').replace(r'\\', '\\')
                            inst_tag, action_tag = f"inst_{self.link_counter}", f"action_link:{target}"
                            self.link_counter += 1; self.text_widget.tag_config(inst_tag, background="#e1e1e1")
                            self.text_widget.insert(tk.END, f" {label} ", self.resolve_tags(current_styles, ["link", inst_tag, action_tag]))
                    last_pos = match.end()
                self.text_widget.insert(tk.END, line[last_pos:].replace(r'\@', '@').replace(r'\\', '\\') + "\n", self.resolve_tags(current_styles, line_extra))
        self.text_widget.see("1.0"); self.text_widget.config(state="disabled"); self.root.update_idletasks()

    def go_home(self):
        for sn in ['main', 'index', 'toc']:
            if sn in self.nodes: self.show_node(sn); return
        if self.node_list: self.show_node(self.node_list[0])

    def go_index(self):
        if "index" in self.nodes: self.show_node("index")
        else: messagebox.showinfo("Index", "No index node found.")

    def go_help(self):
        messagebox.showinfo("Help", "AGViewer Help\n\n- Open: Load .guide\n- Contents/Index: Main/Index nodes\n- Retrace: Back in history\n- Browse: Next/Prev nodes\n- Find: Search text")

    def go_back(self):
        if self.history:
            prev_file, prev_node = self.history.pop()
            if prev_file != self.current_file_path: self.open_file(prev_file, False, False)
            self.show_node(prev_node, False)
            if not self.history: self.retrace_btn.config(state="disabled")

    def go_next(self):
        if self.current_node_name in self.node_list:
            idx = self.node_list.index(self.current_node_name)
            if idx < len(self.node_list) - 1: self.show_node(self.node_list[idx+1])

    def go_prev(self):
        if self.current_node_name in self.node_list:
            idx = self.node_list.index(self.current_node_name)
            if idx > 0: self.show_node(self.node_list[idx-1])

    def on_link_click(self, event):
        idx = self.text_widget.index(f"@{event.x},{event.y}")
        for tag in self.text_widget.tag_names(idx):
            if tag.startswith("action_"):
                data = tag[len("action_"):]
                if ":" in data:
                    ltype, val = data.split(":", 1)
                    if ltype == "link": self.handle_link(val)
                    elif ltype == "system": self.handle_system(val)
                    elif ltype == "beep": self.root.bell()
                return "break"

    def handle_link(self, target):
        original_target, target = target, target.replace('\\', '/')
        if "/" in target or ":" in target:
            if ":" in target: target = target.split(":")[-1]
            parts = target.split('/')
            filename, node = ("/".join(parts[:-1]), parts[-1]) if len(parts) > 1 else (target, "main")
            base = os.path.dirname(self.current_file_path) if self.current_file_path else "."
            possible_paths = [os.path.join(base, filename), os.path.join(base, filename + ".guide"), os.path.join(base, target), os.path.join(base, target + ".guide")]
            for path in possible_paths:
                if os.path.exists(path) and os.path.isfile(path):
                    abs_path = os.path.abspath(path)
                    if abs_path != self.current_file_path: self.open_file(abs_path, False, False)
                    self.show_node(node); return
        self.show_node(original_target)

    def handle_system(self, cmd):
        if messagebox.askyesno("System Command", f"Execute this command?\n\n{cmd}"):
            try: subprocess.Popen(cmd.split('>')[0].strip(), shell=True)
            except Exception as e: messagebox.showerror("Error", f"Failed: {e}")

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("950x750"); AGViewer(root); root.mainloop()
