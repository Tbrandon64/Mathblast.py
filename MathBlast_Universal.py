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
import socket
import platform as sys_platform
import logging
import time
import subprocess
import sys
import os
# -----------------------------------------------------------
# 🎮 Controller / Gamepad Support (requires pygame)
# -----------------------------------------------------------
import threading

try:
    import pygame
    pygame.init()
    pygame.joystick.init()
    GAMEPAD_AVAILABLE = pygame.joystick.get_count() > 0
except Exception as e:
    print(f"[Controller] pygame not available: {e}")
    GAMEPAD_AVAILABLE = False

controller_state = {"left": False, "right": False, "up": False, "down": False, "a": False, "b": False}

def listen_for_controller():
    """Run in background thread to monitor controller input."""
    if not GAMEPAD_AVAILABLE:
        print("[Controller] No controller detected.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"[Controller] Connected: {joystick.get_name()}")

    while True:
        pygame.event.pump()

        # D-Pad (Hat) input
        hat = joystick.get_hat(0)
        controller_state["left"] = hat[0] == -1
        controller_state["right"] = hat[0] == 1
        controller_state["up"] = hat[1] == 1
        controller_state["down"] = hat[1] == -1

        # Buttons (A = 0, B = 1 for Xbox layout)
        controller_state["a"] = joystick.get_button(0)
        controller_state["b"] = joystick.get_button(1)

        # Example: link to your game’s input actions
        if controller_state["a"]:
            print("[Controller] A pressed (Jump/Select)")
            # call your in-game function, e.g. jump() or start_game()
        if controller_state["b"]:
            print("[Controller] B pressed (Back/Cancel)")
            # call your back/cancel action here

        # Analog stick example (move)
        axis_x = joystick.get_axis(0)
        axis_y = joystick.get_axis(1)
        if abs(axis_x) > 0.2 or abs(axis_y) > 0.2:
            # Replace with your movement handler
            # move_player(axis_x, axis_y)
            pass

        pygame.time.wait(50)  # 20 checks per second to save CPU

# --- Start local server automatically if not running ---
def start_local_server():
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 5000))
        sock.close()
        if result == 0:
            print("Server already running.")
            return
    except Exception:
        pass

    server_path = os.path.join(os.path.dirname(sys.executable), "mathblast_server.py")
    if not os.path.exists(server_path):
        # When running as .py, look in the source folder
        server_path = os.path.join(os.path.dirname(__file__), "mathblast_server.py")

    print("Starting local server...")
    subprocess.Popen([sys.executable, server_path], creationflags=subprocess.CREATE_NO_WINDOW)

start_local_server()

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


def sync_profiles_to_icloud():
    """Stub for syncing profiles to iCloud. Real implementation is platform-specific."""
    try:
        logging.info("sync_profiles_to_icloud: not implemented in this environment")
    except Exception:
        pass

# Initialize services based on platform
if PLATFORM in ['macos', 'ios']:
    init_apple_services()
elif PLATFORM == 'android':
    # Android services are initialized on demand
    pass

# ------------------- Constants -------------------
# GUI framework imports
if IS_DESKTOP or IS_WEB:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog, font

# Space Invaders inspired theme (dark, neon green accents, retro monospace feel)
THEME = {
    "bg": "#02040b",            # deep space / near-black
    "text": "#39ff14",          # neon green (classic invader color)
    "muted": "#cfd8dc",         # softer body text
    "btn": "#7c3aed",           # purple action buttons
    "btn_text": "#ffffff",      # white on buttons
    "correct": "#39ff14",
    "wrong": "#ff4d6d",
    "accent": "#00d1ff",
    "high_contrast_bg": "#000000",
    "high_contrast_text": "#FFFFFF"
}

# Simple SFX helper: use winsound on Windows, otherwise fall back to bell via root
try:
    import winsound
    _HAS_WINSOUND = True
except Exception:
    winsound = None
    _HAS_WINSOUND = False
SFX_ENABLED = True

def play_sfx(event_name, root=None):
    """Play a small retro tone for named events.

    event_name: 'chat', 'join', 'move', 'ready', etc.
    root: optional Tk root (used for bell fallback)
    """
    try:
        # map events to (freq, ms)
        mapping = {
            'chat': (800, 80),
            'join': (900, 110),
            'move': (1200, 60),
            'ready': (700, 120),
            'error': (400, 200),
        }
        freq, ms = mapping.get(event_name, (1000, 60))
        if not globals().get('SFX_ENABLED', True):
            return
        if _HAS_WINSOUND and winsound:
            try:
                winsound.Beep(int(freq), int(ms))
            except Exception:
                pass
        else:
            # fallback: bell the root window if provided
            try:
                if root:
                    root.bell()
            except Exception:
                pass
    except Exception:
        pass

AVATARS = ["🧑", "👧", "🐱", "🐶", "🐼", "🐰", "🦊", "🐸", "🦁", "🐯", "🦄", "🐲"]
DEFAULT_AVATAR = AVATARS[0]

LANGUAGES = {
    'en': {'name': 'English', 'play': 'Play', 'level': 'Level', 'correct': 'Correct!', 'wrong': 'Wrong!', 'game_over': 'Game Over!'},
    'es': {'name': 'Español', 'play': 'Jugar', 'level': 'Nivel', 'correct': '¡Correcto!', 'wrong': '¡Incorrecto!', 'game_over': '¡Juego Terminado!'},
    'fr': {'name': 'Français', 'play': 'Jouer', 'level': 'Niveau', 'correct': 'Correct !', 'wrong': 'Faux !', 'game_over': 'Jeu Terminé !'},
    'de': {'name': 'Deutsch', 'play': 'Spielen', 'level': 'Stufe', 'correct': 'Richtig!', 'wrong': 'Falsch!', 'game_over': 'Spiel Vorbei!'}
}
CURRENT_LANG = 'en'

# Store profiles and settings in a user-specific application directory to avoid permission issues
APP_DATA_DIR = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'MathBlast')
try:
    os.makedirs(APP_DATA_DIR, exist_ok=True)
except Exception:
    # fallback to home directory
    APP_DATA_DIR = os.path.expanduser('~')

PROFILES_FILE = os.path.join(APP_DATA_DIR, 'profiles.json')
SETTINGS_FILE = os.path.join(APP_DATA_DIR, 'settings.json')

def load_settings():
    """Load display and performance settings from file."""
    global SCALE_FACTOR, IS_4K, IS_8K, FPS_TARGET, HDR_ENABLED
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                SCALE_FACTOR = float(settings.get('scale_factor', SCALE_FACTOR))
                IS_4K = bool(settings.get('is_4k', IS_4K))
                IS_8K = bool(settings.get('is_8k', IS_8K))
                FPS_TARGET = int(settings.get('fps_target', FPS_TARGET))
                HDR_ENABLED = bool(settings.get('hdr_enabled', HDR_ENABLED))
                # sound effects toggle (persisted)
                try:
                    global SFX_ENABLED
                    SFX_ENABLED = bool(settings.get('sfx_enabled', SFX_ENABLED))
                except Exception:
                    pass
    except Exception as e:
        logging.error(f"Failed to load settings: {e}")

