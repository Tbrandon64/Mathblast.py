# ==============================================================
# MathBlast.py – A fun, adaptive math game with profiles
# ==============================================================
# Save this as MathBlast.py and run with:  python MathBlast.py
# ==============================================================

import random
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import datetime
import sys
import time
import ctypes
import logging

# ------------------- Optional imports (safe) -------------------
try:
    import winsound
except Exception:
    winsound = None

try:
    import wmi
except Exception:
    wmi = None

# ------------------- Logging -----------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------- Constants ---------------------------------
THEME = {
    "bg": "#f8f9fa",
    "btn_bg": "#007bff",
    "btn_fg": "white",
    "btn_active": "#0056b3",
    "font": "Arial"
}

AVATARS = ["Man", "Woman", "Cat", "Dog", "Panda", "Rabbit", "Fox", "Frog", "Lion", "Tiger", "Unicorn", "Dragon"]
ACHIEVEMENTS = {
    "beginner": {"name": "First Steps", "icon": "First"},
    "perfect_10": {"name": "Perfect 10", "icon": "10"},
    "level_master": {"name": "Level Master", "icon": "Master"},
    "math_wizard": {"name": "Math Wizard", "icon": "Wizard"}
}

# ------------------- Profile Helpers ---------------------------
PROFILES_FILE = "mathblast_profiles.json"

def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        logging.warning(f"Failed to load profiles: {e}")
        return {}

def save_profile(name, highest_level, total_correct, game_result=None, stats=None):
    profiles = load_profiles()
    profile = profiles.setdefault(name, {
        "highest_level": 1,
        "total_correct": 0,
        "games_played": 0,
        "games_won": 0,
        "games_lost": 0,
        "avatar": random.choice(AVATARS),
        "achievements": [],
        "stats": {}
    })

    profile["highest_level"] = max(highest_level, profile.get("highest_level", 1))
    profile["total_correct"] = total_correct + profile.get("total_correct", 0)
    profile["games_played"] = profile.get("games_played", 0) + (1 if game_result else 0)
    profile["last_played"] = datetime.datetime.now().isoformat()

    if game_result == "win":
        profile["games_won"] = profile.get("games_won", 0) + 1
    elif game_result == "lose":
        profile["games_lost"] = profile.get("games_lost", 0) + 1

    if stats:
        s = profile["stats"]
        s["max_streak"] = max(s.get("max_streak", 0), stats.get("streak", 0))
        s["perfect_levels"] = s.get("perfect_levels", 0) + (1 if stats.get("no_mistakes") else 0)
        s["total_time"] = s.get("total_time", 0) + stats.get("total_time", 0)
        profile["stats"] = s

    # Check achievements
    ach = set(profile.get("achievements", []))
    if "beginner" not in ach and profile["games_played"] >= 1:
        ach.add("beginner")
    if "perfect_10" not in ach and s.get("max_streak", 0) >= 10:
        ach.add("perfect_10")
    if "level_master" not in ach and profile["highest_level"] >= 5:
        ach.add("level_master")
    if "math_wizard" not in ach and profile["total_correct"] >= 100:
        ach.add("math_wizard")
    profile["achievements"] = list(ach)

    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2)
    except Exception as e:
        logging.error(f"Save failed: {e}")

# ------------------- Layout Manager ---------------------------
class LayoutManager:
    def __init__(self, root):
        self.root = root
        self.base_w, self.base_h = 1200, 800
        self.update_screen()
        self.root.bind("<Configure>", self._on_resize)

    def update_screen(self):
        try:
            self.screen_w = self.root.winfo_screenwidth()
            self.screen_h = self.root.winfo_screenheight()
            self.dpi = self.root.winfo_fpixels('1i')  # Tk DPI
        except Exception:
            self.screen_w = 1200
            self.screen_h = 800
            self.dpi = 96
        self.scale = min(self.screen_w / self.base_w, self.screen_h / self.base_h, 1.0)

    def _on_resize(self, event=None):
        if event and event.widget == self.root:
            self.update_screen()

    def font(self, base):
        return int(base * self.scale)

    def size(self, w, h=None):
        if h is None: h = w
        return int(w * self.scale), int(h * self.scale)

