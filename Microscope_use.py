import threading, sqlite3, tkinter as tk, json, os, csv
from tkinter import ttk, messagebox
from datetime import datetime

import sys
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle — use folder containing the .app / .exe
    BASE_DIR = os.path.dirname(sys.executable)
    # For .app bundles the executable is deep inside; go up to the folder containing the .app
    _app = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
    if os.path.isdir(_app) and not _app.endswith(".app"):
        BASE_DIR = _app
    else:
        BASE_DIR = os.path.dirname(_app)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH  = os.path.join(BASE_DIR, "microscope_usage.db")
CFG_PATH = os.path.join(BASE_DIR, "config.json")

# ── OSU palette ───────────────────────────────────────────────────────────────
SCARLET = "#BB0000"
SCAR_DK = "#8B0000"
GRAY    = "#666666"
WHITE   = "#FFFFFF"
OFFWHITE= "#F8F8F8"
LIGHT   = "#F2F2F2"
BORDER  = "#D8D8D8"   # subtle grey border — not black
DARK    = "#1A1A1A"
MID     = "#555555"
GREEN   = "#2E7D32"

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH) as f: return json.load(f)
    return {}

def save_config(cfg):
    with open(CFG_PATH,"w") as f: json.dump(cfg,f,indent=2)

# ── App ───────────────────────────────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root   = root
        self.config = load_config()
        self.root.title(self.config.get("facility_name","Microscope Usage Tracker"))
        self.root.geometry("720x700")
        self.root.resizable(True, True)
        self.root.configure(bg=WHITE)
        self._local = threading.local()
        self._init_db()
        self._ttk_style()
        self._vars()
        self._build()

    # ── DB ────────────────────────────────────────────────────────────────────
    def _conn(self):
        if not hasattr(self._local,"c"):
            self._local.c = sqlite3.connect(DB_PATH, check_same_thread=False)
        return self._local.c

    def _init_db(self):
        c = sqlite3.connect(DB_PATH)
        c.execute("""CREATE TABLE IF NOT EXISTS usage(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, pi TEXT, user TEXT, user_email TEXT, department TEXT,
            service_description TEXT, start_time TEXT, end_time TEXT,
            usage_duration TEXT, sample_count INTEGER DEFAULT 0,
            microscope_cost REAL DEFAULT 0, sample_cost REAL DEFAULT 0,
            created_at TEXT DEFAULT(datetime('now')))""")
        try: c.execute("ALTER TABLE usage ADD COLUMN user_email TEXT")
        except: pass
        c.commit(); c.close()

    # ── ttk style ─────────────────────────────────────────────────────────────
    def _ttk_style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook",          background=WHITE,   borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab",      background=LIGHT,   foreground=GRAY,
                    font=("Helvetica",10,"bold"), padding=[22,9])
        s.map("TNotebook.Tab",
              background=[("selected",SCARLET)],
              foreground=[("selected",WHITE)])
        s.configure("TFrame",             background=WHITE)
        s.configure("TLabel",             background=WHITE, foreground=DARK,  font=("Helvetica",10))
        s.configure("TRadiobutton",       background=WHITE, foreground=DARK,  font=("Helvetica",10))
        s.configure("TCheckbutton",       background=WHITE, foreground=DARK,  font=("Helvetica",10))
        s.configure("TCombobox",          fieldbackground=WHITE, background=WHITE,
                    foreground=DARK, selectbackground=SCARLET, selectforeground=WHITE,
                    font=("Helvetica",10))
        s.map("TCombobox",  fieldbackground=[("readonly",WHITE)])
        # Combobox dropdown list selection — must be set via option_add, not ttk style
        self.root.option_add("*TCombobox*Listbox.selectBackground", SCARLET)
        self.root.option_add("*TCombobox*Listbox.selectForeground", WHITE)
        self.root.option_add("*TCombobox*Listbox.background",       WHITE)
        self.root.option_add("*TCombobox*Listbox.foreground",       DARK)
        s.configure("TSpinbox",           fieldbackground=WHITE, foreground=DARK, font=("Helvetica",10))
        s.configure("Treeview",           background=WHITE, foreground=DARK,
                    rowheight=28, fieldbackground=WHITE, font=("Helvetica",9))
        s.configure("Treeview.Heading",   background=SCARLET, foreground=WHITE,
                    font=("Helvetica",9,"bold"), relief="flat")
        s.map("Treeview",
              background=[("selected","#F5E6E6")],
              foreground=[("selected",DARK)])
        # Keep heading color fixed — no hover colour change
        s.map("Treeview.Heading",
              background=[("active",SCARLET),("pressed",SCARLET)],
              foreground=[("active",WHITE), ("pressed",WHITE)])

    # ── Widget helpers ────────────────────────────────────────────────────────
    # Shared button constants — change here to affect ALL buttons
    BTN_FONT = ("Helvetica", 10, "bold")
    BTN_PX, BTN_PY = 18, 9

    def _primary_btn(self, parent, text, cmd, bg=SCARLET):
        """Filled button — scarlet (or custom bg), white text."""
        hover = "#8B0000" if bg in (SCARLET, SCAR_DK) else "#888888"
        f   = tk.Frame(parent, bg=bg, cursor="hand2")
        lbl = tk.Label(f, text=text, bg=bg, fg=WHITE,
                       font=self.BTN_FONT, padx=self.BTN_PX, pady=self.BTN_PY)
        lbl.pack()
        for w in (f, lbl):
            w.bind("<Button-1>", lambda e: cmd())
            w.bind("<Enter>",    lambda e, h=hover: (f.config(bg=h),  lbl.config(bg=h)))
            w.bind("<Leave>",    lambda e, b=bg:    (f.config(bg=b),  lbl.config(bg=b)))
        return f

    def _secondary_btn(self, parent, text, cmd):
        """Outline button — white bg, grey 1-px border, dark text."""
        border = tk.Frame(parent, bg=BORDER, cursor="hand2")
        inner  = tk.Frame(border, bg=WHITE,  cursor="hand2")
        inner.pack(padx=1, pady=1)
        lbl = tk.Label(inner, text=text, bg=WHITE, fg=DARK,
                       font=self.BTN_FONT, padx=self.BTN_PX, pady=self.BTN_PY)
        lbl.pack()
        for w in (border, inner, lbl):
            w.bind("<Button-1>", lambda e: cmd())
            w.bind("<Enter>",    lambda e: (inner.config(bg=LIGHT), lbl.config(bg=LIGHT)))
            w.bind("<Leave>",    lambda e: (inner.config(bg=WHITE),  lbl.config(bg=WHITE)))
        return border

    def _entry(self, parent, var, width=None, show=None):
        """Entry with a clean grey border (wrapper-frame trick, no highlight issues)."""
        kw = dict(textvariable=var, bg=WHITE, fg=DARK,
                  font=("Helvetica",10), relief="flat", bd=0,
                  highlightthickness=0, insertbackground=DARK)
        if width:  kw["width"]  = width
        if show:   kw["show"]   = show
        border = tk.Frame(parent, bg=BORDER)
        e = tk.Entry(border, **kw)
        e.pack(fill="x", padx=1, pady=1, ipady=6)
        border._entry = e          # expose inner entry if needed
        return border              # caller grids/packs the border frame

    def _section(self, parent, title):
        """Labelled section with a scarlet left-accent bar."""
        f = tk.Frame(parent, bg=WHITE)
        head = tk.Frame(f, bg=WHITE)
        head.pack(fill="x", pady=(10,4))
        tk.Frame(head, bg=SCARLET, width=4).pack(side="left", fill="y", padx=(0,8))
        tk.Label(head, text=title, bg=WHITE, fg=DARK,
                 font=("Helvetica",11,"bold")).pack(side="left")
        # Wrapper trick — only reliable way to get grey (not black) border on macOS
        wrapper = tk.Frame(f, bg=BORDER)
        wrapper.pack(fill="x")
        body = tk.Frame(wrapper, bg=WHITE)
        body.pack(fill="x", padx=1, pady=1)
        return f, body

    # ── Variables ─────────────────────────────────────────────────────────────
    def _vars(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.v_pi     = tk.StringVar(); self.v_user  = tk.StringVar()
        self.v_email  = tk.StringVar(); self.v_dept  = tk.StringVar()
        self.v_date   = tk.StringVar(value=today)
        self.v_mode   = tk.StringVar(value="")
        # Microscope
        self.v_scope  = tk.StringVar()
        self.v_dur    = tk.StringVar(value="00:00:00")
        self.t_start  = None; self.t_end = None; self._tjob = None
        # Sample prep
        self.sp_type  = tk.StringVar()
        self.sp_count = tk.IntVar(value=0)
        # Shared cost display
        self.v_cost   = tk.StringVar(value="Select a service type to see cost")
        self.v_scope.trace_add("write",  lambda *_: self._cost())
        self.sp_type.trace_add("write",  lambda *_: self._cost())
        self.sp_count.trace_add("write", lambda *_: self._cost())

    # ── Top-level UI ──────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=SCARLET, height=64)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=self.config.get("facility_name","Microscopy Core Facility"),
                 bg=SCARLET, fg=WHITE,
                 font=("Helvetica",17,"bold")).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(hdr, text=datetime.now().strftime("%B %d, %Y"),
                 bg=SCARLET, fg="#FFBBBB",
                 font=("Helvetica",9)).place(relx=0.97, rely=0.5, anchor="e")
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True)
        self._tab_log(nb)
        self._tab_history(nb)
        self._tab_admin(nb)

    # ── LOG USAGE TAB ─────────────────────────────────────────────────────────
    def _tab_log(self, nb):
        outer = tk.Frame(nb, bg=WHITE); nb.add(outer, text="  Log Usage  ")

        canvas = tk.Canvas(outer, bg=WHITE, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        tab = tk.Frame(canvas, bg=WHITE)
        wid = canvas.create_window((0,0), window=tab, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        tab.bind("<Configure>",    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        P = dict(padx=20, pady=4)

        # ── User info ──
        sf, card = self._section(tab, "User Information")
        sf.pack(fill="x", **P)
        card.columnconfigure(1, weight=1)

        rows = [("PI / Lab", self.v_pi), ("User Name", self.v_user),
                ("Email",    self.v_email), ("Department", self.v_dept)]
        for r, (lbl, var) in enumerate(rows):
            tk.Label(card, text=lbl+":", bg=WHITE, fg=MID,
                     font=("Helvetica",10)).grid(row=r, column=0, sticky="w",
                                                  padx=(14,10), pady=6)
            ef = self._entry(card, var)
            ef.grid(row=r, column=1, sticky="ew", padx=(0,14), pady=6)

        # Date row
        tk.Label(card, text="Date:", bg=WHITE, fg=MID,
                 font=("Helvetica",10)).grid(row=len(rows), column=0, sticky="w",
                                              padx=(14,10), pady=(6,10))
        df = tk.Frame(card, bg=WHITE)
        df.grid(row=len(rows), column=1, sticky="w", pady=(6,10), padx=(0,14))
        tk.Frame(df, bg=BORDER).pack(side="left")
        date_inner = tk.Frame(df.winfo_children()[-1], bg=BORDER)
        # Simple date entry
        date_border = tk.Frame(df, bg=BORDER)
        date_border.pack(side="left")
        tk.Entry(date_border, textvariable=self.v_date, bg=WHITE, fg=DARK,
                 font=("Helvetica",10), relief="flat", bd=0,
                 highlightthickness=0, width=14).pack(padx=1, pady=1, ipady=6)
        tk.Label(df, text="  YYYY-MM-DD", bg=WHITE, fg="#AAAAAA",
                 font=("Helvetica",9)).pack(side="left")

        # ── Service type — custom toggle buttons (no system-blue radio dots) ──
        sf2, card2 = self._section(tab, "Service Type")
        sf2.pack(fill="x", **P)
        rrow = tk.Frame(card2, bg=WHITE); rrow.pack(fill="x", padx=14, pady=12)
        self._mode_btns = {}
        for val, lbl in [("Microscope Usage","  Microscope Usage  "),
                          ("Sample Preparation","  Sample Preparation  ")]:
            btn = tk.Label(rrow, text=lbl, bg=LIGHT, fg=MID,
                           font=("Helvetica",10,"bold"), padx=10, pady=7,
                           cursor="hand2", relief="flat")
            btn.pack(side="left", padx=(0,8))
            btn.bind("<Button-1>", lambda e, v=val: self._select_mode(v))
            self._mode_btns[val] = btn

        # ── Dynamic panel placeholder ──
        self._dyn = tk.Frame(tab, bg=WHITE)
        self._dyn.pack(fill="x", **P)
        self._scope_panel  = self._build_scope_panel()
        self._sample_panel = self._build_sample_panel()

        # ── Cost + Save ──
        tk.Label(tab, textvariable=self.v_cost, bg=WHITE, fg=GREEN,
                 font=("Helvetica",11,"bold")).pack(pady=(12,4))
        self._primary_btn(tab, "  Save Entry  ", self._save).pack(pady=(0,20))

    def _build_scope_panel(self):
        inst = [k for k,v in self.config["instruments"].items() if v.get("enabled",True)]
        sf, card = self._section(self._dyn, "Microscope Session")
        card.columnconfigure(1, weight=1)
        tk.Label(card, text="Instrument:", bg=WHITE, fg=MID,
                 font=("Helvetica",10)).grid(row=0, column=0, sticky="w", padx=(14,10), pady=10)
        self.scope_cb = ttk.Combobox(card, textvariable=self.v_scope,
                                      values=inst, state="readonly", width=26)
        self.scope_cb.grid(row=0, column=1, sticky="w", pady=10, padx=(0,14))
        trow = tk.Frame(card, bg=WHITE)
        trow.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(0,12))
        self._start_btn = self._primary_btn(trow, "▶  Start", self._start, bg=GREEN)
        self._start_btn.pack(side="left", padx=(0,8))
        self._stop_btn  = self._primary_btn(trow, "⏹  Stop",  self._stop,  bg="#AAAAAA")
        self._stop_btn.pack(side="left", padx=(0,24))
        tk.Label(trow, text="Duration:", bg=WHITE, fg=MID,
                 font=("Helvetica",10)).pack(side="left")
        tk.Label(trow, textvariable=self.v_dur, bg=WHITE, fg=SCARLET,
                 font=("Helvetica",14,"bold")).pack(side="left", padx=8)
        return sf

    def _build_sample_panel(self):
        sp_types = [v.get("full_name",k)
                    for k,v in self.config.get("sample_prep_types",{}).items() if v.get("enabled",True)]
        sf, card = self._section(self._dyn, "Sample Preparation")
        card.columnconfigure(1, weight=1)
        tk.Label(card, text="Preparation Type:", bg=WHITE, fg=MID,
                 font=("Helvetica",10)).grid(row=0, column=0, sticky="w", padx=(14,10), pady=10)
        self.sp_cb = ttk.Combobox(card, textvariable=self.sp_type,
                                   values=sp_types, state="readonly", width=30)
        self.sp_cb.grid(row=0, column=1, sticky="w", pady=10, padx=(0,14))
        tk.Label(card, text="Number of Samples:", bg=WHITE, fg=MID,
                 font=("Helvetica",10)).grid(row=1, column=0, sticky="w", padx=(14,10), pady=(0,12))
        ttk.Spinbox(card, from_=0, to=500, textvariable=self.sp_count,
                    width=8).grid(row=1, column=1, sticky="w", pady=(0,12), padx=(0,14))
        return sf

    def _select_mode(self, val):
        self.v_mode.set(val)
        for k, btn in self._mode_btns.items():
            if k == val:
                btn.config(bg=SCARLET, fg=WHITE)
            else:
                btn.config(bg=LIGHT, fg=MID)
        self._mode()

    def _mode(self):
        for w in self._dyn.winfo_children(): w.pack_forget()
        if self.v_mode.get() == "Microscope Usage":    self._scope_panel.pack(fill="x")
        elif self.v_mode.get() == "Sample Preparation": self._sample_panel.pack(fill="x")
        self._cost()

    def _cost(self):
        try:
            m = self.v_mode.get()
            if m == "Microscope Usage":
                inst = self.v_scope.get()
                if inst in self.config["instruments"]:
                    r = self.config["instruments"][inst]["hourly_rate"]
                    self.v_cost.set(f"Rate: ${r}/hr  ·  Total shown after stopping timer")
                else: self.v_cost.set("Select an instrument to see rate")
            elif m == "Sample Preparation":
                fname = self.sp_type.get(); n = self.sp_count.get()
                code = self._sp_code_for(fname)
                if code:
                    r = self.config["sample_prep_types"][code]["rate_per_sample"]
                    self.v_cost.set(f"Estimated Cost: ${r*n:.2f}  ({n} samples × ${r})")
                else: self.v_cost.set("Select a preparation type to see cost")
            else: self.v_cost.set("Select a service type to see cost")
        except: pass

    def _tick(self):
        if self.t_start:
            e = datetime.now()-self.t_start
            h,r = divmod(int(e.total_seconds()),3600); m,s = divmod(r,60)
            self.v_dur.set(f"{h:02d}:{m:02d}:{s:02d}")
            self._tjob = self.root.after(1000, self._tick)

    def _set_btn_color(self, btn_frame, bg, fg=WHITE):
        """Update label-button colors across frame and all children."""
        btn_frame.config(bg=bg)
        for w in btn_frame.winfo_children():
            try: w.config(bg=bg, fg=fg)
            except: pass
            for c in w.winfo_children():
                try: c.config(bg=bg, fg=fg)
                except: pass

    def _start(self):
        if not self.v_scope.get():
            messagebox.showwarning("Missing","Select an instrument first."); return
        self.t_start = datetime.now()
        self._set_btn_color(self._start_btn, "#AAAAAA")
        self._set_btn_color(self._stop_btn,  SCARLET)
        self._tick()

    def _stop(self):
        if not self.t_start: return
        self.t_end = datetime.now()
        if self._tjob: self.root.after_cancel(self._tjob); self._tjob=None
        e = self.t_end-self.t_start
        h,r = divmod(int(e.total_seconds()),3600); m,s = divmod(r,60)
        self.v_dur.set(f"{h:02d}:{m:02d}:{s:02d}")
        self._set_btn_color(self._start_btn, GREEN)
        self._set_btn_color(self._stop_btn,  "#AAAAAA")
        inst = self.v_scope.get()
        rate = self.config["instruments"].get(inst,{}).get("hourly_rate",0)
        self.v_cost.set(f"Session Cost: ${rate*e.total_seconds()/3600:.2f}  ({h}h {m}m @ ${rate}/hr)")

    def _validate(self):
        errs=[]
        if not self.v_pi.get().strip():  errs.append("PI / Lab name is required.")
        if not self.v_user.get().strip(): errs.append("User name is required.")
        m = self.v_mode.get()
        if m == "Microscope Usage":
            if not self.v_scope.get(): errs.append("Select an instrument.")
            if not self.t_end:         errs.append("Start and stop the timer before saving.")
        elif m == "Sample Preparation":
            if not self.sp_type.get():     errs.append("Select a preparation type.")
            if self.sp_count.get() <= 0:   errs.append("Sample count must be at least 1.")
        else: errs.append("Select a service type.")
        return errs

    def _save(self):
        errs=self._validate()
        if errs: messagebox.showwarning("Missing Information","\n".join(f"• {e}" for e in errs)); return
        threading.Thread(target=self._save_db, daemon=True).start()

    def _save_db(self):
        conn=self._conn()
        try:
            m=self.v_mode.get()
            if m == "Sample Preparation":
                fname=self.sp_type.get(); n=self.sp_count.get()
                code=self._sp_code_for(fname) or fname
                r=self.config["sample_prep_types"].get(code,{}).get("rate_per_sample",0)
                vals=(self.v_date.get(),self.v_pi.get().strip(),self.v_user.get().strip(),
                      self.v_email.get().strip(),self.v_dept.get().strip(),
                      f"{code} — {fname} (Sample Prep)","N/A","N/A","N/A",n,0.0,round(r*n,2))
            else:
                inst=self.v_scope.get(); r=self.config["instruments"].get(inst,{}).get("hourly_rate",0)
                hrs=(self.t_end-self.t_start).total_seconds()/3600
                vals=(self.v_date.get(),self.v_pi.get().strip(),self.v_user.get().strip(),
                      self.v_email.get().strip(),self.v_dept.get().strip(),
                      f"{inst} Microscope Usage",
                      self.t_start.strftime("%H:%M:%S"),self.t_end.strftime("%H:%M:%S"),
                      self.v_dur.get(),0,round(r*hrs,2),0.0)
            conn.execute(
                "INSERT INTO usage(date,pi,user,user_email,department,service_description,"
                "start_time,end_time,usage_duration,sample_count,microscope_cost,sample_cost)"
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", vals)
            conn.commit()
            self.root.after(0, self._save_ok)
        except Exception as ex:
            self.root.after(0, lambda e=ex: messagebox.showerror("Error",str(e)))

    def _save_ok(self):
        messagebox.showinfo("Saved","Entry saved successfully!")
        for v in [self.v_pi,self.v_user,self.v_email,self.v_dept,self.v_scope,self.sp_type]: v.set("")
        self.v_date.set(datetime.now().strftime("%Y-%m-%d"))
        self.sp_count.set(0); self.t_start=None; self.t_end=None
        self.v_dur.set("00:00:00"); self.v_mode.set(""); self._mode()
        for btn in self._mode_btns.values(): btn.config(bg=LIGHT, fg=MID)
        self.v_cost.set("Select a service type to see cost")
        self._refresh_hist()

    # ── HISTORY TAB ───────────────────────────────────────────────────────────
    def _tab_history(self, nb):
        outer=tk.Frame(nb,bg=WHITE); nb.add(outer,text="  History  ")
        tbar=tk.Frame(outer,bg=WHITE); tbar.pack(fill="x",padx=20,pady=12)
        self._secondary_btn(tbar,"🔄  Refresh",    self._refresh_hist).pack(side="left",padx=(0,8))
        self._secondary_btn(tbar,"📤  Export CSV", self._export_csv).pack(side="left")
        tk.Label(tbar,text="  Clear history is available in Admin tab",
                 bg=WHITE,fg="#AAAAAA",font=("Helvetica",9)).pack(side="right",padx=4)

        cols=("date","pi","user","service","dur","s$","p$","tot")
        self.tree=ttk.Treeview(outer,columns=cols,show="headings",height=20)
        hdrs={"date":"Date","pi":"PI / Lab","user":"User","service":"Service",
              "dur":"Duration","s$":"Scope $","p$":"Sample $","tot":"Total"}
        wds={"date":90,"pi":110,"user":100,"service":185,"dur":75,"s$":65,"p$":70,"tot":65}
        for c in cols: self.tree.heading(c,text=hdrs[c]); self.tree.column(c,width=wds[c],anchor="center")
        vsb=ttk.Scrollbar(outer,orient="vertical",  command=self.tree.yview)
        hsb=ttk.Scrollbar(outer,orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set)
        vsb.pack(side="right",fill="y"); hsb.pack(side="bottom",fill="x")
        self.tree.pack(fill="both",expand=True,padx=20,pady=4)
        self.tree.tag_configure("odd",background="#FDF5F5")
        self._refresh_hist()

    def _refresh_hist(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        c=sqlite3.connect(DB_PATH)
        rows=c.execute("SELECT date,pi,user,service_description,usage_duration,"
                       "microscope_cost,sample_cost FROM usage ORDER BY id DESC LIMIT 300").fetchall()
        c.close()
        for i,r in enumerate(rows):
            tot=(r[5] or 0)+(r[6] or 0)
            self.tree.insert("","end",tags=("odd",) if i%2 else (),
                             values=(r[0],r[1],r[2],r[3],r[4],
                                     f"${r[5]:.2f}",f"${r[6]:.2f}",f"${tot:.2f}"))

    def _clear_hist(self):
        if messagebox.askyesno("Clear History","Permanently delete ALL records?"):
            c=sqlite3.connect(DB_PATH); c.execute("DELETE FROM usage"); c.commit(); c.close()
            self._refresh_hist()

    def _export_csv(self):
        p=os.path.join(BASE_DIR,f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        c=sqlite3.connect(DB_PATH)
        rows=c.execute("SELECT * FROM usage ORDER BY id DESC").fetchall(); c.close()
        with open(p,"w",newline="") as f:
            w=csv.writer(f)
            w.writerow(["ID","Date","PI","User","Email","Dept","Service",
                        "Start","End","Duration","Samples","Scope$","Sample$","Created"])
            w.writerows(rows)
        messagebox.showinfo("Exported",f"Saved to:\n{p}")


    # ── ADMIN TAB ─────────────────────────────────────────────────────────────
    def _tab_admin(self, nb):
        tab=tk.Frame(nb,bg=WHITE); nb.add(tab,text="  Admin  ")
        self.admin_tab=tab
        self._lock_screen()

    def _lock_screen(self):
        for w in self.admin_tab.winfo_children(): w.destroy()

        # Center vertically with expand spacers
        tk.Frame(self.admin_tab,bg=WHITE).pack(fill="both",expand=True)
        mid=tk.Frame(self.admin_tab,bg=WHITE); mid.pack()
        tk.Frame(self.admin_tab,bg=WHITE).pack(fill="both",expand=True)

        # Card: grey border frame
        card_border=tk.Frame(mid,bg=BORDER); card_border.pack(padx=40,pady=20)
        card=tk.Frame(card_border,bg=WHITE); card.pack(padx=1,pady=1,ipadx=50,ipady=20)

        tk.Label(card,text="🔒",bg=WHITE,font=("Helvetica",34)).pack(pady=(20,6))
        tk.Label(card,text="Admin Access",bg=WHITE,fg=SCARLET,
                 font=("Helvetica",14,"bold")).pack()
        tk.Label(card,text="Enter PIN to manage instruments and rates",
                 bg=WHITE,fg=MID,font=("Helvetica",10)).pack(pady=(4,14))

        pin=tk.StringVar()
        pin_border=tk.Frame(card,bg=BORDER); pin_border.pack()
        pin_entry=tk.Entry(pin_border,textvariable=pin,show="●",width=14,
                           justify="center",font=("Helvetica",13),
                           relief="flat",bd=0,highlightthickness=0,bg=WHITE)
        pin_entry.pack(padx=1,pady=1,ipady=8)
        pin_entry.focus()

        self._primary_btn(card,"  Unlock  ",lambda:self._unlock(pin.get())).pack(pady=14)
        pin_entry.bind("<Return>",lambda _:self._unlock(pin.get()))

    def _unlock(self,pin):
        if pin==str(self.config.get("admin_pin","1234")):
            self._admin_panel()
        else:
            messagebox.showerror("Wrong PIN","Incorrect PIN. Try again.")

    def _admin_panel(self):
        for w in self.admin_tab.winfo_children(): w.destroy()

        # Header bar
        hdr=tk.Frame(self.admin_tab,bg=SCARLET,height=46)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="Instrument & Rate Manager",bg=SCARLET,fg=WHITE,
                 font=("Helvetica",13,"bold")).place(relx=0.5,rely=0.5,anchor="center")
        self._secondary_btn(hdr,"🔒  Lock",self._lock_screen).place(relx=0.97,rely=0.5,anchor="e")

        # Scrollable body
        _canvas=tk.Canvas(self.admin_tab,bg=WHITE,highlightthickness=0)
        _sb=ttk.Scrollbar(self.admin_tab,orient="vertical",command=_canvas.yview)
        _canvas.configure(yscrollcommand=_sb.set)
        _sb.pack(side="right",fill="y"); _canvas.pack(fill="both",expand=True)
        body=tk.Frame(_canvas,bg=WHITE)
        _wid=_canvas.create_window((0,0),window=body,anchor="nw")
        _canvas.bind("<Configure>",lambda e:_canvas.itemconfig(_wid,width=e.width))
        body.bind("<Configure>",lambda e:_canvas.configure(scrollregion=_canvas.bbox("all")))
        # inner padding
        body=tk.Frame(body,bg=WHITE); body.pack(fill="both",expand=True,padx=20,pady=12)

        # Instruments table
        tk.Label(body,text="INSTRUMENTS",bg=WHITE,fg=GRAY,
                 font=("Helvetica",8,"bold")).pack(anchor="w",pady=(0,4))
        tborder=tk.Frame(body,bg=BORDER); tborder.pack(fill="both",expand=True)
        tinner=tk.Frame(tborder,bg=WHITE); tinner.pack(fill="both",expand=True,padx=1,pady=1)

        cols=("code","name","hr","on")
        self._atree=ttk.Treeview(tinner,columns=cols,show="headings",height=5)
        for c,h,w in zip(cols,("Code","Full Name","$/hr","Active"),(80,220,70,60)):
            self._atree.heading(c,text=h); self._atree.column(c,width=w,anchor="center")
        self._atree.pack(fill="both",expand=True)
        self._atree_load()

        brow=tk.Frame(body,bg=WHITE); brow.pack(fill="x",pady=8)
        self._primary_btn(brow,"➕  Add",    self._adm_add).pack(side="left",padx=(0,8))
        self._secondary_btn(brow,"✏️  Edit", self._adm_edit).pack(side="left",padx=(0,8))
        self._primary_btn(brow,"🗑  Remove", self._adm_del).pack(side="left")

        # Sample prep types table
        tk.Label(body,text="SAMPLE PREPARATION TYPES",bg=WHITE,fg=GRAY,
                 font=("Helvetica",8,"bold")).pack(anchor="w",pady=(12,4))
        spborder=tk.Frame(body,bg=BORDER); spborder.pack(fill="x")
        spinner=tk.Frame(spborder,bg=WHITE); spinner.pack(fill="x",padx=1,pady=1)
        spcols=("code","name","rate","on")
        self._sptree=ttk.Treeview(spinner,columns=spcols,show="headings",height=5)
        for c,h,w in zip(spcols,("Code","Preparation Type","$/sample","Active"),(70,200,80,60)):
            self._sptree.heading(c,text=h); self._sptree.column(c,width=w,anchor="center")
        self._sptree.pack(fill="x")
        self._sptree_load()

        spbrow=tk.Frame(body,bg=WHITE); spbrow.pack(fill="x",pady=8)
        self._primary_btn(spbrow,"➕  Add",    self._sp_adm_add).pack(side="left",padx=(0,8))
        self._secondary_btn(spbrow,"✏️  Edit", self._sp_adm_edit).pack(side="left",padx=(0,8))
        self._primary_btn(spbrow,"🗑  Remove", self._sp_adm_del).pack(side="left")

        # Clear history
        tk.Label(body,text="CLEAR HISTORY",bg=WHITE,fg=GRAY,
                 font=("Helvetica",8,"bold")).pack(anchor="w",pady=(16,4))
        chborder=tk.Frame(body,bg=BORDER); chborder.pack(fill="x")
        chrow=tk.Frame(chborder,bg=WHITE); chrow.pack(fill="x",padx=1,pady=1)
        inner_ch=tk.Frame(chrow,bg=WHITE); inner_ch.pack(padx=14,pady=10,anchor="w")
        tk.Label(inner_ch,text="Permanently delete all session records.",
                 bg=WHITE,fg=MID,font=("Helvetica",10)).pack(side="left",padx=(0,16))
        self._primary_btn(inner_ch,"🗑  Clear All History",self._clear_hist).pack(side="left")

        # Change PIN
        tk.Label(body,text="CHANGE ADMIN PIN",bg=WHITE,fg=GRAY,
                 font=("Helvetica",8,"bold")).pack(anchor="w",pady=(12,4))
        pborder=tk.Frame(body,bg=BORDER); pborder.pack(fill="x")
        prow=tk.Frame(pborder,bg=WHITE); prow.pack(fill="x",padx=1,pady=1)
        inner=tk.Frame(prow,bg=WHITE); inner.pack(padx=14,pady=10,anchor="w")
        tk.Label(inner,text="New PIN:",bg=WHITE,fg=MID,font=("Helvetica",10)).pack(side="left")
        pv=tk.StringVar()
        pb=tk.Frame(inner,bg=BORDER); pb.pack(side="left",padx=8)
        tk.Entry(pb,textvariable=pv,show="●",width=12,relief="flat",bd=0,
                 highlightthickness=0,font=("Helvetica",10),bg=WHITE).pack(padx=1,pady=1,ipady=5)
        self._primary_btn(inner,"Set PIN",lambda:self._set_pin(pv.get())).pack(side="left")

    def _atree_load(self):
        for r in self._atree.get_children(): self._atree.delete(r)
        for k,v in self.config["instruments"].items():
            self._atree.insert("","end",values=(
                k, v["full_name"], f"${v['hourly_rate']}",
                "Yes" if v.get("enabled",True) else "No"))

    def _sptree_load(self):
        for r in self._sptree.get_children(): self._sptree.delete(r)
        for k,v in self.config.get("sample_prep_types",{}).items():
            self._sptree.insert("","end",values=(
                k, v.get("full_name",k), f"${v['rate_per_sample']}",
                "Yes" if v.get("enabled",True) else "No"))

    def _sp_adm_add(self):  self._sp_dialog()
    def _sp_adm_edit(self):
        sel=self._sptree.selection()
        if not sel: messagebox.showwarning("Select","Select a type to edit."); return
        self._sp_dialog(self._sptree.item(sel[0])["values"][0])
    def _sp_adm_del(self):
        sel=self._sptree.selection()
        if not sel: messagebox.showwarning("Select","Select a type to remove."); return
        k=self._sptree.item(sel[0])["values"][0]
        if messagebox.askyesno("Remove",f"Remove '{k}'?"):
            del self.config["sample_prep_types"][k]; save_config(self.config)
            self._sptree_load(); self._refresh_sp_cb()

    def _sp_dialog(self, key=None):
        win=tk.Toplevel(self.root); win.configure(bg=WHITE)
        win.title("Edit" if key else "Add Preparation Type"); win.grab_set(); win.resizable(False,False)
        hdr=tk.Frame(win,bg=SCARLET,height=40); hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="Sample Preparation Type",bg=SCARLET,fg=WHITE,
                 font=("Helvetica",12,"bold")).place(relx=0.5,rely=0.5,anchor="center")
        d=self.config.get("sample_prep_types",{}).get(key,{}) if key else {}
        form=tk.Frame(win,bg=WHITE,padx=20,pady=14); form.pack()
        flds=[("Code (e.g. SC)",  key or ""),
              ("Full Name",        d.get("full_name","")),
              ("Rate per Sample ($)", str(d.get("rate_per_sample","")))]
        vs=[]
        for r,(lbl,val) in enumerate(flds):
            tk.Label(form,text=lbl+":",bg=WHITE,fg=MID,font=("Helvetica",10)).grid(
                row=r,column=0,sticky="w",pady=6,padx=(0,14))
            v=tk.StringVar(value=val)
            fb=tk.Frame(form,bg=BORDER); fb.grid(row=r,column=1,sticky="ew",pady=6)
            e=tk.Entry(fb,textvariable=v,width=26,relief="flat",bd=0,
                       highlightthickness=0,font=("Helvetica",10),bg=WHITE)
            e.pack(padx=1,pady=1,ipady=5)
            if key and r==0: e.config(state="disabled",bg=LIGHT)
            vs.append(v)
        en=tk.BooleanVar(value=d.get("enabled",True))
        tk.Checkbutton(form,text="Enabled",variable=en,bg=WHITE,
                       font=("Helvetica",10)).grid(row=len(flds),column=1,sticky="w",pady=6)
        def _sv():
            try:
                k2=key or vs[0].get().strip().upper()
                if not k2: messagebox.showwarning("Required","Code is required.",parent=win); return
                if "sample_prep_types" not in self.config: self.config["sample_prep_types"]={}
                self.config["sample_prep_types"][k2]={
                    "full_name": vs[1].get().strip(),
                    "rate_per_sample": float(vs[2].get()),
                    "enabled": en.get()}
                save_config(self.config); self._sptree_load(); self._refresh_sp_cb(); win.destroy()
            except ValueError: messagebox.showerror("Invalid","Rate must be a number.",parent=win)
        self._primary_btn(win,"  Save  ",_sv).pack(pady=10)

    def _sp_code_for(self, full_name):
        """Return code key for a given full_name, or None."""
        for k,v in self.config.get("sample_prep_types",{}).items():
            if v.get("full_name",k) == full_name:
                return k
        return None

    def _refresh_sp_cb(self):
        sp_types=[v.get("full_name",k)
                  for k,v in self.config.get("sample_prep_types",{}).items() if v.get("enabled",True)]
        self.sp_cb["values"]=sp_types

    def _adm_add(self):  self._inst_dialog()
    def _adm_edit(self):
        sel=self._atree.selection()
        if not sel: messagebox.showwarning("Select","Select an instrument to edit."); return
        self._inst_dialog(self._atree.item(sel[0])["values"][0])

    def _inst_dialog(self,key=None):
        win=tk.Toplevel(self.root); win.configure(bg=WHITE)
        win.title("Edit Instrument" if key else "Add Instrument")
        win.grab_set(); win.resizable(False,False)

        hdr=tk.Frame(win,bg=SCARLET,height=40); hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="Edit Instrument" if key else "Add Instrument",
                 bg=SCARLET,fg=WHITE,font=("Helvetica",12,"bold")).place(relx=0.5,rely=0.5,anchor="center")

        d=self.config["instruments"].get(key,{}) if key else {}
        form=tk.Frame(win,bg=WHITE,padx=20,pady=16); form.pack()
        flds=[("Code","key"),("Full Name","full_name"),("Hourly Rate ($)","hourly_rate")]
        vs={}
        for r,(lbl,fld) in enumerate(flds):
            tk.Label(form,text=lbl+":",bg=WHITE,fg=MID,
                     font=("Helvetica",10)).grid(row=r,column=0,sticky="w",pady=6,padx=(0,14))
            v=tk.StringVar(value=str(d.get(fld, key if fld=="key" else "")))
            fb=tk.Frame(form,bg=BORDER); fb.grid(row=r,column=1,sticky="ew",pady=6)
            e=tk.Entry(fb,textvariable=v,width=26,relief="flat",bd=0,
                       highlightthickness=0,font=("Helvetica",10),bg=WHITE)
            e.pack(padx=1,pady=1,ipady=5)
            if key and fld=="key": e.config(state="disabled",bg=LIGHT)
            vs[fld]=v
        en=tk.BooleanVar(value=d.get("enabled",True))
        tk.Checkbutton(form,text="Enabled",variable=en,bg=WHITE,
                       font=("Helvetica",10)).grid(row=len(flds),column=1,sticky="w",pady=6)

        def _sv():
            try:
                k=key or vs["key"].get().strip().upper()
                if not k: messagebox.showwarning("Required","Code is required.",parent=win); return
                self.config["instruments"][k]={
                    "full_name":vs["full_name"].get().strip(),
                    "hourly_rate":float(vs["hourly_rate"].get()),
                    "enabled":en.get()}
                save_config(self.config); self._atree_load(); self._refresh_insts(); win.destroy()
            except ValueError: messagebox.showerror("Invalid","Rates must be numbers.",parent=win)

        self._primary_btn(win,"  Save  ",_sv).pack(pady=12)

    def _adm_del(self):
        sel=self._atree.selection()
        if not sel: messagebox.showwarning("Select","Select an instrument to remove."); return
        k=self._atree.item(sel[0])["values"][0]
        if messagebox.askyesno("Remove",f"Remove '{k}'? History is preserved."):
            del self.config["instruments"][k]; save_config(self.config)
            self._atree_load(); self._refresh_insts()

    def _refresh_insts(self):
        inst=[k for k,v in self.config["instruments"].items() if v.get("enabled",True)]
        self.scope_cb["values"]=inst

    def _set_pin(self,pin):
        if len(str(pin))<4: messagebox.showwarning("Too Short","PIN must be 4+ characters."); return
        self.config["admin_pin"]=pin; save_config(self.config)
        messagebox.showinfo("Updated","Admin PIN changed.")

if __name__=="__main__":
    root=tk.Tk()
    App(root)
    root.mainloop()
