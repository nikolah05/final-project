import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import csv, os

# theme
BG="#c94c4c"; CARD="#ffffff"; SOFT="#e7bcbc"; DEEP="#a33838"
GREEN="#4caf72"; GOLD="#e8a838"; MUTED="#8a8a8a"; FONT="Segoe UI"

HEADERS = ["task","focus_minutes","break_minutes","total_reps","start_time","end_time","status","task_completed"]

# couldn't start a sess without a task
NO_TOPIC_LABEL = "🗒  No specific topic"
# logged value in the .csv file
NO_TOPIC_VALUE = "No specific topic"

def _resolve_task_name(value):
    """Map the dropdown selection to (task_name, is_generic).

    is_generic is True when the session is not tied to a real task, so the
    caller knows to skip anything that only makes sense for a real task
    (e.g. asking to mark it completed)."""
    if not value or value == NO_TOPIC_LABEL:
        return NO_TOPIC_VALUE, True
    return value, False

# session model
class PomodoroSession:
    def __init__(self, task, focus_minutes, break_minutes, total_reps,
                 start_time, end_time="", status="In Progress", task_completed=False):
        self._task = task
        self._focus_minutes = int(focus_minutes)
        self._break_minutes = int(break_minutes)
        self._total_reps = int(total_reps)
        self._start_time = start_time
        self._end_time = end_time
        self._status = status
        self._task_completed = task_completed if isinstance(task_completed, bool) else str(task_completed) == "Yes"

    @property
    def task(self): return self._task
    @property
    def focus_minutes(self): return self._focus_minutes
    @property
    def break_minutes(self): return self._break_minutes
    @property
    def total_reps(self): return self._total_reps
    @property
    def start_time(self): return self._start_time
    @property
    def status(self): return self._status
    @property
    def task_completed(self): return self._task_completed
    @property
    def end_time(self): return self._end_time
    @end_time.setter
    def end_time(self, v): self._end_time = v
    @status.setter
    def status(self, v): self._status = v
    @task_completed.setter
    def task_completed(self, v): self._task_completed = bool(v)

    def date_str(self):
        return self._start_time[:10] if self._start_time else ""
    def to_row(self):
        return [self._task, self._focus_minutes, self._break_minutes, self._total_reps,
                self._start_time, self._end_time, self._status, "Yes" if self._task_completed else "No"]
    @classmethod
    def from_row(cls, row):
        return cls(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7] == "Yes")

# load log
def load_sessions(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) < 8 or row[0] == "task": continue
                try: out.append(PomodoroSession.from_row(row))
                except (ValueError, IndexError): continue
    except FileNotFoundError:
        pass
    return list(reversed(out))

# save log
def save_session(path, session):
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new: w.writerow(HEADERS)
        w.writerow(session.to_row())

# home bar
def _home_bar(page, on_home, title):
    bar = tk.Frame(page, bg=CARD, height=58); bar.pack(fill="x"); bar.pack_propagate(False)
    tk.Button(bar, text="⌂  Home", font=(FONT,12,"bold"), bg=DEEP, fg=CARD, relief="flat",
              padx=14, cursor="hand2", activebackground=BG, activeforeground=CARD,
              command=on_home).pack(side="left", padx=14, pady=10)
    tk.Label(bar, text=title, font=(FONT,17,"bold"), bg=CARD, fg=DEEP).pack(side="left", padx=4)

# history window
def _history(page, manager):
    win = tk.Toplevel(page.winfo_toplevel()); win.title("Pomodoro History")
    win.geometry("820x540"); win.configure(bg=CARD)
    tk.Label(win, text="Session history", font=(FONT,16,"bold"), bg=CARD, fg=DEEP).pack(pady=(16,4))
    bar = tk.Frame(win, bg=CARD); bar.pack(fill="x", padx=20)
    tk.Label(bar, text="Filter:", bg=CARD, fg=DEEP, font=(FONT,11,"bold")).pack(side="left")
    fvar = tk.StringVar(value="All")
    summary = tk.Label(win, text="", bg=CARD, fg=MUTED, font=(FONT,11,"italic"))
    cols = ("Task","Focus","Break","Reps","Date","Status","Done")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=15)
    for c,w in zip(cols, (200,70,70,60,130,100,70)):
        tree.heading(c, text=c); tree.column(c, width=w, anchor="center")
    def refresh():
        for r in tree.get_children(): tree.delete(r)
        f = fvar.get()
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        shown = 0
        for s in load_sessions(manager.pomodoro_file):
            if f == "Today" and s.date_str() != today: continue
            if f == "This Week" and s.date_str() < week_start: continue
            if f == "Finished" and s.status != "Finished": continue
            if f == "Cancelled" and s.status != "Cancelled": continue
            tree.insert("", "end", values=(s.task, f"{s.focus_minutes}m", f"{s.break_minutes}m",
                        s.total_reps, s.start_time[:16], s.status, "✅" if s.task_completed else "—"))
            shown += 1
        summary.config(text=f"{shown} session(s)")
    for label in ("All","Today","This Week","Finished","Cancelled"):
        tk.Radiobutton(bar, text=label, variable=fvar, value=label, bg=CARD, fg=DEEP,
                       selectcolor=SOFT, activebackground=CARD, font=(FONT,10),
                       command=refresh).pack(side="left", padx=4)
    summary.pack(pady=2)
    tree.pack(fill="both", expand=True, padx=20, pady=10)
    refresh()

