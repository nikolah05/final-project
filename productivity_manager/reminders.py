import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta

# theme
BG="#c94c4c"; CARD="#ffffff"; SOFT="#e7bcbc"; DEEP="#a33838"
GREEN="#4caf72"; GOLD="#e8a838"; MUTED="#8a8a8a"; FONT="Segoe UI"

# home bar
def _home_bar(page, show_page, title):
    bar = tk.Frame(page, bg=CARD, height=58); bar.pack(fill="x"); bar.pack_propagate(False)
    tk.Button(bar, text="⌂  Home", font=(FONT,12,"bold"), bg=DEEP, fg=CARD, relief="flat",
              padx=14, cursor="hand2", activebackground=BG, activeforeground=CARD,
              command=lambda: show_page("Main Menu")).pack(side="left", padx=14, pady=10)
    tk.Label(bar, text=title, font=(FONT,17,"bold"), bg=CARD, fg=DEEP).pack(side="left", padx=4)

# add / edit form  (reminders only)
def _form(page, manager, refresh, existing=None):
    editing = existing is not None
    win = tk.Toplevel(page.winfo_toplevel())
    win.title("Edit Reminder" if editing else "Add Reminder")
    win.geometry("420x460"); win.configure(bg=CARD); win.resizable(False, False)
    tk.Label(win, text=("Edit Reminder" if editing else "New Reminder"), font=(FONT,16,"bold"),
             bg=DEEP, fg=CARD, pady=12).pack(fill="x")
    form = tk.Frame(win, bg=CARD, padx=24, pady=16); form.pack(fill="both", expand=True)

    def field(t): tk.Label(form, text=t, font=(FONT,10,"bold"), bg=CARD, fg=DEEP).pack(anchor="w", pady=(10,2))
    field("Title")
    title_e = tk.Entry(form, font=(FONT,11)); title_e.pack(fill="x", ipady=3)
    field("Description")
    desc_e = tk.Text(form, font=(FONT,11), height=4); desc_e.pack(fill="x")
    field("Remind me in")
    row = tk.Frame(form, bg=CARD); row.pack(anchor="w")
    d_e = tk.Entry(row, width=6, font=(FONT,11)); d_e.grid(row=0, column=0)
    tk.Label(row, text="d", bg=CARD, fg=MUTED).grid(row=0, column=1, padx=(2,8))
    h_e = tk.Entry(row, width=6, font=(FONT,11)); h_e.grid(row=0, column=2)
    tk.Label(row, text="h", bg=CARD, fg=MUTED).grid(row=0, column=3, padx=(2,8))
    m_e = tk.Entry(row, width=6, font=(FONT,11)); m_e.grid(row=0, column=4)
    tk.Label(row, text="m", bg=CARD, fg=MUTED).grid(row=0, column=5, padx=2)
    for e in (d_e,h_e,m_e): e.insert(0,"0")
    if editing:
        title_e.insert(0, existing.title); desc_e.insert("1.0", existing.description)
        tk.Label(form, text=f"(current deadline: {existing.deadline})", font=(FONT,9,"italic"),
                 bg=CARD, fg=MUTED).pack(anchor="w", pady=(6,0))

    def save():
        title = title_e.get().strip()
        desc = desc_e.get("1.0","end").strip()
        if not title:
            messagebox.showerror("Error", "Title is required.", parent=win); return
        if len(title) > 50:
            messagebox.showerror("Error", "Title must be 50 characters or fewer.", parent=win); return
        try:
            d=int(d_e.get() or 0); h=int(h_e.get() or 0); m=int(m_e.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Time fields must be numbers.", parent=win); return
        deadline = (datetime.now()+timedelta(days=d,hours=h,minutes=m)).strftime("%Y-%m-%d %H:%M:%S")
        if editing:
            manager.update_reminder(existing.title, existing.deadline, title, desc, deadline)
        else:
            manager.add_reminder(title, desc, deadline)
        win.destroy(); refresh()

    tk.Button(form, text="Save Reminder", font=(FONT,12,"bold"), bg=BG, fg=CARD, relief="flat",
              cursor="hand2", activebackground=DEEP, activeforeground=CARD, command=save).pack(fill="x", pady=(20,0), ipady=4)

# reminders screen
def open_reminders(page, show_page, manager):
    for w in page.winfo_children(): w.destroy()
    _home_bar(page, show_page, "⏰  Reminders")

    toolbar = tk.Frame(page, bg=BG); toolbar.pack(fill="x", padx=24, pady=(10,0))
    search_v = tk.StringVar()
    tk.Label(toolbar, text="🔎", bg=BG, fg=CARD, font=(FONT,13)).pack(side="left")
    tk.Entry(toolbar, textvariable=search_v, font=(FONT,11), width=24).pack(side="left", padx=(4,6), ipady=2)
    tk.Button(toolbar, text="Search", font=(FONT,11,"bold"), bg=CARD, fg=DEEP, relief="flat",
              cursor="hand2", activebackground=SOFT, command=lambda: build()).pack(side="left")
    tk.Button(toolbar, text="＋  Add Reminder", font=(FONT,12,"bold"), bg=CARD, fg=DEEP, relief="flat",
              cursor="hand2", activebackground=SOFT, command=lambda: _form(page, manager, build)).pack(side="right")

    def _matches(obj, query):
        q = query.lower().strip()
        if not q: return True
        return q in (obj.title or "").lower() or q in (getattr(obj, "description", "") or "").lower()

    def _is_overdue(obj, now):
        try:
            return datetime.strptime(obj.deadline, "%Y-%m-%d %H:%M:%S") < now
        except (ValueError, TypeError):
            return False

    holder = {}
    def build():
        old = holder.get("f")
        if old: old.destroy()
        wrap = tk.Frame(page, bg=BG); wrap.pack(fill="both", expand=True, padx=24, pady=14)
        holder["f"] = wrap
        query = search_v.get()
        now = datetime.now()

        items = [("reminder", r) for r in manager.search_reminders(query)]
        try:
            items += [("task", t) for t in manager.load_tasks() if _matches(t, query)]
        except Exception:
            pass

        active, overdue = [], []
        for kind, obj in items:
            (overdue if _is_overdue(obj, now) else active).append((kind, obj))
        active.sort(key=lambda it: it[1].deadline)
        overdue.sort(key=lambda it: it[1].deadline)

        _column(wrap, "✅  Active", GREEN, active, page, manager, build)
        _column(wrap, "🔴  Overdue", DEEP, overdue, page, manager, build)
    build()

# one column  (items are (kind, obj) tuples: kind is "reminder" or "task")
def _column(parent, heading, color, items, page, manager, refresh):
    col = tk.Frame(parent, bg=BG); col.pack(side="left", fill="both", expand=True, padx=8)
    tk.Label(col, text=heading, font=(FONT,13,"bold"), bg=color, fg=CARD, pady=6).pack(fill="x")
    canvas = tk.Canvas(col, bg=BG, highlightthickness=0)
    sb = tk.Scrollbar(col, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=inner, anchor="nw"); canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
    if not items:
        tk.Label(inner, text="— none —", font=(FONT,11,"italic"), bg=BG, fg=SOFT).pack(pady=20); return
    for kind, r in items:
        is_task = (kind == "task")
        card = tk.Frame(inner, bg=CARD, padx=12, pady=8, highlightthickness=1, highlightbackground=SOFT)
        card.pack(fill="x", padx=4, pady=4)

        head = tk.Frame(card, bg=CARD); head.pack(fill="x")
        badge_txt, badge_bg, badge_fg = ("TASK", GOLD, CARD) if is_task else ("REMINDER", SOFT, DEEP)
        tk.Label(head, text=badge_txt, font=(FONT,8,"bold"), bg=badge_bg, fg=badge_fg, padx=6).pack(side="left")
        tk.Label(head, text=r.title, font=(FONT,12,"bold"), bg=CARD, fg=DEEP, anchor="w",
                 wraplength=170, justify="left").pack(side="left", padx=(6,0))

        tk.Label(card, text=f"⏰ {r.deadline}", font=(FONT,10), bg=CARD, fg=MUTED, anchor="w").pack(fill="x", pady=(4,0))
        desc = getattr(r, "description", "") or ""
        if desc.strip():
            preview = desc[:90] + ("…" if len(desc) > 90 else "")
            tk.Label(card, text=preview, font=(FONT,10), bg=CARD, fg=MUTED, anchor="w",
                     wraplength=220, justify="left").pack(fill="x", pady=(4,0))

        if is_task:
            tk.Label(card, text="Manage in Task Manager", font=(FONT,9,"italic"),
                     bg=CARD, fg=MUTED, anchor="e").pack(fill="x", pady=(4,0))
        else:
            btns = tk.Frame(card, bg=CARD); btns.pack(anchor="e", pady=(4,0))
            tk.Button(btns, text="✎ Edit", font=(FONT,9,"bold"), bg=SOFT, fg=DEEP, relief="flat",
                      cursor="hand2", command=lambda x=r: _form(page, manager, refresh, existing=x)).pack(side="left", padx=4)
            tk.Button(btns, text="🗑", font=(FONT,10), bg=CARD, fg=DEEP, relief="flat", cursor="hand2",
                      command=lambda x=r: _delete(x, manager, refresh)).pack(side="left")

# delete  (reminders only)
def _delete(reminder, manager, refresh):
    if messagebox.askyesno("Delete", f"Delete reminder '{reminder.title}'?"):
        manager.delete_reminder(reminder.title, reminder.deadline); refresh()