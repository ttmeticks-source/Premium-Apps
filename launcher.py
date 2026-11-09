#!/usr/bin/env python3
"""Premium Apps: rounded macOS/Windows desktop launcher.

This release stores accounts, apps, reports and notifications locally on this
computer. A hosted backend is required to share them between different devices.
"""
import os, sys, uuid, shutil, sqlite3, hashlib, hmac, subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

APP = "Premium Apps"
BG, PANEL, PANEL2 = "#101115", "#1B1D23", "#262933"
GOLD, HOVER, BLACK = "#E3C323", "#F3D94E", "#101115"
WHITE, MUTED, GREEN, RED = "#F7F7F8", "#A8ABB5", "#5BC995", "#E66B6B"

def root_dir():
    if os.name == "nt": base = Path(os.getenv("APPDATA", Path.home()))
    elif sys.platform == "darwin": base = Path.home() / "Library" / "Application Support"
    else: base = Path(os.getenv("XDG_DATA_HOME", Path.home()/".local"/"share"))
    p = base / APP
    p.mkdir(parents=True, exist_ok=True)
    return p

ROOT = root_dir()
LIBRARY = ROOT / "Library"
LIBRARY.mkdir(exist_ok=True)

def make_hash(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000)
    return salt.hex(), digest.hex()

def check_hash(password, salt, expected, iterations=600000):
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), iterations).hex()
    return hmac.compare_digest(digest, expected)