# pomodoro screen
def open_pomodoro(page, show_page, manager):
    for w in page.winfo_children(): w.destroy()
    active = [None]
    state = {"running": False, "paused": False, "after_id": None, "timer": 0,
             "rep": 1, "reps": 0, "is_break": False, "focus": 0, "brk": 0, "generic": False}

    def safe_home():
        if state["running"]:
            if not messagebox.askyesno("Leave?", "A session is running. Leave without saving?"): return
            _cancel(save=False)
        show_page("Main Menu")
    _home_bar(page, safe_home, "⏳  Pomodoro")

    wrap = tk.Frame(page, bg=BG); wrap.pack(expand=True)
    tk.Label(wrap, text="Focus Timer", font=(FONT,24,"bold"), bg=BG, fg=CARD).pack(pady=(20,12))

    def task_titles():
        try:
            return [t.title for t in manager.load_tasks()]
        except Exception:
            return []

    selected = tk.StringVar(value=NO_TOPIC_LABEL)
    tk.Label(wrap, text="Task", bg=BG, fg=CARD, font=(FONT,12,"bold")).pack()
    om = tk.OptionMenu(wrap, selected, NO_TOPIC_LABEL, *task_titles())
    om.config(bg=CARD, fg=DEEP, relief="flat", font=(FONT,11), width=28, highlightthickness=0); om.pack(pady=(2,2))

    def refresh_tasks():
        menu = om["menu"]
        menu.delete(0, "end")
        options = [NO_TOPIC_LABEL] + task_titles()
        for label in options:
            menu.add_command(label=label, command=tk._setit(selected, label))
        if selected.get() not in options:
            selected.set(NO_TOPIC_LABEL)
    om["menu"].config(postcommand=refresh_tasks)

    tk.Label(wrap, text="Leave it on “No specific topic” to just focus.",
             bg=BG, fg=SOFT, font=(FONT,10,"italic")).pack(pady=(0,10))

    fields = tk.Frame(wrap, bg=BG); fields.pack(pady=4)
    def field(parent, label, default):
        col = tk.Frame(parent, bg=BG); col.pack(side="left", padx=10)
        tk.Label(col, text=label, bg=BG, fg=CARD, font=(FONT,11,"bold")).pack()
        e = tk.Entry(col, width=8, font=(FONT,12), justify="center"); e.insert(0, default); e.pack(pady=3)
        return e
    focus_e = field(fields, "Focus (min)", "25")
    break_e = field(fields, "Break (min)", "5")
    reps_e = field(fields, "Repetitions", "4")

    timer_lbl = tk.Label(wrap, text="00:00", font=(FONT,52,"bold"), bg=BG, fg=CARD); timer_lbl.pack(pady=(16,2))
    status_lbl = tk.Label(wrap, text="Ready when you are.", bg=BG, fg=SOFT, font=(FONT,13)); status_lbl.pack(pady=(0,12))

    def fmt(s): return f"{s//60:02}:{s%60:02}"

    def finish():
        state["running"] = False
        s = active[0]
        if state["generic"]:
            if s:
                s.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                s.status = "Finished"; s.task_completed = False
                save_session(manager.pomodoro_file, s)
            messagebox.showinfo("Complete!", "All repetitions finished! 🎉\nSession logged.")
        else:
            done = messagebox.askyesno("Complete!", "All repetitions finished!\nMark this task as completed?")
            if s:
                s.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                s.status = "Finished"; s.task_completed = done
                save_session(manager.pomodoro_file, s)
            if done and s and manager.complete_task_by_title(s.task):
                messagebox.showinfo("Done", "Task moved to completed. Great work! ✅")
            else:
                messagebox.showinfo("Done", "Session logged.")
        active[0] = None; timer_lbl.config(text="00:00"); status_lbl.config(text="All done! 🎉")

    def tick():
        if not state["running"] or state["paused"]: return
        timer_lbl.config(text=fmt(state["timer"]))
        if state["timer"] > 0:
            state["timer"] -= 1; state["after_id"] = page.after(1000, tick); return
        page.bell()
        if not state["is_break"]:
            if state["rep"] >= state["reps"]: finish(); return
            state["is_break"] = True; state["timer"] = state["brk"] * 60
            status_lbl.config(text=f"☕ Break ({state['rep']}/{state['reps']})")
        else:
            state["rep"] += 1; state["is_break"] = False; state["timer"] = state["focus"] * 60
            status_lbl.config(text=f"🎯 Focus {state['rep']}/{state['reps']}")
        tick()

    def start():
        if state["running"]:
            messagebox.showwarning("Running", "A session is already running."); return
        task_name, generic = _resolve_task_name(selected.get())
        try:
            f, b, r = int(focus_e.get()), int(break_e.get()), int(reps_e.get())
        except ValueError:
            messagebox.showerror("Invalid", "Focus, break and repetitions must be whole numbers."); return
        if f <= 0 or b < 0 or r <= 0:
            messagebox.showerror("Invalid", "Use positive numbers (break may be 0)."); return
        active[0] = PomodoroSession(task_name, f, b, r, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        state.update({"running": True, "paused": False, "is_break": False, "rep": 1,
                      "reps": r, "focus": f, "brk": b, "timer": f * 60, "after_id": None,
                      "generic": generic})
        label = "No topic" if generic else task_name
        status_lbl.config(text=f"🎯 Focus 1/{r}  ·  {label}"); tick()

    def pause():
        if not state["running"]: return
        if not state["paused"]:
            state["paused"] = True
            if state["after_id"]: page.after_cancel(state["after_id"]); state["after_id"] = None
            status_lbl.config(text="⏸ Paused"); pause_btn.config(text="▶ Resume")
        else:
            state["paused"] = False; pause_btn.config(text="⏸ Pause"); tick()

    def _cancel(save=True):
        state["running"] = False; state["paused"] = False
        if state["after_id"]: page.after_cancel(state["after_id"]); state["after_id"] = None
        if save and active[0]:
            s = active[0]; s.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); s.status = "Cancelled"
            save_session(manager.pomodoro_file, s)
        active[0] = None; timer_lbl.config(text="00:00"); pause_btn.config(text="⏸ Pause")

    def cancel():
        if not state["running"]: return
        if messagebox.askyesno("Cancel", "Cancel this session? It will be logged as cancelled."):
            _cancel(save=True); status_lbl.config(text="❌ Cancelled")

    btns = tk.Frame(wrap, bg=BG); btns.pack(pady=8)
    cfg = dict(font=(FONT,12,"bold"), relief="flat", width=12, cursor="hand2")
    tk.Button(btns, text="▶ Start", bg=GREEN, fg=CARD, command=start, **cfg).grid(row=0, column=0, padx=6)
    pause_btn = tk.Button(btns, text="⏸ Pause", bg=GOLD, fg=CARD, command=pause, **cfg)
    pause_btn.grid(row=0, column=1, padx=6)
    tk.Button(btns, text="✖ Cancel", bg=DEEP, fg=CARD, command=cancel, **cfg).grid(row=0, column=2, padx=6)
    tk.Button(wrap, text="📋 View session history", bg=CARD, fg=DEEP, relief="flat",
              font=(FONT,11,"bold"), cursor="hand2", activebackground=SOFT,
              command=lambda: _history(page, manager)).pack(pady=(12,0))


