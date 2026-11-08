#!/usr/bin/env python3
"""Premium Apps — lightweight macOS launcher. Uses only Python's standard library."""
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

APP_NAME = "Premium Apps"
STORAGE = Path.home() / "Library" / "Application Support" / APP_NAME / "Apps"
BG = "#111114"
PANEL = "#1b1b20"
GOLD = "#d6b900"
TEXT = "#f4f4f4"
MUTED = "#a4a4ad"


class PremiumApps:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("850x620")
        self.root.minsize(720, 520)
        self.root.configure(bg=BG)
        STORAGE.mkdir(parents=True, exist_ok=True)
        self.username = ""
        self.is_admin = False
        self.selected = None
        self.show_login()

    def clear(self):
        self.root.unbind("<Return>")
        for child in self.root.winfo_children():
            child.destroy()

    def label(self, parent, text, size=11, color=TEXT, bold=False, **kwargs):
        return tk.Label(parent, text=text, font=("Helvetica", size, "bold" if bold else "normal"),
                        bg=kwargs.pop("bg", BG), fg=color, **kwargs)

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, font=("Helvetica", 10, "bold"),
                         bg=GOLD if primary else "#303038", fg="#111114" if primary else TEXT,
                         activebackground="#ead23a", activeforeground="#111114",
                         relief="flat", padx=16, pady=9, cursor="hand2")

    def show_login(self):
        self.clear()
        wrap = tk.Frame(self.root, bg=BG)
        wrap.place(relx=.5, rely=.48, anchor="center")
        self.label(wrap, "✦", 44, GOLD, True).pack(pady=(0, 4))
        self.label(wrap, "PREMIUM APPS", 26, GOLD, True).pack()
        self.label(wrap, "Your personal application library", 11, MUTED).pack(pady=(6, 28))
        form = tk.Frame(wrap, bg=BG)
        form.pack()
        self.label(form, "Username", 10, MUTED).grid(row=0, column=0, sticky="w", pady=7)
        self.user_entry = tk.Entry(form, width=30, font=("Helvetica", 12), bg=PANEL,
                                   fg=TEXT, insertbackground=TEXT, relief="flat")
        self.user_entry.grid(row=0, column=1, padx=(18, 0), ipady=8)
        self.label(form, "Password", 10, MUTED).grid(row=1, column=0, sticky="w", pady=7)
        self.pass_entry = tk.Entry(form, width=30, show="•", font=("Helvetica", 12), bg=PANEL,
                                   fg=TEXT, insertbackground=TEXT, relief="flat")
        self.pass_entry.grid(row=1, column=1, padx=(18, 0), ipady=8)
        self.button(wrap, "OPEN LIBRARY", self.login, True).pack(pady=28, fill="x")
        self.user_entry.focus_set()
        self.root.bind("<Return>", lambda _event: self.login())

    def login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        if not username or not password:
            messagebox.showwarning("Missing details", "Enter a username and password.")
            return
        self.username = username
        # PremiumOwner opens the local import controls. This is a local UI role,
        # not a remotely verified account or a security boundary.
        self.is_admin = username.casefold() == "premiumowner"
        self.show_dashboard()

    def show_dashboard(self):
        self.clear()
        top = tk.Frame(self.root, bg="#202026", height=58)
        top.pack(fill="x")
        self.label(top, "PREMIUM APPS", 15, GOLD, True, bg="#202026").pack(side="left", padx=22, pady=17)
        self.label(top, f"Signed in as {self.username}", 10, MUTED, bg="#202026").pack(side="left", padx=15)
        self.button(top, "LOG OUT", self.show_login).pack(side="right", padx=18, pady=10)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=22)
        self.label(body, "APPLICATION LIBRARY", 19, TEXT, True).pack(anchor="w")
        self.label(body, "Apps stored on this Mac", 10, MUTED).pack(anchor="w", pady=(4, 16))

        self.list_frame = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground="#34343c")
        self.list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(self.list_frame, bg=PANEL, fg=TEXT, selectbackground=GOLD,
                                  selectforeground="#111114", font=("Helvetica", 12),
                                  relief="flat", borderwidth=0, highlightthickness=0,
                                  activestyle="none")
        self.listbox.pack(fill="both", expand=True, padx=14, pady=14)
        self.listbox.bind("<<ListboxSelect>>", self.select_item)
        bar = tk.Frame(body, bg=BG)
        bar.pack(fill="x", pady=(14, 0))
        self.button(bar, "OPEN SELECTED", self.open_selected, True).pack(side="left")
        if self.is_admin:
            self.button(bar, "＋ ADD APP / FILE", self.add_item).pack(side="left", padx=10)
            self.button(bar, "REMOVE", self.remove_item).pack(side="left")
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for item in sorted(STORAGE.iterdir(), key=lambda p: p.name.casefold()):
            self.listbox.insert(tk.END, item.name)

    def select_item(self, _event=None):
        selection = self.listbox.curselection()
        self.selected = self.listbox.get(selection[0]) if selection else None

    def add_item(self):
        paths = filedialog.askopenfilenames(title="Choose apps or files to add")
        if not paths:
            folder = filedialog.askdirectory(title="Or choose an app folder")
            paths = [folder] if folder else []
        for raw in paths:
            source = Path(raw)
            target = STORAGE / source.name
            try:
                if source.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(source, target)
                else:
                    shutil.copy2(source, target)
            except Exception as exc:
                messagebox.showerror("Could not add item", f"{source.name}: {exc}")
        self.refresh()

    def open_selected(self):
        self.select_item()
        if not self.selected:
            messagebox.showinfo("Choose an app", "Select an item in the library first.")
            return
        target = STORAGE / self.selected
        try:
            subprocess.Popen(["open", str(target)])
        except Exception as exc:
            messagebox.showerror("Could not open item", str(exc))

    def remove_item(self):
        self.select_item()
        if not self.selected:
            messagebox.showinfo("Choose an item", "Select an item to remove.")
            return
        target = STORAGE / self.selected
        if not messagebox.askyesno("Remove item", f"Remove {self.selected} from this Mac?"):
            return
        try:
            shutil.rmtree(target) if target.is_dir() else target.unlink()
            self.selected = None
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Could not remove item", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    PremiumApps(root)
    root.mainloop()
