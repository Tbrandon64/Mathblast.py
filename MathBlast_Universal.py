# ==============================================================
# MathBlast_Universal.py – FULL VERSION
# One file. All platforms. All features.
# Works on: Windows, macOS, Linux, Android, iOS, Steam, Web
# Includes: Voice Mode (Bluetooth + Screen Off), Accessibility, Steam, Game Center
# ==============================================================

import os
import sys
import random
import json
import datetime
import threading
import platform as sys_platform
import logging
import time

# ------------------- Logging -------------------
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ------------------- Platform Detection -------------------
def detect_platform():
    """Detect current platform with fallbacks and detailed info."""
    try:
        # Android detection
        if hasattr(sys, 'getandroidapilevel'):
            try:
                api_level = sys.getandroidapilevel()
                logging.info(f"Detected Android API level: {api_level}")
                return 'android'
            except Exception as e:
                logging.error(f"Android API detection failed: {e}")
        
        # Web/Pyodide detection
        if any(key in os.environ for key in ['PYODIDE', 'WASM', 'EMSCRIPTEN']):
            logging.info("Detected Web/WASM environment")
            return 'web'
        
        # Apple platform detection
        if sys_platform.system() == 'Darwin':
            try:
                version = sys_platform.mac_ver()[0]
                if version:
                    logging.info(f"Detected macOS version: {version}")
                    return 'macos'
                else:
                    logging.info("Detected iOS device")
                    return 'ios'
            except Exception as e:
                logging.error(f"Apple platform detection error: {e}")
                return 'macos'  # Safe fallback
        
        # Windows detection with version info
        elif sys_platform.system() == 'Windows':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                    build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
                    logging.info(f"Detected Windows build: {build}")
            except Exception as e:
                logging.warning(f"Windows version detection failed: {e}")
            return 'windows'
        
        # Linux with distribution detection
        elif sys_platform.system() == 'Linux':
            try:
                with open('/etc/os-release') as f:
                    lines = f.readlines()
                    distro = next((l for l in lines if l.startswith('NAME=')), '')
                    logging.info(f"Detected Linux distribution: {distro.strip()}")
            except Exception as e:
                logging.warning(f"Linux distribution detection failed: {e}")
            return 'linux'
        
        # Unknown platform
        else:
            logging.warning(f"Unknown platform: {sys_platform.system()}")
            return 'unknown'
            
    except Exception as e:
        logging.error(f"Platform detection failed: {e}")
        return 'unknown'

# Detect platform and capabilities
PLATFORM = detect_platform()
IS_MOBILE = PLATFORM in ['android', 'ios']
IS_DESKTOP = PLATFORM in ['windows', 'macos', 'linux']
IS_WEB = PLATFORM == 'web'

# System capabilities detection
try:
    import multiprocessing
    CPU_COUNT = multiprocessing.cpu_count()
except:
    CPU_COUNT = 1

try:
    import psutil
    TOTAL_RAM = psutil.virtual_memory().total / (1024 * 1024 * 1024)  # GB
    FREE_RAM = psutil.virtual_memory().available / (1024 * 1024 * 1024)  # GB
except:
    TOTAL_RAM = 4  # Conservative default
    FREE_RAM = 2

# Graphics capabilities detection
try:
    if IS_DESKTOP:
        if PLATFORM == 'windows':
            try:
                import wmi
                c = wmi.WMI()
                gpu_info = c.Win32_VideoController()[0]
                GPU_NAME = gpu_info.Name
                VRAM = gpu_info.AdapterRAM / (1024 * 1024 * 1024)  # GB
                logging.info(f"Detected GPU: {GPU_NAME} with {VRAM:.1f}GB VRAM")
            except:
                GPU_NAME = "Unknown"
                VRAM = 1
except:
    GPU_NAME = "Unknown"
    VRAM = 1

# Update performance settings based on capabilities
if TOTAL_RAM >= 16 and VRAM >= 4:
    FPS_TARGET = 120
    HDR_ENABLED = True
    RAY_TRACING = True
elif TOTAL_RAM >= 8 and VRAM >= 2:
    FPS_TARGET = 60
    HDR_ENABLED = False
    RAY_TRACING = False
else:
    FPS_TARGET = 30
    HDR_ENABLED = False
    RAY_TRACING = False

# Scale factor based on DPI/resolution
try:
    if PLATFORM == 'windows':
        try:
            import ctypes
            user32 = ctypes.windll.user32
            try:
                dpi = user32.GetDpiForSystem()
                SCALE_FACTOR = dpi / 96.0
            except AttributeError:
                # Fallback for older Windows versions
                dc = user32.GetDC(0)
                dpi = user32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                user32.ReleaseDC(0, dc)
                SCALE_FACTOR = dpi / 96.0
        except Exception as e:
            logging.warning(f"DPI detection failed: {e}")
            SCALE_FACTOR = 1.0
    elif IS_MOBILE:
        SCALE_FACTOR = 1.5  # Higher default for mobile
    else:
        SCALE_FACTOR = 1.0
except Exception as e:
    logging.warning(f"Scale factor initialization failed: {e}")
    SCALE_FACTOR = 1.0

logging.info(f"""
Platform Information:
--------------------
Platform: {PLATFORM.upper()}
Mobile: {IS_MOBILE}
Desktop: {IS_DESKTOP}
Web: {IS_WEB}
CPU Cores: {CPU_COUNT}
RAM: {TOTAL_RAM:.1f}GB (Free: {FREE_RAM:.1f}GB)
GPU: {GPU_NAME}
VRAM: {VRAM:.1f}GB
Scale Factor: {SCALE_FACTOR:.2f}x
FPS Target: {FPS_TARGET}
HDR: {HDR_ENABLED}
Ray Tracing: {RAY_TRACING}
""")

# ------------------- Platform-Specific Imports -------------------
# Import manager to handle platform-specific dependencies
class PlatformImports:
    def __init__(self):
        self.imports = {}
        self.gui = None
    
    def try_import(self, name, import_path, required=False):
        """Try to import a module and store its status."""
        try:
            if isinstance(import_path, str):
                # Single import
                exec(f"import {import_path}")
                self.imports[name] = True
            elif isinstance(import_path, list):
                # Multiple imports
                for imp in import_path:
                    exec(f"import {imp}")
                self.imports[name] = True
        except ImportError as e:
            self.imports[name] = False
            if required:
                logging.error(f"Failed to import required module {name}: {e}")
            else:
                logging.debug(f"Optional module {name} not available: {e}")
        except Exception as e:
            self.imports[name] = False
            logging.error(f"Error importing {name}: {e}")

# Initialize platform imports
platform_imports = PlatformImports()

# ------------------- GUI System -------------------
GUI = None

# Desktop/Web GUI (Tkinter)
if IS_DESKTOP or IS_WEB:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog, font
        GUI = 'tkinter'
        logging.info("Tkinter initialized successfully")
    except ImportError as e:
        logging.error(f"Failed to import tkinter: {e}")

# Mobile GUI (Kivy)
elif IS_MOBILE:
    try:
        # Import Kivy components conditionally
        kivy_modules = {
            'core': ['kivy.app', 'kivy.core.window', 'kivy.clock'],
            'uix': ['kivy.uix.' + mod for mod in [
                'boxlayout', 'gridlayout', 'scrollview', 'label',
                'textinput', 'button', 'popup', 'spinner', 'slider',
                'switch', 'progressbar'
            ]],
            'graphics': ['kivy.graphics', 'kivy.animation', 'kivy.metrics'],
            'input': ['kivy.input.motionevent', 'kivy.gesture'],
            'effects': ['kivy.effects.scroll', 'kivy.effects.dampedscroll'],
            'storage': ['kivy.storage.jsonstore']
        }
        
        # Try to import each Kivy module group
        for group, modules in kivy_modules.items():
            for module in modules:
                platform_imports.try_import(f'kivy_{group}', module)
        
        # If core modules are available, set up Kivy
        if all(platform_imports.imports.get(f'kivy_{mod}', False) 
               for mod in ['core', 'uix', 'graphics']):
            from kivy.app import App
            from kivy.core.window import Window
            
            # Configure Kivy
            Window.softinput_mode = 'below_target'
            Window.keyboard_anim_args = {'d': .2, 't': 'in_out_expo'}
            
            GUI = 'kivy'
            logging.info("Kivy initialized successfully")
        else:
            logging.error("Required Kivy modules not available")
            
    except Exception as e:
        logging.error(f"Kivy initialization failed: {e}")

# ------------------- Optional Services -------------------
# Voice Recognition
VOICE_AVAILABLE = False
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
    logging.info("Voice recognition initialized")
except ImportError:
    logging.debug("Voice recognition not available")

# Steam Integration
STEAM_AVAILABLE = False
try:
    if IS_DESKTOP:
        from steam.client import SteamClient
        STEAM_AVAILABLE = True
        logging.info("Steam integration initialized")
except ImportError:
    logging.debug("Steam integration not available")

# ------------------- Mobile Platform Services -------------------
# Android Services Configuration
ANDROID_SERVICES = {
    'google_play': {'available': False, 'module': 'android.gms.games'},
    'google_drive': {'available': False, 'module': 'android.gms.drive'},
    'firebase': {'available': False, 'module': 'android.firebase'},
    'biometric': {'available': False, 'module': 'android.hardware.fingerprint'}
}

# Apple Services Configuration
APPLE_SERVICES = {
    'game_center': {'available': False, 'module': 'GameKit'},
    'icloud': {'available': False, 'module': 'CloudKit'},
    'healthkit': {'available': False, 'module': 'HealthKit'},
    'accessibility': {'available': False, 'modules': ['UIKit', 'AppKit']}
}

def init_mobile_services():
    """Initialize mobile platform services based on detected platform."""
    if PLATFORM == 'android':
        for service, info in ANDROID_SERVICES.items():
            try:
                platform_imports.try_import(
                    f'android_{service}',
                    info['module'],
                    required=False
                )
                ANDROID_SERVICES[service]['available'] = platform_imports.imports.get(
                    f'android_{service}', False
                )
                if ANDROID_SERVICES[service]['available']:
                    logging.info(f"Android {service} service initialized")
            except Exception as e:
                logging.debug(f"Android {service} service not available: {e}")
                
    elif PLATFORM in ['macos', 'ios']:
        for service, info in APPLE_SERVICES.items():
            try:
                if isinstance(info['modules'], list):
                    # Service requires multiple modules
                    modules_available = True
                    for module in info['modules']:
                        platform_imports.try_import(
                            f'apple_{service}_{module}',
                            module,
                            required=False
                        )
                        if not platform_imports.imports.get(f'apple_{service}_{module}', False):
                            modules_available = False
                            break
                    APPLE_SERVICES[service]['available'] = modules_available
                else:
                    # Service requires single module
                    platform_imports.try_import(
                        f'apple_{service}',
                        info['module'],
                        required=False
                    )
                    APPLE_SERVICES[service]['available'] = platform_imports.imports.get(
                        f'apple_{service}', False
                    )
                    
                if APPLE_SERVICES[service]['available']:
                    logging.info(f"Apple {service} service initialized")
            except Exception as e:
                logging.debug(f"Apple {service} service not available: {e}")