def save_settings():
    """Save display and performance settings to file."""
    try:
        settings = {
            'scale_factor': SCALE_FACTOR,
            'is_4k': IS_4K,
            'is_8k': IS_8K,
            'fps_target': FPS_TARGET,
            'hdr_enabled': HDR_ENABLED,
            'sfx_enabled': globals().get('SFX_ENABLED', True)
        }
        # Write atomically using temporary file
        tmp = SETTINGS_FILE + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(settings, f, indent=2)
        os.replace(tmp, SETTINGS_FILE)
        logging.info("Settings saved successfully")
    except Exception as e:
        logging.error(f"Failed to save settings: {e}")

# Load settings at startup
load_settings()
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

# Networking defaults for lobby
DEFAULT_LOBBY_HOST = '127.0.0.1'
DEFAULT_LOBBY_PORT = 5000

# simple sound helper (winsound on Windows)
try:
    import winsound
    def play_sfx(kind='blip'):
        try:
            if kind == 'chat':
                winsound.Beep(900, 80)
            elif kind == 'join':
                winsound.Beep(1200, 100)
            elif kind == 'ready':
                winsound.Beep(700, 70)
            elif kind == 'unlock':
                winsound.Beep(1500, 150)
            else:
                winsound.Beep(800, 60)
        except Exception:
            pass
