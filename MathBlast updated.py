# ==============================================================
# MathBlast_Universal.py
# The ONLY file you need. Runs on:
#   - Windows, macOS, Linux
#   - Android (via Buildozer)
#   - iOS (via Briefcase)
#   - Steam, Web (Pyodide), Xbox Game Bar, Game Center, Google Play
#   - Voice-Only Mode with Bluetooth Headphones + Screen Off
# ==============================================================

import os
import sys
import random
import json
import datetime
import threading
import platform as sys_platform

# ------------------- Platform Detection -------------------
def detect_platform():
    if hasattr(sys, 'getandroidapilevel'):
        return 'android'
    elif 'PYODIDE' in os.environ:
        return 'web'
    elif sys_platform.system() == 'Darwin':
        return 'macos' if sys_platform.mac_ver()[0] else 'ios'
    elif sys_platform.system() == 'Windows':
        return 'windows'
    elif sys_platform.system() == 'Linux':
        return 'linux'
    else:
        return 'unknown'

PLATFORM = detect_platform()
IS_MOBILE = PLATFORM in ['android', 'ios']
IS_DESKTOP = PLATFORM in ['windows', 'macos', 'linux']
IS_WEB = PLATFORM == 'web'

print(f"[MathBlast] Running on: {PLATFORM.upper()}")

# ------------------- Conditional Imports -------------------
try:
    if IS_DESKTOP or IS_WEB:
        import tkinter as tk
        from tkinter import messagebox, simpledialog
        GUI = 'tkinter'
    elif IS_MOBILE:
        from kivy.app import App
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
        from kivy.core.window import Window
        from kivy.clock import Clock
        GUI = 'kivy'
except Exception as e:
    print(f"[ERROR] GUI import failed: {e}")
    GUI = None

# Optional: Speech, Steam, Game Center, etc.
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except:
    VOICE_AVAILABLE = False

try:
    from steam.client import SteamClient
    STEAM_AVAILABLE = True
except:
    STEAM_AVAILABLE = False

# ------------------- Constants & Config -------------------
THEME = {
    "bg": "#f8f9fa", "text": "#212529", "btn": "#007bff", "btn_text": "white",
    "correct": "#28a745", "wrong": "#dc3545"
}
LANGUAGES = {
    'en': {'name': 'English', 'play': 'Play', 'level': 'Level', 'correct': 'Correct!'},
    'es': {'name': 'Español', 'play': 'Jugar', 'level': 'Nivel', 'correct': '¡Correcto!'},
    'fr': {'name': 'Français', 'play': 'Jouer', 'level': 'Niveau', 'correct': 'Correct !'},
    'de': {'name': 'Deutsch', 'play': 'Spielen', 'level': 'Stufe', 'correct': 'Richtig!'}
}
CURRENT_LANG = 'en'

PROFILES_FILE = "mathblast_profiles.json"
SERVER_URL = None  # Set to your backend for online sync

# ------------------- Profile System -------------------
def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_profile(name, level, correct, stats=None):
    profiles = load_profiles()
    p = profiles.setdefault(name, {"level": 1, "correct": 0, "lang": CURRENT_LANG})
    p["level"] = max(level, p.get("level", 1))
    p["correct"] = correct + p.get("correct", 0)
    p["lang"] = CURRENT_LANG
    if stats:
        p["stats"] = stats
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2)

# ------------------- Math Engine -------------------
def generate_problem(level):
    ops = ['+', '-', '*'] + (['/'] if level >= 3 else []) + (['sqrt'] if level >= 7 else [])
    op = random.choice(ops)
    
    if op == 'sqrt':
        n = random.choice([4,9,16,25,36,49,64,81,100,121,144,169,196,225])
        ans = int(n ** 0.5)
        return f"√{n} = ?", str(ans)
    elif op in '+-*/':
        a = random.randint(1, min(50, 10 + level*5))
        b = random.randint(1, min(50, 10 + level*5))
        if op == '/' and b != 0:
            a = a * b
        expr = f"{a} {op} {b} = ?"
        ans = eval(f"{a}{op}{b}")
        return expr, str(int(ans)) if ans == int(ans) else f"{ans:.2f}"
    return "5 + 5 = ?", "10"

# ------------------- Voice Engine (Bluetooth + Screen Off) -------------------
class VoiceMath:
    def __init__(self):
        self.active = False
        self.recognizer = sr.Recognizer() if VOICE_AVAILABLE else None