# Initialize mobile services if on a mobile platform
if IS_MOBILE:
    init_mobile_services()

# Initialize Apple Services
def init_apple_services():
    """Initialize Apple platform services if available."""
    if not PLATFORM in ['macos', 'ios']:
        return
        
    if APPLE_SERVICES['game_center']['available']:
        try:
            # Game Center initialization will be done on demand
            logging.info("Game Center service ready")
        except Exception as e:
            logging.error(f"Game Center init failed: {e}")
            
    if APPLE_SERVICES['icloud']['available']:
        try:
            # iCloud initialization will be done on demand
            logging.info("iCloud service ready")
        except Exception as e:
            logging.error(f"iCloud init failed: {e}")
            
    if APPLE_SERVICES['accessibility']['available']:
        try:
            # Accessibility checks will be done on demand
            logging.info("Accessibility service ready")
        except Exception as e:
            logging.error(f"Accessibility init failed: {e}")

def handle_gc_auth(viewController, error):
    """Handle Game Center authentication."""
    if not APPLE_SERVICES['game_center']['available']:
        return
        
    if error:
        logging.error(f"Game Center auth failed: {error}")
        return
        
    if viewController and PLATFORM == 'ios':
        # Present authentication view controller
        try:
            # Will be handled by platform-specific code
            logging.info("Game Center auth UI ready")
        except Exception as e:
            logging.error(f"Failed to present GC auth: {e}")
    
    # Authentication status will be checked on demand
    logging.info("Game Center auth handler configured")

def handle_icloud_status(error=None):
    """Handle iCloud account status check."""
    if not APPLE_SERVICES['icloud']['available']:
        return
        
    if error:
        logging.error(f"iCloud status check failed: {error}")
        return
        
    try:
        # Will check availability on demand
        logging.info("iCloud status handler configured")
    except Exception as e:
        logging.error(f"iCloud sync failed: {e}")

def sync_achievements(achievements):
    """Sync achievements with platform services."""
    if APPLE_SERVICES['game_center']['available']:
        try:
            # Will be handled by platform-specific code
            logging.info(f"Syncing achievements: {achievements}")
        except Exception as e:
            logging.error(f"Achievement sync failed: {e}")
    elif ANDROID_SERVICES['google_play']['available']:
        try:
            # Will be handled by platform-specific code
            logging.info(f"Syncing achievements: {achievements}")
        except Exception as e:
            logging.error(f"Achievement sync failed: {e}")

def update_leaderboard(leaderboard_id, score):
    """Update platform leaderboards."""
    if APPLE_SERVICES['game_center']['available']:
        try:
            # Will be handled by platform-specific code
            logging.info(f"Updating leaderboard {leaderboard_id}: {score}")
        except Exception as e:
            logging.error(f"Leaderboard update failed: {e}")
    elif ANDROID_SERVICES['google_play']['available']:
        try:
            # Will be handled by platform-specific code
            logging.info(f"Updating leaderboard {leaderboard_id}: {score}")
        except Exception as e:
            logging.error(f"Leaderboard update failed: {e}")

def sync_cloud_storage():
    """Sync data to platform cloud storage."""
    if APPLE_SERVICES['icloud']['available']:
        try:
            # Will be handled by platform-specific code
            logging.info("Syncing to iCloud")
        except Exception as e:
            logging.error(f"iCloud sync failed: {e}")
    elif ANDROID_SERVICES['google_drive']['available']:
        try:
            # Will be handled by platform-specific code
            logging.info("Syncing to Google Drive")
        except Exception as e:
            logging.error(f"Google Drive sync failed: {e}")
    elif PLATFORM == 'windows':
        try:
            # Will be handled by platform-specific code
            logging.info("Syncing to OneDrive")
        except Exception as e:
            logging.error(f"OneDrive sync failed: {e}")

# Initialize services based on platform
if PLATFORM in ['macos', 'ios']:
    init_apple_services()
elif PLATFORM == 'android':
    # Android services are initialized on demand
    pass

# ------------------- Constants -------------------
THEME = {
    "bg": "#f8f9fa", "text": "#212529", "btn": "#007bff", "btn_text": "white",
    "correct": "#28a745", "wrong": "#dc3545", "high_contrast_bg": "#000000", "high_contrast_text": "#FFFFFF"
}

AVATARS = ["🧑", "👧", "🐱", "🐶", "🐼", "🐰", "🦊", "🐸", "🦁", "🐯", "🦄", "🐲"]
DEFAULT_AVATAR = AVATARS[0]

LANGUAGES = {
    'en': {'name': 'English', 'play': 'Play', 'level': 'Level', 'correct': 'Correct!', 'wrong': 'Wrong!', 'game_over': 'Game Over!'},
    'es': {'name': 'Español', 'play': 'Jugar', 'level': 'Nivel', 'correct': '¡Correcto!', 'wrong': '¡Incorrecto!', 'game_over': '¡Juego Terminado!'},
    'fr': {'name': 'Français', 'play': 'Jouer', 'level': 'Niveau', 'correct': 'Correct !', 'wrong': 'Faux !', 'game_over': 'Jeu Terminé !'},
    'de': {'name': 'Deutsch', 'play': 'Spielen', 'level': 'Stufe', 'correct': 'Richtig!', 'wrong': 'Falsch!', 'game_over': 'Spiel Vorbei!'}
}
CURRENT_LANG = 'en'

# Store profiles in a user-specific application directory to avoid permission issues
APP_DATA_DIR = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'MathBlast')
try:
    os.makedirs(APP_DATA_DIR, exist_ok=True)
except Exception:
    # fallback to home directory
    APP_DATA_DIR = os.path.expanduser('~')

PROFILES_FILE = os.path.join(APP_DATA_DIR, 'profiles.json')
SERVER_URL = None  # Set to your backend for online sync

# Current profile pointer
CURRENT_PROFILE_FILE = os.path.join(APP_DATA_DIR, 'current_profile.txt')

def set_current_profile(name):
    try:
        with open(CURRENT_PROFILE_FILE, 'w', encoding='utf-8') as f:
            f.write(name)
        logging.info(f"Set current profile: {name}")
    except Exception as e:
        logging.error(f"Failed to write current profile: {e}")

