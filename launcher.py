#!/usr/bin/env python3
"""Premium Apps: rounded macOS/Windows desktop launcher.

This release stores accounts, apps, reports and notifications locally on this
computer. A hosted backend is required to share them between different devices.
"""
import os, sys, uuid, shutil, sqlite3, hashlib, subprocess
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
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240000)
    return salt.hex(), digest.hex()

def check_hash(password, salt, expected):
    return make_hash(password, bytes.fromhex(salt))[1] == expected

class Store:
    def __init__(self):
        self.db = sqlite3.connect(ROOT / "premium_apps.db")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(k TEXT PRIMARY KEY,v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members(name TEXT PRIMARY KEY,banned INTEGER DEFAULT 0,joined TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS apps(id TEXT PRIMARY KEY,title TEXT,file TEXT,path TEXT,uploader TEXT,status TEXT,scan TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY,member TEXT,message TEXT,reply TEXT DEFAULT '',created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS notices(id TEXT PRIMARY KEY,member TEXT,message TEXT,read INTEGER DEFAULT 0,created TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        self.db.commit()
    def get(self,k):
        r=self.db.execute("SELECT v FROM config WHERE k=?",(k,)).fetchone()
        return r["v"] if r else ""
    def set(self,k,v):
        self.db.execute("INSERT INTO config VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,v)); self.db.commit()
    def configured(self):
        return bool(self.get("owner_salt") and self.get("member_salt"))
    def setup(self,owner,member):
        a,b=make_hash(owner); c,d=make_hash(member)
        for k,v in [("owner_salt",a),("owner_hash",b),("member_salt",c),("member_hash",d)]: self.set(k,v)
    def login(self,name,password):
        if name.lower()=="premiumowner":
            return "owner" if check_hash(password,self.get("owner_salt"),self.get("owner_hash")) else None
        if not check_hash(password,self.get("member_salt"),self.get("member_hash")): return None
        r=self.db.execute("SELECT banned FROM members WHERE name=?",(name,)).fetchone()
        if r and r["banned"]: return "banned"
        self.db.execute("INSERT OR IGNORE INTO members(name) VALUES(?)",(name,)); self.db.commit()
        return "member"

def screening(path):
    flagged={".bat",".cmd",".ps1",".vbs",".js",".sh",".command",".scr",".msi"}
    if path.suffix.lower() in flagged: return "CAUTION: script/installer type. Manual inspection required."
    if path.suffix.lower() in {".zip",".7z",".rar"}: return "CAUTION: archive. Inspect its contents manually."
    return "NOT SCANNED: metadata only. Owner must review manually."

class PremiumApps(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(APP); self.geometry("1080x720"); self.minsize(850,600); self.configure(fg_color=BG)
        self.store=Store(); self.user=""; self.role=""; self.content=None
        icon=Path(__file__).with_name("PremiumApps.ico")
        if os.name=="nt" and icon.exists():
            try: self.iconbitmap(str(icon))
            except tk.TclError: pass
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.setup_screen() if not self.store.configured() else self.login_screen()
    def close(self):
        self.store.db.close(); self.destroy()
    def btn(self,parent,text,fn,kind="gold",width=150):
        palette={"gold":(GOLD,HOVER,BLACK),"dark":(PANEL2,"#363B47",BLACK),
                 "red":(RED,"#F08080",BLACK),"green":(GREEN,"#79DBAA",BLACK)}
        fg,hover,txt=palette[kind]
        return ctk.CTkButton(parent,text=text,command=fn,width=width,height=42,corner_radius=14,
            fg_color=fg,hover_color=hover,text_color=txt,border_width=0,
            font=ctk.CTkFont(size=13,weight="bold"),cursor="hand2")
    def field(self,parent,placeholder,secret=False):
        return ctk.CTkEntry(parent,placeholder_text=placeholder,show="•" if secret else "",
            height=44,corner_radius=12,fg_color=PANEL,text_color=WHITE,
            placeholder_text_color=MUTED,border_color="#3A3E49")
    def clear(self):
        for w in self.winfo_children(): w.destroy()
    def heading(self,parent,title,sub):
        ctk.CTkLabel(parent,text=title,text_color=WHITE,font=ctk.CTkFont(size=25,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(parent,text=sub,text_color=MUTED,font=ctk.CTkFont(size=12),
                     wraplength=760,justify="left").pack(anchor="w",pady=(4,16))
    def card(self,parent):
        f=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=18)
        f.pack(fill="x",padx=8,pady=7)
        return f
    def setup_screen(self):
        self.clear()
        f=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=24,border_width=1,border_color="#343741")
        f.place(relx=.5,rely=.5,anchor="center")
        ctk.CTkLabel(f,text="✦",text_color=GOLD,font=ctk.CTkFont(size=52,weight="bold")).pack(padx=48,pady=(26,0))
        ctk.CTkLabel(f,text="PREMIUM APPS",text_color=GOLD,font=ctk.CTkFont(size=27,weight="bold")).pack()
        ctk.CTkLabel(f,text="Create the owner login and one shared member password",text_color=MUTED).pack(pady=(5,18))
        self.owner_pw=self.field(f,"Owner password (PremiumOwner)",True); self.owner_pw.pack(fill="x",padx=28,pady=6)
        self.member_pw=self.field(f,"Shared password for ALL members",True); self.member_pw.pack(fill="x",padx=28,pady=6)
        self.member_confirm=self.field(f,"Confirm shared member password",True); self.member_confirm.pack(fill="x",padx=28,pady=6)
        ctk.CTkLabel(f,text="Members cannot change this password. Give the same password to every member.",text_color=MUTED,wraplength=360).pack(padx=25,pady=10)
        self.btn(f,"SAVE SETUP",self.finish_setup,width=330).pack(padx=28,pady=(5,28))
    def finish_setup(self):
        a,b,c=self.owner_pw.get(),self.member_pw.get(),self.member_confirm.get()
        if len(a)<10 or len(b)<10:
            messagebox.showwarning("Password too short","Use at least 10 characters for each password."); return
        if b!=c:
            messagebox.showwarning("Does not match","Please confirm the shared member password."); return
        self.store.setup(a,b)
        messagebox.showinfo("Setup saved","Owner username: PremiumOwner\nAll other users share the member password.")
        self.login_screen()
    def login_screen(self):
        self.clear()
        f=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=24,border_width=1,border_color="#343741")
        f.place(relx=.5,rely=.5,anchor="center")
        ctk.CTkLabel(f,text="✦",text_color=GOLD,font=ctk.CTkFont(size=54,weight="bold")).pack(padx=60,pady=(28,0))
        ctk.CTkLabel(f,text="PREMIUM APPS",text_color=GOLD,font=ctk.CTkFont(size=28,weight="bold")).pack()
        ctk.CTkLabel(f,text="Sign in to your library",text_color=MUTED).pack(pady=(4,20))
        self.login_name=self.field(f,"Username"); self.login_name.pack(fill="x",padx=34,pady=6)
        self.login_pw=self.field(f,"Password",True); self.login_pw.pack(fill="x",padx=34,pady=6)
        self.btn(f,"SIGN IN",self.login,width=330).pack(fill="x",padx=34,pady=(16,8))
        ctk.CTkLabel(f,text="Members all use the same shared password.",text_color=MUTED).pack(pady=(4,25))
        self.bind("<Return>",lambda e:self.login())
    def login(self):
        name,pw=self.login_name.get().strip(),self.login_pw.get()
        if not name or not pw: messagebox.showwarning("Missing details","Enter both fields."); return
        role=self.store.login(name,pw)
        if role=="banned": messagebox.showerror("Access denied","This member account has been banned."); return
        if not role: messagebox.showerror("Sign-in failed","Username or password is incorrect."); return
        self.unbind("<Return>"); self.user,self.role=name,role; self.dashboard()
    def dashboard(self):
        self.clear(); self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        side=ctk.CTkFrame(self,width=218,corner_radius=0,fg_color="#17191F")
        side.grid(row=0,column=0,sticky="nsew"); side.grid_propagate(False)
        ctk.CTkLabel(side,text="✦",text_color=GOLD,font=ctk.CTkFont(size=48,weight="bold")).pack(pady=(25,0))
        ctk.CTkLabel(side,text="PREMIUM APPS",text_color=GOLD,font=ctk.CTkFont(size=17,weight="bold")).pack()
        ctk.CTkLabel(side,text=f"{self.user} · {self.role.title()}",text_color=MUTED).pack(pady=(5,22))
        tabs=["Apps","Members"]+(["Reports","Submissions"] if self.role=="owner" else ["Publish","Support","Notifications"])
        for t in tabs: self.btn(side,t.upper(),lambda name=t:self.open_tab(name),"gold" if t=="Apps" else "dark",178).pack(padx=16,pady=5)
        ctk.CTkFrame(side,fg_color="transparent").pack(expand=True,fill="both")
        self.btn(side,"LOG OUT",self.login_screen,"red",178).pack(padx=16,pady=22)
        self.content=ctk.CTkFrame(self,fg_color=BG,corner_radius=0)
        self.content.grid(row=0,column=1,sticky="nsew",padx=28,pady=24)
        self.open_tab("Apps")
    def open_tab(self,name):
        for w in self.content.winfo_children(): w.destroy()
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
        self.heading(self.content,"APP LIBRARY","Browse and download apps approved by the owner.")
        area=self.scroll(); rows=self.store.db.execute("SELECT * FROM apps WHERE status='published' ORDER BY created DESC").fetchall()
        if not rows: ctk.CTkLabel(area,text="No published apps yet.",text_color=MUTED).pack(pady=35)
        for r in rows:
            f=self.card(area)
            ctk.CTkLabel(f,text=r["title"],text_color=WHITE,font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=16,pady=(12,2))
            ctk.CTkLabel(f,text=f"by {r['uploader']}  ·  {r['file']}",text_color=MUTED).pack(anchor="w",padx=16,pady=(0,8))
            self.btn(f,"DOWNLOAD",lambda row=r:self.download(row),width=125).pack(anchor="e",padx=14,pady=(0,12))
    def download(self,row):
        folder=filedialog.askdirectory(title="Choose download folder")
        if not folder:return
        src=Path(row["path"]); dst=Path(folder)/row["file"]
        try:
            shutil.copytree(src,dst) if src.is_dir() else shutil.copy2(src,dst)
            messagebox.showinfo("Downloaded",f"Saved to:\n{dst}")
        except Exception as e: messagebox.showerror("Download failed",str(e))
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
        self.heading(self.content,"CONTACT SUPPORT","Send a message to PremiumOwner. Replies appear in Notifications.")
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
        self.heading(self.content,"MEMBERS","Owner can ban or unban accounts. All members share one fixed password.")
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