class Store:
    def __init__(self):
        self.db = sqlite3.connect(ROOT / "premium_apps.db")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(k TEXT PRIMARY KEY,v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members(name TEXT PRIMARY KEY,password_salt TEXT,password_hash TEXT,banned INTEGER DEFAULT 0,joined TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS apps(id TEXT PRIMARY KEY,title TEXT,file TEXT,path TEXT,uploader TEXT,status TEXT,scan TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY,member TEXT,message TEXT,reply TEXT DEFAULT '',created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS notices(id TEXT PRIMARY KEY,member TEXT,message TEXT,read INTEGER DEFAULT 0,created TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        columns={row["name"] for row in self.db.execute("PRAGMA table_info(members)")}
        if "password_salt" not in columns:
            self.db.execute("ALTER TABLE members ADD COLUMN password_salt TEXT")
        if "password_hash" not in columns:
            self.db.execute("ALTER TABLE members ADD COLUMN password_hash TEXT")
        self.db.commit()
        # Keep the owner credential as a salted PBKDF2 hash, never plaintext.
        # Only seed it on first launch; do not overwrite a locally changed hash.
        if not self.get("owner_salt") or not self.get("owner_hash"):
            self.set("owner_salt","2c08a0bfde51b914eaa105bba376d8fb")
            self.set("owner_hash","c0dbb5f2894199f2338ef4ae8e2ff3dc7ffaaf22cc4a01d64c33c4cab0863997")
    def get(self,k):
        r=self.db.execute("SELECT v FROM config WHERE k=?",(k,)).fetchone()
        return r["v"] if r else ""
    def set(self,k,v):
        self.db.execute("INSERT INTO config VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,v)); self.db.commit()
    def owner_login(self,password):
        return check_hash(password,self.get("owner_salt"),self.get("owner_hash"),600000)
    def register(self,name,password):
        if name.casefold()=="premiumowner":
            return False
        existing=self.db.execute(
            "SELECT name,password_hash FROM members WHERE name=? COLLATE NOCASE",(name,)
        ).fetchone()
        if existing and existing["password_hash"]:
            return False
        salt,digest=make_hash(password)
        if existing:
            # Let accounts from the old shared-password version claim their
            # existing username and set a private password without losing bans.
            self.db.execute(
                "UPDATE members SET password_salt=?,password_hash=? WHERE name=?",
                (salt,digest,existing["name"])
            )
        else:
            self.db.execute(
                "INSERT INTO members(name,password_salt,password_hash) VALUES(?,?,?)",
                (name,salt,digest)
            )
        self.db.commit()
        return True
    def login(self,name,password):
        r=self.db.execute("SELECT password_salt,password_hash,banned FROM members WHERE name=? COLLATE NOCASE",(name,)).fetchone()
        if not r or not r["password_salt"] or not r["password_hash"]:
            return None
        if r["banned"]:
            return "banned"
        return "member" if check_hash(password,r["password_salt"],r["password_hash"]) else None

def screening(path):
    flagged={".bat",".cmd",".ps1",".vbs",".js",".sh",".command",".scr",".msi"}
    if path.suffix.lower() in flagged: return "CAUTION: script/installer type. Manual inspection required."
    if path.suffix.lower() in {".zip",".7z",".rar"}: return "CAUTION: archive. Inspect its contents manually."
    return "NOT SCANNED: metadata only. Owner must review manually."

class PremiumApps(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(APP); self.geometry("1180x780"); self.minsize(920,640); self.configure(fg_color=BG)
        self.store=Store(); self.user=""; self.role=""; self.content=None
        icon=Path(__file__).with_name("PremiumApps.ico")
        if os.name=="nt" and icon.exists():
            try: self.iconbitmap(str(icon))
            except tk.TclError: pass
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.login_screen()
    def close(self):
        self.store.db.close(); self.destroy()
    def btn(self,parent,text,fn,kind="gold",width=150):
        palette={"gold":(GOLD,HOVER,BLACK),"dark":("#30343E","#3C414D",WHITE),
                 "red":(RED,"#F08080",BLACK),"green":(GREEN,"#79DBAA",BLACK)}
        fg,hover,txt=palette[kind]
        return ctk.CTkButton(parent,text=text,command=fn,width=width,height=42,corner_radius=14,
            fg_color=fg,hover_color=hover,text_color=txt,border_width=0,
            font=ctk.CTkFont(size=13,weight="bold"),cursor="hand2")
    def field(self,parent,placeholder,secret=False):
        return ctk.CTkEntry(parent,placeholder_text=placeholder,show="•" if secret else "",
            height=46,corner_radius=13,fg_color="#20232B",text_color=WHITE,
            placeholder_text_color="#858B98",border_color="#3A3E49",
            border_width=1,font=ctk.CTkFont(size=14))
    def clear(self):
        for w in self.winfo_children(): w.destroy()
    def heading(self,parent,title,sub):
        ctk.CTkLabel(parent,text=title,text_color=WHITE,
            font=ctk.CTkFont(size=28,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(parent,text=sub,text_color=MUTED,font=ctk.CTkFont(size=13),
            wraplength=800,justify="left").pack(anchor="w",pady=(5,16))
    def card(self,parent):
        f=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=18,
                       border_width=1,border_color="#292D36")
        f.pack(fill="x",padx=4,pady=7)
        return f
    def stat_card(self,parent,label,value,accent=GOLD):
        f=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=16,
                       border_width=1,border_color="#292D36")
        ctk.CTkLabel(f,text=label.upper(),text_color=MUTED,
            font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w",padx=15,pady=(12,2))
        ctk.CTkLabel(f,text=str(value),text_color=accent,
            font=ctk.CTkFont(size=25,weight="bold")).pack(anchor="w",padx=15,pady=(0,12))
        return f
    def login_screen(self):
        self.clear()
        f=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=24,border_width=1,border_color="#343741")
        f.place(relx=.5,rely=.5,anchor="center")
        ctk.CTkLabel(f,text="✦",text_color=GOLD,font=ctk.CTkFont(size=58,weight="bold")).pack(padx=74,pady=(30,0))
        ctk.CTkLabel(f,text="PREMIUM APPS",text_color=GOLD,font=ctk.CTkFont(size=30,weight="bold")).pack()
        ctk.CTkLabel(f,text="YOUR APPS. YOUR SPACE.",text_color=MUTED,
            font=ctk.CTkFont(size=11,weight="bold")).pack(pady=(3,20))
        self.login_name=self.field(f,"Username")
        self.login_name.pack(fill="x",padx=36,pady=7)
        self.login_pw=self.field(f,"Password",True)
        self.login_pw.pack(fill="x",padx=36,pady=7)
        self.btn(f,"SIGN IN",self.login,width=340).pack(fill="x",padx=36,pady=(18,8))
        self.btn(f,"CREATE ACCOUNT",self.signup_screen,"dark",340).pack(fill="x",padx=36,pady=(0,14))
        ctk.CTkLabel(f,text="Members use their own account credentials.",text_color=MUTED,
            font=ctk.CTkFont(size=11)).pack(pady=(3,27))
        self.bind("<Return>",lambda e:self.login())
    def login(self):
        name,pw=self.login_name.get().strip(),self.login_pw.get()
        if not name or not pw:
            messagebox.showwarning("Missing details","Enter your username and password.")
            return
        if name.casefold()=="premiumowner":
            if not self.store.owner_login(pw):
                messagebox.showerror("Sign-in failed","Username or password is incorrect.")
                return
            self.unbind("<Return>")
            self.user,self.role="Owner","owner"
            self.dashboard()
            return
        role=self.store.login(name,pw)
        if role=="banned":
            messagebox.showerror("Access denied","This member account has been banned.")
            return
        if not role:
            messagebox.showerror("Sign-in failed","Username or password is incorrect.")
            return
        self.unbind("<Return>")
        self.user,self.role=name,role
        self.dashboard()
    def signup_screen(self):
        self.clear()
        f=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=24,border_width=1,border_color="#343741")
        f.place(relx=.5,rely=.5,anchor="center")
        ctk.CTkLabel(f,text="✦",text_color=GOLD,font=ctk.CTkFont(size=48,weight="bold")).pack(padx=55,pady=(24,0))
        ctk.CTkLabel(f,text="CREATE ACCOUNT",text_color=GOLD,font=ctk.CTkFont(size=25,weight="bold")).pack()
        ctk.CTkLabel(f,text="Choose a username and your own private password.",text_color=MUTED,wraplength=340).pack(pady=(5,16))
        self.signup_name=self.field(f,"Username (3–24 characters)")
        self.signup_name.pack(fill="x",padx=30,pady=6)
        self.signup_pw=self.field(f,"Create password (at least 10 characters)",True)
        self.signup_pw.pack(fill="x",padx=30,pady=6)
        self.signup_confirm=self.field(f,"Confirm password",True)
        self.signup_confirm.pack(fill="x",padx=30,pady=6)
        self.btn(f,"CREATE ACCOUNT",self.create_account,width=320).pack(fill="x",padx=30,pady=(15,8))
        self.btn(f,"BACK TO SIGN IN",self.login_screen,"dark",320).pack(fill="x",padx=30,pady=(0,24))
    def create_account(self):
        name=self.signup_name.get().strip()
        password=self.signup_pw.get()
        confirm=self.signup_confirm.get()
        if len(name)<3 or len(name)>24 or not all(ch.isalnum() or ch in "._-" for ch in name):
            messagebox.showwarning("Invalid username","Use 3–24 letters, numbers, dots, underscores, or hyphens.")
            return
        if len(password)<10:
            messagebox.showwarning("Password too short","Use at least 10 characters.")
            return
        if password!=confirm:
            messagebox.showwarning("Passwords do not match","Please enter the same password in both fields.")
            return
        try:
            created=self.store.register(name,password)
        except sqlite3.IntegrityError:
            created=False
        if not created:
            messagebox.showerror("Username unavailable","That username is already registered. Choose another.")
            return
        messagebox.showinfo("Account created","Your account has been created. Sign in with your username and password.")
        self.login_screen()
        self.login_name.insert(0,name)
    def dashboard(self):
        self.clear()
        self.grid_columnconfigure(1,weight=1)
        self.grid_rowconfigure(0,weight=1)
        side=ctk.CTkFrame(self,width=230,corner_radius=0,fg_color="#15171D")
        side.grid(row=0,column=0,sticky="nsew")
        side.grid_propagate(False)
        ctk.CTkLabel(side,text="✦",text_color=GOLD,
            font=ctk.CTkFont(size=48,weight="bold")).pack(pady=(25,0))
        ctk.CTkLabel(side,text="PREMIUM APPS",text_color=GOLD,
            font=ctk.CTkFont(size=17,weight="bold")).pack()
        ctk.CTkLabel(side,text="APP CENTER",text_color="#727987",
            font=ctk.CTkFont(size=10,weight="bold")).pack(pady=(2,18))
        ctk.CTkFrame(side,height=1,fg_color="#2A2E37").pack(fill="x",padx=17,pady=(0,14))
        ctk.CTkLabel(side,text=self.user,text_color=WHITE,
            font=ctk.CTkFont(size=14,weight="bold")).pack(anchor="w",padx=19)
        ctk.CTkLabel(side,text="OWNER ACCOUNT" if self.role=="owner" else "MEMBER ACCOUNT",
            text_color=GOLD if self.role=="owner" else MUTED,
            font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w",padx=19,pady=(3,20))
        tabs=["Apps"]+(["Members","Reports","Submissions"] if self.role=="owner"
                        else ["Publish","Support","Notifications"])
        self.nav_buttons={}
        for t in tabs:
            label={"Apps":"APP LIBRARY","Members":"MEMBERS","Reports":"SUPPORT REPORTS",
                   "Submissions":"APP REVIEW","Publish":"PUBLISH APP",
                   "Support":"CONTACT SUPPORT","Notifications":"NOTIFICATIONS"}[t]
            b=self.btn(side,label,lambda name=t:self.open_tab(name),
                       "gold" if t=="Apps" else "dark",194)
            b.configure(anchor="w",height=43,corner_radius=12)
            b.pack(padx=17,pady=4)
            self.nav_buttons[t]=b
        ctk.CTkFrame(side,fg_color="transparent").pack(expand=True,fill="both")
        self.btn(side,"LOG OUT",self.login_screen,"red",194).pack(padx=17,pady=20)
        main=ctk.CTkFrame(self,fg_color=BG,corner_radius=0)
        main.grid(row=0,column=1,sticky="nsew")
        main.grid_columnconfigure(0,weight=1)
        main.grid_rowconfigure(0,weight=1)
        self.content=ctk.CTkFrame(main,fg_color=BG,corner_radius=0)
        self.content.grid(row=0,column=0,sticky="nsew",padx=30,pady=26)
        self.open_tab("Apps")
    def open_tab(self,name):
        allowed={"Apps","Publish","Support","Notifications"}
        if self.role=="owner":
            allowed.update({"Members","Reports","Submissions"})
        if name not in allowed:
            return
        for tab,button in self.nav_buttons.items():
            button.configure(fg_color=GOLD if tab==name else "#30343E",
                             hover_color=HOVER if tab==name else "#3C414D",
                             text_color=BLACK if tab==name else WHITE)
        for w in self.content.winfo_children():
            w.destroy()
        {"Apps":self.apps_tab,"Members":self.members_tab,"Reports":self.reports_tab,
         "Submissions":self.submissions_tab,"Publish":self.publish_tab,
         "Support":self.support_tab,"Notifications":self.notifications_tab}[name]()
    def scroll(self):
        f=ctk.CTkScrollableFrame(self.content,fg_color=PANEL,corner_radius=18)
        f.pack(fill="both",expand=True,pady=(8,0)); return f
    def choose_path(self):
        p=filedialog.askopenfilename(title="Select app or file")
        if not p: p=filedialog.askdirectory(title="Or select an app bundle/folder")
        return Path(p) if p else None
    def add_file(self,path,title,status):
        ident=uuid.uuid4().hex; dest=LIBRARY/(ident+"_"+path.name)
        try:
            shutil.copytree(path,dest) if path.is_dir() else shutil.copy2(path,dest)
        except Exception as e: messagebox.showerror("Upload failed",str(e)); return
        self.store.db.execute("INSERT INTO apps VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (ident,title or path.stem,path.name,str(dest),self.user,status,screening(path)))
        self.store.db.commit()
        messagebox.showinfo("Saved","App saved locally.\n\n"+screening(path))
    def apps_tab(self):
        self.heading(self.content,"APP LIBRARY","Discover approved apps. Search by app name, uploader, or filename.")
        rows=self.store.db.execute(
            "SELECT * FROM apps WHERE status='published' ORDER BY created DESC"
        ).fetchall()
        strip=ctk.CTkFrame(self.content,fg_color="transparent")
        strip.pack(fill="x",pady=(0,12))
        self.stat_card(strip,"Available apps",len(rows)).pack(side="left",fill="x",expand=True,padx=(0,7))
        own_count=self.store.db.execute(
            "SELECT COUNT(*) FROM apps WHERE uploader=?",(self.user,)
        ).fetchone()[0]
        self.stat_card(strip,"Your submissions",own_count,GREEN).pack(
            side="left",fill="x",expand=True,padx=7)
        searchwrap=ctk.CTkFrame(self.content,fg_color="transparent")
        searchwrap.pack(fill="x",pady=(0,8))
        self.app_search=self.field(searchwrap,"⌕  Search apps...")
        self.app_search.pack(fill="x",expand=True)
        self.app_area=self.scroll()
        self.app_rows=rows
        self.app_search.bind("<KeyRelease>",self.filter_apps)
        self.render_apps(rows)
    def filter_apps(self,event=None):
        term=self.app_search.get().strip().casefold()
        rows=[r for r in self.app_rows if term in " ".join(
            str(r[k] or "") for k in ("title","uploader","file")
        ).casefold()]
        self.render_apps(rows)
    def render_apps(self,rows):
        for w in self.app_area.winfo_children():
            w.destroy()
        if not rows:
            title="No apps match your search." if self.app_search.get().strip() else "The library is empty"
            ctk.CTkLabel(self.app_area,text=title,text_color=WHITE,
                font=ctk.CTkFont(size=17,weight="bold")).pack(pady=(38,4))
            ctk.CTkLabel(self.app_area,text="Approved apps will appear here.",
                text_color=MUTED).pack(pady=(0,34))
            return
        for r in rows:
            f=self.card(self.app_area)
            header=ctk.CTkFrame(f,fg_color="transparent")
            header.pack(fill="x",padx=17,pady=(14,2))
            ctk.CTkLabel(header,text=r["title"],text_color=WHITE,
                font=ctk.CTkFont(size=17,weight="bold")).pack(side="left",anchor="w")
            ctk.CTkLabel(header,text="APPROVED",text_color=GREEN,
                font=ctk.CTkFont(size=10,weight="bold")).pack(side="right")
            ctk.CTkLabel(f,text=f"Uploaded by {r['uploader']}  ·  {r['file']}",
                text_color=MUTED,font=ctk.CTkFont(size=12)).pack(anchor="w",padx=17,pady=(3,10))
            self.btn(f,"DOWNLOAD  ↓",lambda row=r:self.download(row),width=145).pack(
                anchor="e",padx=15,pady=(0,14))
    def download(self,row):
        folder=filedialog.askdirectory(title="Choose where to save the app")
        if not folder:
            return
        src=Path(row["path"])
        dst=Path(folder)/row["file"]
        try:
            if not src.exists():
                raise FileNotFoundError("The stored app file could not be found.")
            if dst.exists():
                if not messagebox.askyesno("Replace existing item",
                    f"{dst.name} already exists in that folder. Replace it?"):
                    return
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            shutil.copytree(src,dst) if src.is_dir() else shutil.copy2(src,dst)
            messagebox.showinfo("Download complete",f"Saved successfully to:\n{dst}")
        except Exception as e:
            messagebox.showerror("Download failed",str(e))
    def publish_tab(self):
        self.heading(self.content,"SUBMIT AN APP","Members can submit any app file or app folder for owner approval.")
        f=self.card(self.content)
        self.title_entry=self.field(f,"App title"); self.title_entry.pack(fill="x",padx=18,pady=(18,8))
        self.btn(f,"CHOOSE FILE / APP FOLDER",self.member_upload,"gold",230).pack(anchor="w",padx=18,pady=(5,18))
        ctk.CTkLabel(self.content,text="Submissions are hidden from the public library until approved. Automated malware clearance is not provided.",text_color=MUTED,wraplength=740,justify="left").pack(anchor="w",pady=12)
    def member_upload(self):
        p=self.choose_path()
        if p:self.add_file(p,self.title_entry.get().strip() or p.stem,"pending")
    def submissions_tab(self):
        self.heading(self.content,"APP REVIEW","Check each submission yourself. The built-in check only flags some file types; it is not antivirus.")
        area=self.scroll(); rows=self.store.db.execute("SELECT * FROM apps WHERE status='pending' ORDER BY created").fetchall()
        if not rows: ctk.CTkLabel(area,text="No pending apps.",text_color=MUTED).pack(pady=35)
        for r in rows:
            f=self.card(area)
            ctk.CTkLabel(f,text=r["title"],text_color=WHITE,font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=15,pady=(12,3))
            ctk.CTkLabel(f,text=f"Submitted by {r['uploader']} · {r['file']}",text_color=MUTED).pack(anchor="w",padx=15)
            ctk.CTkLabel(f,text=r["scan"],text_color="#EBCB58",wraplength=680,justify="left").pack(anchor="w",padx=15,pady=8)
            row=ctk.CTkFrame(f,fg_color="transparent"); row.pack(anchor="e",padx=12,pady=(0,12))
            self.btn(row,"SHOW FILE",lambda x=r:self.reveal(x), "dark",115).pack(side="left",padx=3)
            self.btn(row,"APPROVE",lambda x=r:self.status(x["id"],"published"),"green",105).pack(side="left",padx=3)
            self.btn(row,"REJECT",lambda x=r:self.status(x["id"],"rejected"),"red",90).pack(side="left",padx=3)
        self.btn(self.content,"＋ PUBLISH OWNER APP",self.owner_upload,width=220).pack(anchor="w",pady=12)
    def owner_upload(self):
        p=self.choose_path()
        if p:self.add_file(p,p.stem,"published")
    def status(self,ident,value):
        self.store.db.execute("UPDATE apps SET status=? WHERE id=?",(value,ident)); self.store.db.commit(); self.open_tab("Submissions")
    def reveal(self,row):
        path=Path(row["path"])
        try:
            if os.name=="nt": os.startfile(str(path.parent))
            elif sys.platform=="darwin": subprocess.Popen(["open","-R",str(path)])
            else: subprocess.Popen(["xdg-open",str(path.parent)])
        except Exception as e: messagebox.showerror("Could not open folder",str(e))
    def support_tab(self):
        self.heading(self.content,"CONTACT SUPPORT","Send a message to support. Replies appear in Notifications.")
        f=self.card(self.content)
        self.message_box=ctk.CTkTextbox(f,height=210,corner_radius=12,fg_color=PANEL2,text_color=WHITE)
        self.message_box.pack(fill="both",expand=True,padx=18,pady=18)
        self.btn(f,"SEND MESSAGE",self.send_report,width=170).pack(anchor="e",padx=18,pady=(0,18))
    def send_report(self):
        msg=self.message_box.get("1.0","end").strip()
        if not msg:messagebox.showwarning("Empty message","Write a message first.");return
        self.store.db.execute("INSERT INTO reports(id,member,message) VALUES(?,?,?)",(uuid.uuid4().hex,self.user,msg))
        self.store.db.commit();self.message_box.delete("1.0","end")
        messagebox.showinfo("Sent","Support message saved on this computer.")
    def reports_tab(self):
        self.heading(self.content,"SUPPORT REPORTS","Read member messages and reply. Replies create notifications.")
        area=self.scroll(); rows=self.store.db.execute("SELECT * FROM reports ORDER BY created DESC").fetchall()
        if not rows:ctk.CTkLabel(area,text="No reports yet.",text_color=MUTED).pack(pady=35)
        for r in rows:
            f=self.card(area)
            ctk.CTkLabel(f,text=f"{r['member']} · {r['created']}",text_color=GOLD,font=ctk.CTkFont(weight="bold")).pack(anchor="w",padx=15,pady=(12,5))
            ctk.CTkLabel(f,text=r["message"],text_color=WHITE,wraplength=690,justify="left").pack(anchor="w",padx=15,pady=(0,8))
            if r["reply"]:ctk.CTkLabel(f,text="Reply: "+r["reply"],text_color=GREEN,wraplength=690,justify="left").pack(anchor="w",padx=15,pady=(0,8))
            self.btn(f,"REPLY & NOTIFY",lambda row=r:self.reply(row),width=160).pack(anchor="e",padx=12,pady=(0,12))
    def reply(self,row):
        win=ctk.CTkToplevel(self);win.title("Reply to member");win.geometry("480x300");win.configure(fg_color=BG);win.transient(self)
        box=ctk.CTkTextbox(win,corner_radius=12,fg_color=PANEL,text_color=WHITE);box.pack(fill="both",expand=True,padx=18,pady=18)
        box.insert("1.0",row["reply"])
        def send():
            msg=box.get("1.0","end").strip()
            if not msg:return
            self.store.db.execute("UPDATE reports SET reply=? WHERE id=?",(msg,row["id"]))
            self.store.db.execute("INSERT INTO notices(id,member,message) VALUES(?,?,?)",(uuid.uuid4().hex,row["member"],"Support replied: "+msg))
            self.store.db.commit();win.destroy();self.open_tab("Reports")
            messagebox.showinfo("Reply saved","A notification was created in this local app.")
        self.btn(win,"SEND REPLY & NOTIFY",send,width=210).pack(anchor="e",padx=18,pady=(0,18))
    def notifications_tab(self):
        self.heading(self.content,"NOTIFICATIONS","Support replies and messages for your account.")
        area=self.scroll();rows=self.store.db.execute("SELECT * FROM notices WHERE member=? ORDER BY created DESC",(self.user,)).fetchall()
        if not rows:ctk.CTkLabel(area,text="You're all caught up.",text_color=MUTED).pack(pady=35)
        for r in rows:
            f=self.card(area);ctk.CTkLabel(f,text=r["message"],text_color=WHITE,wraplength=700,justify="left").pack(anchor="w",padx=15,pady=14)
            self.store.db.execute("UPDATE notices SET read=1 WHERE id=?",(r["id"],))
        self.store.db.commit()
    def members_tab(self):
        if self.role!="owner":
            return
        self.heading(self.content,"MEMBERS","Manage member accounts and access to this local library.")
        area=self.scroll();rows=self.store.db.execute("SELECT * FROM members ORDER BY name COLLATE NOCASE").fetchall()
        if not rows:ctk.CTkLabel(area,text="No member accounts yet on this computer.",text_color=MUTED).pack(pady=35)
        for r in rows:
            f=self.card(area);ctk.CTkLabel(f,text=r["name"],text_color=WHITE,font=ctk.CTkFont(size=14,weight="bold")).pack(side="left",padx=15,pady=13)
            ctk.CTkLabel(f,text="BANNED" if r["banned"] else "ACTIVE",text_color=RED if r["banned"] else GREEN).pack(side="left",padx=8)
            if self.role=="owner":
                text="UNBAN" if r["banned"] else "BAN"
                self.btn(f,text,lambda row=r:self.ban(row),"dark" if r["banned"] else "red",100).pack(side="right",padx=12,pady=8)
    def ban(self,row):
        self.store.db.execute("UPDATE members SET banned=? WHERE name=?",(0 if row["banned"] else 1,row["name"]))
        self.store.db.commit();self.open_tab("Members")

if __name__=="__main__":
    PremiumApps().mainloop()