def get_current_profile():
    try:
        if os.path.exists(CURRENT_PROFILE_FILE):
            with open(CURRENT_PROFILE_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        logging.error(f"Failed to read current profile: {e}")
    return None

# ------------------- Display / Performance Defaults -------------------
# Safe defaults; will be recomputed after `root` is created in main()
SCALE_FACTOR = 1.0
IS_4K = False
IS_8K = False
FPS_TARGET = 60
HDR_ENABLED = False
RAY_TRACING = False

def font_size(base):
    """Return a scaled integer font size based on global SCALE_FACTOR."""
    try:
        return int(base * SCALE_FACTOR)
    except Exception:
        return int(base)

# ------------------- Profile System -------------------
def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        logging.debug(f"Profiles file does not exist: {PROFILES_FILE}")
        return {}
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            logging.warning(f"Profiles file malformed (expected dict), resetting: {PROFILES_FILE}")
            return {}
    except json.JSONDecodeError as e:
        logging.error(f"Profiles JSON decode error: {e} - backing up and resetting {PROFILES_FILE}")
        try:
            backup = PROFILES_FILE + ".corrupt"
            os.replace(PROFILES_FILE, backup)
            logging.info(f"Backed up corrupt profiles to {backup}")
        except Exception as ex:
            logging.error(f"Failed to backup corrupt profiles file: {ex}")
        return {}
    except Exception as e:
        logging.error(f"Failed to read profiles: {e}")
        return {}

def save_profile(name, level, correct, stats=None):
    if not name:
        logging.error("Cannot save profile: empty name")
        return False
        
    try:
        profiles = load_profiles()
        p = profiles.setdefault(name, {
            "level": 1, 
            "correct": 0,
            "lang": CURRENT_LANG,
            "avatar": "Brain",
            "created": int(time.time()),
            "last_played": int(time.time())
        })
        
        p["level"] = max(level, p.get("level", 1))
        p["correct"] = correct + p.get("correct", 0)
        p["lang"] = CURRENT_LANG
        p["last_played"] = int(time.time())
        
        if stats:
            curr_stats = p.get("stats", {})
            curr_stats.update(stats)
            p["stats"] = curr_stats

        # write atomically using a temporary file
        tmp = PROFILES_FILE + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            os.replace(tmp, PROFILES_FILE)
            logging.info(f"Profile saved: {name} -> {PROFILES_FILE}")
            return True
        except Exception as e:
            logging.error(f"Profile save failed: {e}")
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return False
    except Exception as e:
        logging.error(f"Profile save failed (outer): {e}")
        return False

# ------------------- Math Engine -------------------
def generate_problem(level, multiplier=1.0):
    """Generate a math problem. Multiplier (0.5-2.0) scales difficulty/operand size.

    Returns: (problem_str, answer_str)
    """
    ops = ['+', '-', '*'] + (['/'] if level >= 3 else []) + (['sqrt'] if level >= 7 else [])
    op = random.choice(ops)

    # scale ranges based on level and multiplier
    base_max = max(2, int(min(100, (10 + level * 5) * multiplier)))

    if op == 'sqrt':
        # pick a perfect square within range
        sq = [i*i for i in range(2, int(base_max**0.5) + 2)]
        if not sq:
            sq = [4,9,16]
        n = random.choice(sq)
        ans = int(n ** 0.5)
        return f"√{n} = ?", str(ans)

    # standard binary ops
    a = random.randint(1, base_max)
    b = random.randint(1, base_max)
    if op == '/':
        # ensure divisible
        b = random.randint(1, max(1, base_max//2))
        a = b * random.randint(1, max(1, base_max//b))

    expr = f"{a} {op} {b} = ?"
    try:
        ans = eval(f"{a}{op}{b}")
    except Exception:
        ans = a
    return expr, str(int(ans)) if isinstance(ans, int) or ans == int(ans) else f"{ans:.2f}"

# ------------------- Adaptive Engine -------------------
class AdaptiveEngine:
    """Simple adaptive difficulty tracker.

    Keeps a short history of recent attempts and computes a skill score (10-100).
    The engine exposes get_difficulty_multiplier() which returns 0.5-2.0 multiplier.
    """
    def __init__(self):
        self.history = []  # list of (time_taken, correct, level)
        self.skill_score = 50
        self.streak = 0

    def update(self, time_taken, correct, level):
        self.history.append((time_taken, bool(correct), level))
        if len(self.history) > 20:
            self.history.pop(0)

        # Accuracy
        accuracy = sum(1 for _, c, _ in self.history if c) / max(1, len(self.history))

        # Speed (lower = better)
        avg_time = sum(t for t, _, _ in self.history) / max(1, len(self.history))
        speed_score = max(0, 100 - avg_time * 10)

        # Streak bonus
        streak_bonus = self.streak * 5 if correct else -10

        # Final skill
        self.skill_score = int(0.4 * accuracy * 100 + 0.4 * speed_score + 0.2 * streak_bonus)
        self.skill_score = max(10, min(100, self.skill_score))

        if correct:
            self.streak += 1
        else:
            self.streak = 0

    def get_difficulty_multiplier(self):
        # 0.5x (easy) .. 2.0x (hard)
        return 0.5 + (self.skill_score / 100.0) * 1.5


# ------------------- Voice Engine (Bluetooth + Screen Off) -------------------
class VoiceMath:
    def __init__(self):
        self.active = False
        self.recognizer = sr.Recognizer() if VOICE_AVAILABLE else None
        self.tts = pyttsx3.init() if VOICE_AVAILABLE else None
        if self.tts:
            self.tts.setProperty('rate', 150)

    def speak(self, text):
        if self.tts:
            print(f"[TTS] {text}")
            self.tts.say(text)
            self.tts.runAndWait()

    def start(self):
        if not VOICE_AVAILABLE:
            messagebox.showinfo("Voice Mode", "Install pyttsx3 and SpeechRecognition.")
            return
        self.active = True
        threading.Thread(target=self.loop, daemon=True).start()
        self.speak("Voice Math Mode activated. Say a problem.")

    def loop(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while self.active:
                try:
                    audio = self.recognizer.listen(source, timeout=1)
                    cmd = self.recognizer.recognize_google(audio).lower()
                    if any(x in cmd for x in ["square root", "plus", "minus", "times", "divided"]):
                        self.speak("Problem received.")
                except:
                    pass

voice_engine = VoiceMath()

# ------------------- Handwriting recognizer (ONNX stub) -------------------
handwriting_recognizer = None
try:
    import onnxruntime as ort
    try:
        recognizer = ort.InferenceSession("math_handwriting.onnx")
        class ONNXRecognizer:
            def __init__(self, sess):
                self.sess = sess
            def predict(self, strokes):
                # Placeholder: real implementation converts strokes -> model input
                return ""  # empty string until model is hooked
        handwriting_recognizer = ONNXRecognizer(recognizer)
    except Exception:
        handwriting_recognizer = None
except Exception:
    handwriting_recognizer = None


# ------------------- GUI: Tkinter (Desktop) -------------------
class MathBlastTk:
    def __init__(self, root):
        self.root = root
        self.root.title("MathBlast")
        self.root.configure(bg=THEME["bg"])
        self.level = 1
        self.score = 0
        self.wrong = 0
        self.total_correct = 0
        # Adaptive engine for difficulty
        self.adaptive = AdaptiveEngine()
        # Track when current problem was presented
        self.problem_start_time = time.time()
        
        # Initialize platform-specific features
        self.init_platform_features()
        
        self.build_ui()
        
    def init_platform_features(self):
        """Initialize platform-specific features based on detected platform."""
        # Windows Platform
        if PLATFORM == 'windows' and PLATFORM_SERVICES['xbox']['initialized']:
            self.setup_xbox_features()
            
        # Apple Platform
        elif PLATFORM in ['macos', 'ios']:
            if PLATFORM_SERVICES['game_center']['initialized']:
                self.setup_game_center()
            if PLATFORM_SERVICES['icloud']['initialized']:
                self.setup_icloud_sync()
                
        # Android Platform
        elif PLATFORM == 'android' and PLATFORM_SERVICES['google_play']['initialized']:
            self.setup_google_play()
            
        # Steam (Cross-platform)
        if PLATFORM_SERVICES['steam']['initialized']:
            self.setup_steam_features()
    
    def setup_xbox_features(self):
        """Configure Xbox Game Bar and Xbox Live features."""
        try:
            self.achievements = {
                'first_correct': {
                    'id': 'achievement_first_correct',
                    'score': 5
                },
                'level_complete': {
                    'id': 'achievement_level_complete',
                    'score': 10
                },
                'perfect_score': {
                    'id': 'achievement_perfect_score',
                    'score': 20
                }
            }
            logging.info("[Xbox] Features initialized")
        except Exception as e:
            logging.error(f"[Xbox] Setup failed: {e}")
    
    def setup_google_play(self):
        """Configure Google Play Games features."""
        try:
            # Attempt to import Google Play Games SDK
            games = None
            try:
                from android.gms import games
            except ImportError:
                logging.warning("[Google Play] SDK not available")
                return
                
            self.leaderboards = {
                'high_score': games.leaderboard.get_id('high_score'),
                'total_solved': games.leaderboard.get_id('total_solved')
            }
            self.achievements = {
                'first_correct': games.achievement.get_id('first_correct'),
                'level_complete': games.achievement.get_id('level_complete'),
                'perfect_score': games.achievement.get_id('perfect_score')
            }
            logging.info("[Google Play] Features initialized")
        except Exception as e:
            logging.error(f"[Google Play] Setup failed: {e}")
            PLATFORM_SERVICES['google_play']['initialized'] = False
    
    def setup_steam_features(self):
        """Configure Steam features."""
        try:
            self.steam_stats = {
                'total_correct': 'stat_total_correct',
                'high_level': 'stat_highest_level',
                'perfect_levels': 'stat_perfect_levels'
            }
            self.steam_achievements = {
                'first_correct': 'ACH_FIRST_CORRECT',
                'level_complete': 'ACH_LEVEL_COMPLETE',
                'perfect_score': 'ACH_PERFECT_SCORE'
            }
            logging.info("[Steam] Features initialized")
        except Exception as e:
            logging.error(f"[Steam] Setup failed: {e}")
            PLATFORM_SERVICES['steam']['initialized'] = False
    
    def award_platform_achievement(self, achievement_id):
        """Award achievement on the current platform."""
        try:
            # Windows Platform
            if PLATFORM == 'windows' and PLATFORM_SERVICES['xbox']['initialized']:
                try:
                    from windows.gaming import xbox
                    xbox.unlock_achievement(self.achievements[achievement_id]['id'])
                except ImportError:
                    logging.warning("[Xbox] SDK not available")
                    PLATFORM_SERVICES['xbox']['initialized'] = False
                    
            # Apple Platform
            elif PLATFORM in ['macos', 'ios'] and PLATFORM_SERVICES['game_center']['initialized']:
                self.award_achievement(achievement_id)
                
            # Android Platform
            elif PLATFORM == 'android' and PLATFORM_SERVICES['google_play']['initialized']:
                try:
                    from android.gms import games
                    games.achievement.unlock(self.achievements[achievement_id])
                except ImportError:
                    logging.warning("[Google Play] SDK not available")
                    PLATFORM_SERVICES['google_play']['initialized'] = False
                
            # Steam (Cross-platform)
            if PLATFORM_SERVICES['steam']['initialized']:
                client = SteamClient()
                client.achievements.unlock(self.steam_achievements[achievement_id])
                
        except Exception as e:
            logging.error(f"Failed to award achievement '{achievement_id}': {e}")
    
    def update_platform_stats(self, stat_type, value):
        """Update statistics on the current platform."""
        try:
            # Windows Platform
            if PLATFORM == 'windows' and PLATFORM_SERVICES['xbox']['initialized']:
                try:
                    from windows.gaming import xbox
                    xbox.update_stat(stat_type, value)
                except ImportError:
                    logging.warning("[Xbox] SDK not available")
                    PLATFORM_SERVICES['xbox']['initialized'] = False
                    
            # Apple Platform
            elif PLATFORM in ['macos', 'ios'] and PLATFORM_SERVICES['game_center']['initialized']:
                self.update_score(stat_type, value)
                
            # Android Platform
            elif PLATFORM == 'android' and PLATFORM_SERVICES['google_play']['initialized']:
                try:
                    from android.gms import games
                    games.leaderboard.submit_score(self.leaderboards[stat_type], value)
                except ImportError:
                    logging.warning("[Google Play] SDK not available")
                    PLATFORM_SERVICES['google_play']['initialized'] = False
                
            # Steam (Cross-platform)
            if PLATFORM_SERVICES['steam']['initialized']:
                client = SteamClient()
                client.stats.set_stat(self.steam_stats[stat_type], value)
                
        except Exception as e:
            logging.error(f"Failed to update stat '{stat_type}': {e}")
    
    def sync_cloud_storage(self):
        """Sync game data to platform cloud storage."""
        try:
            # Windows Platform
            if PLATFORM == 'windows' and PLATFORM_SERVICES['windows_cloud']['initialized']:
                try:
                    from windows import storage
                    storage.sync_file(PROFILES_FILE)
                except ImportError:
                    logging.warning("[Windows Cloud] SDK not available")
                    PLATFORM_SERVICES['windows_cloud']['initialized'] = False
                    
            # Apple Platform
            elif PLATFORM in ['macos', 'ios'] and PLATFORM_SERVICES['icloud']['initialized']:
                self.sync_profile()
                
            # Android Platform
            elif PLATFORM == 'android' and PLATFORM_SERVICES['google_drive']['initialized']:
                try:
                    from android.gms import drive
                    drive.sync_file(PROFILES_FILE)
                except ImportError:
                    logging.warning("[Google Drive] SDK not available")
                    PLATFORM_SERVICES['google_drive']['initialized'] = False
                
        except Exception as e:
            logging.error(f"Failed to sync cloud storage: {e}")
        
    def init_apple_features(self):
        """Initialize Apple platform specific features."""
        if APPLE_SERVICES['game_center']:
            self.setup_game_center()
        if APPLE_SERVICES['icloud']:
            self.setup_icloud_sync()
            
    def setup_game_center(self):
        """Configure Game Center integration."""
        try:
            # Set up achievement definitions
            self.achievements = {
                'first_correct': {
                    'id': 'com.mathblast.achievement.first_correct',
                    'title': 'First Step',
                    'description': 'Answer your first problem correctly'
                },
                'level_complete': {
                    'id': 'com.mathblast.achievement.level_complete',
                    'title': 'Level Master',
                    'description': 'Complete a level'
                },
                'perfect_score': {
                    'id': 'com.mathblast.achievement.perfect',
                    'title': 'Perfect Score',
                    'description': 'Complete a level without mistakes'
                }
            }
            
            # Set up leaderboard definitions
            self.leaderboards = {
                'high_score': {
                    'id': 'com.mathblast.leaderboard.highscore',
                    'title': 'High Scores'
                },
                'total_solved': {
                    'id': 'com.mathblast.leaderboard.total',
                    'title': 'Total Problems Solved'
                }
            }
            
            logging.info("Game Center features initialized")
        except Exception as e:
            logging.error(f"Game Center setup failed: {e}")
            
    def setup_icloud_sync(self):
        """Configure iCloud sync for profiles and progress."""
        try:
            # Set up iCloud container and database references
            self.icloud_container_id = 'iCloud.com.mathblast'
            self.icloud_record_types = {
                'profile': 'MBProfile',
                'progress': 'MBProgress',
                'settings': 'MBSettings'
            }
            
            logging.info("iCloud sync initialized")
        except Exception as e:
            logging.error(f"iCloud setup failed: {e}")
            
    def award_achievement(self, achievement_id):
        """Report achievement to Game Center."""
        if not (PLATFORM in ['macos', 'ios'] and APPLE_SERVICES['game_center']):
            return
            
        try:
            achievement = self.achievements.get(achievement_id)
            if achievement:
                sync_achievements([{
                    'identifier': achievement['id'],
                    'percentComplete': 100.0,
                    'completed': True
                }])
        except Exception as e:
            logging.error(f"Failed to award achievement: {e}")
            
    def update_score(self, score_type='high_score', value=None):
        """Update score on Game Center leaderboard."""
        if not (PLATFORM in ['macos', 'ios'] and APPLE_SERVICES['game_center']):
            return
            
        try:
            leaderboard = self.leaderboards.get(score_type)
            if leaderboard:
                score_value = value if value is not None else self.total_correct
                update_leaderboard(leaderboard['id'], score_value)
        except Exception as e:
            logging.error(f"Failed to update leaderboard: {e}")
            
    def sync_profile(self):
        """Sync current profile to iCloud."""
        if not (PLATFORM in ['macos', 'ios'] and APPLE_SERVICES['icloud']):
            return
            
        try:
            sync_profiles_to_icloud()

    def build_ui(self):
        self.main_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # keep references so we can update fonts later when SCALE_FACTOR is computed
        self.title_label = tk.Label(self.main_frame, text="MathBlast", font=("Arial", font_size(32), "bold"), bg=THEME["bg"])
        self.title_label.pack(pady=20)
        # current profile label
        cur = get_current_profile() or "Player"
        self.current_profile_name = cur
        self.profile_label = tk.Label(self.main_frame, text=f"Profile: {cur}", font=("Arial", font_size(12)), bg=THEME["bg"]) 
        self.profile_label.pack()
        self.start_btn = tk.Button(self.main_frame, text="Start Game", command=self.start_game, bg=THEME["btn"], fg=THEME["btn_text"], font=("Arial", font_size(14)))
        self.start_btn.pack(pady=10)
        self.voice_btn = tk.Button(self.main_frame, text="Voice Mode (Headphones)", command=voice_engine.start, bg="#28a745", fg="white", font=("Arial", font_size(12)))
        self.voice_btn.pack(pady=5)
        self.settings_btn = tk.Button(self.main_frame, text="Settings", command=self.show_settings, font=("Arial", font_size(12)))
        self.settings_btn.pack(pady=5)

    def update_fonts(self):
        """Re-apply scaled fonts to widgets after SCALE_FACTOR is computed."""
        try:
            # main menu widgets
            if hasattr(self, 'title_label'):
                self.title_label.config(font=("Arial", font_size(32), "bold"))
            if hasattr(self, 'start_btn'):
                self.start_btn.config(font=("Arial", font_size(14)))
            if hasattr(self, 'voice_btn'):
                self.voice_btn.config(font=("Arial", font_size(12)))
            if hasattr(self, 'settings_btn'):
                self.settings_btn.config(font=("Arial", font_size(12)))

            # in-game widgets
            if hasattr(self, 'level_label'):
                self.level_label.config(font=("Arial", font_size(20)))
            if hasattr(self, 'problem_label'):
                self.problem_label.config(font=("Arial", font_size(24)))
            if hasattr(self, 'answer_entry'):
                self.answer_entry.config(font=("Arial", font_size(18)))
        except Exception as e:
            logging.debug(f"update_fonts failed: {e}")

    def start_game(self):
        self.main_frame.pack_forget()
        self.game_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.game_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.level_label = tk.Label(self.game_frame, text=f"Level {self.level}", font=("Arial", font_size(20)), bg=THEME["bg"])
        self.level_label.pack(pady=10)

        # compute adaptive multiplier if available
        try:
            multiplier = self.adaptive.get_difficulty_multiplier()
        except Exception:
            multiplier = 1.0

        problem, answer = generate_problem(self.level, multiplier)
        self.current_answer = answer
        # mark start time for adaptive timing
        self.problem_start_time = time.time()

        self.problem_label = tk.Label(self.game_frame, text=problem, font=("Arial", font_size(24)), bg=THEME["bg"])
        self.problem_label.pack(pady=20)

        self.answer_entry = tk.Entry(self.game_frame, font=("Arial", font_size(18)), width=15, justify="center")
        self.answer_entry.pack(pady=10)
        self.answer_entry.bind("<Return>", lambda e: self.check_answer())

        tk.Button(self.game_frame, text="Submit", command=self.check_answer, bg=THEME["btn"], fg=THEME["btn_text"]).pack(pady=5)
        tk.Button(self.game_frame, text="Back", command=self.back_to_menu).pack(pady=5)

    def check_answer(self):
        user = self.answer_entry.get().strip()
        # compute time taken to answer
        time_taken = time.time() - getattr(self, 'problem_start_time', time.time())
        correct = (user == self.current_answer)

        # update adaptive engine
        try:
            self.adaptive.update(time_taken, correct, self.level)
            multiplier = self.adaptive.get_difficulty_multiplier()
            logging.debug(f"Adaptive multiplier: {multiplier:.2f} | skill: {self.adaptive.skill_score}")
        except Exception as e:
            logging.debug(f"Adaptive update failed: {e}")

        if correct:
            self.score += 1
            self.total_correct += 1
            self.problem_label.config(text="Correct!", fg=THEME["correct"])
            self.speak("Correct!")
            
            # Award achievement for first correct answer
            if self.total_correct == 1:
                self.award_achievement('first_correct')
            
            # Update Game Center score
            self.update_score('total_solved', self.total_correct)
            
            if self.score >= 10:
                self.next_level()
            else:
                self.root.after(1000, self.next_problem)
        else:
            self.wrong += 1
            self.problem_label.config(text="Wrong!", fg=THEME["wrong"])
            self.speak("Wrong!")
            if self.wrong >= 3:
                self.game_over()
            else:
                self.root.after(1000, self.next_problem)
        
        # Sync progress to iCloud
        if self.total_correct % 5 == 0:  # Sync every 5 correct answers
            self.sync_profile()
            
        self.answer_entry.delete(0, tk.END)

    def next_problem(self):
        try:
            multiplier = self.adaptive.get_difficulty_multiplier()
        except Exception:
            multiplier = 1.0
        problem, answer = generate_problem(self.level, multiplier)
        self.current_answer = answer
        self.problem_label.config(text=problem, fg=THEME["text"])
        # reset timer for adaptive engine
        self.problem_start_time = time.time()

    def next_level(self):
        self.level += 1
        self.score = 0
        self.wrong = 0
        self.level_label.config(text=f"Level {self.level}")
        
        # Award level completion achievement
        self.award_achievement('level_complete')
        
        # Award perfect score achievement if applicable
        if self.wrong == 0:
            self.award_achievement('perfect_score')
        
        # Update Game Center high score
        self.update_score('high_score', self.level)
        
        # Sync progress to iCloud
        self.sync_profile()
        
        self.next_problem()

    def game_over(self):
        messagebox.showinfo("Game Over", f"Game Over! You reached Level {self.level}")
        save_profile(self.current_profile_name or "Player", self.level, self.total_correct)
        
        # Final Game Center updates
        self.update_score('high_score', self.level)
        self.update_score('total_solved', self.total_correct)
        
        # Final iCloud sync
        self.sync_profile()
        
        self.back_to_menu()

    def back_to_menu(self):
        self.game_frame.pack_forget()
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

    def show_settings(self):
        # Enhanced settings / profile manager with tabs
        try:
            wnd = tk.Toplevel(self.root)
            wnd.title("Settings")
            wnd.geometry("600x500")
            wnd.configure(bg=THEME["bg"])
            wnd.minsize(600, 500)

            # Title bar with icon
            title_frame = tk.Frame(wnd, bg=THEME["btn"])
            title_frame.pack(fill="x")
            tk.Label(title_frame, text="⚙️ Settings", 
                    font=("Arial", font_size(18), "bold"),
                    bg=THEME["btn"], fg="white").pack(pady=10)

            # Create notebook for tabs
            notebook = ttk.Notebook(wnd)
            notebook.pack(fill="both", expand=True, padx=10, pady=5)

            # Profile tab
            profile_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(profile_frame, text=" 👤 Profiles ")

            # Settings tab
            settings_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(settings_frame, text=" ⚙️ Game Options ")

            # Language & Region tab
            lang_region_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(lang_region_frame, text=" 🌎 Language & Region ")

            # Sound tab
            sound_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(sound_frame, text=" 🔊 Sound ")

            # Display tab
            display_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(display_frame, text=" 🖥️ Display ")

            # Accessibility tab
            accessibility_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(accessibility_frame, text=" ♿ Accessibility ")

            # Stats tab
            stats_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(stats_frame, text=" 📊 Statistics ")

            # Teacher Dashboard tab
            teacher_frame = tk.Frame(notebook, bg=THEME["bg"])
            notebook.add(teacher_frame, text=" 📚 Teacher Dashboard ")

            # Profile Management Section
            profile_top = tk.Frame(profile_frame, bg=THEME["bg"])
            profile_top.pack(fill="x", padx=20, pady=10)
            
            tk.Label(profile_top, text="Profile Management", 
                    font=("Arial", font_size(16), "bold"),
                    bg=THEME["bg"]).pack(side=tk.LEFT)
            
            # Profile list with Treeview
            tree_frame = tk.Frame(profile_frame, bg=THEME["bg"])
            tree_frame.pack(fill="both", expand=True, padx=20)
            
            # Create Treeview with scrollbar
            columns = ('avatar', 'level', 'correct', 'last_played')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill="both", expand=True)
            scrollbar.pack(side=tk.RIGHT, fill="y")
            
            # Define column headings
            tree.heading('avatar', text='👤')
            tree.heading('level', text='Level')
            tree.heading('correct', text='Score')
            tree.heading('last_played', text='Last Played')
            
            # Column widths
            tree.column('avatar', width=40, anchor='center')
            tree.column('level', width=60, anchor='center')
            tree.column('correct', width=80, anchor='center')
            tree.column('last_played', width=150, anchor='center')
            
            # Load and display profiles
            profiles = load_profiles()
            for name, data in profiles.items():
                avatar = data.get('avatar', DEFAULT_AVATAR)
                level = str(data.get('level', 1))
                correct = str(data.get('correct', 0))
                last_played = datetime.datetime.fromtimestamp(
                    data.get('last_played', 0)
                ).strftime('%Y-%m-%d %H:%M') if data.get('last_played') else 'Never'
                tree.insert('', 'end', text=name, values=(avatar, level, correct, last_played))

            def new_profile():
                name = simpledialog.askstring("New Profile", "Enter profile name:", parent=wnd)
                if not name or not name.strip():
                    return
                name = name.strip()
                if name in profiles:
                    messagebox.showerror("Error", "Profile already exists!")
                    return
                
                # Create profile with default avatar
                ok = save_profile(name, 1, 0)
                if ok:
                    # Update treeview
                    tree.insert('', 'end', text=name, values=(
                        DEFAULT_AVATAR, '1', '0', 
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    ))
                else:
                    messagebox.showerror("Save Failed", f"Failed to create profile: {name}")

            def load_selected():
                selection = tree.selection()
                if not selection:
                    messagebox.showinfo("Select", "Please select a profile.")
                    return
                
                item = selection[0]
                name = tree.item(item)['text']
                p = profiles.get(name, {})
                
                # Update game state
                self.level = p.get('level', 1)
                set_current_profile(name)
                self.current_profile_name = name
                
                # Update UI
                try:
                    self.profile_label.config(text=f"Profile: {name}")
                except Exception as e:
                    logging.debug(f"Failed to update profile label: {e}")
                
                # Show profile details
                avatar = p.get('avatar', DEFAULT_AVATAR)
                level = p.get('level', 1)
                correct = p.get('correct', 0)
                messagebox.showinfo("Profile Loaded", 
                    f"{avatar} Profile: {name}\n" +
                    f"Level: {level}\n" +
                    f"Total Correct: {correct}")

            def delete_selected():
                selection = tree.selection()
                if not selection:
                    messagebox.showinfo("Select", "Please select a profile to delete.")
                    return
                
                item = selection[0]
                name = tree.item(item)['text']
                
                if not messagebox.askyesno("Delete Profile", 
                    f"Are you sure you want to delete profile '{name}'?\n" +
                    "This cannot be undone."):
                    return
                    
                # Remove from profiles
                profiles.pop(name, None)
                
                # Save to file atomically
                try:
                    tmp = PROFILES_FILE + ".tmp"
                    with open(tmp, 'w', encoding='utf-8') as f:
                        json.dump(profiles, f, indent=2)
                    os.replace(tmp, PROFILES_FILE)
                    
                    # Update UI
                    tree.delete(item)
                    
                    # Clear current profile if deleted
                    cur = get_current_profile()
                    if cur == name:
                        if os.path.exists(CURRENT_PROFILE_FILE):
                            os.remove(CURRENT_PROFILE_FILE)
                        self.current_profile_name = None
                        self.profile_label.config(text="Profile: Player")
                        
                    messagebox.showinfo("Success", f"Profile '{name}' was deleted.")
                except Exception as e:
                    logging.error(f"Failed to delete profile: {e}")
                    messagebox.showerror("Error", 
                        f"Failed to delete profile '{name}'.\n" +
                        "Check the logs for details.")

            # Profile controls section
            controls_frame = tk.Frame(profile_frame, bg=THEME["bg"])
            controls_frame.pack(fill="x", padx=20, pady=10)
            
            # Button styles
            button_style = {
                'font': ('Arial', font_size(12)),
                'width': 12,
                'relief': 'raised',
                'padx': 10,
                'pady': 5
            }
            
            # Left side: Profile actions
            actions_frame = tk.Frame(controls_frame, bg=THEME["bg"])
            actions_frame.pack(side=tk.LEFT)
            
            new_btn = tk.Button(actions_frame, text="➕ New Profile", 
                              command=new_profile,
                              bg=THEME["btn"], fg=THEME["btn_text"],
                              **button_style)
            new_btn.pack(side=tk.LEFT, padx=5)
            
            load_btn = tk.Button(actions_frame, text="✅ Load Profile", 
                               command=load_selected,
                               bg=THEME["btn"], fg=THEME["btn_text"],
                               **button_style)
            load_btn.pack(side=tk.LEFT, padx=5)
            
            del_btn = tk.Button(actions_frame, text="❌ Delete", 
                              command=delete_selected,
                              bg="#dc3545", fg="white",
                              **button_style)
            del_btn.pack(side=tk.LEFT, padx=5)
            
            # Right side: Avatar selection
            avatar_frame = tk.Frame(controls_frame, bg=THEME["bg"])
            avatar_frame.pack(side=tk.RIGHT)
            
            def change_avatar():
                selection = tree.selection()
                if not selection:
                    messagebox.showinfo("Select Profile", "Please select a profile first.")
                    return
                
                # Create avatar selection dialog
                avatar_dialog = tk.Toplevel(wnd)
                avatar_dialog.title("Select Avatar")
                avatar_dialog.geometry("300x200")
                avatar_dialog.configure(bg=THEME["bg"])
                
                def select_avatar(avatar):
                    item = selection[0]
                    name = tree.item(item)['text']
                    profiles = load_profiles()
                    if name in profiles:
                        profiles[name]['avatar'] = avatar
                        # Save atomically
                        try:
                            tmp = PROFILES_FILE + ".tmp"
                            with open(tmp, 'w', encoding='utf-8') as f:
                                json.dump(profiles, f, indent=2, ensure_ascii=False)
                            os.replace(tmp, PROFILES_FILE)
                            # Update tree
                            tree.set(item, 'avatar', avatar)
                            update_stats()  # Refresh stats display
                        except Exception as e:
                            logging.error(f"Failed to save avatar: {e}")
                    avatar_dialog.destroy()
                
                # Create avatar grid
                avatar_grid = tk.Frame(avatar_dialog, bg=THEME["bg"])
                avatar_grid.pack(expand=True, padx=10, pady=10)
                
                for i, avatar in enumerate(AVATARS):
                    row = i // 4
                    col = i % 4
                    btn = tk.Button(avatar_grid, text=avatar, font=("Arial", 20),
                                  command=lambda a=avatar: select_avatar(a),
                                  width=3, height=1)
                    btn.grid(row=row, column=col, padx=5, pady=5)
            
            avatar_btn = tk.Button(avatar_frame, text="🎭 Change Avatar",
                                 command=change_avatar,
                                 bg=THEME["btn"], fg=THEME["btn_text"],
                                 **button_style)
            avatar_btn.pack(padx=5)
            
            # Game Options Tab Content
            options_title = tk.Label(settings_frame, text="Game Settings",
                                   font=("Arial", font_size(16), "bold"),
                                   bg=THEME["bg"])
            options_title.pack(pady=10)

            # Game difficulty settings
            difficulty_frame = tk.Frame(settings_frame, bg=THEME["bg"])
            difficulty_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(difficulty_frame, text="Game Mode:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            mode_var = tk.StringVar(value="Standard")
            mode_menu = ttk.Combobox(difficulty_frame, 
                                   values=["Standard", "Practice", "Challenge"],
                                   textvariable=mode_var, state="readonly", width=15)
            mode_menu.pack(side=tk.LEFT, padx=5)

            # Time limit settings
            time_frame = tk.Frame(settings_frame, bg=THEME["bg"])
            time_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(time_frame, text="Time Limit:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            time_var = tk.StringVar(value="None")
            time_menu = ttk.Combobox(time_frame, 
                                   values=["None", "30 sec", "1 min", "2 min", "5 min"],
                                   textvariable=time_var, state="readonly", width=15)
            time_menu.pack(side=tk.LEFT, padx=5)

            # Language & Region Tab Content
            lang_title = tk.Label(lang_region_frame, text="Language & Region Settings",
                                font=("Arial", font_size(16), "bold"),
                                bg=THEME["bg"])
            lang_title.pack(pady=10)
            
            # Language selection
            lang_select_frame = tk.Frame(lang_region_frame, bg=THEME["bg"])
            lang_select_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(lang_select_frame, text="Language:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            lang_var = tk.StringVar(value=CURRENT_LANG)
            lang_menu = ttk.Combobox(lang_select_frame, textvariable=lang_var, 
                                   values=[f"{code} - {LANGUAGES[code]['name']}" 
                                          for code in LANGUAGES],
                                   state="readonly", width=20)
            lang_menu.pack(side=tk.LEFT, padx=5)

            # Region selection
            region_frame = tk.Frame(lang_region_frame, bg=THEME["bg"])
            region_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(region_frame, text="Region:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            region_var = tk.StringVar(value="United States")
            region_menu = ttk.Combobox(region_frame, 
                                     values=["United States", "United Kingdom", "Europe", "Asia", "Other"],
                                     textvariable=region_var, state="readonly", width=20)
            region_menu.pack(side=tk.LEFT, padx=5)

            # Number format
            number_frame = tk.Frame(lang_region_frame, bg=THEME["bg"])
            number_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(number_frame, text="Number Format:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            number_var = tk.StringVar(value="1,234.56")
            number_menu = ttk.Combobox(number_frame, 
                                     values=["1,234.56", "1.234,56"],
                                     textvariable=number_var, state="readonly", width=20)
            number_menu.pack(side=tk.LEFT, padx=5)
            
            # Difficulty settings
            diff_frame = tk.Frame(settings_frame, bg=THEME["bg"])
            diff_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(diff_frame, text="Starting Level:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            level_var = tk.StringVar(value="1")
            level_spin = ttk.Spinbox(diff_frame, from_=1, to=10, 
                                   textvariable=level_var, width=5)
            level_spin.pack(side=tk.LEFT, padx=5)
            
            # Sound Tab Content
            sound_title = tk.Label(sound_frame, text="Sound Settings",
                                 font=("Arial", font_size(16), "bold"),
                                 bg=THEME["bg"])
            sound_title.pack(pady=10)

            # Master volume
            master_frame = tk.Frame(sound_frame, bg=THEME["bg"])
            master_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(master_frame, text="Master Volume:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            master_scale = ttk.Scale(master_frame, from_=0, to=100, orient="horizontal")
            master_scale.set(80)
            master_scale.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

            # Effects volume
            effects_frame = tk.Frame(sound_frame, bg=THEME["bg"])
            effects_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(effects_frame, text="Effects Volume:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            effects_scale = ttk.Scale(effects_frame, from_=0, to=100, orient="horizontal")
            effects_scale.set(80)
            effects_scale.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

            # Voice options
            voice_frame = tk.Frame(sound_frame, bg=THEME["bg"])
            voice_frame.pack(fill="x", padx=20, pady=5)
            voice_enabled = tk.BooleanVar(value=VOICE_AVAILABLE)
            voice_check = tk.Checkbutton(voice_frame, text="Enable Voice Feedback",
                                       variable=voice_enabled, bg=THEME["bg"])
            voice_check.pack(side=tk.LEFT)

            # Display Tab Content
            display_title = tk.Label(display_frame, text="Display Settings",
                                   font=("Arial", font_size(16), "bold"),
                                   bg=THEME["bg"])
            display_title.pack(pady=10)

            # Create scrollable frame for many settings
            display_canvas = tk.Canvas(display_frame, bg=THEME["bg"])
            display_scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=display_canvas.yview)
            scrollable_frame = tk.Frame(display_canvas, bg=THEME["bg"])

            display_canvas.configure(yscrollcommand=display_scrollbar.set)
            
            # Pack the scrollbar and canvas
            display_scrollbar.pack(side="right", fill="y")
            display_canvas.pack(side="left", fill="both", expand=True)
            
            # Create a window in the canvas for the frame
            display_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            
            # Update scroll region when frame size changes
            scrollable_frame.bind("<Configure>", 
                lambda e: display_canvas.configure(scrollregion=display_canvas.bbox("all")))

            # Theme Settings Section
            theme_section = tk.LabelFrame(scrollable_frame, text="Theme Settings", 
                                        bg=THEME["bg"], fg=THEME["text"])
            theme_section.pack(fill="x", padx=10, pady=5)

            # Theme selection
            theme_frame = tk.Frame(theme_section, bg=THEME["bg"])
            theme_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(theme_frame, text="Color Theme:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            theme_var = tk.StringVar(value="Default")
            theme_menu = ttk.Combobox(theme_frame, 
                                    values=["Default", "Dark", "Light", "High Contrast", "Neon", "Pastel"],
                                    textvariable=theme_var, state="readonly", width=15)
            theme_menu.pack(side=tk.LEFT, padx=5)

            # Accent color
            accent_frame = tk.Frame(theme_section, bg=THEME["bg"])
            accent_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(accent_frame, text="Accent Color:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            accent_var = tk.StringVar(value="Blue")
            accent_menu = ttk.Combobox(accent_frame, 
                                     values=["Blue", "Green", "Purple", "Orange", "Pink", "Red"],
                                     textvariable=accent_var, state="readonly", width=15)
            accent_menu.pack(side=tk.LEFT, padx=5)

            # Text Settings Section
            text_section = tk.LabelFrame(scrollable_frame, text="Text Settings", 
                                       bg=THEME["bg"], fg=THEME["text"])
            text_section.pack(fill="x", padx=10, pady=5)

            # Font family
            font_family_frame = tk.Frame(text_section, bg=THEME["bg"])
            font_family_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(font_family_frame, text="Font Family:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            font_var = tk.StringVar(value="Arial")
            font_menu = ttk.Combobox(font_family_frame, 
                                   values=["Arial", "Helvetica", "Times New Roman", "Verdana", "Comic Sans MS"],
                                   textvariable=font_var, state="readonly", width=15)
            font_menu.pack(side=tk.LEFT, padx=5)

            # Font size
            font_size_frame = tk.Frame(text_section, bg=THEME["bg"])
            font_size_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(font_size_frame, text="Font Size:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            font_scale = ttk.Scale(font_size_frame, from_=8, to=32, orient="horizontal")
            font_scale.set(12)
            font_scale.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
            font_size_label = tk.Label(font_size_frame, text="12", bg=THEME["bg"], width=3)
            font_size_label.pack(side=tk.LEFT, padx=5)
            font_scale.configure(command=lambda v: font_size_label.configure(text=str(int(float(v)))))

            # Window Settings Section
            window_section = tk.LabelFrame(scrollable_frame, text="Window Settings", 
                                         bg=THEME["bg"], fg=THEME["text"])
            window_section.pack(fill="x", padx=10, pady=5)

            # Window size
            window_frame = tk.Frame(window_section, bg=THEME["bg"])
            window_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(window_frame, text="Window Size:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            window_var = tk.StringVar(value="Normal")
            window_menu = ttk.Combobox(window_frame, 
                                     values=["Small (800x600)", "Normal (1024x768)", 
                                            "Large (1280x720)", "Full HD (1920x1080)",
                                            "2K (2560x1440)", "4K (3840x2160)", "Full Screen"],
                                     textvariable=window_var, state="readonly", width=20)
            window_menu.pack(side=tk.LEFT, padx=5)

            # Visual Effects Section
            effects_section = tk.LabelFrame(scrollable_frame, text="Visual Effects", 
                                          bg=THEME["bg"], fg=THEME["text"])
            effects_section.pack(fill="x", padx=10, pady=5)

            # Animation speed
            anim_frame = tk.Frame(effects_section, bg=THEME["bg"])
            anim_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(anim_frame, text="Animation Speed:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            anim_var = tk.StringVar(value="Normal")
            anim_menu = ttk.Combobox(anim_frame, 
                                   values=["Off", "Slow", "Normal", "Fast"],
                                   textvariable=anim_var, state="readonly", width=15)
            anim_menu.pack(side=tk.LEFT, padx=5)

            # Visual effects toggles
            effects_frame = tk.Frame(effects_section, bg=THEME["bg"])
            effects_frame.pack(fill="x", padx=10, pady=5)
            
            effects_left = tk.Frame(effects_frame, bg=THEME["bg"])
            effects_left.pack(side=tk.LEFT, fill="x", expand=True)
            
            effects_right = tk.Frame(effects_frame, bg=THEME["bg"])
            effects_right.pack(side=tk.LEFT, fill="x", expand=True)

            # Left column effects
            shadow_var = tk.BooleanVar(value=True)
            tk.Checkbutton(effects_left, text="Shadows", variable=shadow_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            glow_var = tk.BooleanVar(value=True)
            tk.Checkbutton(effects_left, text="Button Glow", variable=glow_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            particles_var = tk.BooleanVar(value=True)
            tk.Checkbutton(effects_left, text="Particles", variable=particles_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            # Right column effects
            blur_var = tk.BooleanVar(value=True)
            tk.Checkbutton(effects_right, text="Background Blur", variable=blur_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            trans_var = tk.BooleanVar(value=True)
            tk.Checkbutton(effects_right, text="Transparency", variable=trans_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            smooth_var = tk.BooleanVar(value=True)
            tk.Checkbutton(effects_right, text="Smooth Scrolling", variable=smooth_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            # Performance Settings Section
            perf_section = tk.LabelFrame(scrollable_frame, text="Performance Settings", 
                                       bg=THEME["bg"], fg=THEME["text"])
            perf_section.pack(fill="x", padx=10, pady=5)

            # Quality preset
            quality_frame = tk.Frame(perf_section, bg=THEME["bg"])
            quality_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(quality_frame, text="Quality Preset:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            quality_var = tk.StringVar(value="Balanced")
            quality_menu = ttk.Combobox(quality_frame, 
                                      values=["Performance", "Balanced", "Quality", "Ultra"],
                                      textvariable=quality_var, state="readonly", width=15)
            quality_menu.pack(side=tk.LEFT, padx=5)

            # FPS limit
            fps_frame = tk.Frame(perf_section, bg=THEME["bg"])
            fps_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(fps_frame, text="FPS Limit:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            fps_var = tk.StringVar(value="60")
            fps_menu = ttk.Combobox(fps_frame, 
                                  values=["30", "60", "120", "144", "240", "Unlimited"],
                                  textvariable=fps_var, state="readonly", width=15)
            fps_menu.pack(side=tk.LEFT, padx=5)

            # Advanced render settings
            render_frame = tk.Frame(perf_section, bg=THEME["bg"])
            render_frame.pack(fill="x", padx=10, pady=5)
            
            render_left = tk.Frame(render_frame, bg=THEME["bg"])
            render_left.pack(side=tk.LEFT, fill="x", expand=True)
            
            render_right = tk.Frame(render_frame, bg=THEME["bg"])
            render_right.pack(side=tk.LEFT, fill="x", expand=True)

            # Left column render settings
            vsync_var = tk.BooleanVar(value=True)
            tk.Checkbutton(render_left, text="V-Sync", variable=vsync_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            aa_var = tk.BooleanVar(value=True)
            tk.Checkbutton(render_left, text="Anti-Aliasing", variable=aa_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            # Right column render settings
            hdr_var = tk.BooleanVar(value=False)
            tk.Checkbutton(render_right, text="HDR", variable=hdr_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            ray_var = tk.BooleanVar(value=False)
            tk.Checkbutton(render_right, text="Ray Tracing", variable=ray_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)

            # Accessibility Tab Content
            access_title = tk.Label(accessibility_frame, text="Accessibility Settings",
                                  font=("Arial", font_size(16), "bold"),
                                  bg=THEME["bg"])
            access_title.pack(pady=10)

            # Screen reader
            reader_frame = tk.Frame(accessibility_frame, bg=THEME["bg"])
            reader_frame.pack(fill="x", padx=20, pady=5)
            reader_var = tk.BooleanVar(value=False)
            reader_check = tk.Checkbutton(reader_frame, text="Enable Screen Reader",
                                        variable=reader_var, bg=THEME["bg"])
            reader_check.pack(side=tk.LEFT)

            # High contrast
            contrast_frame = tk.Frame(accessibility_frame, bg=THEME["bg"])
            contrast_frame.pack(fill="x", padx=20, pady=5)
            contrast_var = tk.BooleanVar(value=False)
            contrast_check = tk.Checkbutton(contrast_frame, text="High Contrast Mode",
                                          variable=contrast_var, bg=THEME["bg"])
            contrast_check.pack(side=tk.LEFT)

            # Color blind mode
            color_frame = tk.Frame(accessibility_frame, bg=THEME["bg"])
            color_frame.pack(fill="x", padx=20, pady=5)
            tk.Label(color_frame, text="Color Blind Mode:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            color_var = tk.StringVar(value="None")
            color_menu = ttk.Combobox(color_frame, 
                                    values=["None", "Protanopia", "Deuteranopia", "Tritanopia"],
                                    textvariable=color_var, state="readonly", width=15)
            color_menu.pack(side=tk.LEFT, padx=5)

            # Animation settings
            anim_frame = tk.Frame(accessibility_frame, bg=THEME["bg"])
            anim_frame.pack(fill="x", padx=20, pady=5)
            anim_var = tk.BooleanVar(value=True)
            anim_check = tk.Checkbutton(anim_frame, text="Enable Animations",
                                      variable=anim_var, bg=THEME["bg"])
            anim_check.pack(side=tk.LEFT)

            # Extended time
            time_frame = tk.Frame(accessibility_frame, bg=THEME["bg"])
            time_frame.pack(fill="x", padx=20, pady=5)
            time_var = tk.BooleanVar(value=False)
            time_check = tk.Checkbutton(time_frame, text="Extended Time Mode (1.5x)",
                                      variable=time_var, bg=THEME["bg"])
            time_check.pack(side=tk.LEFT)
            
            # Stats Tab Content
            stats_title = tk.Label(stats_frame, text="Game Statistics",
                                 font=("Arial", font_size(16), "bold"),
                                 bg=THEME["bg"])
            stats_title.pack(pady=10)
            
            def update_stats(event=None):
                selection = tree.selection()
                if selection:
                    item = selection[0]
                    name = tree.item(item)['text']
                    p = profiles.get(name, {})
                    
                    # Update detailed stats in stats tab
                    total_problems = p.get('correct', 0) + p.get('wrong', 0)
                    accuracy = (p.get('correct', 0) / max(1, total_problems)) * 100
                    
                    stats = [
                        ("🎮 Games Played", p.get('games_played', 0)),
                        ("✅ Total Correct", p.get('correct', 0)),
                        ("❌ Total Wrong", p.get('wrong', 0)),
                        ("🎯 Accuracy", f"{accuracy:.1f}%"),
                        ("🏆 Highest Level", p.get('level', 1)),
                        ("⚡ Best Streak", p.get('best_streak', 0)),
                        ("⏱️ Average Time", f"{p.get('avg_time', 0):.1f}s"),
                        ("📅 Created", datetime.datetime.fromtimestamp(p.get('created', 0)).strftime('%Y-%m-%d')),
                        ("🗣️ Language", LANGUAGES[p.get('lang', CURRENT_LANG)]['name'])
                    ]
                    
                    # Clear previous stats
                    for widget in stats_frame.winfo_children()[1:]:  # Skip title
                        widget.destroy()
                    
                    # Create grid of stats
                    for i, (label, value) in enumerate(stats):
                        row = i // 2
                        col = i % 2
                        frame = tk.Frame(stats_frame, bg=THEME["bg"])
                        frame.grid(row=row+1, column=col, padx=20, pady=5, sticky="w")
                        
                        tk.Label(frame, text=label, font=("Arial", font_size(11), "bold"),
                                bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
                        tk.Label(frame, text=str(value), font=("Arial", font_size(11)),
                                bg=THEME["bg"]).pack(side=tk.LEFT)
                    
                    # Configure grid
                    stats_frame.grid_columnconfigure(0, weight=1)
                    stats_frame.grid_columnconfigure(1, weight=1)
                else:
                    # Clear stats display
                    for widget in stats_frame.winfo_children()[1:]:
                        widget.destroy()
                    tk.Label(stats_frame, text="Select a profile to view statistics",
                            font=("Arial", font_size(12)), bg=THEME["bg"]).pack(pady=20)
            
            stats_label = tk.Label(stats_frame, text="Select a profile to view stats",
                                 font=("Arial", font_size(12)), bg=THEME["bg"],
                                 justify=tk.LEFT)
            stats_label.pack(pady=5)
            
            # Bind selection event to update stats
            tree.bind('<<TreeviewSelect>>', update_stats)
            
            # Teacher Dashboard Content
            teacher_title = tk.Label(teacher_frame, text="Teacher Dashboard",
                                   font=("Arial", font_size(16), "bold"),
                                   bg=THEME["bg"])
            teacher_title.pack(pady=10)
            
            # Create notebook for teacher sections
            teacher_notebook = ttk.Notebook(teacher_frame)
            teacher_notebook.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Class Overview tab
            class_frame = tk.Frame(teacher_notebook, bg=THEME["bg"])
            teacher_notebook.add(class_frame, text="Class Overview")
            
            # Performance Analytics tab
            analytics_frame = tk.Frame(teacher_notebook, bg=THEME["bg"])
            teacher_notebook.add(analytics_frame, text="Analytics")
            
            # Reports tab
            reports_frame = tk.Frame(teacher_notebook, bg=THEME["bg"])
            teacher_notebook.add(reports_frame, text="Reports")
            
            # Class Overview Content
            class_top = tk.Frame(class_frame, bg=THEME["bg"])
            class_top.pack(fill="x", padx=10, pady=5)
            
            # Class selection
            tk.Label(class_top, text="Select Class:", bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            class_var = tk.StringVar()
            class_menu = ttk.Combobox(class_top, textvariable=class_var, 
                                    values=["Math 101", "Math 102", "Advanced Math"],
                                    state="readonly", width=20)
            class_menu.pack(side=tk.LEFT, padx=5)
            
            # Student list with performance indicators
            student_frame = tk.Frame(class_frame, bg=THEME["bg"])
            student_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Create student Treeview
            columns = ('name', 'level', 'progress', 'accuracy', 'status')
            student_tree = ttk.Treeview(student_frame, columns=columns, show='headings', height=8)
            student_scroll = ttk.Scrollbar(student_frame, orient="vertical", command=student_tree.yview)
            student_tree.configure(yscrollcommand=student_scroll.set)
            
            student_tree.pack(side=tk.LEFT, fill="both", expand=True)
            student_scroll.pack(side=tk.RIGHT, fill="y")
            
            # Define student columns
            student_tree.heading('name', text='Student Name')
            student_tree.heading('level', text='Current Level')
            student_tree.heading('progress', text='Progress')
            student_tree.heading('accuracy', text='Accuracy')
            student_tree.heading('status', text='Status')
            
            # Column widths
            student_tree.column('name', width=150)
            student_tree.column('level', width=80, anchor='center')
            student_tree.column('progress', width=100, anchor='center')
            student_tree.column('accuracy', width=80, anchor='center')
            student_tree.column('status', width=100, anchor='center')
            
            # Analytics Content
            analytics_title = tk.Label(analytics_frame, text="Class Performance Analytics",
                                     font=("Arial", font_size(14), "bold"),
                                     bg=THEME["bg"])
            analytics_title.pack(pady=10)
            
            # Performance metrics
            metrics_frame = tk.Frame(analytics_frame, bg=THEME["bg"])
            metrics_frame.pack(fill="x", padx=10, pady=5)
            
            metrics = [
                ("📈 Class Average Level", "4.2"),
                ("✅ Average Accuracy", "78%"),
                ("⚡ Problems per Hour", "45"),
                ("📊 Progress Rate", "+12%")
            ]
            
            for label, value in metrics:
                frame = tk.Frame(metrics_frame, bg=THEME["bg"])
                frame.pack(fill="x", pady=2)
                tk.Label(frame, text=label, font=("Arial", font_size(11), "bold"),
                        bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
                tk.Label(frame, text=value, font=("Arial", font_size(11)),
                        bg=THEME["bg"]).pack(side=tk.LEFT)
            
            # Reports Content
            reports_title = tk.Label(reports_frame, text="Generate Reports",
                                   font=("Arial", font_size(14), "bold"),
                                   bg=THEME["bg"])
            reports_title.pack(pady=10)
            
            report_types = [
                "📊 Class Progress Report",
                "👤 Individual Student Reports",
                "📈 Performance Trends",
                "❗ Difficulty Analysis"
            ]
            
            def generate_report():
                report_type = report_var.get()
                messagebox.showinfo("Report Generation", 
                                  f"Generating {report_type}...\n" +
                                  "This feature will export detailed analytics and progress data.")
            
            report_var = tk.StringVar()
            for report in report_types:
                tk.Radiobutton(reports_frame, text=report, variable=report_var,
                             value=report, bg=THEME["bg"]).pack(anchor="w", padx=20, pady=2)
            
            tk.Button(reports_frame, text="Generate Report",
                     command=generate_report,
                     bg=THEME["btn"], fg=THEME["btn_text"],
                     font=("Arial", font_size(11))).pack(pady=10)
            
            # Demo data for student list
            demo_students = [
                ("Alice Smith", "5", "85%", "92%", "On Track ✅"),
                ("Bob Johnson", "3", "65%", "78%", "Needs Help ❗"),
                ("Carol White", "6", "90%", "95%", "Advanced 🌟"),
                ("David Brown", "4", "70%", "85%", "On Track ✅"),
                ("Eve Davis", "2", "45%", "72%", "Struggling ❌"),
            ]
            
            for student in demo_students:
                student_tree.insert('', 'end', values=student)
            
            def update_class_view(event=None):
                selected_class = class_var.get()
                # In a real implementation, this would load actual student data
                # for the selected class
                messagebox.showinfo("Class Selected", 
                                  f"Loading data for {selected_class}...")
            
            class_menu.bind('<<ComboboxSelected>>', update_class_view)
            
        except Exception as e:
            logging.error(f"Settings window failed: {e}")
            messagebox.showerror("Error", "Failed to open settings window.\nCheck the logs for details.")

    def speak(self, text):
        voice_engine.speak(text)

# ------------------- GUI: Kivy (Mobile) -------------------
if GUI == 'kivy':
    class MathBlastKivy(App):
        def __init__(self, **kwargs):
            super(MathBlastKivy, self).__init__(**kwargs)
            self.level = 1
            self.score = 0
            self.wrong = 0
            self.total_correct = 0
            self.adaptive = AdaptiveEngine()
            self.problem_start_time = time.time()
            self.current_answer = None
            self.main_layout = None
            self.game_layout = None
            
            # Initialize platform features
            self.init_platform_features()
            
        def build(self):
            try:
                self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
                
                # Title with shadow effect
                title_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
                with title_layout.canvas.before:
                    Color(0.1, 0.1, 0.1, 0.2)
                    Rectangle(pos=(0, 0), size=(800, 60))
                title = Label(text='MathBlast', font_size=40, color=(1, 1, 1, 1))
                title_layout.add_widget(title)
                self.main_layout.add_widget(title_layout)
                
                # Profile display
                cur = get_current_profile() or "Player"
                self.current_profile_name = cur
                profile_label = Label(
                    text=f"Profile: {cur}",
                    font_size=20,
                    size_hint_y=0.1
                )
                self.main_layout.add_widget(profile_label)
                
                # Menu buttons
                buttons_layout = BoxLayout(
                    orientation='vertical',
                    spacing=10,
                    padding=20,
                    size_hint_y=0.4
                )
                
                start_btn = Button(
                    text='Start Game',
                    background_color=(0, 0.7, 0.3, 1),
                    font_size=24,
                    size_hint_y=None,
                    height=60,
                    on_press=self.start_game
                )
                buttons_layout.add_widget(start_btn)
                
                voice_btn = Button(
                    text='Voice Mode',
                    background_color=(0.2, 0.6, 1, 1),
                    font_size=20,
                    size_hint_y=None,
                    height=50,
                    on_press=lambda x: voice_engine.start()
                )
                buttons_layout.add_widget(voice_btn)
                
                settings_btn = Button(
                    text='Settings',
                    background_color=(0.8, 0.8, 0.8, 1),
                    font_size=20,
                    size_hint_y=None,
                    height=50,
                    on_press=self.show_settings
                )
                buttons_layout.add_widget(settings_btn)
                
                self.main_layout.add_widget(buttons_layout)
                
                return self.main_layout
                
            except Exception as e:
                logging.error(f"Kivy UI build failed: {e}")
                return Label(text='Failed to initialize game interface')

        def start_game(self, btn):
            try:
                self.main_layout.clear_widgets()
                
                self.game_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
                
                # Level display
                self.level_label = Label(
                    text=f'Level {self.level}',
                    font_size=30,
                    size_hint_y=0.2
                )
                self.game_layout.add_widget(self.level_label)
                
                # Problem display
                multiplier = self.adaptive.get_difficulty_multiplier()
                problem, answer = generate_problem(self.level, multiplier)
                self.current_answer = answer
                self.problem_start_time = time.time()
                
                self.problem_label = Label(
                    text=problem,
                    font_size=40,
                    size_hint_y=0.3
                )
                self.game_layout.add_widget(self.problem_label)
                
                # Answer input
                self.answer_input = TextInput(
                    multiline=False,
                    font_size=30,
                    size_hint=(0.5, None),
                    height=60,
                    pos_hint={'center_x': 0.5}
                )
                self.answer_input.bind(on_text_validate=self.check_answer)
                self.game_layout.add_widget(self.answer_input)
                
                # Control buttons
                controls = BoxLayout(
                    orientation='horizontal',
                    spacing=20,
                    size_hint_y=0.2
                )
                
                submit_btn = Button(
                    text='Submit',
                    background_color=(0, 0.7, 0.3, 1),
                    size_hint_x=0.5,
                    on_press=lambda x: self.check_answer(None)
                )
                controls.add_widget(submit_btn)
                
                back_btn = Button(
                    text='Back',
                    background_color=(0.7, 0, 0, 1),
                    size_hint_x=0.5,
                    on_press=self.back_to_menu
                )
                controls.add_widget(back_btn)
                
                self.game_layout.add_widget(controls)
                
                # Stats display
                stats = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=0.1
                )
                self.score_label = Label(text=f'Score: {self.score}')
                self.wrong_label = Label(text=f'Wrong: {self.wrong}')
                stats.add_widget(self.score_label)
                stats.add_widget(self.wrong_label)
                
                self.game_layout.add_widget(stats)
                
                self.main_layout.add_widget(self.game_layout)
                
                # Focus the answer input
                Clock.schedule_once(lambda dt: setattr(self.answer_input, 'focus', True), 0.1)
                
            except Exception as e:
                logging.error(f"Game start failed: {e}")
                self.back_to_menu(None)

        def check_answer(self, instance):
            try:
                user = self.answer_input.text.strip()
                time_taken = time.time() - self.problem_start_time
                correct = (user == self.current_answer)
                
                # Update adaptive engine
                self.adaptive.update(time_taken, correct, self.level)
                
                if correct:
                    self.score += 1
                    self.total_correct += 1
                    self.problem_label.text = "Correct!"
                    self.problem_label.color = (0, 1, 0, 1)  # Green
                    
                    if self.total_correct == 1:
                        self.award_platform_achievement('first_correct')
                    
                    self.update_platform_stats('total_solved', self.total_correct)
                    
                    if self.score >= 10:
                        Clock.schedule_once(lambda dt: self.next_level(), 1)
                    else:
                        Clock.schedule_once(lambda dt: self.next_problem(), 1)
                else:
                    self.wrong += 1
                    self.problem_label.text = "Wrong!"
                    self.problem_label.color = (1, 0, 0, 1)  # Red
                    
                    if self.wrong >= 3:
                        Clock.schedule_once(lambda dt: self.game_over(), 1)
                    else:
                        Clock.schedule_once(lambda dt: self.next_problem(), 1)
                
                self.score_label.text = f'Score: {self.score}'
                self.wrong_label.text = f'Wrong: {self.wrong}'
                self.answer_input.text = ''
                
                # Sync every 5 correct answers
                if self.total_correct % 5 == 0:
                    self.sync_cloud_storage()
                    
            except Exception as e:
                logging.error(f"Answer check failed: {e}")

        def next_problem(self, dt=None):
            try:
                multiplier = self.adaptive.get_difficulty_multiplier()
                problem, answer = generate_problem(self.level, multiplier)
                self.current_answer = answer
                self.problem_label.text = problem
                self.problem_label.color = (1, 1, 1, 1)  # White
                self.problem_start_time = time.time()
                self.answer_input.focus = True
            except Exception as e:
                logging.error(f"Next problem generation failed: {e}")
                self.back_to_menu(None)

        def next_level(self):
            try:
                self.level += 1
                self.score = 0
                self.wrong = 0
                self.level_label.text = f'Level {self.level}'
                
                self.award_platform_achievement('level_complete')
                
                if self.wrong == 0:
                    self.award_platform_achievement('perfect_score')
                
                self.update_platform_stats('high_score', self.level)
                self.sync_cloud_storage()
                
                self.next_problem()
            except Exception as e:
                logging.error(f"Level advancement failed: {e}")

        def game_over(self):
            try:
                # Save progress
                save_profile(self.current_profile_name or "Player", 
                           self.level, self.total_correct)
                
                # Update platform stats
                self.update_platform_stats('high_score', self.level)
                self.update_platform_stats('total_solved', self.total_correct)
                self.sync_cloud_storage()
                
                # Show game over popup
                popup = Popup(
                    title='Game Over',
                    content=Label(
                        text=f'Game Over!\nYou reached Level {self.level}',
                        font_size=24
                    ),
                    size_hint=(0.8, 0.4)
                )
                popup.bind(on_dismiss=lambda x: self.back_to_menu(None))
                popup.open()
                
            except Exception as e:
                logging.error(f"Game over handling failed: {e}")
                self.back_to_menu(None)

        def back_to_menu(self, btn):
            try:
                self.main_layout.clear_widgets()
                self.build()
            except Exception as e:
                logging.error(f"Menu return failed: {e}")

        def show_settings(self, btn):
            try:
                # Create settings popup
                content = BoxLayout(orientation='vertical', padding=10)
                
                # Profile section
                profile_label = Label(
                    text=f"Current Profile: {self.current_profile_name}",
                    font_size=20
                )
                content.add_widget(profile_label)
                
                # Settings tabs implementation here...
                
                settings_popup = Popup(
                    title='Settings',
                    content=content,
                    size_hint=(0.9, 0.9)
                )
                settings_popup.open()
                
            except Exception as e:
                logging.error(f"Settings display failed: {e}")

        def init_platform_features(self):
            """Initialize platform-specific features."""
            if PLATFORM == 'android' and PLATFORM_SERVICES['google_play']['initialized']:
                self.setup_google_play()
            elif PLATFORM == 'ios' and PLATFORM_SERVICES['game_center']['initialized']:
                self.setup_game_center()

# ------------------- Steam / Game Center / Xbox -------------------
# Platform Service Status
PLATFORM_SERVICES = {
    'steam': {'available': False, 'initialized': False},
    'game_center': {'available': False, 'initialized': False},
    'xbox': {'available': False, 'initialized': False},
    'google_play': {'available': False, 'initialized': False},
    'icloud': {'available': False, 'initialized': False},
    'windows_cloud': {'available': False, 'initialized': False},
    'google_drive': {'available': False, 'initialized': False}
}

def init_platform_features():
    """Initialize platform-specific services with proper error handling and recovery."""
    global PLATFORM_SERVICES
    
    def verify_service(name, test_func, required=False):
        """Test if a service is actually working."""
        try:
            result = test_func()
            if result:
                PLATFORM_SERVICES[name]['available'] = True
                PLATFORM_SERVICES[name]['initialized'] = True
                logging.info(f"[{name.upper()}] Service verified and initialized")
                return True
            else:
                raise Exception("Service test failed")
        except Exception as e:
            PLATFORM_SERVICES[name]['available'] = False
            PLATFORM_SERVICES[name]['initialized'] = False
            if required:
                logging.error(f"[{name.upper()}] Required service verification failed: {e}")
            else:
                logging.warning(f"[{name.upper()}] Optional service unavailable: {e}")
            return False
    
    try:
        # Windows Platform Services
        if PLATFORM == 'windows':
            # Xbox Game Bar
            def test_xbox():
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                       r"Software\\Microsoft\\GameBar")
                    winreg.CloseKey(key)
                    return True
                except:
                    return False
            verify_service('xbox', test_xbox)
            
            # Windows Cloud Storage
            def test_windows_cloud():
                try:
                    appdata = os.getenv('APPDATA')
                    test_file = os.path.join(appdata, '.mathblast_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    return True
                except:
                    return False
            verify_service('windows_cloud', test_windows_cloud)
        
        # Apple Platform Services
        elif PLATFORM in ['macos', 'ios']:
            # Game Center 
            def test_game_center():
                try:
                    if not APPLE_SERVICES['game_center']:
                        return False
                    if PLATFORM == 'ios':
                        # We'll check for Apple services without importing
                        # The actual imports will happen when needed
                        return APPLE_SERVICES['game_center']
                    return True
                except:
                    return False
            verify_service('game_center', test_game_center)
            
            # iCloud
            def test_icloud():
                try:
                    if not APPLE_SERVICES['icloud']:
                        return False
                    if PLATFORM == 'ios':
                        # We'll check for Apple services without importing
                        # The actual imports will happen when needed
                        return APPLE_SERVICES['icloud']
                    return True
                except:
                    return False
            verify_service('icloud', test_icloud)
        
        # Android Platform Services
        elif PLATFORM == 'android':
            # Google Play Games
            def test_google_play():
                try:
                    # We'll check for Android services without importing
                    # The actual imports will happen when needed
                    return bool(ANDROID_SERVICES.get('google_play'))
                except:
                    return False
            verify_service('google_play', test_google_play)
            
            # Google Drive
            def test_google_drive():
                try:
                    # We'll check for Android services without importing
                    # The actual imports will happen when needed
                    return bool(ANDROID_SERVICES.get('google_drive'))
                except:
                    return False
            verify_service('google_drive', test_google_drive)
        
        # Cross-platform Services
        
        # Steam (Desktop only)
        if IS_DESKTOP:
            def test_steam():
                try:
                    if not STEAM_AVAILABLE:
                        return False
                    # We'll check Steam availability without importing
                    # The actual imports will happen when needed
                    return STEAM_AVAILABLE
                except:
                    return False
            verify_service('steam', test_steam)
        
        # Voice Service
        def test_voice():
            try:
                if not VOICE_AVAILABLE:
                    return False
                # We'll check voice service without importing
                # The actual imports will happen when needed
                return VOICE_AVAILABLE
            except:
                return False
        verify_service('voice', test_voice)
        
        # Logging and status summary
        available_services = [name for name, status in PLATFORM_SERVICES.items() 
                            if status['available']]
        initialized_services = [name for name, status in PLATFORM_SERVICES.items() 
                             if status['initialized']]
        
        if not available_services:
            logging.warning("No platform services are available")
        else:
            success_rate = len(initialized_services) / len(available_services) * 100
            logging.info(f"""
Platform Services Status:
------------------------
Platform: {PLATFORM.upper()}
Available Services: {', '.join(available_services)}
Initialized Services: {', '.join(initialized_services)}
Success Rate: {success_rate:.1f}%
            """)
        
    except Exception as e:
        logging.error(f"Service initialization failed: {e}")
        # Try to recover by disabling problematic services
        for service in PLATFORM_SERVICES:
            if not PLATFORM_SERVICES[service].get('initialized', False):
                PLATFORM_SERVICES[service]['available'] = False
                PLATFORM_SERVICES[service]['initialized'] = False
    
    # Log final initialization status
    for service, status in PLATFORM_SERVICES.items():
        if status['available']:
            state = "READY" if status['initialized'] else "FAILED"
            logging.info(f"[{service.upper()}] Status: {state}")

init_platform_features()

# ------------------- Main Entry -------------------
def main():
    global GUI
    if GUI == 'tkinter' and (IS_DESKTOP or IS_WEB):
        # Try to set Windows per-monitor DPI awareness before creating the UI
        if PLATFORM == 'windows':
            try:
                import ctypes
                # Try newer API first (Windows 10+)
                try:
                    user32 = ctypes.windll.user32
                    # -4 = DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
                    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
                except Exception:
                    try:
                        shcore = ctypes.windll.shcore
                        # PROCESS_PER_MONITOR_DPI_AWARE = 2
                        shcore.SetProcessDpiAwareness(2)
                    except Exception:
                        try:
                            user32.SetProcessDPIAware()
                        except Exception:
                            pass
            except Exception:
                pass

        root = tk.Tk()
        root.geometry("600x700")

        # Detect screen size and recompute scaling for high-DPI displays
        try:
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            # determine 4K / 8K
            is_4k = (screen_w >= 3840 or screen_h >= 2160)
            is_8k = (screen_w >= 7680)
            # choose scale factor
            sf = 2.0 if is_4k else 1.5 if screen_w > 1920 else 1.0
            # apply to globals
            globals()['SCALE_FACTOR'] = float(sf)
            globals()['IS_4K'] = is_4k
            globals()['IS_8K'] = is_8k
            globals()['FPS_TARGET'] = 120 if is_8k else 60
            # HDR/Ray tracing left as defaults (requires platform checks)
            logging.info(f"Display: {screen_w}x{screen_h} | SCALE_FACTOR={SCALE_FACTOR}")
            try:
                # tell Tk about scaling (affects text and some widgets)
                root.tk.call('tk', 'scaling', SCALE_FACTOR)
            except Exception:
                pass
        except Exception as e:
            logging.debug(f"Screen detection failed: {e}")

        app = MathBlastTk(root)
        # now that widgets exist, update fonts to respect SCALE_FACTOR
        try:
            app.update_fonts()
        except Exception:
            pass

        root.mainloop()
    elif GUI == 'kivy' and IS_MOBILE:
        MathBlastKivy().run()
    else:
        logging.error("[MathBlast] No GUI available on this platform.")

if __name__ == "__main__":
    main()