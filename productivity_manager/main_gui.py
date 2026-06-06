import os, sys
import tkinter as tk
from tkinter import messagebox

# theme
BG="#c94c4c"; CARD="#ffffff"; SOFT="#e7bcbc"; DEEP="#a33838"
GREEN="#4caf72"; GOLD="#e8a838"; MUTED="#8a8a8a"; FONT="Segoe UI"

# data folder
def _data_dir():
    base = os.path.dirname(sys.executable) if getattr(sys,"frozen",False) else os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "data"); os.makedirs(d, exist_ok=True); return d

import os, csv, time, random, itertools
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Task model
class Task:
    def __init__(self, title, description, deadline, difficulty,
                 urgent, important, created_at, completed, weekday):
        self._title = title
        self._description = description
        self._deadline = deadline
        self._difficulty = int(difficulty)
        self._urgent = str(urgent) == "True"
        self._important = str(important) == "True"
        self._created_at = created_at
        self._completed = str(completed) == "True"
        self._weekday = weekday

    @property
    def title(self): return self._title
    @property
    def description(self): return self._description
    @property
    def deadline(self): return self._deadline
    @property
    def difficulty(self): return self._difficulty
    @property
    def urgent(self): return self._urgent
    @property
    def important(self): return self._important
    @property
    def created_at(self): return self._created_at
    @property
    def completed(self): return self._completed
    @property
    def weekday(self): return self._weekday

    @title.setter
    def title(self, v):
        if len(v) > 50: raise ValueError("Title too long.")
        self._title = v
    @description.setter
    def description(self, v):
        if len(v) > 250: raise ValueError("Description too long.")
        self._description = v
    @difficulty.setter
    def difficulty(self, v):
        v = int(v)
        if not 1 <= v <= 10: raise ValueError("Difficulty 1-10.")
        self._difficulty = v
    @urgent.setter
    def urgent(self, v): self._urgent = bool(v)
    @important.setter
    def important(self, v): self._important = bool(v)
    @completed.setter
    def completed(self, v): self._completed = bool(v)

    def is_overdue(self):
        try:
            return datetime.now() > datetime.strptime(self._deadline, "%Y-%m-%d %H:%M:%S") and not self._completed
        except ValueError:
            return False

    def eisenhower_rank(self):
        u, i = self._urgent, self._important
        if u and i: return 1
        if i and not u: return 2
        if u and not i: return 3
        return 4

    def to_row(self):
        return [self._title, self._description, self._deadline, self._difficulty,
                self._urgent, self._important, self._created_at, self._completed, self._weekday]

    @classmethod
    def from_row(cls, row): return cls(*row[:9])

    @staticmethod
    def load_all(path):
        out = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 9:
                        try: out.append(Task.from_row(row))
                        except (ValueError, TypeError): continue
        except FileNotFoundError: pass
        return out

    @staticmethod
    def save_all(path, tasks):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for t in tasks: w.writerow(t.to_row())

    def copy(self): return Task(*self.to_row())
    def __eq__(self, other):
        return isinstance(other, Task) and self.to_row() == other.to_row()

# Reminder model
class Reminder:
    def __init__(self, title, description, deadline):
        self._title = title
        self._description = description
        self._deadline = deadline

    @property
    def title(self): return self._title
    @property
    def description(self): return self._description
    @property
    def deadline(self): return self._deadline
    @title.setter
    def title(self, v): self._title = v
    @description.setter
    def description(self, v): self._description = v
    @deadline.setter
    def deadline(self, v): self._deadline = v

    def is_overdue(self):
        try: return datetime.now() > datetime.strptime(self._deadline, "%Y-%m-%d %H:%M:%S")
        except ValueError: return False

    def matches(self, kw):
        kw = kw.lower().strip()
        return not kw or kw in self._title.lower() or kw in self._description.lower()

    def to_row(self): return [self._title, self._description, self._deadline]
    @classmethod
    def from_row(cls, row): return cls(row[0], row[1], row[2])

    @staticmethod
    def load_all(path):
        out = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 3: out.append(Reminder.from_row(row))
        except FileNotFoundError: pass
        return out

    @staticmethod
    def save_all(path, items):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in items: w.writerow(r.to_row())

# Journal model
class JournalEntry:
    def __init__(self, title, body, created_at):
        self._title = title
        self._body = body
        self._created_at = created_at

    @property
    def title(self): return self._title
    @property
    def body(self): return self._body
    @property
    def created_at(self): return self._created_at
    @title.setter
    def title(self, v): self._title = v
    @body.setter
    def body(self, v): self._body = v

    def matches(self, q):
        q = q.lower().strip()
        return not q or q in self._title.lower() or q in self._body.lower()

    def to_row(self): return [self._title, self._body, self._created_at]
    @classmethod
    def from_row(cls, row): return cls(row[0], row[1], row[2])

    @staticmethod
    def load_all(path):
        out = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 3: out.append(JournalEntry.from_row(row))
        except FileNotFoundError: pass
        return out

    @staticmethod
    def save_all(path, items):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for e in items: w.writerow(e.to_row())

# Sort base
class SortingAlgorithm(ABC):
    @abstractmethod
    def sort(self, items, key_fn, reverse=False): ...
    @property
    def complexity(self): return "unknown"

