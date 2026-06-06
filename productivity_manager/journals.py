import tkinter as tk
from tkinter import messagebox

# theme
BG="#c94c4c"; CARD="#ffffff"; SOFT="#e7bcbc"; DEEP="#a33838"
SIDE="#b03c3c"; FIELD="#d45f5f"; MUTED="#8a8a8a"; FONT="Segoe UI"

# home bar
def _home_bar(page, on_home, title):
    bar = tk.Frame(page, bg=CARD, height=58); bar.pack(fill="x"); bar.pack_propagate(False)
    tk.Button(bar, text="⌂  Home", font=(FONT,12,"bold"), bg=DEEP, fg=CARD, relief="flat",
              padx=14, cursor="hand2", activebackground=BG, activeforeground=CARD,
              command=on_home).pack(side="left", padx=14, pady=10)
    tk.Label(bar, text=title, font=(FONT,17,"bold"), bg=CARD, fg=DEEP).pack(side="left", padx=4)

# journal screen
def open_journal(page, show_page, manager):
    for w in page.winfo_children(): w.destroy()
    state = {"notes": manager.load_journals(), "active": None, "unsaved": False, "query": ""}

    def safe_home():
        if _confirm_unsaved(): show_page("Main Menu")
    _home_bar(page, safe_home, "📓  Journal")

    content = tk.Frame(page, bg=BG); content.pack(fill="both", expand=True)
    editor = tk.Frame(content, bg=BG); editor.pack(side="left", fill="both", expand=True, padx=(24,12), pady=20)
    sidebar = tk.Frame(content, bg=SIDE, width=270); sidebar.pack(side="right", fill="y"); sidebar.pack_propagate(False)

    # editor -> new note
    top = tk.Frame(editor, bg=BG); top.pack(fill="x", pady=(0,12))
    tk.Label(top, text="New note:", bg=BG, fg=CARD, font=(FONT,12,"bold")).pack(side="left")
    title_e = tk.Entry(top, font=(FONT,12), width=22, bg=FIELD, fg=CARD, insertbackground=CARD, relief="flat")
    title_e.pack(side="left", padx=8, ipady=4)
    tk.Button(top, text="＋ Create", bg=CARD, fg=DEEP, relief="flat", font=(FONT,11,"bold"),
              cursor="hand2", activebackground=SOFT, command=lambda: create()).pack(side="left")

    open_lbl = tk.Label(editor, text="No note open", bg=BG, fg=CARD, font=(FONT,13,"bold"), anchor="w")
    open_lbl.pack(fill="x", pady=(0,6))
    text = tk.Text(editor, font=(FONT,12), bg=FIELD, fg=CARD, insertbackground=CARD,
                   relief="flat", wrap="word", state="disabled", padx=10, pady=10)
    text.pack(fill="both", expand=True)
    text.bind("<<Modified>>", lambda e: mark_unsaved())
    save_btn = tk.Button(editor, text="💾 Save", bg=CARD, fg=DEEP, relief="flat", font=(FONT,12,"bold"),
                         cursor="hand2", activebackground=SOFT, state="disabled", command=lambda: save())
    save_btn.pack(anchor="e", pady=(10,0))

    # sidebar -> search + list
    tk.Label(sidebar, text="Your notes", bg=SIDE, fg=CARD, font=(FONT,14,"bold")).pack(pady=(16,6))
    search_v = tk.StringVar()
    srow = tk.Frame(sidebar, bg=SIDE); srow.pack(fill="x", padx=12, pady=(0,6))
    tk.Entry(srow, textvariable=search_v, font=(FONT,11), bg=FIELD, fg=CARD,
             insertbackground=CARD, relief="flat").pack(side="left", fill="x", expand=True, ipady=3)
    tk.Button(srow, text="🔎", bg=CARD, fg=DEEP, relief="flat", font=(FONT,11), cursor="hand2",
              command=lambda: do_search()).pack(side="left", padx=(4,0))
    tk.Frame(sidebar, bg=CARD, height=1).pack(fill="x", padx=12)
    canvas = tk.Canvas(sidebar, bg=SIDE, highlightthickness=0)
    sb = tk.Scrollbar(sidebar, orient="vertical", command=canvas.yview); canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
    lst = tk.Frame(canvas, bg=SIDE)
    win = canvas.create_window((0,0), window=lst, anchor="nw")
    lst.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

    def do_search(): state["query"] = search_v.get(); refresh()

    def mark_unsaved():
        if text.edit_modified():
            state["unsaved"] = True; text.edit_modified(False)

    def _confirm_unsaved():
        if not state["unsaved"] or state["active"] is None: return True
        a = messagebox.askyesnocancel("Unsaved", "Save changes before continuing?")
        if a is None: return False
        if a: save()
        state["unsaved"] = False; return True

    def refresh():
        for w in lst.winfo_children(): w.destroy()
        q = state["query"].strip().lower()
        visible = [(i,n) for i,n in enumerate(state["notes"]) if n.matches(q)]
        if not visible:
            tk.Label(lst, text=("No matches." if q else "No notes yet."), bg=SIDE, fg=CARD,
                     font=(FONT,11,"italic")).pack(pady=20); return
        for i,note in visible:
            row = tk.Frame(lst, bg=SIDE); row.pack(fill="x", padx=8, pady=4)
            tk.Button(row, text=note.title, bg=CARD, fg=DEEP, relief="flat", font=(FONT,11),
                      anchor="w", wraplength=150, justify="left", cursor="hand2",
                      command=lambda idx=i: open_note(idx)).pack(side="left", fill="x", expand=True, ipady=4, padx=(0,4))
            tk.Button(row, text="🗑", bg=SIDE, fg=CARD, relief="flat", font=(FONT,12), cursor="hand2",
                      command=lambda idx=i: delete(idx)).pack(side="right")

    def open_note(index):
        if not _confirm_unsaved(): return
        state["active"] = index; state["unsaved"] = False
        note = state["notes"][index]
        open_lbl.config(text=f"✎  {note.title}")
        text.config(state="normal"); text.delete("1.0","end"); text.insert("1.0", note.body)
        text.edit_modified(False); save_btn.config(state="normal")

    def save():
        i = state["active"]
        if i is None: return
        state["notes"][i].body = text.get("1.0","end-1c")
        manager.save_journals(state["notes"]); state["unsaved"] = False
        messagebox.showinfo("Saved", f'Note "{state["notes"][i].title}" saved.')

    def create():
        if not _confirm_unsaved(): return
        t = title_e.get().strip()
        if not t:
            messagebox.showerror("Missing title", "Enter a title."); return
        if t.lower() in [n.title.lower() for n in state["notes"]]:
            messagebox.showerror("Duplicate", f'A note named "{t}" already exists.'); return
        manager.add_journal(t)
        state["notes"] = manager.load_journals()
        title_e.delete(0,"end"); search_v.set(""); state["query"] = ""
        refresh(); open_note(len(state["notes"]) - 1)

    def delete(index):
        title = state["notes"][index].title
        if not messagebox.askyesno("Delete", f'Delete "{title}"?'): return
        if state["active"] == index: clear_editor()
        elif state["active"] is not None and state["active"] > index: state["active"] -= 1
        del state["notes"][index]; manager.save_journals(state["notes"]); refresh()

    def clear_editor():
        state["active"] = None; state["unsaved"] = False
        open_lbl.config(text="No note open")
        text.config(state="normal"); text.delete("1.0","end"); text.config(state="disabled")
        save_btn.config(state="disabled")

    refresh()