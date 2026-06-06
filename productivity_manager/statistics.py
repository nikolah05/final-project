import tkinter as tk

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

# statistics screen
def open_statistics(page, show_page, manager):
    for w in page.winfo_children(): w.destroy()
    _home_bar(page, show_page, "📊  Statistics")
    body = tk.Frame(page, bg=BG); body.pack(fill="both", expand=True, padx=34, pady=20)

    def build():
        for w in body.winfo_children(): w.destroy()
        s = manager.weekly_summary()
        tk.Label(body, text="Weekly summary", font=(FONT,16,"bold"), bg=BG, fg=CARD).pack(anchor="w", pady=(0,8))
        grid = tk.Frame(body, bg=CARD, padx=18, pady=14); grid.pack(anchor="w")
        rows = [("Active tasks", s["active"]), ("Completed tasks", s["completed"]),
                ("Overdue tasks", s["overdue"]), ("Reminders", s["reminders"]),
                ("Journal entries", s["journals"]), ("Pomodoro this week", s["pomodoro_week"])]
        for i,(k,v) in enumerate(rows):
            tk.Label(grid, text=k, font=(FONT,11,"bold"), bg=CARD, fg=DEEP, width=20, anchor="w").grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(grid, text=str(v), font=(FONT,11), bg=CARD, fg=MUTED, anchor="w").grid(row=i, column=1, sticky="w", padx=10)
        tk.Button(body, text="🔄 Refresh", font=(FONT,11,"bold"), bg=SOFT, fg=DEEP, relief="flat",
                  cursor="hand2", command=build).pack(anchor="w", pady=(10,0))

        tk.Label(body, text="Algorithm performance", font=(FONT,16,"bold"), bg=BG, fg=CARD).pack(anchor="w", pady=(20,4))
        tk.Label(body, text="Times the loop-based sort (O(n²)) against the recursive sort (O(n log n)).",
                 font=(FONT,10), bg=BG, fg=SOFT, justify="left").pack(anchor="w")
        tk.Button(body, text="▶ Run analysis", font=(FONT,12,"bold"), bg=BG, fg=CARD, relief="flat",
                  cursor="hand2", activebackground=DEEP, activeforeground=CARD,
                  command=lambda: _results(page, manager)).pack(anchor="w", pady=12)
    build()

# results window
def _results(page, manager):
    win = tk.Toplevel(page.winfo_toplevel()); win.title("Performance"); win.geometry("560x430"); win.configure(bg=CARD)
    tk.Label(win, text="Bubble sort  vs  Merge sort", font=(FONT,15,"bold"), bg=CARD, fg=DEEP).pack(pady=(14,8))
    res = manager.benchmark_sorts(sizes=(100,250,500,1000))
    tbl = tk.Frame(win, bg=CARD); tbl.pack(padx=16)
    for c,h in enumerate(["n","Bubble (s)","Merge (s)","Bubble / Merge"]):
        tk.Label(tbl, text=h, font=(FONT,11,"bold"), bg=DEEP, fg=CARD, width=13, relief="groove").grid(row=0, column=c)
    for i,r in enumerate(res, start=1):
        ratio = (r["bubble"]/r["merge"]) if r["merge"] else 0
        for c,v in enumerate([r["size"], f"{r['bubble']:.5f}", f"{r['merge']:.5f}", f"{ratio:.1f}×"]):
            tk.Label(tbl, text=str(v), font=(FONT,11), bg=CARD, fg=DEEP, width=13, relief="groove").grid(row=i, column=c)
    tk.Label(win, justify="left", bg=CARD, fg=MUTED, font=(FONT,10), wraplength=520,
             text=("\nBubble sort does about n² comparisons, so its time roughly quadruples when n "
                   "doubles. Merge sort does about n log n work and grows far more slowly. The last "
                   "column shows that gap widening as n grows.")).pack(padx=16, pady=10, anchor="w")