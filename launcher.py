import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
from tkinterdnd2 import DND_FILES, TkinterDnD

class PremiumAppsLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Premium Apps")
        self.root.geometry("600x500")
        self.root.configure(bg="#121212")
        
        # Simulated Local Registry storage directory
        self.storage_dir = os.path.join(os.path.expanduser("~"), "PremiumApps_Storage")
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

        self.show_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_screen()
        
        # Centered Heading Label
        title_lbl = tk.Label(self.root, text="PREMIUM APPS", font=("Helvetica", 24, "bold"), fg="#FFD700", bg="#121212")
        title_lbl.pack(pady=40)
        
        # User input fields frame
        form_frame = tk.Frame(self.root, bg="#121212")
        form_frame.pack(pady=10)
        
        tk.Label(form_frame, text="Username:", font=("Helvetica", 12), fg="#FFFFFF", bg="#121212").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=25, bg="#1F1F1F", fg="#FFFFFF", insertbackground="white")
        self.username_entry.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Password:", font=("Helvetica", 12), fg="#FFFFFF", bg="#121212").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=25, show="*", bg="#1F1F1F", fg="#FFFFFF", insertbackground="white")
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Submit Button
        login_btn = tk.Button(self.root, text="Launch Dashboard", font=("Helvetica", 12, "bold"), bg="#FFD700", fg="#121212", 
                             activebackground="#CCA100", activeforeground="#121212", width=20, command=self.authenticate_user)
        login_btn.pack(pady=30)

    def authenticate_user(self):
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get().strip()
        
        if not user or not pwd:
            messagebox.showwarning("Incomplete Entry", "Please provide both a username and password to launch.")
            return
            
        # Check for administrative role privilege parameters
        if user == "PremiumOwner":
            self.show_dashboard(is_admin=True, username=user, password=pwd)
        else:
            self.show_dashboard(is_admin=False, username=user, password=pwd)

    def show_dashboard(self, is_admin, username, password):
        self.clear_screen()
        
        # Top Metadata Status panel
        top_bar = tk.Frame(self.root, bg="#1F1F1F", height=50)
        top_bar.pack(fill="x", side="top")
        
        user_info = f"Active User: {username}  |  Session Password: {password}"
        info_lbl = tk.Label(top_bar, text=user_info, font=("Helvetica", 10), fg="#A0A0A0", bg="#1F1F1F")
        info_lbl.pack(side="left", padx=15, pady=10)
        
        logout_btn = tk.Button(top_bar, text="Exit Session", font=("Helvetica", 9), bg="#D32F2F", fg="#FFFFFF", command=self.show_login_screen)
        logout_btn.pack(side="right", padx=15, pady=8)
        
        # Main Layout frame
        main_frame = tk.Frame(self.root, bg="#121212")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_text = "ADMIN APPS DEPLOYMENT PANEL" if is_admin else "APPS REPOSITORY"
        panel_title = tk.Label(main_frame, text=title_text, font=("Helvetica", 16, "bold"), fg="#FFD700", bg="#121212")
        panel_title.pack(anchor="w", pady=(0, 10))
        
        # Main Display Framework
        self.display_frame = tk.LabelFrame(main_frame, text="APPS", font=("Helvetica", 12, "bold"), fg="#FFFFFF", bg="#1A1A1A", bd=2, relief="groove")
        self.display_frame.pack(fill="both", expand=True)
        
        if is_admin:
            # Set up drag and drop zone parameters
            self.display_frame.drop_target_register(DND_FILES)
            self.display_frame.dnd_bind('<<Drop>>', self.handle_file_drop)
            
            self.drop_hint = tk.Label(self.display_frame, text="[Drag & Drop Any App or File Here to Paste into Registry]", 
                                      font=("Helvetica", 11, "italic"), fg="#888888", bg="#1A1A1A")
            self.drop_hint.pack(pady=20)
        
        self.app_list_box = tk.Listbox(self.display_frame, bg="#242424", fg="#FFFFFF", font=("Helvetica", 11), selectbackground="#FFD700", selectforeground="#121212", bd=0, highlightthickness=0)
        self.app_list_box.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Bottom controls container
        action_bar = tk.Frame(main_frame, bg="#121212")
        action_bar.pack(fill="x", side="bottom", pady=(10, 0))
        
        launch_btn = tk.Button(action_bar, text="Download / Execute Selected App", font=("Helvetica", 11, "bold"), bg="#4CAF50", fg="#FFFFFF", command=self.launch_selected_app)
        launch_btn.pack(side="left")
        
        self.refresh_app_list()

    def handle_file_drop(self, event):
        file_path = event.data.strip('{}') # Clean operating system path wrapping layout formatting
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            destination = os.path.join(self.storage_dir, file_name)
            
            try:
                if os.path.isdir(file_path):
                    shutil.copytree(file_path, destination, dirs_exist_ok=True)
                else:
                    shutil.copy2(file_path, destination)
                messagebox.showinfo("Registry Sync", f"Successfully pasted application: {file_name}")
                self.refresh_app_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to sync file path metadata: {str(e)}")

    def refresh_app_list(self):
        self.app_list_box.delete(0, tk.END)
        for entry in os.listdir(self.storage_dir):
            self.app_list_box.insert(tk.END, entry)

    def launch_selected_app(self):
        selected_index = self.app_list_box.curselection()
        if not selected_index:
            messagebox.showwarning("Selection Required", "Please choose an application inside the panel first.")
            return
            
        app_name = self.app_list_box.get(selected_index)
        target_path = os.path.join(self.storage_dir, app_name)
        
        try:
            os.startfile(target_path) if hasattr(os, 'startfile') else os.system(f'open "{target_path}"')
        except Exception as e:
            messagebox.showerror("Execution Fault", f"Could not launch selected environment file: {str(e)}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = PremiumAppsLauncher(root)
    root.mainloop()
