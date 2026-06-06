import tkinter as tk
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

# scroll region
def _scroll(parent):
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
    sb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    win = canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.winfo_exists() and canvas.yview_scroll(int(-ev.delta/120), "units")))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    return inner

# detail popup
def _popup(page, item):
    win = tk.Toplevel(page.winfo_toplevel()); win.title(item["title"])
    win.geometry("400x320"); win.configure(bg=CARD); win.resizable(False, False)
    tag = "Task" if item["kind"] == "task" else "Reminder"
    tk.Label(win, text=item["title"], font=(FONT,15,"bold"), bg=DEEP, fg=CARD, wraplength=360, pady=12).pack(fill="x")
    body = tk.Frame(win, bg=CARD, padx=22, pady=16); body.pack(fill="both", expand=True)
    def row(k,v):
        f = tk.Frame(body, bg=CARD); f.pack(fill="x", pady=3)
        tk.Label(f, text=k, font=(FONT,10,"bold"), bg=CARD, fg=MUTED, width=11, anchor="w").pack(side="left")
        tk.Label(f, text=str(v), font=(FONT,11), bg=CARD, fg=DEEP, anchor="w", wraplength=240, justify="left").pack(side="left")
    row("Type", tag); row("Deadline", item["deadline"])
    if item["difficulty"] is not None: row("Difficulty", item["difficulty"])
    row("Details", item["description"] or "—")

# schedule screen
def open_schedule(page, show_page, manager):
    for w in page.winfo_children(): w.destroy()
    _home_bar(page, show_page, "📅  Weekly Schedule")
    toolbar = tk.Frame(page, bg=BG); toolbar.pack(fill="x", padx=24, pady=(8,0))
    tk.Button(toolbar, text="🔄 Refresh", font=(FONT,11,"bold"), bg=CARD, fg=DEEP, relief="flat",
              cursor="hand2", activebackground=SOFT,
              command=lambda: open_schedule(page, show_page, manager)).pack(side="right")
    holder = _scroll(page)

    today = datetime.now().date()
    days = [today + timedelta(days=i) for i in range(7)]
    buckets = {d: [] for d in days}
    overdue, later = [], []
    for it in manager.schedule_items():
        try:
            dt = datetime.strptime(it["deadline"], "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            later.append(it); continue
        if dt < today: overdue.append(it)
        elif dt in buckets: buckets[dt].append(it)
        else: later.append(it)

    def mini(parent, it):
        color = DEEP if it["kind"] == "task" else GOLD
        card = tk.Frame(parent, bg=CARD, padx=8, pady=5, highlightthickness=1, highlightbackground=SOFT)
        card.pack(fill="x", pady=3)
        tk.Frame(card, bg=color, width=4, height=28).pack(side="left", padx=(0,6))
        inner = tk.Frame(card, bg=CARD); inner.pack(side="left", fill="x", expand=True)
        tk.Label(inner, text=it["title"], font=(FONT,10,"bold"), bg=CARD, fg=DEEP, anchor="w",
                 wraplength=130, justify="left").pack(fill="x")
        tk.Label(inner, text=it["deadline"][11:16], font=(FONT,9), bg=CARD, fg=MUTED, anchor="w").pack(fill="x")
        for w in (card, inner) + tuple(inner.winfo_children()):
            w.configure(cursor="hand2"); w.bind("<Button-1>", lambda e, x=it: _popup(page, x))

    if overdue:
        strip = tk.Frame(holder, bg=BG); strip.pack(fill="x", padx=10, pady=(12,4))
        tk.Label(strip, text=f"🔴  Overdue ({len(overdue)})", font=(FONT,13,"bold"),
                 bg=DEEP, fg=CARD, anchor="w", padx=10, pady=4).pack(fill="x")
        box = tk.Frame(strip, bg=BG); box.pack(fill="x")
        for it in sorted(overdue, key=lambda x: x["deadline"]): mini(box, it)

    grid = tk.Frame(holder, bg=BG); grid.pack(fill="both", expand=True, padx=10, pady=10)
    for i, d in enumerate(days):
        col = tk.Frame(grid, bg=BG); col.grid(row=0, column=i, sticky="nsew", padx=4)
        grid.grid_columnconfigure(i, weight=1)
        head = GREEN if d == today else DEEP
        tk.Label(col, text=d.strftime("%a"), font=(FONT,11,"bold"), bg=head, fg=CARD).pack(fill="x")
        tk.Label(col, text=d.strftime("%d %b"), font=(FONT,9), bg=SOFT, fg=DEEP).pack(fill="x")
        items = sorted(buckets[d], key=lambda x: x["deadline"])
        if not items:
            tk.Label(col, text="—", font=(FONT,10), bg=BG, fg=SOFT).pack(pady=8)
        for it in items: mini(col, it)

    if later:
        strip = tk.Frame(holder, bg=BG); strip.pack(fill="x", padx=10, pady=(4,16))
        tk.Label(strip, text=f"📌  Later ({len(later)})", font=(FONT,13,"bold"),
                 bg=GOLD, fg=CARD, anchor="w", padx=10, pady=4).pack(fill="x")
        box = tk.Frame(strip, bg=BG); box.pack(fill="x")
        for it in sorted(later, key=lambda x: x["deadline"]): mini(box, it)