if __name__ == "__main__":
    import sys

    def _data_dir():
        base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        d = os.path.join(base, "data"); os.makedirs(d, exist_ok=True); return d

    class _Task:
        def __init__(self, title): self.title = title

    class _StandaloneManager:
        """Minimal manager that mirrors main_gui's CSV layout, so this screen
        reads/writes the exact same files as the full app."""
        def __init__(self, data_dir):
            self._tasks = os.path.join(data_dir, "tasks.csv")
            self._completed = os.path.join(data_dir, "completed.csv")
            self._pomodoro = os.path.join(data_dir, "pomodoro.csv")

        @property
        def pomodoro_file(self): return self._pomodoro

        def _read_task_rows(self, path):
            rows = []
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for row in csv.reader(f):
                        if len(row) >= 9: rows.append(row)
            except FileNotFoundError:
                pass
            return rows

        def load_tasks(self):
            return [_Task(r[0]) for r in self._read_task_rows(self._tasks)]

        def complete_task_by_title(self, title):
            rows = self._read_task_rows(self._tasks)
            keep, moved = [], None
            for r in rows:
                if moved is None and r[0] == title:
                    moved = r
                else:
                    keep.append(r)
            if moved is None:
                return False
            with open(self._tasks, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(keep)
            done = list(moved)
            done[7] = "True"  # flag as completed
            with open(self._completed, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(done)
            return True

    root = tk.Tk()
    root.title("Pomodoro")
    root.geometry("760x720")
    root.minsize(640, 640)
    root.configure(bg=BG)

    mgr = _StandaloneManager(_data_dir())
    page = tk.Frame(root, bg=BG); page.pack(fill="both", expand=True)

    def show_page(_name):
        pass

    open_pomodoro(page, show_page, mgr)
    root.mainloop()