# Loop sort
class BubbleSort(SortingAlgorithm):
    @property
    def complexity(self): return "O(n^2)"
    def sort(self, items, key_fn, reverse=False):
        arr = items[:]
        n = len(arr)
        for i in range(n):
            swapped = False
            for j in range(n - i - 1):
                a, b = key_fn(arr[j]), key_fn(arr[j + 1])
                if (a > b) if not reverse else (a < b):
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
            if not swapped: break
        return arr

# Recursion sort
class MergeSort(SortingAlgorithm):
    @property
    def complexity(self): return "O(n log n)"
    def sort(self, items, key_fn, reverse=False):
        if len(items) <= 1: return items[:]
        mid = len(items) // 2
        left = self.sort(items[:mid], key_fn, reverse)
        right = self.sort(items[mid:], key_fn, reverse)
        return self._merge(left, right, key_fn, reverse)
    def _merge(self, left, right, key_fn, reverse):
        res = []; i = j = 0
        while i < len(left) and j < len(right):
            take = (key_fn(left[i]) <= key_fn(right[j])) if not reverse else (key_fn(left[i]) >= key_fn(right[j]))
            if take: res.append(left[i]); i += 1
            else: res.append(right[j]); j += 1
        res.extend(left[i:]); res.extend(right[j:])
        return res

# Logic expression
class LogicalExpression:
    def __init__(self, name, formula, var_labels, func, task_vars):
        self.name = name
        self.formula = formula
        self.var_labels = var_labels
        self._func = func
        self._task_vars = task_vars
    def evaluate(self, *vals): return bool(self._func(*vals))
    def evaluate_task(self, t): return bool(self._func(*self._task_vars(t)))
    def task_values(self, t): return self._task_vars(t)
    def truth_table(self):
        n = len(self.var_labels)
        return [(c, self.evaluate(*c)) for c in itertools.product([False, True], repeat=n)]
    def headers(self): return list(self.var_labels) + [self.formula]

EXPRESSIONS = [
    LogicalExpression("Important and not completed", "p AND (NOT q)",
                      ["important (p)", "completed (q)"],
                      lambda p, q: p and not q, lambda t: (t.important, t.completed)),
    LogicalExpression("Urgent and not completed", "p AND (NOT q)",
                      ["urgent (p)", "completed (q)"],
                      lambda p, q: p and not q, lambda t: (t.urgent, t.completed)),
    LogicalExpression("Important and urgent", "p AND q",
                      ["important (p)", "urgent (q)"],
                      lambda p, q: p and q, lambda t: (t.important, t.urgent)),
    LogicalExpression("Important or urgent", "p OR q",
                      ["important (p)", "urgent (q)"],
                      lambda p, q: p or q, lambda t: (t.important, t.urgent)),
]
DEFAULT_EXPRESSION = EXPRESSIONS[0]
def get_expression(name):
    for e in EXPRESSIONS:
        if e.name == name: return e
    return DEFAULT_EXPRESSION