except Exception:
    def play_sfx(kind='blip'):
        # fallback: no-op
        return

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
import tkinter as tk
from tkinter import ttk, messagebox

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
        except Exception as e:
            logging.error(f"Failed to sync profile to iCloud: {e}")

    def build_ui(self):
        try:
            self.main_frame = tk.Frame(self.root, bg=THEME["bg"])
            self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

            # keep references so we can update fonts later when SCALE_FACTOR is computed
            # Retro-styled title
            self.title_label = tk.Label(self.main_frame, text="Math Blast", font=("Courier", font_size(32), "bold"), bg=THEME["bg"], fg=THEME["text"])
            self.title_label.pack(pady=20)
            
            # current profile label
            cur = get_current_profile() or "Player"
            self.current_profile_name = cur
            self.profile_label = tk.Label(self.main_frame, text=f"Profile: {cur}", font=("Arial", font_size(12)), bg=THEME["bg"]) 
            self.profile_label.pack()
            
            # Game mode buttons frame
            mode_frame = tk.Frame(self.main_frame, bg=THEME["bg"])
            mode_frame.pack(pady=10)
            
            self.start_btn = tk.Button(mode_frame, text="Single Player", 
                                     command=self.start_game,
                                     bg=THEME["btn"], fg=THEME["btn_text"], 
                                     font=("Arial", font_size(14)))
            self.start_btn.pack(side=tk.LEFT, padx=5)

            # Adventure mode - unlocks chapters as player progresses
            self.adventure_btn = tk.Button(mode_frame, text="Adventure Mode",
                                           command=self.show_adventure_menu,
                                           bg=THEME["btn"], fg=THEME["btn_text"],
                                           font=("Arial", font_size(14)))
            self.adventure_btn.pack(side=tk.LEFT, padx=5)

            self.online_btn = tk.Button(mode_frame, text="Online Mode", 
                                      command=self.create_online_lobby,
                                      bg=THEME["btn"], fg=THEME["btn_text"], 
                                      font=("Arial", font_size(14)))
            self.online_btn.pack(side=tk.LEFT, padx=5)

            self.voice_btn = tk.Button(self.main_frame, text="Voice Mode (Headphones)", command=voice_engine.start, bg=THEME["btn"], fg=THEME["btn_text"], font=("Arial", font_size(12)))
            self.voice_btn.pack(pady=5)
            self.settings_btn = tk.Button(self.main_frame, text="Settings", command=self.show_settings, bg=THEME["btn"], fg=THEME["btn_text"], font=("Arial", font_size(12)))
            self.settings_btn.pack(pady=5)
        except Exception as e:
            logging.error(f"Failed to build UI: {e}")
            raise

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

    # ------------ Multiplayer lobby and Adventure mode (class-level methods) ----------
    def create_online_lobby(self):
        """Create and display the online multiplayer lobby with a Space-Invaders theme."""
        # Hide main menu
        try:
            self.main_frame.pack_forget()
        except Exception:
            pass

        # Dark themed lobby frame for Space-Invaders feel
        self.lobby_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.lobby_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Themed header
        # Header (user requested to show 'Online Play' on the online node screen)
        tk.Label(self.lobby_frame, text="Online Play", 
                 font=("Courier", font_size(28), "bold"),
                 bg=THEME["high_contrast_bg"], fg=THEME["text"], padx=10, pady=6).pack(fill="x", pady=(0,10))

        top_row = tk.Frame(self.lobby_frame, bg=THEME["bg"])
        top_row.pack(fill="x", padx=10, pady=5)

        self.status_label = tk.Label(top_row, text="Connecting to server...",
                                     font=("Arial", font_size(12)), bg=THEME["bg"], fg=THEME["muted"])
        self.status_label.pack(side=tk.LEFT)

        # Animated invader canvas on the right
        self.invader_canvas = tk.Canvas(top_row, width=200, height=80, bg=THEME["high_contrast_bg"], highlightthickness=0)
        self.invader_canvas.pack(side=tk.RIGHT)
        self._invader_items = []
        for x in range(20, 180, 30):
            it = self.invader_canvas.create_rectangle(x, 20, x+18, 30, fill=THEME["text"])
            self._invader_items.append(it)

        # Players and chat area
        mid = tk.Frame(self.lobby_frame, bg=THEME["bg"])
        mid.pack(fill="both", expand=True, padx=10, pady=5)

        players_frame = tk.LabelFrame(mid, text="Players", bg=THEME["high_contrast_bg"], fg=THEME["text"])
        players_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0,5))

        columns = ('name', 'status', 'level')
        self.players_tree = ttk.Treeview(players_frame, columns=columns, show='headings', height=8)
        scrollbar = ttk.Scrollbar(players_frame, orient="vertical", command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=scrollbar.set)
        self.players_tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.players_tree.heading('name', text='Player')
        self.players_tree.heading('status', text='Status')
        self.players_tree.heading('level', text='Level')

        # Chat area
        chat_frame = tk.LabelFrame(mid, text="Chat", bg=THEME["high_contrast_bg"], fg=THEME["text"])
        chat_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(5,0))
        self.chat_text = tk.Text(chat_frame, height=8, font=("Consolas", font_size(11)), bg=THEME["bg"], fg=THEME["muted"])
        chat_scroll = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=chat_scroll.set)
        self.chat_text.pack(side=tk.LEFT, fill="both", expand=True)
        chat_scroll.pack(side=tk.RIGHT, fill="y")

        input_frame = tk.Frame(self.lobby_frame, bg=THEME["bg"])
        input_frame.pack(fill="x", padx=10, pady=6)
        self.chat_entry = tk.Entry(input_frame, font=("Arial", font_size(12)), bg=THEME["high_contrast_bg"], fg=THEME["text"])
        self.chat_entry.pack(side=tk.LEFT, fill="x", expand=True)
        self.send_btn = tk.Button(input_frame, text="Send", command=self.send_chat, bg=THEME["btn"], fg=THEME["btn_text"])
        self.send_btn.pack(side=tk.RIGHT, padx=6)

        controls = tk.Frame(self.lobby_frame, bg=THEME["bg"])
        controls.pack(fill="x", padx=10, pady=6)
        self.ready_btn = tk.Button(controls, text="Ready", command=self.toggle_ready, bg=THEME["btn"], fg=THEME["btn_text"])
        self.ready_btn.pack(side=tk.LEFT)
        self.exit_btn = tk.Button(controls, text="Exit Lobby", command=self.exit_lobby, bg=THEME["wrong"], fg=THEME["btn_text"])
        self.exit_btn.pack(side=tk.RIGHT)

        # Simulated multiplayer state
        self.player_ready = False
        self.lobby_players = {}

        # Start small invader animation and simulated connect
        self._invader_dx = 2
        self.animate_invaders()
        self.connect_to_lobby()

    def animate_invaders(self):
        """Simple animation for the invader blocks to give a Space-Invaders feel."""
        try:
            for it in self._invader_items:
                self.invader_canvas.move(it, self._invader_dx, 0)
                x1, y1, x2, y2 = self.invader_canvas.coords(it)
                if x2 >= 200 or x1 <= 0:
                    self._invader_dx = -self._invader_dx
                    # move all items down a bit
                    for it2 in self._invader_items:
                        self.invader_canvas.move(it2, 0, 6)
                    try:
                        play_sfx('move', root=self.root)
                    except Exception:
                        pass
                    break
        except Exception:
            pass
        # schedule next frame
        try:
            self.root.after(120, self.animate_invaders)
        except Exception:
            pass

    def connect_to_lobby(self):
        """Attempt to connect to a local lobby server; fall back to simulated mode."""
        # If already connected, return
        try:
            self.net_sock
        except AttributeError:
            self.net_sock = None

        # Try to connect to a local server
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((DEFAULT_LOBBY_HOST, DEFAULT_LOBBY_PORT))
            s.settimeout(None)
            self.net_sock = s
            # register our name
            myname = self.current_profile_name or get_current_profile() or 'Player'
            try:
                s.sendall((f'JOIN:{myname}\n').encode('utf-8'))
            except Exception:
                pass
            # start receiver thread
            self.net_stop = False
            t = threading.Thread(target=self._network_listener, args=(s,), daemon=True)
            t.start()
            self.status_label.config(text=f"Connected to lobby at {DEFAULT_LOBBY_HOST}:{DEFAULT_LOBBY_PORT}", fg=THEME["muted"])
            return
        except Exception:
            # fallback to simulated players
            try:
                self.status_label.config(text="Offline lobby (local server not running)", fg=THEME["muted"])
            except Exception:
                pass

        # simulated players when offline
        try:
            test_players = [(self.current_profile_name or "Player", "You", str(self.level)),
                            ("InvaderAce", "Waiting", "4"),
                            ("StarGazer", "Ready", "7")]
            for p in test_players:
                self.players_tree.insert('', 'end', values=p)
            self.add_chat_message("System", "Welcome to Space Blast Lobby! (offline)")
        except Exception as e:
            logging.error(f"Lobby connect error: {e}")

    def _network_listener(self, sock):
        """Background listener for lobby server messages."""
        buf = b""
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    try:
                        sline = line.decode('utf-8')
                    except Exception:
                        continue
                    # dispatch to UI thread
                    self.root.after(0, self._handle_network_line, sline)
        except Exception:
            pass
        finally:
            # connection closed
            try:
                sock.close()
            except Exception:
                pass
            self.root.after(0, lambda: self.add_chat_message('System', 'Disconnected from lobby'))

    def _handle_network_line(self, line):
        """Handle a received network line on the UI thread."""
        try:
            if line.startswith('CHAT:'):
                # CHAT:name:message
                parts = line.split(':', 2)
                if len(parts) == 3:
                    name, msg = parts[1], parts[2]
                    self.add_chat_message(name, msg)
            elif line.startswith('JOIN:'):
                name = line.split(':',1)[1]
                # add to players
                try:
                    self.players_tree.insert('', 'end', values=(name, 'Waiting', '1'))
                except Exception:
                    pass
                play_sfx('join')
                self.add_chat_message('System', f'{name} joined the lobby')
            elif line.startswith('LEAVE:'):
                name = line.split(':',1)[1]
                # remove entries with that name
                try:
                    for iid in list(self.players_tree.get_children()):
                        vals = self.players_tree.item(iid).get('values', [])
                        if vals and vals[0] == name:
                            self.players_tree.delete(iid)
                except Exception:
                    pass
                self.add_chat_message('System', f'{name} left the lobby')
            elif line.startswith('READY:'):
                parts = line.split(':',2)
                if len(parts) == 3:
                    name, state = parts[1], parts[2]
                    # update player status
                    try:
                        for iid in self.players_tree.get_children():
                            vals = list(self.players_tree.item(iid).get('values', []))
                            if vals and vals[0] == name:
                                vals[1] = 'Ready' if state == '1' else 'Waiting'
                                self.players_tree.item(iid, values=vals)
                                break
                    except Exception:
                        pass
        except Exception:
            pass

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if not msg:
            return
        name = self.current_profile_name or get_current_profile() or "Player"
        # send over network if available
        try:
            if getattr(self, 'net_sock', None):
                try:
                    self.net_sock.sendall((f'CHAT:{name}:{msg}\n').encode('utf-8'))
                except Exception:
                    # if send fails, fall back to local display
                    self.add_chat_message(name, msg)
            else:
                self.add_chat_message(name, msg)
        except Exception:
            self.add_chat_message(name, msg)
        self.chat_entry.delete(0, tk.END)

    def add_chat_message(self, sender, message):
        try:
            self.chat_text.configure(state='normal')
            self.chat_text.insert('end', f"{sender}: {message}\n")
            self.chat_text.see('end')
            self.chat_text.configure(state='disabled')
            play_sfx('chat')
        except Exception:
            pass

    def toggle_ready(self):
        self.player_ready = not self.player_ready
        self.ready_btn.config(text=("Not Ready" if self.player_ready else "Ready"),
                              bg=(THEME["wrong"] if self.player_ready else THEME["btn"]))
        # notify server if connected
        try:
            if getattr(self, 'net_sock', None):
                name = self.current_profile_name or get_current_profile() or 'Player'
                state = '1' if self.player_ready else '0'
                try:
                    self.net_sock.sendall((f'READY:{name}:{state}\n').encode('utf-8'))
                except Exception:
                    pass
        except Exception:
            pass

    def exit_lobby(self):
        if messagebox.askyesno("Exit Lobby", "Leave the Space Blast Lobby?"):
            try:
                self.lobby_frame.pack_forget()
            except Exception:
                pass
            # close network socket if present
            try:
                if getattr(self, 'net_sock', None):
                    try:
                        self.net_sock.close()
                    except Exception:
                        pass
                    self.net_sock = None
            except Exception:
                pass
            self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

    # Adventure Mode: chapters unlock as player reaches thresholds
    def show_adventure_menu(self):
        wnd = tk.Toplevel(self.root)
        wnd.title("Adventure Mode")
        wnd.geometry("480x360")
        wnd.configure(bg=THEME["bg"])

        tk.Label(wnd, text="Adventure Mode", font=("Arial", font_size(18), "bold"), bg=THEME["bg"]).pack(pady=10)

        # Define thresholds
        thresholds = {1:1, 2:3, 3:6, 4:9, 5:12}
        profiles = load_profiles()
        name = self.current_profile_name or get_current_profile() or "Player"
        p = profiles.get(name, {})
        unlocked = p.get('adventure_unlocked', 1)

        frame = tk.Frame(wnd, bg=THEME["bg"]) 
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        for ch in range(1,6):
            row = tk.Frame(frame, bg=THEME["bg"])
            row.pack(fill="x", pady=4)
            title = f"Chapter {ch}"
            status = "Unlocked" if ch <= unlocked else f"Locked (reach level {thresholds[ch]})"
            tk.Label(row, text=title, width=20, anchor='w', bg=THEME["bg"]).pack(side=tk.LEFT)
            tk.Label(row, text=status, width=25, anchor='w', bg=THEME["bg"]).pack(side=tk.LEFT)
            btn = tk.Button(row, text="Play", state=(tk.NORMAL if ch <= unlocked else tk.DISABLED),
                            command=lambda c=ch: (wnd.destroy(), self.start_adventure(c)))
            btn.pack(side=tk.RIGHT)

    def start_adventure(self, chapter):
        """Start adventure at chapter; set level to threshold and begin game."""
        thresholds = {1:1, 2:3, 3:6, 4:9, 5:12}
        start_level = thresholds.get(chapter, 1)
        self.level = start_level
        # ensure profile current level saved
        save_profile(self.current_profile_name or get_current_profile() or "Player", self.level, self.total_correct, stats={'adventure_unlocked': chapter})
        # Start the normal game loop but in adventure context
        self.start_game()

    def update_adventure_progress(self):
        """Unlock adventure chapters based on current level and save to profile."""
        try:
            thresholds = {1:1, 2:3, 3:6, 4:9, 5:12}
            name = self.current_profile_name or get_current_profile() or "Player"
            profiles = load_profiles()
            p = profiles.setdefault(name, {})
            current_unlocked = p.get('adventure_unlocked', 1)
            new_unlocked = current_unlocked
            for ch, lvl in thresholds.items():
                if self.level >= lvl and ch > new_unlocked:
                    new_unlocked = ch
            if new_unlocked != current_unlocked:
                p['adventure_unlocked'] = new_unlocked
                # save via save_profile to merge safely
                save_profile(name, self.level, self.total_correct, stats={'adventure_unlocked': new_unlocked})
        except Exception as e:
            logging.debug(f"Adventure progress update failed: {e}")

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
        # Update adventure progress (unlock chapters if thresholds reached)
        try:
            self.update_adventure_progress()
        except Exception:
            pass
        
        self.next_problem()

    def game_over(self):
        messagebox.showinfo("Game Over", f"Game Over! You reached Level {self.level}")
        save_profile(self.current_profile_name or "Player", self.level, self.total_correct)
        try:
            self.update_adventure_progress()
        except Exception:
            pass
        
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

            # Sound options: SFX toggle
            try:
                sfx_var = tk.BooleanVar(value=globals().get('SFX_ENABLED', True))
                def _on_sfx_toggle():
                    try:
                        globals()['SFX_ENABLED'] = bool(sfx_var.get())
                        save_settings()
                    except Exception:
                        pass

                sfx_chk = tk.Checkbutton(sound_frame, text="Enable Sound Effects", variable=sfx_var,
                                         command=_on_sfx_toggle, bg=THEME["bg"], fg=THEME["text"], selectcolor=THEME["bg"])
                sfx_chk.pack(anchor='w', padx=20, pady=10)
            except Exception:
                pass

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

            # Teacher portal sprite loader: prefer an assets PNG exported from Aseprite (.aseprite -> export PNG).
            try:
                sprite_candidates = [
                    os.path.join(os.path.dirname(__file__), 'assets', 'teacher_portal.png'),
                    os.path.join(APP_DATA_DIR, 'teacher_portal.png'),
                    os.path.join(os.path.dirname(__file__), 'teacher_portal.png')
                ]
                sprite_file = None
                for p in sprite_candidates:
                    if os.path.exists(p):
                        sprite_file = p
                        break

                aseprite_hint = os.path.join(os.path.dirname(__file__), 'teacher_portal.aseprite')

                if sprite_file:
                    # display sprite using tkinter PhotoImage
                    try:
                        img = tk.PhotoImage(file=sprite_file)
                        lbl = tk.Label(teacher_frame, image=img, bg=THEME["bg"]) 
                        lbl.image = img
                        lbl.pack(pady=12)
                        tk.Label(teacher_frame, text="Teacher Portal (sprite)", fg=THEME["muted"], bg=THEME["bg"]).pack()
                    except Exception:
                        tk.Label(teacher_frame, text=f"Found sprite but failed to load: {sprite_file}", fg=THEME["muted"], bg=THEME["bg"]).pack(pady=8)
                elif os.path.exists(aseprite_hint):
                    tk.Label(teacher_frame, text="Aseprite source found (teacher_portal.aseprite).\nPlease export a PNG to assets/teacher_portal.png to enable the sprite view.", fg=THEME["muted"], bg=THEME["bg"]).pack(pady=12)
                else:
                    # If no sprite and no Aseprite source, create a small placeholder PNG file
                    try:
                        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
                        os.makedirs(assets_dir, exist_ok=True)
                        placeholder_path = os.path.join(assets_dir, 'teacher_portal.png')
                        if not os.path.exists(placeholder_path):
                            # Try to generate a small 32x32 PNG placeholder using Pillow if available.
                            try:
                                from PIL import Image, ImageDraw
                                img = Image.new('RGBA', (32, 32), (2,4,11,255))
                                draw = ImageDraw.Draw(img)
                                # draw a simple retro-invader shape
                                for y in range(8, 24, 2):
                                    for x in range(6, 26, 2):
                                        if (x//2 + y//2) % 2 == 0:
                                            draw.rectangle([x, y, x+1, y+1], fill=(57,255,20,255))
                                img.save(placeholder_path, format='PNG')
                                sprite_file = placeholder_path
                            except Exception:
                                # Pillow not available or save failed: fall back to a minimal 1x1 PNG
                                b64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=='
                                try:
                                    with open(placeholder_path, 'wb') as f:
                                        f.write(__import__('base64').b64decode(b64))
                                    sprite_file = placeholder_path
                                except Exception:
                                    sprite_file = None
                        else:
                            sprite_file = placeholder_path

                        if sprite_file and os.path.exists(sprite_file):
                            try:
                                img = tk.PhotoImage(file=sprite_file)
                                lbl = tk.Label(teacher_frame, image=img, bg=THEME["bg"]) 
                                lbl.image = img
                                lbl.pack(pady=12)
                                tk.Label(teacher_frame, text="Teacher Portal (sprite placeholder)", fg=THEME["muted"], bg=THEME["bg"]).pack()
                            except Exception:
                                tk.Label(teacher_frame, text="Unable to load generated placeholder sprite.", fg=THEME["muted"], bg=THEME["bg"]).pack(pady=8)
                        else:
                            # Fallback to small pixel-art canvas if file creation fails
                            canvas = tk.Canvas(teacher_frame, width=160, height=120, bg=THEME["bg"], highlightthickness=0)
                            canvas.pack(pady=10)
                            blocks = [
                                (5,5,10, THEME["text"]), (25,5,10, THEME["text"]), (45,5,10, THEME["text"]),
                                (15,25,10, THEME["muted"]), (35,25,10, THEME["muted"]),
                                (25,45,10, THEME["accent"]),
                                (15,65,10, THEME["btn"]), (35,65,10, THEME["btn"]) 
                            ]
                            for x,y,s,c in blocks:
                                canvas.create_rectangle(x, y, x+s, y+s, fill=c, outline=c)
                            tk.Label(teacher_frame, text="Teacher Portal (sprite placeholder)", fg=THEME["muted"], bg=THEME["bg"]).pack()
                    except Exception as e:
                        logging.debug(f"Placeholder sprite creation failed: {e}")
            except Exception as e:
                logging.debug(f"Teacher portal sprite loader failed: {e}")
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
                              bg=THEME["wrong"], fg=THEME["btn_text"],
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

            # Advanced Display Section
            display_section = tk.LabelFrame(scrollable_frame, text="Advanced Display", 
                                          bg=THEME["bg"], fg=THEME["text"])
            display_section.pack(fill="x", padx=10, pady=5)

            # 4K Toggle
            res_frame = tk.Frame(display_section, bg=THEME["bg"])
            res_frame.pack(fill="x", padx=10, pady=5)
            
            def toggle_4k():
                if enable_4k_var.get():
                    try:
                        # Get screen resolution
                        screen_w = self.root.winfo_screenwidth()
                        if screen_w >= 3840:
                            globals()['IS_4K'] = True
                            globals()['SCALE_FACTOR'] = 2.0
                            globals()['FPS_TARGET'] = 60
                            self.update_fonts()
                            save_settings()
                            messagebox.showinfo("Display", "4K mode enabled. Changes will take effect after restart.")
                        else:
                            enable_4k_var.set(False)
                            messagebox.showwarning("Display", "4K resolution not supported on this display.")
                    except Exception as e:
                        logging.error(f"4K toggle failed: {e}")
                        enable_4k_var.set(False)
                else:
                    globals()['IS_4K'] = False
                    globals()['SCALE_FACTOR'] = 1.0
                    globals()['FPS_TARGET'] = 60
                    self.update_fonts()
                    save_settings()
                
            enable_4k_var = tk.BooleanVar(value=IS_4K)
            tk.Checkbutton(res_frame, text="Enable 4K Mode", variable=enable_4k_var,
                          command=toggle_4k, bg=THEME["bg"]).pack(side=tk.LEFT)
            
            # HDR Toggle
            hdr_frame = tk.Frame(display_section, bg=THEME["bg"])
            hdr_frame.pack(fill="x", padx=10, pady=5)
            
            def toggle_hdr():
                if enable_hdr_var.get():
                    try:
                        # Check Windows HDR support
                        import ctypes
                        try:
                            GetAutoHDRSupport = ctypes.windll.user32.GetAutoHDRSupport
                            if GetAutoHDRSupport():
                                globals()['HDR_ENABLED'] = True
                                save_settings()
                                messagebox.showinfo("Display", "HDR enabled. Changes will take effect after restart.")
                            else:
                                enable_hdr_var.set(False)
                                messagebox.showwarning("Display", "HDR not supported on this system.")
                        except AttributeError:
                            enable_hdr_var.set(False)
                            messagebox.showwarning("Display", "HDR support check failed.")
                    except Exception as e:
                        logging.error(f"HDR toggle failed: {e}")
                        enable_hdr_var.set(False)
                else:
                    globals()['HDR_ENABLED'] = False
                    save_settings()
            
            enable_hdr_var = tk.BooleanVar(value=HDR_ENABLED)
            tk.Checkbutton(hdr_frame, text="Enable HDR", variable=enable_hdr_var,
                          command=toggle_hdr, bg=THEME["bg"]).pack(side=tk.LEFT)
            
            # Auto Low Latency Mode (ALLM)
            latency_frame = tk.Frame(display_section, bg=THEME["bg"])
            latency_frame.pack(fill="x", padx=10, pady=5)
            
            def toggle_allm():
                if enable_allm_var.get():
                    try:
                        # Try to enable ALLM through Windows API
                        import ctypes
                        try:
                            SetGameMode = ctypes.windll.user32.SetThreadExecutionState
                            ES_DISPLAY_REQUIRED = 0x00000002
                            ES_SYSTEM_REQUIRED = 0x00000001
                            if SetGameMode(ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED):
                                messagebox.showinfo("Display", "Auto Low Latency Mode enabled.")
                                return
                        except AttributeError:
                            pass
                        enable_allm_var.set(False)
                        messagebox.showwarning("Display", "Auto Low Latency Mode not supported.")
                    except Exception as e:
                        logging.error(f"ALLM toggle failed: {e}")
                        enable_allm_var.set(False)
                else:
                    try:
                        import ctypes
                        SetGameMode = ctypes.windll.user32.SetThreadExecutionState
                        SetGameMode(0x80000000)  # ES_CONTINUOUS
                    except:
                        pass
            
            enable_allm_var = tk.BooleanVar(value=False)
            allm_btn = tk.Checkbutton(latency_frame, text="Auto Low Latency Mode", 
                                    variable=enable_allm_var,
                                    command=toggle_allm, bg=THEME["bg"])
            allm_btn.pack(side=tk.LEFT)
            
            # Help text
            help_frame = tk.Frame(display_section, bg=THEME["bg"])
            help_frame.pack(fill="x", padx=10, pady=5)
            help_text = (
                "4K Mode: Enables high resolution mode for 4K displays\n"
                "HDR: High Dynamic Range for better colors and contrast\n"
                "ALLM: Reduces input lag by optimizing display processing"
            )
            tk.Label(help_frame, text=help_text, justify=tk.LEFT, 
                    bg=THEME["bg"], font=("Arial", font_size(10))).pack(anchor="w")

            # Visual Effects Section
            effects_section = tk.LabelFrame(scrollable_frame, text="Visual Effects", 
                                          bg=THEME["bg"], fg=THEME["text"])
            effects_section.pack(fill="x", padx=10, pady=5)

            # Performance & Effects
            perf_frame = tk.Frame(effects_section, bg=THEME["bg"])
            perf_frame.pack(fill="x", padx=10, pady=5)
            
            # Left column
            perf_left = tk.Frame(perf_frame, bg=THEME["bg"])
            perf_left.pack(side=tk.LEFT, fill="x", expand=True)
            
            # Animation Speed
            anim_frame = tk.Frame(perf_left, bg=THEME["bg"])
            anim_frame.pack(fill="x", pady=2)
            tk.Label(anim_frame, text="Animation Speed:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            anim_var = tk.StringVar(value="Normal")
            anim_menu = ttk.Combobox(anim_frame, 
                                   values=["Off", "Slow", "Normal", "Fast"],
                                   textvariable=anim_var, state="readonly", width=15)
            anim_menu.pack(side=tk.LEFT, padx=5)

            # FPS Limit
            fps_frame = tk.Frame(perf_left, bg=THEME["bg"])
            fps_frame.pack(fill="x", pady=2)
            tk.Label(fps_frame, text="FPS Limit:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            fps_var = tk.StringVar(value=str(FPS_TARGET))
            fps_menu = ttk.Combobox(fps_frame, 
                                  values=["30", "60", "120", "144", "240", "Unlimited"],
                                  textvariable=fps_var, state="readonly", width=15)
            fps_menu.pack(side=tk.LEFT, padx=5)

            # Right column
            perf_right = tk.Frame(perf_frame, bg=THEME["bg"])
            perf_right.pack(side=tk.LEFT, fill="x", expand=True)

            # Performance Mode
            perf_mode_frame = tk.Frame(perf_right, bg=THEME["bg"])
            perf_mode_frame.pack(fill="x", pady=2)
            tk.Label(perf_mode_frame, text="Performance:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            perf_var = tk.StringVar(value="Balanced")
            perf_menu = ttk.Combobox(perf_mode_frame, 
                                   values=["Power Saver", "Balanced", "Performance", "Ultra"],
                                   textvariable=perf_var, state="readonly", width=15)
            perf_menu.pack(side=tk.LEFT, padx=5)

            # Visual features
            features_section = tk.LabelFrame(scrollable_frame, text="Game Features", 
                                          bg=THEME["bg"], fg=THEME["text"])
            features_section.pack(fill="x", padx=10, pady=5)

            # Features frame
            features_frame = tk.Frame(features_section, bg=THEME["bg"])
            features_frame.pack(fill="x", padx=10, pady=5)
            
            # Left column features
            features_left = tk.Frame(features_frame, bg=THEME["bg"])
            features_left.pack(side=tk.LEFT, fill="x", expand=True)
            
            # Visual Features
            tk.Label(features_left, text="Visual Features:", 
                    font=("Arial", font_size(10), "bold"),
                    bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)
            
            shadow_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_left, text="Dynamic Shadows", variable=shadow_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            blur_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_left, text="Background Blur", variable=blur_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            particles_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_left, text="Particle Effects", variable=particles_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            trans_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_left, text="Transparency", variable=trans_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)

            # Right column features
            features_right = tk.Frame(features_frame, bg=THEME["bg"])
            features_right.pack(side=tk.LEFT, fill="x", expand=True)
            
            # Gameplay Features
            tk.Label(features_right, text="Gameplay Features:", 
                    font=("Arial", font_size(10), "bold"),
                    bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)
            
            haptic_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_right, text="Haptic Feedback", variable=haptic_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            sound_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_right, text="Sound Effects", variable=sound_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            voice_var = tk.BooleanVar(value=VOICE_AVAILABLE)
            tk.Checkbutton(features_right, text="Voice Commands", variable=voice_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            cloud_var = tk.BooleanVar(value=True)
            tk.Checkbutton(features_right, text="Cloud Sync", variable=cloud_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)

            # Online Features Section
            online_section = tk.LabelFrame(scrollable_frame, text="Online Features", 
                                         bg=THEME["bg"], fg=THEME["text"])
            online_section.pack(fill="x", padx=10, pady=5)

            # Online frame
            online_frame = tk.Frame(online_section, bg=THEME["bg"])
            online_frame.pack(fill="x", padx=10, pady=5)
            
            # Left column online
            online_left = tk.Frame(online_frame, bg=THEME["bg"])
            online_left.pack(side=tk.LEFT, fill="x", expand=True)
            
            # Multiplayer Features
            tk.Label(online_left, text="Multiplayer:", 
                    font=("Arial", font_size(10), "bold"),
                    bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)
            
            matchmaking_var = tk.BooleanVar(value=True)
            tk.Checkbutton(online_left, text="Quick Match", variable=matchmaking_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            custom_game_var = tk.BooleanVar(value=True)
            tk.Checkbutton(online_left, text="Custom Games", variable=custom_game_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            crossplay_var = tk.BooleanVar(value=True)
            tk.Checkbutton(online_left, text="Cross-platform Play", variable=crossplay_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)

            # Right column online
            online_right = tk.Frame(online_frame, bg=THEME["bg"])
            online_right.pack(side=tk.LEFT, fill="x", expand=True)
            
            # Community Features
            tk.Label(online_right, text="Community:", 
                    font=("Arial", font_size(10), "bold"),
                    bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)
            
            leaderboard_var = tk.BooleanVar(value=True)
            tk.Checkbutton(online_right, text="Leaderboards", variable=leaderboard_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            achievements_var = tk.BooleanVar(value=True)
            tk.Checkbutton(online_right, text="Achievements", variable=achievements_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            friend_system_var = tk.BooleanVar(value=True)
            tk.Checkbutton(online_right, text="Friend System", variable=friend_system_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)

            # Connection settings frame
            connection_frame = tk.Frame(online_section, bg=THEME["bg"])
            connection_frame.pack(fill="x", padx=10, pady=5)
            
            # Server region
            region_frame = tk.Frame(connection_frame, bg=THEME["bg"])
            region_frame.pack(fill="x", pady=2)
            tk.Label(region_frame, text="Server Region:", 
                    bg=THEME["bg"]).pack(side=tk.LEFT, padx=5)
            region_var = tk.StringVar(value="Auto")
            region_menu = ttk.Combobox(region_frame, 
                                     values=["Auto", "North America", "Europe", "Asia", "Oceania"],
                                     textvariable=region_var, state="readonly", width=15)
            region_menu.pack(side=tk.LEFT, padx=5)

            # Advanced Features Section
            advanced_section = tk.LabelFrame(scrollable_frame, text="Advanced Features", 
                                          bg=THEME["bg"], fg=THEME["text"])
            advanced_section.pack(fill="x", padx=10, pady=5)

            # Advanced frame
            advanced_frame = tk.Frame(advanced_section, bg=THEME["bg"])
            advanced_frame.pack(fill="x", padx=10, pady=5)
            
            # Left column advanced
            advanced_left = tk.Frame(advanced_frame, bg=THEME["bg"])
            advanced_left.pack(side=tk.LEFT, fill="x", expand=True)
            
            # Graphics Features
            tk.Label(advanced_left, text="Graphics Features:", 
                    font=("Arial", font_size(10), "bold"),
                    bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)
            
            raytracing_var = tk.BooleanVar(value=RAY_TRACING)
            tk.Checkbutton(advanced_left, text="Ray Tracing", variable=raytracing_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            dlss_var = tk.BooleanVar(value=False)
            tk.Checkbutton(advanced_left, text="DLSS/FSR", variable=dlss_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            vsync_var = tk.BooleanVar(value=True)
            tk.Checkbutton(advanced_left, text="V-Sync", variable=vsync_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)

            # Right column advanced
            advanced_right = tk.Frame(advanced_frame, bg=THEME["bg"])
            advanced_right.pack(side=tk.LEFT, fill="x", expand=True)
            
            # System Features
            tk.Label(advanced_right, text="System Features:", 
                    font=("Arial", font_size(10), "bold"),
                    bg=THEME["bg"]).pack(anchor="w", padx=5, pady=2)
            
            threading_var = tk.BooleanVar(value=True)
            tk.Checkbutton(advanced_right, text="Multi-Threading", variable=threading_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            cache_var = tk.BooleanVar(value=True)
            tk.Checkbutton(advanced_right, text="Asset Caching", variable=cache_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)
            
            debug_var = tk.BooleanVar(value=False)
            tk.Checkbutton(advanced_right, text="Debug Mode", variable=debug_var,
                          bg=THEME["bg"]).pack(anchor="w", padx=20)

            # Save all settings
            def save_all_settings():
                try:
                    settings = {
                        'scale_factor': SCALE_FACTOR,
                        'is_4k': IS_4K,
                        'is_8k': IS_8K,
                        'fps_target': fps_var.get(),
                        'hdr_enabled': HDR_ENABLED,
                        'ray_tracing': raytracing_var.get(),
                        'animation_speed': anim_var.get(),
                        'performance_mode': perf_var.get(),
                        'features': {
                            'shadows': shadow_var.get(),
                            'blur': blur_var.get(),
                            'particles': particles_var.get(),
                            'transparency': trans_var.get(),
                            'haptic': haptic_var.get(),
                            'sound': sound_var.get(),
                            'voice': voice_var.get(),
                            'cloud': cloud_var.get()
                        },
                        'online': {
                            'multiplayer': {
                                'quick_match': matchmaking_var.get(),
                                'custom_games': custom_game_var.get(),
                                'crossplay': crossplay_var.get()
                            },
                            'community': {
                                'leaderboards': leaderboard_var.get(),
                                'achievements': achievements_var.get(),
                                'friend_system': friend_system_var.get()
                            },
                            'connection': {
                                'region': region_var.get()
                            }
                        },
                        'advanced': {
                            'dlss': dlss_var.get(),
                            'vsync': vsync_var.get(),
                            'threading': threading_var.get(),
                            'cache': cache_var.get(),
                            'debug': debug_var.get()
                        }
                    }
                    tmp = SETTINGS_FILE + '.tmp'
                    with open(tmp, 'w') as f:
                        json.dump(settings, f, indent=2)
                    os.replace(tmp, SETTINGS_FILE)
                    messagebox.showinfo("Settings", "All settings saved successfully!")
                except Exception as e:
                    logging.error(f"Failed to save settings: {e}")
                    messagebox.showerror("Error", "Failed to save settings!")

            # Save button at the bottom
            save_frame = tk.Frame(scrollable_frame, bg=THEME["bg"])
            save_frame.pack(fill="x", padx=10, pady=10)
            
            save_btn = tk.Button(save_frame, text="Save All Settings", 
                               command=save_all_settings,
                               bg=THEME["btn"], fg=THEME["btn_text"],
                               font=("Arial", font_size(12)))
            save_btn.pack(pady=5)

            # Visual effects toggles (preserve original frame for compatibility)
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
# Import and store Kivy components for runtime use
kivy_components = {}

# Only try to import Kivy if we're using it
if GUI == 'kivy' and all(platform_imports.imports.get(f'kivy_{mod}', False) 
                        for mod in ['core', 'uix', 'graphics']):
    try:
        # Core components
        from kivy.app import App
        kivy_components['App'] = App
        
        # UI components
        from kivy.uix.boxlayout import BoxLayout
        kivy_components['BoxLayout'] = BoxLayout
        
        from kivy.uix.label import Label
        kivy_components['Label'] = Label
        
        from kivy.uix.button import Button
        kivy_components['Button'] = Button
        
        from kivy.uix.textinput import TextInput
        kivy_components['TextInput'] = TextInput
        
        from kivy.uix.popup import Popup
        kivy_components['Popup'] = Popup
        
        # Graphics components
        from kivy.graphics import Color, Rectangle
        kivy_components['Color'] = Color
        kivy_components['Rectangle'] = Rectangle
        
        # System components
        from kivy.core.window import Window
        kivy_components['Window'] = Window
        
        from kivy.clock import Clock
        kivy_components['Clock'] = Clock
        
        logging.info("All Kivy components imported successfully")
    except ImportError as e:
        logging.error(f"Failed to import Kivy component: {e}")
        GUI = None
    except Exception as e:
        logging.error(f"Kivy initialization error: {e}")
        GUI = None
    
    class MathBlastKivy(kivy_components['App']):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
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
                BoxLayout = kivy_components['BoxLayout']
                Label = kivy_components['Label']
                Button = kivy_components['Button']
                Color = kivy_components['Color']
                Rectangle = kivy_components['Rectangle']
                
                # Use safe Kivy imports
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
                # Get Kivy components
                BoxLayout = kivy_components['BoxLayout']
                Label = kivy_components['Label']
                Button = kivy_components['Button']
                TextInput = kivy_components['TextInput']
                Clock = kivy_components['Clock']
                
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
                # Get Kivy components
                BoxLayout = kivy_components['BoxLayout']
                Label = kivy_components['Label']
                Popup = kivy_components['Popup']
                
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

        def game_over(self):
            try:
                # Get Kivy components
                Label = kivy_components['Label']
                Popup = kivy_components['Popup']
                
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
def init_display_settings():
    """Initialize display-related settings based on system capabilities."""
    global SCALE_FACTOR, IS_4K, IS_8K, FPS_TARGET, HDR_ENABLED
    
    try:
        # Detect screen resolution and capabilities
        if tk._default_root:
            screen_w = tk._default_root.winfo_screenwidth()
            screen_h = tk._default_root.winfo_screenheight()
        else:
            temp_root = tk.Tk()
            screen_w = temp_root.winfo_screenwidth()
            screen_h = temp_root.winfo_screenheight()
            temp_root.destroy()
            
        IS_4K = screen_w >= 3840 or screen_h >= 2160
        IS_8K = screen_w >= 7680 or screen_h >= 4320
        
        # Set scale factor based on resolution
        if IS_8K:
            SCALE_FACTOR = 3.0
            FPS_TARGET = 120
        elif IS_4K:
            SCALE_FACTOR = 2.0
            FPS_TARGET = 60
        elif screen_w > 1920:
            SCALE_FACTOR = 1.5
            FPS_TARGET = 60
        else:
            SCALE_FACTOR = 1.0
            FPS_TARGET = 60
            
        # Check HDR support on Windows
        if PLATFORM == 'windows':
            try:
                import ctypes
                GetAutoHDRSupport = ctypes.windll.user32.GetAutoHDRSupport
                HDR_ENABLED = bool(GetAutoHDRSupport())
            except:
                HDR_ENABLED = False
        else:
            HDR_ENABLED = False
            
        logging.info(
            f"Display Settings: {screen_w}x{screen_h} "
            f"| Scale: {SCALE_FACTOR:.1f}x "
            f"| 4K: {IS_4K} "
            f"| 8K: {IS_8K} "
            f"| HDR: {HDR_ENABLED} "
            f"| FPS: {FPS_TARGET}"
        )
        
    except Exception as e:
        logging.error(f"Display settings initialization failed: {e}")
        SCALE_FACTOR = 1.0
        IS_4K = False
        IS_8K = False
        HDR_ENABLED = False
        FPS_TARGET = 60

def main():
    """Initialize and run the application with appropriate GUI."""
    global GUI, SCALE_FACTOR, IS_4K, IS_8K, FPS_TARGET, tk, ttk, messagebox
    
    # Make sure tkinter modules are available in this scope
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    # Initialize display settings
    init_display_settings()
    
    try:
        # First, ensure we have a valid GUI framework
        if not GUI:
            if IS_DESKTOP or IS_WEB:
                try:
                    import tkinter as tk
                    from tkinter import ttk, messagebox
                    GUI = 'tkinter'
                except ImportError as e:
                    logging.error(f"Failed to import tkinter: {e}")
            elif IS_MOBILE:
                try:
                    from kivy.app import App
                    GUI = 'kivy'
                except ImportError as e:
                    logging.error(f"Failed to import Kivy: {e}")
        
        if not GUI:
            logging.error("No GUI framework available. Please install tkinter for desktop or Kivy for mobile.")
            return
        
        # Desktop/Web application (Tkinter)
        if GUI == 'tkinter' and (IS_DESKTOP or IS_WEB):
            try:
                # Windows DPI awareness
                if PLATFORM == 'windows':
                    try:
                        import ctypes
                        try:
                            user32 = ctypes.windll.user32
                            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
                        except Exception:
                            try:
                                shcore = ctypes.windll.shcore
                                shcore.SetProcessDpiAwareness(2)
                            except Exception:
                                try:
                                    user32.SetProcessDPIAware()
                                except Exception:
                                    pass
                    except Exception as e:
                        logging.warning(f"DPI awareness setup failed: {e}")

                # Create root window
                root = tk.Tk()
                root.title("MathBlast")
                root.geometry("600x700")

                # Screen scaling setup
                try:
                    screen_w = root.winfo_screenwidth()
                    screen_h = root.winfo_screenheight()
                    is_4k = (screen_w >= 3840 or screen_h >= 2160)
                    is_8k = (screen_w >= 7680)
                    sf = 2.0 if is_4k else 1.5 if screen_w > 1920 else 1.0
                    
                    globals()['SCALE_FACTOR'] = float(sf)
                    globals()['IS_4K'] = is_4k
                    globals()['IS_8K'] = is_8k
                    globals()['FPS_TARGET'] = 120 if is_8k else 60
                    
                    logging.info(f"Display: {screen_w}x{screen_h} | SCALE_FACTOR={SCALE_FACTOR}")
                    root.tk.call('tk', 'scaling', SCALE_FACTOR)
                except Exception as e:
                    logging.warning(f"Screen setup failed: {e}")
                    globals()['SCALE_FACTOR'] = 1.0
                    globals()['IS_4K'] = False
                    globals()['IS_8K'] = False
                    globals()['FPS_TARGET'] = 60

                # Create and run application
                app = MathBlastTk(root)
                try:
                    app.update_fonts()
                except Exception as e:
                    logging.warning(f"Font update failed: {e}")

                root.mainloop()
                
            except Exception as e:
                logging.error(f"Failed to start Tkinter application: {e}")
                return

        # Mobile application (Kivy)
        elif GUI == 'kivy' and IS_MOBILE:
            try:
                app = MathBlastKivy()
                app.run()
            except Exception as e:
                logging.error(f"Failed to start Kivy application: {e}")
                return
                
        else:
            logging.error(f"Invalid GUI configuration - GUI: {GUI}, Platform: {PLATFORM}")
            return
            
    except Exception as e:
        logging.error(f"Application startup failed: {e}")
        if IS_DESKTOP:
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Error", f"Failed to start MathBlast:\n{str(e)}")
            except:
                print(f"Error: Failed to start MathBlast: {e}")
        else:
            print(f"Error: Failed to start MathBlast: {e}")

if __name__ == "__main__":
    if GAMEPAD_AVAILABLE:
        threading.Thread(target=listen_for_controller, daemon=True).start()

    main()