# ------------------- Main App ---------------------------------
class MathBlastApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MathBlast")
        self.root.configure(bg=THEME["bg"])
        self.layout = LayoutManager(root)

        self.current_profile = tk.StringVar()
        self.score = tk.IntVar()
        self.goal = tk.IntVar(value=10)
        self.level = tk.IntVar(value=1)
        self.wrong = tk.IntVar()
        self.total_correct = tk.IntVar()
        self.answer_var = tk.StringVar()
        self.game_stats = {}

        self.build_main_menu()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------- UI Builders ---------------------------
    def build_main_menu(self):
        self.clear_frame()
        frame = tk.Frame(self.root, bg=THEME["bg"])
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(frame, text="MathBlast", font=("Arial", self.layout.font(32), "bold"),
                 bg=THEME["bg"]).pack(pady=20)

        # Profile selector
        self.profile_menu = ttk.Combobox(frame, textvariable=self.current_profile, state="readonly")
        self.profile_menu.pack(pady=10, fill="x")
        self.refresh_profiles()

        tk.Button(frame, text="New Profile", command=self.new_profile_dialog,
                  **self.btn_style()).pack(pady=5, fill="x")

        tk.Button(frame, text="Play", command=self.start_game,
                  **self.btn_style()).pack(pady=15, fill="x")

        tk.Button(frame, text="Exit", command=self.root.quit,
                  bg="#dc3545", fg="white", **self.btn_style()).pack(pady=5, fill="x")

    def build_game_screen(self):
        self.clear_frame()
        frame = tk.Frame(self.root, bg=THEME["bg"])
        frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Header
        tk.Label(frame, textvariable=tk.StringVar(), font=("Arial", self.layout.font(24), "bold"),
                 bg=THEME["bg"]).pack()
        self.level_label = tk.Label(frame, text="Level 1", font=("Arial", self.layout.font(20)),
                                    bg=THEME["bg"])
        self.level_label.pack(pady=5)

        # Problem
        prob_frame = tk.Frame(frame, bg=THEME["bg"])
        prob_frame.pack(pady=20)
        self.problem_lbl = tk.Label(prob_frame, text="", font=("Arial", self.layout.font(28)),
                                    bg=THEME["bg"])
        self.problem_lbl.pack(side="left", padx=10)
        self.result_lbl = tk.Label(prob_frame, text="", font=("Arial", self.layout.font(28), "bold"),
                                   bg=THEME["bg"])
        self.result_lbl.pack(side="left", padx=10)

        # Answer
        ans_frame = tk.Frame(frame, bg=THEME["bg"])
        ans_frame.pack(pady=10)
        self.entry = tk.Entry(ans_frame, textvariable=tk.StringVar(), font=("Arial", self.layout.font(20)),
                              width=15, justify="center")
        self.entry.pack(side="left", padx=5)
        self.entry.bind("<Return>", lambda e: self.check_answer())

        tk.Button(ans_frame, text="Submit", command=self.check_answer,
                  **self.btn_style()).pack(side="left", padx=5)

        # Status
        self.status_lbl = tk.Label(frame, text="", font=("Arial", self.layout.font(12)),
                                   bg=THEME["bg"], justify="left")
        self.status_lbl.pack(pady=10, anchor="w")

        tk.Button(frame, text="Back to Menu", command=self.back_to_menu,
                  **self.btn_style()).pack(pady=10)

    # ------------------- Helpers -------------------------------
    def btn_style(self):
        return {
            "font": ("Arial", self.layout.font(14), "bold"),
            "bg": THEME["btn_bg"],
            "fg": THEME["btn_fg"],
            "activebackground": THEME["btn_active"],
            "relief": "raised",
            "padx": 10,
            "pady": 5
        }

    def clear_frame(self):
        for child in self.root.winfo_children():
            child.destroy()

    def refresh_profiles(self):
        profiles = load_profiles()
        names = sorted(profiles.keys())
        self.profile_menu["values"] = names
        if names and not self.current_profile.get():
            self.current_profile.set(names[0])

    def new_profile_dialog(self):
        name = tk.simpledialog.askstring("New Profile", "Enter name:")
        if not name or not name.strip():
            return
        name = name.strip()
        if name in load_profiles():
            messagebox.showinfo("Exists", "Profile already exists!")
            return
        save_profile(name, 1, 0)
        self.refresh_profiles()
        self.current_profile.set(name)

    # ------------------- Game Logic ----------------------------
    def start_game(self):
        if not self.current_profile.get():
            messagebox.showwarning("No Profile", "Create or select a profile first!")
            return
        self.build_game_screen()
        self.reset_game()
        self.new_problem()

    def reset_game(self):
        self.score.set(0)
        self.wrong.set(0)
        self.level.set(1)
        self.goal.set(10)
        self.total_correct.set(0)
        self.game_stats = {
            "streak": 0,
            "max_streak": 0,
            "no_mistakes": True,
            "problems_by_type": {"addition":0, "subtraction":0, "multiplication":0, "division":0},
            "total_time": 0,
            "level_start": datetime.datetime.now()
        }

    def new_problem(self):
        level = self.level.get()
        streak = self.game_stats.get("streak", 0)
        diff = min(1.0, 0.5 + level*0.1 + streak*0.05)

        ops = ["+", "-"]
        if level >= 2: ops.append("*")
        if level >= 3: ops.append("/")

        op = random.choice(ops)
        if op in "+-":
            mx = int(50 * diff)
            a, b = random.randint(1, mx), random.randint(1, mx)
            if op == "-" and diff < 0.7:
                a, b = max(a,b), min(a,b)
        else:
            mx = int(12 * diff)
            a, b = random.randint(1, mx), random.randint(1, mx)
            if op == "/":
                a = a * b

        if op == "+": ans = a + b
        elif op == "-": ans = a - b
        elif op == "*": ans = a * b
        else: ans = a / b

        self.game_stats["problems_by_type"][
            {"+": "addition", "-": "subtraction", "*": "multiplication", "/": "division"}[op]
        ] += 1

        self.answer_var.set(str(ans))
        self.problem_lbl.config(text=f"{a} {op} {b} = ?")

    def check_answer(self):
        try:
            user = float(self.entry.get())
            correct = float(self.answer_var.get())
            if abs(user - correct) < 0.01:
                self.game_stats["streak"] = self.game_stats.get("streak", 0) + 1
                self.game_stats["max_streak"] = max(self.game_stats.get("max_streak", 0), self.game_stats["streak"])
                self.score.set(self.score.get() + 1)
                self.total_correct.set(self.total_correct.get() + 1)
                self.result_lbl.config(text="Correct", fg="green")
                self.beep(1000, 150)
                if self.score.get() >= self.goal.get():
                    self.next_level()
                else:
                    self.new_problem()
            else:
                self.game_stats["streak"] = 0
                self.game_stats["no_mistakes"] = False
                self.wrong.set(self.wrong.get() + 1)
                self.result_lbl.config(text="Wrong", fg="red")
                self.beep(300, 200)
                if self.wrong.get() >= 3:
                    self.game_over()
                else:
                    self.new_problem()
            self.entry.delete(0, tk.END)
            self.update_status()
            self.root.after(800, lambda: self.result_lbl.config(text=""))
        except ValueError:
            pass

    def next_level(self):
        lvl = self.level.get() + 1
        self.level.set(lvl)
        self.goal.set(self.goal.get() + 5)
        self.score.set(0)
        self.wrong.set(0)

        now = datetime.datetime.now()
        self.game_stats["level_time"] = (now - self.game_stats["level_start"]).total_seconds()
        self.game_stats["total_time"] = self.game_stats.get("total_time", 0) + self.game_stats["level_time"]
        self.game_stats["level_start"] = now

        save_profile(self.current_profile.get(), lvl, self.total_correct.get(),
                     game_result="win", stats=self.game_stats)

        self.level_label.config(text=f"Level {lvl}")
        self.beep(1500, 120); self.beep(2000, 120)
        self.new_problem()

    def game_over(self):
        now = datetime.datetime.now()
        self.game_stats["level_time"] = (now - self.game_stats["level_start"]).total_seconds()
        self.game_stats["total_time"] = self.game_stats.get("total_time", 0) + self.game_stats["level_time"]
        save_profile(self.current_profile.get(), self.level.get(), self.total_correct.get(),
                     game_result="lose", stats=self.game_stats)
        self.problem_lbl.config(text="Game Over!")
        self.entry.config(state="disabled")
        self.beep(500, 200); self.beep(350, 400)

    def update_status(self):
        prof = load_profiles().get(self.current_profile.get(), {})
        games = prof.get("games_played", 0)
        win_rate = (prof.get("games_won", 0) / games * 100) if games else 0
        self.status_lbl.config(
            text=f"{prof.get('avatar','User')} {self.current_profile.get()}\n"
                 f"Score: {self.score.get()}/{self.goal.get()} | Wrong: {self.wrong.get()}/3 | Level: {self.level.get()}\n"
                 f"Best: {prof.get('highest_level',1)} | Total: {prof.get('total_correct',0)+self.total_correct.get()}\n"
                 f"Games: {games} | Win: {win_rate:.1f}%"
        )

    def back_to_menu(self):
        self.build_main_menu()

    def beep(self, freq, dur):
        if winsound:
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass

    def on_close(self):
        self.root.destroy()

# ------------------- Run App -----------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MathBlastApp(root)
    root.mainloop()