# Coordinator
class Schedule_Manager:
    SORT_OPTIONS = ["A-Z", "Z-A", "Easiest first", "Hardest first", "By deadline"]

    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self._tasks = os.path.join(data_dir, "tasks.csv")
        self._completed = os.path.join(data_dir, "completed.csv")
        self._reminders = os.path.join(data_dir, "reminders.csv")
        self._journals = os.path.join(data_dir, "journals.csv")
        self._pomodoro = os.path.join(data_dir, "pomodoro.csv")
        self._bubble = BubbleSort()
        self._merge = MergeSort()
        self.expression = DEFAULT_EXPRESSION

    @property
    def pomodoro_file(self): return self._pomodoro

    # tasks
    def load_tasks(self): return Task.load_all(self._tasks)
    def load_completed(self): return Task.load_all(self._completed)
    def rewrite_tasks(self, tasks): Task.save_all(self._tasks, tasks)
    def save_new_task(self, task):
        with open(self._tasks, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(task.to_row())
    def delete_task(self, task):
        self.rewrite_tasks([t for t in self.load_tasks() if t != task])
    def update_task(self, original, updated):
        self.rewrite_tasks([updated if t == original else t for t in self.load_tasks()])
    def mark_completed(self, task):
        self.rewrite_tasks([t for t in self.load_tasks() if t != task])
        done = task.copy(); done.completed = True
        with open(self._completed, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(done.to_row())
    def mark_incomplete(self, task):
        Task.save_all(self._completed, [t for t in self.load_completed() if t != task])
        back = task.copy(); back.completed = False
        self.save_new_task(back)
    def complete_task_by_title(self, title):
        for t in self.load_tasks():
            if t.title == title:
                self.mark_completed(t); return True
        return False

    def sort_tasks(self, tasks, how):
        rank = lambda x: x.eisenhower_rank()
        if how == "A-Z": return self._bubble.sort(tasks, lambda x: (x.title.lower(), rank(x)))
        if how == "Z-A": return self._bubble.sort(tasks, lambda x: (x.title.lower(), rank(x)), True)
        if how == "Easiest first": return self._merge.sort(tasks, lambda x: (x.difficulty, rank(x)))
        if how == "Hardest first": return self._merge.sort(tasks, lambda x: (x.difficulty, rank(x)), True)
        if how == "By deadline": return self._merge.sort(tasks, lambda x: (x.deadline, rank(x)))
        return tasks

    def get_eisenhower_quadrants(self, tasks):
        labels = {1: "Do First", 2: "Schedule", 3: "Delegate", 4: "Eliminate"}
        out = {v: [] for v in labels.values()}
        for t in tasks: out[labels[t.eisenhower_rank()]].append(t)
        return out

    def tasks_by_weekday(self):
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        grouped = {d: [] for d in order}
        for t in self.load_tasks(): grouped.setdefault(t.weekday, []).append(t)
        return [(d, grouped.get(d, [])) for d in order]

    # searches
    def search_tasks_by_title(self, kw):
        kw = kw.lower().strip()
        return [t for t in self.load_tasks() if kw in t.title.lower()]
    def search_tasks_by_weekday(self, day):
        return [t for t in self.load_tasks() if t.weekday == day]
    def logical_search_tasks(self, expr=None):
        expr = expr or self.expression
        return [t for t in self.load_tasks() if expr.evaluate_task(t)]
    def tasks_by_truth_values(self, important, urgent):
        return [t for t in self.load_tasks() if t.important == important and t.urgent == urgent]

    # reminders
    def load_reminders(self): return Reminder.load_all(self._reminders)
    def save_reminders(self, items): Reminder.save_all(self._reminders, items)
    def add_reminder(self, title, description, deadline):
        items = self.load_reminders(); items.append(Reminder(title, description, deadline)); self.save_reminders(items)
    def update_reminder(self, old_title, old_deadline, title, description, deadline):
        out, done = [], False
        for r in self.load_reminders():
            if not done and r.title == old_title and r.deadline == old_deadline:
                out.append(Reminder(title, description, deadline)); done = True
            else: out.append(r)
        self.save_reminders(out)
    def delete_reminder(self, title, deadline):
        out, done = [], False
        for r in self.load_reminders():
            if not done and r.title == title and r.deadline == deadline:
                done = True; continue
            out.append(r)
        self.save_reminders(out)
    def search_reminders(self, kw):
        return [r for r in self.load_reminders() if r.matches(kw)]

    # journals
    def load_journals(self): return JournalEntry.load_all(self._journals)
    def save_journals(self, items): JournalEntry.save_all(self._journals, items)
    def add_journal(self, title, body=""):
        items = self.load_journals()
        e = JournalEntry(title, body, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        items.append(e); self.save_journals(items); return e
    def search_journals(self, q):
        return [e for e in self.load_journals() if e.matches(q)]

    # schedule
    def schedule_items(self):
        items, seen = [], set()
        for t in self.load_tasks():
            if t.completed: continue
            k = t.title.strip().lower()
            if k in seen: continue
            seen.add(k)
            items.append({"kind": "task", "title": t.title, "description": t.description,
                          "deadline": t.deadline, "difficulty": t.difficulty})
        for r in self.load_reminders():
            k = r.title.strip().lower()
            if k in seen: continue
            seen.add(k)
            items.append({"kind": "reminder", "title": r.title, "description": r.description,
                          "deadline": r.deadline, "difficulty": None})
        return items

    # analysis
    @staticmethod
    def _random_tasks(n):
        ts = "2025-01-01 00:00:00"
        return [Task(f"T{random.randint(0,99999)}", "", ts, random.randint(1, 10),
                     random.choice([True, False]), random.choice([True, False]), ts, False, "Monday")
                for _ in range(n)]
    def benchmark_sorts(self, sizes=(100, 250, 500, 1000)):
        out = []
        key = lambda x: (x.difficulty, x.eisenhower_rank())
        for n in sizes:
            data = self._random_tasks(n)
            t0 = time.perf_counter(); self._bubble.sort(data, key); b = time.perf_counter() - t0
            t0 = time.perf_counter(); self._merge.sort(data, key); m = time.perf_counter() - t0
            out.append({"size": n, "bubble": b, "merge": m})
        return out

    def export_all(self, dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        written = []
        for label, loader in [("tasks", self.load_tasks), ("completed", self.load_completed),
                              ("reminders", self.load_reminders), ("journals", self.load_journals)]:
            out = os.path.join(dest_dir, f"{label}_{stamp}.csv")
            with open(out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                for obj in loader(): w.writerow(obj.to_row())
            written.append(out)
        return written

    def weekly_summary(self):
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).date()
        active = self.load_tasks()
        sessions = 0
        try:
            from pomodoro import load_sessions
            for s in load_sessions(self._pomodoro):
                try:
                    if datetime.strptime(s.start_time[:10], "%Y-%m-%d").date() >= week_start:
                        sessions += 1
                except (ValueError, AttributeError): continue
        except Exception: pass
        return {"active": len(active), "completed": len(self.load_completed()),
                "overdue": sum(1 for t in active if t.is_overdue()),
                "reminders": len(self.load_reminders()),
                "journals": len(self.load_journals()), "pomodoro_week": sessions}

from pomodoro import open_pomodoro
from journals import open_journal
from reminders import open_reminders
from schedule import open_schedule
from statistics import open_statistics

WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# window
root = tk.Tk()
root.title("Productivity Hub")
root.geometry("1180x820")
root.minsize(940, 660)
root.configure(bg=BG)

DATA_DIR = _data_dir()
manager = Schedule_Manager(DATA_DIR)

container = tk.Frame(root, bg=BG)
container.pack(fill="both", expand=True)
pages = {}

def show_page(name): pages[name].tkraise()

def page_frame(name):
    f = tk.Frame(container, bg=BG)
    f.place(x=0, y=0, relwidth=1, relheight=1)
    pages[name] = f
    return f

# shared widgets
def home_bar(page, title):
    bar = tk.Frame(page, bg=CARD, height=58)
    bar.pack(fill="x"); bar.pack_propagate(False)
    tk.Button(bar, text="⌂  Home", font=(FONT,12,"bold"), bg=DEEP, fg=CARD,
              relief="flat", padx=14, cursor="hand2", activebackground=BG,
              activeforeground=CARD, command=lambda: show_page("Main Menu")).pack(side="left", padx=14, pady=10)
    tk.Label(bar, text=title, font=(FONT,17,"bold"), bg=CARD, fg=DEEP).pack(side="left", padx=4)
    return bar

def primary_btn(parent, text, cmd, **kw):
    return tk.Button(parent, text=text, font=(FONT,12,"bold"), bg=BG, fg=CARD,
                     relief="flat", cursor="hand2", activebackground=DEEP,
                     activeforeground=CARD, command=cmd, **kw)

def ghost_btn(parent, text, cmd, **kw):
    return tk.Button(parent, text=text, font=(FONT,11,"bold"), bg=CARD, fg=DEEP,
                     relief="flat", cursor="hand2", activebackground=SOFT,
                     activeforeground=DEEP, command=cmd, **kw)

def section(parent, text):
    tk.Label(parent, text=text, font=(FONT,15,"bold"), bg=BG, fg=CARD).pack(anchor="w", pady=(6,6))

def scroll_area(parent):
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
    sb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    win = canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.winfo_exists() and canvas.yview_scroll(int(-ev.delta/120), "units")))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    return inner

# task form (add / edit)
def task_form(existing=None, on_done=None):
    editing = existing is not None
    win = tk.Toplevel(root)
    win.title("Edit Task" if editing else "Add Task")
    win.geometry("460x620"); win.configure(bg=CARD); win.resizable(False, False)

    tk.Label(win, text=("Edit Task" if editing else "New Task"), font=(FONT,17,"bold"),
             bg=DEEP, fg=CARD, pady=12).pack(fill="x")
    form = tk.Frame(win, bg=CARD, padx=26, pady=14); form.pack(fill="both", expand=True)

    def field(label):
        tk.Label(form, text=label, font=(FONT,10,"bold"), bg=CARD, fg=DEEP).pack(anchor="w", pady=(10,2))

    field("Title")
    title_e = tk.Entry(form, font=(FONT,11)); title_e.pack(fill="x", ipady=3)
    field("Description")
    desc_e = tk.Text(form, font=(FONT,11), height=3); desc_e.pack(fill="x")
    field("Deadline date  (YYYY-MM-DD)")
    date_e = tk.Entry(form, font=(FONT,11)); date_e.pack(fill="x", ipady=3)
    field("Deadline time  (HH:MM)")
    time_e = tk.Entry(form, font=(FONT,11)); time_e.pack(fill="x", ipady=3)
    field("Difficulty  (1-10)")
    diff_e = tk.Spinbox(form, from_=1, to=10, font=(FONT,11), width=5); diff_e.pack(anchor="w", ipady=3)

    flags = tk.Frame(form, bg=CARD); flags.pack(anchor="w", pady=(12,0))
    urgent_v = tk.BooleanVar(); important_v = tk.BooleanVar()
    tk.Checkbutton(flags, text="Urgent", variable=urgent_v, bg=CARD, fg=DEEP,
                   font=(FONT,11), activebackground=CARD, selectcolor=SOFT).pack(side="left", padx=(0,16))
    tk.Checkbutton(flags, text="Important", variable=important_v, bg=CARD, fg=DEEP,
                   font=(FONT,11), activebackground=CARD, selectcolor=SOFT).pack(side="left")

    now = __import__("datetime").datetime.now()
    if editing:
        title_e.insert(0, existing.title)
        desc_e.insert("1.0", existing.description)
        d, _, t = existing.deadline.partition(" ")
        date_e.insert(0, d); time_e.insert(0, t[:5])
        diff_e.delete(0, "end"); diff_e.insert(0, str(existing.difficulty))
        urgent_v.set(existing.urgent); important_v.set(existing.important)
    else:
        date_e.insert(0, now.strftime("%Y-%m-%d")); time_e.insert(0, "17:00")
        diff_e.delete(0, "end"); diff_e.insert(0, "5")

    def save():
        from datetime import datetime
        title = title_e.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required.", parent=win); return
        if len(title) > 50:
            messagebox.showerror("Error", "Title must be 50 characters or fewer.", parent=win); return
        try:
            dl = datetime.strptime(f"{date_e.get().strip()} {time_e.get().strip()}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Use date YYYY-MM-DD and time HH:MM.", parent=win); return
        try:
            diff = int(diff_e.get())
            if not 1 <= diff <= 10: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Difficulty must be 1-10.", parent=win); return

        deadline = dl.strftime("%Y-%m-%d %H:%M:%S")
        weekday = dl.strftime("%A")
        if editing:
            updated = Task(title, desc_e.get("1.0","end").strip(), deadline, diff,
                           urgent_v.get(), important_v.get(), existing.created_at, False, weekday)
            manager.update_task(existing, updated)
        else:
            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            manager.save_new_task(Task(title, desc_e.get("1.0","end").strip(), deadline, diff,
                                       urgent_v.get(), important_v.get(), created, False, weekday))
        win.destroy()
        if on_done: on_done()

    primary_btn(form, "Save Task", save, pady=6).pack(fill="x", pady=(20,0))

# task detail popup
def task_popup(task, on_change):
    win = tk.Toplevel(root)
    win.title(task.title); win.geometry("440x460"); win.configure(bg=CARD); win.resizable(False, False)
    tk.Label(win, text=task.title, font=(FONT,16,"bold"), bg=DEEP, fg=CARD,
             wraplength=400, pady=12).pack(fill="x")
    body = tk.Frame(win, bg=CARD, padx=24, pady=14); body.pack(fill="both", expand=True)

    def row(k, v):
        f = tk.Frame(body, bg=CARD); f.pack(fill="x", pady=3)
        tk.Label(f, text=f"{k}", font=(FONT,10,"bold"), bg=CARD, fg=MUTED, width=12, anchor="w").pack(side="left")
        tk.Label(f, text=str(v), font=(FONT,11), bg=CARD, fg=DEEP, anchor="w", wraplength=270, justify="left").pack(side="left")

    quad = {1:"Do First",2:"Schedule",3:"Delegate",4:"Eliminate"}[task.eisenhower_rank()]
    row("Deadline", task.deadline)
    row("Weekday", task.weekday)
    row("Difficulty", task.difficulty)
    row("Urgent", "Yes" if task.urgent else "No")
    row("Important", "Yes" if task.important else "No")
    row("Quadrant", quad)
    row("Description", task.description or "—")
    if task.is_overdue():
        tk.Label(body, text="⚠ Overdue", font=(FONT,12,"bold"), bg=CARD, fg="red").pack(pady=(8,0))

    btns = tk.Frame(body, bg=CARD); btns.pack(fill="x", pady=(16,0))
    def do_complete():
        manager.mark_completed(task); win.destroy(); on_change()
    def do_edit():
        win.destroy(); task_form(existing=task, on_done=on_change)
    def do_delete():
        if messagebox.askyesno("Delete", f"Delete '{task.title}'?", parent=win):
            manager.delete_task(task); win.destroy(); on_change()
    if not task.completed:
        primary_btn(btns, "✔ Complete", do_complete).pack(side="left", padx=(0,6))
    ghost_btn(btns, "✎ Edit", do_edit).pack(side="left", padx=6)
    tk.Button(btns, text="🗑 Delete", font=(FONT,11,"bold"), bg=SOFT, fg=DEEP,
              relief="flat", cursor="hand2", command=do_delete).pack(side="right")

def task_card(parent, task, on_change):
    card = tk.Frame(parent, bg=CARD, padx=12, pady=8, highlightthickness=1, highlightbackground=SOFT)
    card.pack(fill="x", padx=2, pady=4)
    line = "🔴 " if task.is_overdue() else ""
    tk.Label(card, text=f"{line}{task.title}", font=(FONT,12,"bold"), bg=CARD, fg=DEEP, anchor="w").pack(fill="x")
    tk.Label(card, text=f"⏰ {task.deadline}   •   difficulty {task.difficulty}",
             font=(FONT,10), bg=CARD, fg=MUTED, anchor="w").pack(fill="x")
    for w in (card,) + tuple(card.winfo_children()):
        w.bind("<Button-1>", lambda e, t=task: task_popup(t, on_change))
        w.configure(cursor="hand2")

# views
def view_tasks():
    win = tk.Toplevel(root); win.title("View Tasks"); win.geometry("620x680"); win.configure(bg=BG)
    bar = tk.Frame(win, bg=BG); bar.pack(fill="x", padx=16, pady=12)
    tk.Label(bar, text="Sort", font=(FONT,10,"bold"), bg=BG, fg=CARD).pack(side="left")
    sort_v = tk.StringVar(value=Schedule_Manager.SORT_OPTIONS[0])
    om = tk.OptionMenu(bar, sort_v, *Schedule_Manager.SORT_OPTIONS, command=lambda e: refresh())
    om.config(bg=CARD, fg=DEEP, relief="flat", font=(FONT,10), highlightthickness=0); om.pack(side="left", padx=(4,12))
    tk.Label(bar, text="Search", font=(FONT,10,"bold"), bg=BG, fg=CARD).pack(side="left")
    search_v = tk.StringVar()
    e = tk.Entry(bar, textvariable=search_v, font=(FONT,11)); e.pack(side="left", padx=4, ipady=2)
    ghost_btn(bar, "Go", lambda: refresh()).pack(side="left")
    holder = scroll_area(win)
    def refresh():
        for w in holder.winfo_children(): w.destroy()
        tasks = manager.search_tasks_by_title(search_v.get())
        tasks = manager.sort_tasks(tasks, sort_v.get())
        if not tasks:
            tk.Label(holder, text="No tasks.", font=(FONT,11,"italic"), bg=BG, fg=SOFT).pack(pady=20); return
        for t in tasks: task_card(holder, t, refresh)
    refresh()

def completed_tasks():
    win = tk.Toplevel(root); win.title("Completed"); win.geometry("560x620"); win.configure(bg=BG)
    holder = scroll_area(win)
    def refresh():
        for w in holder.winfo_children(): w.destroy()
        tasks = manager.load_completed()
        if not tasks:
            tk.Label(holder, text="No completed tasks yet.", font=(FONT,11,"italic"), bg=BG, fg=SOFT).pack(pady=20); return
        for t in tasks:
            card = tk.Frame(holder, bg=CARD, padx=12, pady=8, highlightthickness=1, highlightbackground=SOFT)
            card.pack(fill="x", padx=2, pady=4)
            tk.Label(card, text=f"✔ {t.title}", font=(FONT,12,"bold"), bg=CARD, fg=DEEP, anchor="w").pack(side="left")
            def restore(task=t):
                if messagebox.askyesno("Restore", f"Move '{task.title}' back to active tasks?", parent=win):
                    manager.mark_incomplete(task); refresh()
            ghost_btn(card, "↩ Mark active", restore).pack(side="right")
    refresh()

def eisenhower():
    win = tk.Toplevel(root); win.title("Eisenhower Matrix"); win.geometry("720x600"); win.configure(bg=BG)
    quads = manager.get_eisenhower_quadrants(manager.load_tasks())
    meta = [("Do First", GREEN, "Urgent + Important"), ("Schedule", GOLD, "Important, not urgent"),
            ("Delegate", DEEP, "Urgent, not important"), ("Eliminate", MUTED, "Neither")]
    grid = tk.Frame(win, bg=BG); grid.pack(fill="both", expand=True, padx=14, pady=14)
    for i,(name,color,sub) in enumerate(meta):
        cell = tk.Frame(grid, bg=CARD, highlightthickness=2, highlightbackground=color)
        cell.grid(row=i//2, column=i%2, sticky="nsew", padx=8, pady=8)
        tk.Label(cell, text=name, font=(FONT,13,"bold"), bg=color, fg=CARD, pady=6).pack(fill="x")
        tk.Label(cell, text=sub, font=(FONT,9,"italic"), bg=CARD, fg=MUTED).pack(anchor="w", padx=10, pady=(4,0))
        if quads[name]:
            for t in quads[name]:
                tk.Label(cell, text=f"• {t.title}", font=(FONT,11), bg=CARD, fg=DEEP, anchor="w").pack(fill="x", padx=12, pady=1)
        else:
            tk.Label(cell, text="— empty —", font=(FONT,10,"italic"), bg=CARD, fg=SOFT).pack(padx=12, pady=6)
    for i in range(2):
        grid.grid_columnconfigure(i, weight=1); grid.grid_rowconfigure(i, weight=1)

def truth_table():
    expr = manager.expression
    win = tk.Toplevel(root); win.title("Truth Table"); win.geometry("560x340"); win.configure(bg=CARD)
    tk.Label(win, text=expr.name, font=(FONT,15,"bold"), bg=CARD, fg=DEEP).pack(pady=(16,2))
    tk.Label(win, text=f"Expression:  {expr.formula}", font=(FONT,11), bg=CARD, fg=MUTED).pack(pady=(0,12))
    tbl = tk.Frame(win, bg=CARD); tbl.pack()
    for c,h in enumerate(expr.headers()):
        tk.Label(tbl, text=h, font=(FONT,11,"bold"), bg=DEEP, fg=CARD, width=16, relief="groove").grid(row=0, column=c)
    for r,(combo,res) in enumerate(expr.truth_table(), start=1):
        bg = SOFT if res else CARD
        for c,val in enumerate(list(combo)+[res]):
            tk.Label(tbl, text=str(val), font=(FONT,11), bg=bg, fg=DEEP, width=16, relief="groove").grid(row=r, column=c)
    tk.Label(win, text="Highlighted rows satisfy the expression.", font=(FONT,9,"italic"), bg=CARD, fg=MUTED).pack(pady=12)

def by_weekday():
    win = tk.Toplevel(root); win.title("Tasks by Weekday"); win.geometry("640x680"); win.configure(bg=BG)
    holder = scroll_area(win)
    def refresh():
        for w in holder.winfo_children(): w.destroy()
        for day, tasks in manager.tasks_by_weekday():
            tk.Label(holder, text=f"{day}  ({len(tasks)})", font=(FONT,12,"bold"),
                     bg=DEEP, fg=CARD, anchor="w", padx=10, pady=4).pack(fill="x", padx=8, pady=(10,2))
            if not tasks:
                tk.Label(holder, text="— none —", font=(FONT,10,"italic"), bg=BG, fg=SOFT).pack(anchor="w", padx=20); continue
            for t in tasks: task_card(holder, t, refresh)
    refresh()

def logical_search():
    win = tk.Toplevel(root); win.title("Logical Search"); win.geometry("640x680"); win.configure(bg=BG)
    P_LABEL, Q_LABEL = "Important", "Urgent"
    combos = [("p = T , q = T", True, True), ("p = T , q = F", True, False),
              ("p = F , q = T", False, True), ("p = F , q = F", False, False)]
    bar = tk.Frame(win, bg=BG); bar.pack(fill="x", padx=16, pady=12)
    tk.Label(bar, text="Truth-table row", font=(FONT,10,"bold"), bg=BG, fg=CARD).pack(side="left")
    sel = tk.StringVar(value=combos[0][0])
    om = tk.OptionMenu(bar, sel, *[c[0] for c in combos], command=lambda e: refresh())
    om.config(bg=CARD, fg=DEEP, relief="flat", font=(FONT,11), width=14, highlightthickness=0); om.pack(side="left", padx=6)
    tk.Label(win, text=f"Logical variables:    p = {P_LABEL}      q = {Q_LABEL}",
             font=(FONT,10), bg=BG, fg=SOFT).pack(fill="x", padx=18, pady=(0,2))
    desc = tk.Label(win, text="", font=(FONT,11,"italic"), bg=BG, fg=CARD)
    desc.pack(fill="x", padx=18, pady=(0,6))
    holder = scroll_area(win)
    def phrase(p, q): return f"{'' if p else 'NOT '}{P_LABEL}   AND   {'' if q else 'NOT '}{Q_LABEL}"
    def refresh():
        for w in holder.winfo_children(): w.destroy()
        want_p, want_q = next((p, q) for (lbl, p, q) in combos if lbl == sel.get())
        desc.config(text=f"Showing only tasks that are:   {phrase(want_p, want_q)}")
        matched = manager.tasks_by_truth_values(want_p, want_q)
        tk.Label(holder, text=f"{len(matched)} task(s) match this exact row",
                 font=(FONT,12,"bold"), bg=BG, fg=CARD).pack(anchor="w", pady=(0,8))
        if not matched:
            tk.Label(holder, text="No tasks have this exact combination.",
                     font=(FONT,11), bg=BG, fg=SOFT).pack(anchor="w"); return
        for t in matched:
            card = tk.Frame(holder, bg=CARD, padx=12, pady=8, highlightthickness=2, highlightbackground=GREEN)
            card.pack(fill="x", padx=2, pady=4)
            tk.Label(card, text=t.title, font=(FONT,12,"bold"), bg=CARD, fg=DEEP, anchor="w").pack(fill="x")
            tk.Label(card, text=f"{P_LABEL} = {'T' if t.important else 'F'}      {Q_LABEL} = {'T' if t.urgent else 'F'}      ⏰ {t.deadline}",
                     font=(FONT,10), bg=CARD, fg=MUTED, anchor="w").pack(fill="x", pady=(2,0))
            for w in (card,) + tuple(card.winfo_children()):
                w.configure(cursor="hand2"); w.bind("<Button-1>", lambda e, x=t: task_popup(x, refresh))
    refresh()

# task manager page
def build_task_manager(page):
    home_bar(page, "🗂  Task Manager")
    wrap = tk.Frame(page, bg=BG); wrap.pack(expand=True)
    tk.Label(wrap, text="Manage your tasks", font=(FONT,22,"bold"), bg=BG, fg=CARD).pack(pady=(30,20))
    grid = tk.Frame(wrap, bg=BG); grid.pack()
    actions = [
        ("＋  Add Task", lambda: task_form(on_done=lambda: None)),
        ("📋  View Tasks", view_tasks),
        ("✔  Completed", completed_tasks),
        ("🧭  Eisenhower", eisenhower),
        ("🔣  Truth Table", truth_table),
        ("🗓  By Weekday", by_weekday),
        ("🔎  Logical Search", logical_search),
    ]
    for i,(text,cmd) in enumerate(actions):
        b = tk.Button(grid, text=text, font=(FONT,13,"bold"), bg=CARD, fg=DEEP,
                      relief="flat", width=22, height=2, cursor="hand2",
                      activebackground=SOFT, activeforeground=DEEP, command=cmd)
        b.grid(row=i//2, column=i%2, padx=10, pady=8)

# settings page
def build_settings(page):
    home_bar(page, "⚙  Settings")
    body = tk.Frame(page, bg=BG); body.pack(fill="both", expand=True, padx=34, pady=22)
    section(body, "Active logical condition")
    tk.Label(body, text="Used by the Truth Table and Logical Search screens.",
             font=(FONT,10), bg=BG, fg=SOFT).pack(anchor="w", pady=(0,8))
    cur = tk.Label(body, text=f"Current:  {manager.expression.name}  ({manager.expression.formula})",
                   font=(FONT,11), bg=BG, fg=CARD); cur.pack(anchor="w", pady=(0,8))
    ev = tk.StringVar(value=manager.expression.name)
    om = tk.OptionMenu(body, ev, *[e.name for e in EXPRESSIONS])
    om.config(bg=CARD, fg=DEEP, relief="flat", font=(FONT,10), highlightthickness=0); om.pack(anchor="w")
    def apply_():
        manager.expression = get_expression(ev.get())
        cur.config(text=f"Current:  {manager.expression.name}  ({manager.expression.formula})")
        messagebox.showinfo("Updated", f"Now using: {manager.expression.name}")
    primary_btn(body, "Apply", apply_, padx=18, pady=4).pack(anchor="w", pady=12)
    tk.Frame(body, bg=DEEP, height=2).pack(fill="x", pady=18)

    section(body, "Color theme")
    tk.Label(body, text="Pick a palette — it applies instantly across every screen and is remembered next time.",
             font=(FONT,10), bg=BG, fg=SOFT, wraplength=620, justify="left").pack(anchor="w", pady=(0,10))
    swatches = tk.Frame(body, bg=BG); swatches.pack(anchor="w")
    for i, tname in enumerate(PALETTES):
        p = PALETTES[tname]
        chosen = (tname == current_theme)
        cell = tk.Frame(swatches, bg=p["DEEP"] if chosen else BG, padx=3, pady=3)
        cell.grid(row=i//3, column=i%3, padx=8, pady=8)
        b = tk.Button(cell, text=("● " if chosen else "") + tname, font=(FONT,12,"bold"),
                      bg=p["BG"], fg=p["CARD"], activebackground=p["DEEP"], activeforeground=p["CARD"],
                      relief="flat", width=16, height=2, cursor="hand2",
                      command=lambda n=tname: apply_theme(n))
        b.pack()
        dots = tk.Frame(cell, bg=p["BG"]); dots.pack(fill="x")
        for c in ("DEEP","SOFT","GREEN","GOLD"):
            tk.Frame(dots, bg=p[c], width=24, height=8).pack(side="left", padx=1, pady=2)

    tk.Frame(body, bg=DEEP, height=2).pack(fill="x", pady=18)
    section(body, "Export all data")
    tk.Label(body, text="Saves timestamped CSV copies into the data/exports folder.",
             font=(FONT,10), bg=BG, fg=SOFT).pack(anchor="w", pady=(0,8))
    def export_():
        dest = os.path.join(DATA_DIR, "exports")
        written = manager.export_all(dest)
        messagebox.showinfo("Exported", f"Wrote {len(written)} files to:\n{dest}")
    primary_btn(body, "Export now", export_, padx=18, pady=4).pack(anchor="w", pady=12)

# main menu
def build_main_menu(page):
    tk.Label(page, text="Productivity Hub", font=(FONT,34,"bold"), bg=BG, fg=CARD).pack(pady=(64,2))
    tk.Label(page, text="Plan  •  Focus  •  Reflect", font=(FONT,14), bg=BG, fg=SOFT).pack(pady=(0,34))
    grid = tk.Frame(page, bg=BG); grid.pack()
    menu = [("🗂","Task Manager"),("📅","Schedule"),("⏳","Pomodoro Session"),
            ("📓","Journal"),("⏰","Reminders"),("📊","Statistics"),("⚙","Settings")]
    for i,(icon,name) in enumerate(menu):
        b = tk.Button(grid, text=f"{icon}\n{name}", font=(FONT,14,"bold"), bg=CARD, fg=DEEP,
                      relief="flat", width=15, height=4, cursor="hand2",
                      activebackground=SOFT, activeforeground=DEEP, command=lambda n=name: show_page(n))
        b.grid(row=i//3, column=i%3, padx=16, pady=14)

# palettes
PALETTES = {
    "Coral":  {"BG":"#c94c4c","CARD":"#ffffff","SOFT":"#e7bcbc","DEEP":"#a33838","GREEN":"#4caf72","GOLD":"#e8a838","MUTED":"#8a8a8a","SIDE":"#b03c3c","FIELD":"#d45f5f"},
    "Ocean":  {"BG":"#2a6f97","CARD":"#ffffff","SOFT":"#bcd6e6","DEEP":"#184e6f","GREEN":"#3fa372","GOLD":"#e0a02e","MUTED":"#7e909c","SIDE":"#245e80","FIELD":"#3a86b5"},
    "Forest": {"BG":"#3a7d44","CARD":"#ffffff","SOFT":"#c6e0c9","DEEP":"#235b2c","GREEN":"#2e8b57","GOLD":"#dca52e","MUTED":"#7e8d7e","SIDE":"#316b3a","FIELD":"#4a9456"},
    "Plum":   {"BG":"#6a4c93","CARD":"#ffffff","SOFT":"#d8c8e8","DEEP":"#46305f","GREEN":"#4caf72","GOLD":"#e0a82e","MUTED":"#897e98","SIDE":"#5d4180","FIELD":"#7e5cab"},
    "Slate":  {"BG":"#2f3b45","CARD":"#ffffff","SOFT":"#c4ced6","DEEP":"#1b242b","GREEN":"#4caf72","GOLD":"#e0a82e","MUTED":"#8a949c","SIDE":"#28333c","FIELD":"#3c4a55"},
    "Sunset": {"BG":"#e07a5f","CARD":"#ffffff","SOFT":"#f4d6cc","DEEP":"#b5503a","GREEN":"#4caf72","GOLD":"#d9a430","MUTED":"#9a8278","SIDE":"#cf6a50","FIELD":"#ea9078"},
}
THEME_FILE = os.path.join(DATA_DIR, "theme.txt")

def _saved_theme():
    try:
        with open(THEME_FILE, encoding="utf-8") as f:
            n = f.read().strip()
            if n in PALETTES: return n
    except OSError: pass
    return "Coral"

current_theme = _saved_theme()

# apply colors
def _set_palette(name):
    import pomodoro, journals, reminders, schedule, statistics
    p = PALETTES[name]
    base = ("BG","CARD","SOFT","DEEP","GREEN","GOLD","MUTED")
    for k in base: globals()[k] = p[k]
    for mod in (pomodoro, journals, reminders, schedule, statistics):
        for k in base:
            if hasattr(mod, k): setattr(mod, k, p[k])
    journals.SIDE = p["SIDE"]; journals.FIELD = p["FIELD"]

def build_all_pages():
    root.configure(bg=BG); container.configure(bg=BG)
    for page in pages.values():
        page.configure(bg=BG)
        for w in page.winfo_children(): w.destroy()
    build_main_menu(pages["Main Menu"])
    build_task_manager(pages["Task Manager"])
    build_settings(pages["Settings"])
    open_schedule(pages["Schedule"], show_page, manager)
    open_pomodoro(pages["Pomodoro Session"], show_page, manager)
    open_journal(pages["Journal"], show_page, manager)
    open_reminders(pages["Reminders"], show_page, manager)
    open_statistics(pages["Statistics"], show_page, manager)

def apply_theme(name):
    global current_theme
    if name not in PALETTES: return
    current_theme = name
    _set_palette(name)
    container.configure(bg=globals()["BG"])
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as f: f.write(name)
    except OSError: pass
    build_all_pages()
    show_page("Settings")

# build pages
for _name in ("Main Menu","Task Manager","Settings","Schedule",
              "Pomodoro Session","Journal","Reminders","Statistics"):
    page_frame(_name)
_set_palette(current_theme)
container.configure(bg=globals()["BG"])
build_all_pages()

show_page("Main Menu")
root.mainloop()