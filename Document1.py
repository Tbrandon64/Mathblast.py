#import modules
import random
import tkinter as tk
from tkinter import ttk
import winsound  # for sound effects
import json
import os  # for file operations
try:
    import requests  # for online features
except Exception:
    requests = None
    logging.warning("requests module not available; online features disabled")
import datetime
import threading
import uuid
import logging
import sys
import time
import ctypes
try:
    import wmi  # for detecting external keyboards
except ImportError:
    # If wmi not available, try to install it
    import subprocess
    try:
        subprocess.check_call(['pip', 'install', 'wmi'])
        import wmi
    except Exception as e:
        logging.warning(f"Could not install wmi module: {e}")
        wmi = None
from pathlib import Path

class LayoutManager:
    def __init__(self, root):
        self.root = root
        self.base_width = 1920  # reference width for scaling
        self.base_height = 1080  # reference height for scaling
        self.min_width = 800
        self.min_height = 600
        self.is_foldable = self._check_foldable_support()
        self.current_orientation = "landscape"
        self.update_screen_info()
        
        # Bind to screen changes
        self.root.bind('<Configure>', self._on_window_configure)
        
    def _check_foldable_support(self):
        """Check if running on a foldable device (Windows 11 feature detection)"""
        try:
            # Try to get Windows build number
            win_ver = sys.getwindowsversion()
            if win_ver.major >= 10:  # Windows 10 or higher
                # Get more detailed version info from Windows API
                class OSVERSIONINFOEXW(ctypes.Structure):
                    _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                              ('dwMajorVersion', ctypes.c_ulong),
                              ('dwMinorVersion', ctypes.c_ulong),
                              ('dwBuildNumber', ctypes.c_ulong),
                              ('dwPlatformId', ctypes.c_ulong),
                              ('szCSDVersion', ctypes.c_wchar * 128),
                              ('wServicePackMajor', ctypes.c_ushort),
                              ('wServicePackMinor', ctypes.c_ushort),
                              ('wSuiteMask', ctypes.c_ushort),
                              ('wProductType', ctypes.c_byte),
                              ('wReserved', ctypes.c_byte)]

                os_version = OSVERSIONINFOEXW()
                os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
                retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
                
                # Check for Windows 11 builds that support foldables
                return os_version.dwBuildNumber >= 22000
        except Exception:
            pass
        return False
        
    def update_screen_info(self):
        """Update screen dimensions and DPI info"""
        try:
            # Get primary screen metrics
            user32 = ctypes.windll.user32
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
            
            # Get DPI awareness - helps with high DPI displays
            awareness = ctypes.c_int()
            errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
            self.dpi_scaling = 1.0
            if errorCode == 0:  # Success
                if awareness.value == 0:  # DPI Unaware
                    self.dpi_scaling = 1.0
                elif awareness.value == 1:  # System DPI Aware
                    self.dpi_scaling = user32.GetDpiForSystem() / 96.0
                else:  # Per Monitor DPI Aware
                    monitor = user32.MonitorFromWindow(self.root.winfo_id(), 0x02)  # MONITOR_DEFAULTTONEAREST
                    dpi_x = ctypes.c_uint()
                    dpi_y = ctypes.c_uint()
                    ctypes.windll.shcore.GetDpiForMonitor(monitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
                    self.dpi_scaling = dpi_x.value / 96.0
        except Exception as e:
            logging.warning(f"Error getting screen metrics: {e}")
            # Fallback to tk's screen dimensions
            self.screen_width = self.root.winfo_screenwidth()
            self.screen_height = self.root.winfo_screenheight()
            self.dpi_scaling = 1.0
            
        # Update orientation
        old_orientation = self.current_orientation
        self.current_orientation = "portrait" if self.screen_height > self.screen_width else "landscape"
        return old_orientation != self.current_orientation
            
    def get_font_size(self, base_size):
        """Scale font size based on screen dimensions and DPI"""
        width_scale = min(1.0, self.screen_width / (self.base_width * self.dpi_scaling))
        height_scale = min(1.0, self.screen_height / (self.base_height * self.dpi_scaling))
        scale = min(width_scale, height_scale)
        return max(8, int(base_size * scale))  # minimum 8pt font
        
    def get_widget_size(self, base_width, base_height=None):
        """Scale widget dimensions"""
        if base_height is None:
            base_height = base_width
            
        width_scale = min(1.0, self.screen_width / self.base_width)
        height_scale = min(1.0, self.screen_height / self.base_height)
        
        width = max(50, int(base_width * width_scale))
        height = max(50, int(base_height * height_scale))
        return width, height
        
    def _on_window_configure(self, event=None):
        """Handle window resize events"""
        if event and event.widget == self.root:
            orientation_changed = self.update_screen_info()
            if orientation_changed and hasattr(self, 'on_orientation_change'):
                self.on_orientation_change(self.current_orientation)

# Touch screen and virtual keyboard support
class TouchScreenManager:
    def __init__(self, root):
        self.root = root
        self.touch_enabled = self._check_touch_support()
        self.virtual_kbd = None
        self.current_entry = None
        self.gesture_start = None
        self.last_tap_time = 0
        self.external_kbd_connected = False
        
        # Start keyboard detection
        self._check_external_keyboard()
        # Set up periodic check for keyboard changes
        self._schedule_kbd_check()
        
    def _check_touch_support(self):
        """Check if device supports touch input"""
        try:
            # Check Windows touch point capabilities
            user32 = ctypes.windll.user32
            touch_points = user32.GetSystemMetrics(95)  # SM_MAXIMUMTOUCHES
            return touch_points > 0
        except Exception:
            return False
            
    def _check_external_keyboard(self):
        """Check for external keyboards (Bluetooth or USB)"""
        try:
            if 'wmi' in sys.modules:  # If WMI is available, use it for detailed detection
                c = wmi.WMI()
                
                # Count connected keyboards (both USB and Bluetooth)
                keyboards = c.Win32_Keyboard()
                bt_devices = c.Win32_PnPEntity(PNPClass="Bluetooth")
                
                # Check for Bluetooth HID devices (keyboards)
                bt_kbd_count = sum(1 for dev in bt_devices 
                                 if "keyboard" in dev.Name.lower() or 
                                    "input device" in dev.Name.lower())
                                    
                # Check USB keyboards (excluding built-in laptop keyboard)
                usb_kbd_count = sum(1 for kbd in keyboards 
                                  if "usb" in kbd.Name.lower() or
                                     "bluetooth" in kbd.Name.lower())
                                     
                has_external = (bt_kbd_count > 0) or (usb_kbd_count > 1)
            else:
                # Fallback: Check Windows API for connected devices
                try:
                    # Use GetRawInputDeviceList to count keyboards
                    class RAWINPUTDEVICELIST(ctypes.Structure):
                        _fields_ = [
                            ("hDevice", ctypes.c_void_p),
                            ("dwType", ctypes.c_uint32)
                        ]

                    GetRawInputDeviceList = ctypes.windll.user32.GetRawInputDeviceList
                    devices = (RAWINPUTDEVICELIST * 256)()
                    device_count = ctypes.c_uint32(256)
                    size = ctypes.sizeof(RAWINPUTDEVICELIST)
                    
                    GetRawInputDeviceList(ctypes.byref(devices), 
                                        ctypes.byref(device_count), 
                                        size)
                                        
                    # Type 1 is RIM_TYPEKEYBOARD
                    kbd_count = sum(1 for d in devices[:device_count.value] 
                                  if d.dwType == 1)
                    
                    # If more than one keyboard detected (built-in + external)
                    has_external = kbd_count > 1
                    
                except Exception:
                    # If Windows API call fails, assume no external keyboard
                    has_external = False
            
            old_state = self.external_kbd_connected
            self.external_kbd_connected = has_external
            
            # Log keyboard connection changes
            if old_state != self.external_kbd_connected:
                if self.external_kbd_connected:
                    logging.info("External keyboard connected - disabling virtual keyboard")
                    self.hide_keyboard()  # Hide virtual keyboard if showing
                else:
                    logging.info("External keyboard disconnected - virtual keyboard enabled")
                    
        except Exception as e:
            logging.warning(f"Error checking keyboards: {e}")
            # Default to not blocking virtual keyboard on error
            self.external_kbd_connected = False
            
    def _schedule_kbd_check(self):
        """Schedule periodic checks for keyboard connection changes"""
        # Check every 5 seconds for keyboard changes
        self._check_external_keyboard()
        self.root.after(5000, self._schedule_kbd_check)
            
    def create_virtual_keyboard(self, numeric_only=False):
        """Create virtual keyboard window"""
        if self.virtual_kbd:
            self.virtual_kbd.destroy()
            
        self.virtual_kbd = tk.Toplevel(self.root)
        self.virtual_kbd.overrideredirect(True)  # No window decorations
        self.virtual_kbd.attributes('-topmost', True)  # Stay on top
        
        # Use a dark theme for keyboard
        self.virtual_kbd.configure(bg='#2d2d2d')
        
        if numeric_only:
            self._create_numeric_keyboard()
        else:
            self._create_full_keyboard()
            
    def _create_numeric_keyboard(self):
        """Create numeric keypad layout"""
        keys_frame = tk.Frame(self.virtual_kbd, bg='#2d2d2d')
        keys_frame.pack(padx=5, pady=5)
        
        # Number pad layout
        num_keys = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['.', '0', '⌫']  # Backspace
        ]
        
        for row in num_keys:
            frame = tk.Frame(keys_frame, bg='#2d2d2d')
            frame.pack()
            for key in row:
                cmd = lambda x=key: self._press_key(x)
                btn = tk.Button(frame, text=key, width=5, height=2,
                              font=('Arial', 18),
                              bg='#3d3d3d', fg='white',
                              activebackground='#4d4d4d',
                              command=cmd)
                btn.pack(side=tk.LEFT, padx=2, pady=2)
                
        # Add done button
        tk.Button(self.virtual_kbd, text='Done', width=20, height=2,
                 font=('Arial', 14),
                 bg='#007acc', fg='white',
                 activebackground='#1a8cdd',
                 command=self.hide_keyboard).pack(pady=5)
                
    def _create_full_keyboard(self):
        """Create full alphanumeric keyboard layout"""
        keys_frame = tk.Frame(self.virtual_kbd, bg='#2d2d2d')
        keys_frame.pack(padx=5, pady=5)
        
        # Standard QWERTY layout
        key_rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['⇧', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '⌫']
        ]
        
        self.shift_on = False
        for row in key_rows:
            frame = tk.Frame(keys_frame, bg='#2d2d2d')
            frame.pack()
            for key in row:
                cmd = lambda x=key: self._press_key(x)
                btn = tk.Button(frame, text=key, width=4, height=2,
                              font=('Arial', 14),
                              bg='#3d3d3d', fg='white',
                              activebackground='#4d4d4d',
                              command=cmd)
                btn.pack(side=tk.LEFT, padx=2, pady=2)
                
        # Spacebar and done
        tk.Button(keys_frame, text='Space', width=30, height=2,
                 font=('Arial', 14),
                 bg='#3d3d3d', fg='white',
                 activebackground='#4d4d4d',
                 command=lambda: self._press_key(' ')).pack(pady=2)
                 
        tk.Button(self.virtual_kbd, text='Done', width=20, height=2,
                 font=('Arial', 14),
                 bg='#007acc', fg='white',
                 activebackground='#1a8cdd',
                 command=self.hide_keyboard).pack(pady=5)
                
    def _press_key(self, key):
        """Handle virtual key press"""
        if not self.current_entry:
            return
            
        if key == '⌫':  # Backspace
            self.current_entry.delete(len(self.current_entry.get())-1, tk.END)
        elif key == '⇧':  # Shift
            self.shift_on = not self.shift_on
            # Update key labels
            for child in self.virtual_kbd.winfo_children():
                if isinstance(child, tk.Frame):
                    for btn in child.winfo_children():
                        if isinstance(btn, tk.Button) and len(btn['text']) == 1:
                            btn['text'] = btn['text'].upper() if self.shift_on else btn['text'].lower()
        else:
            # Insert the key (shifted if shift is on)
            insert_key = key.upper() if self.shift_on else key
            self.current_entry.insert(tk.END, insert_key)
            if self.shift_on:  # Auto-disable shift after one character
                self.shift_on = False
                self._press_key('⇧')
                
    def show_keyboard(self, entry_widget, numeric=False):
        """Show virtual keyboard for the given entry widget"""
        # Don't show virtual keyboard if external keyboard is connected
        if self.external_kbd_connected:
            return
            
        # Refresh keyboard check before showing
        self._check_external_keyboard()
        if self.external_kbd_connected:
            return
            
        self.current_entry = entry_widget
        self.create_virtual_keyboard(numeric_only=numeric)
        
        # Position keyboard at bottom of screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        kbd_width = min(screen_width, 800)  # Max width 800px
        kbd_height = min(screen_height // 3, 400)  # Max 1/3 of screen height
        
        self.virtual_kbd.geometry(f"{kbd_width}x{kbd_height}+{(screen_width-kbd_width)//2}+{screen_height-kbd_height}")
        
        # Add a small indicator that external keyboard can be used
        indicator = tk.Label(self.virtual_kbd,
                           text="Tip: You can also use a physical keyboard",
                           font=('Arial', 10),
                           fg='#888888',
                           bg='#2d2d2d')
        indicator.pack(pady=(0, 5))
        
    def hide_keyboard(self):
        """Hide the virtual keyboard"""
        if self.virtual_kbd:
            self.virtual_kbd.destroy()
            self.virtual_kbd = None
        self.current_entry = None
        
    def bind_touch_events(self, widget):
        """Bind touch event handling to a widget"""
        widget.bind('<Button-1>', self._touch_start)
        widget.bind('<B1-Motion>', self._touch_move)
        widget.bind('<ButtonRelease-1>', self._touch_end)
        
        if isinstance(widget, tk.Entry):
            widget.bind('<FocusIn>', lambda e: self.show_keyboard(widget, 
                numeric='numeric' in str(widget.config('validate'))))
            
    def _touch_start(self, event):
        """Handle touch start event"""
        self.gesture_start = (event.x, event.y)
        
        # Check for double-tap
        now = time.time()
        if now - self.last_tap_time < 0.3:  # 300ms window for double-tap
            self._handle_double_tap(event)
        self.last_tap_time = now
        
    def _touch_move(self, event):
        """Handle touch move/drag event"""
        if not self.gesture_start:
            return
            
        dx = event.x - self.gesture_start[0]
        dy = event.y - self.gesture_start[1]
        
        # Detect swipe gestures
        if abs(dx) > 50:  # Horizontal swipe
            self._handle_swipe('right' if dx > 0 else 'left')
            self.gesture_start = None
        elif abs(dy) > 50:  # Vertical swipe
            self._handle_swipe('down' if dy > 0 else 'up')
            self.gesture_start = None
            
    def _touch_end(self, event):
        """Handle touch end event"""
        self.gesture_start = None
        
    def _handle_swipe(self, direction):
        """Handle swipe gesture"""
        # Navigation handlers based on direction
        handlers = {
            'right': lambda: None,  # Can add navigation logic here
            'left': lambda: None,
            'up': lambda: None,
            'down': lambda: None
        }
        if direction in handlers:
            handlers[direction]()
            
    def _handle_double_tap(self, event):
        """Handle double-tap gesture"""
        widget = event.widget
        # Add double-tap actions here based on widget type
        pass

# Initialize managers at app start
layout_mgr = None
touch_mgr = None

def init_managers(root):
    """Initialize the layout and touch screen managers"""
    global layout_mgr, touch_mgr
    layout_mgr = LayoutManager(root)
    touch_mgr = TouchScreenManager(root)
    return layout_mgr, touch_mgr
    global layout_mgr
    layout_mgr = LayoutManager(root)
    
    # Enable DPI awareness
    try:
        awareness = ctypes.c_int()
        errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        if errorCode == 0:
            if awareness.value == 0:  # DPI unaware
                # Try to set per-monitor DPI awareness
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass
    
    # Configure minimum window size
    root.minsize(layout_mgr.min_width, layout_mgr.min_height)
    return layout_mgr


def init_layout_manager(root):
    """Compatibility wrapper: return only the LayoutManager instance.

    Some callsites expect a function named `init_layout_manager` that returns
    the layout manager. Internally we already have `init_managers` which
    returns (layout_mgr, touch_mgr). This wrapper keeps compatibility.
    """
    lm, _ = init_managers(root)
    return lm

# Set up logging
log_dir = Path.home() / "MathBlast_Logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "math_blast.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

SESSION_TIMEOUT = 1800  # 30 minutes in seconds

# Server & sync configuration
SERVER_URL = "http://math-blast-server.example.com"  # Replace with actual server URL when deployed
SYNC_INTERVAL = 300  # Sync every 5 minutes
LAST_SYNC_KEY = "last_sync_timestamp"
ANALYTICS_FILE = "math_blast_analytics.json"

class GameAnalytics:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.datetime.now()
        self.load_analytics()
    
    def load_analytics(self):
        try:
            if os.path.exists(ANALYTICS_FILE):
                with open(ANALYTICS_FILE, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {
                    'total_games': 0,
                    'total_correct': 0,
                    'total_wrong': 0,
                    'average_time_per_problem': 0,
                    'problems_by_type': {'addition': 0, 'subtraction': 0, 'multiplication': 0, 'division': 0},
                    'level_completion_times': {},
                    'peak_hours': [0] * 24,  # Hour-based activity tracking
                    'sessions': []
                }
        except Exception as e:
            logging.error(f"Error loading analytics: {e}")
            self.data = {'sessions': []}
    
    def save_analytics(self):
        try:
            with open(ANALYTICS_FILE, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            logging.error(f"Error saving analytics: {e}")
    
    def track_problem(self, problem_type, is_correct, time_taken):
        self.data['problems_by_type'][problem_type] = self.data['problems_by_type'].get(problem_type, 0) + 1
        if is_correct:
            self.data['total_correct'] += 1
        else:
            self.data['total_wrong'] += 1
        
        # Update average time
        total = self.data['total_correct'] + self.data['total_wrong']
        old_avg = self.data['average_time_per_problem']
        self.data['average_time_per_problem'] = (old_avg * (total - 1) + time_taken) / total
        
        # Track peak hours
        current_hour = datetime.datetime.now().hour
        self.data['peak_hours'][current_hour] += 1
        
        self.save_analytics()
    
    def start_session(self, profile_name):
        session = {
            'id': self.session_id,
            'profile': profile_name,
            'start_time': self.session_start.isoformat(),
            'problems_solved': 0,
            'correct_answers': 0,
            'highest_level': 1
        }
        self.data['sessions'].append(session)
        self.save_analytics()
    
    def update_session(self, problems_solved, correct_answers, highest_level):
        for session in self.data['sessions']:
            if session['id'] == self.session_id:
                session['problems_solved'] = problems_solved
                session['correct_answers'] = correct_answers
                session['highest_level'] = highest_level
                session['last_update'] = datetime.datetime.now().isoformat()
                break
        self.save_analytics()
    
    def end_session(self):
        for session in self.data['sessions']:
            if session['id'] == self.session_id:
                session['end_time'] = datetime.datetime.now().isoformat()
                break
        self.save_analytics()

# Initialize analytics
analytics = GameAnalytics()

# Available avatars (emoji)
AVATARS = ["👨", "👩", "🐱", "🐶", "🐼", "🐰", "🦊", "🐸", "🦁", "🐯", "🦄", "🐲"]

# Achievement definitions
ACHIEVEMENTS = {
    'beginner': {'name': '🌟 Math Rookie', 'desc': 'Complete your first game', 'icon': '🌟'},
    'speed_demon': {'name': '⚡ Speed Demon', 'desc': 'Answer 10 questions in under 30 seconds', 'icon': '⚡'},
    'perfect_10': {'name': '💯 Perfect 10', 'desc': 'Get 10 correct answers in a row', 'icon': '💯'},
    'level_master': {'name': '👑 Level Master', 'desc': 'Reach level 5', 'icon': '👑'},
    'challenge_king': {'name': '🏆 Challenge King', 'desc': 'Win 5 player challenges', 'icon': '🏆'},
    'math_wizard': {'name': '🧙‍♂️ Math Wizard', 'desc': 'Solve 100 problems correctly', 'icon': '🧙‍♂️'},
    'no_mistake': {'name': '✨ Flawless', 'desc': 'Complete a level with no mistakes', 'icon': '✨'},
    'speed_run': {'name': '🚀 Speed Runner', 'desc': 'Complete a level in under 2 minutes', 'icon': '🚀'},
    'division_master': {'name': '➗ Division Master', 'desc': 'Solve 20 division problems correctly', 'icon': '➗'},
    'multiplier': {'name': '✖️ Multiplication Master', 'desc': 'Solve 20 multiplication problems correctly', 'icon': '✖️'}
}

# Challenge types
CHALLENGE_TYPES = {
    'speed': {'name': '⚡ Speed Battle', 'desc': 'First to solve 10 problems wins'},
    'endurance': {'name': '💪 Endurance Match', 'desc': 'Most correct answers in 5 minutes'},
    'precision': {'name': '🎯 Precision Duel', 'desc': 'First to make 3 mistakes loses'},
    'level_race': {'name': '🏃 Level Race', 'desc': 'First to complete the level wins'}
}

# Online game functions
class OnlineManager:
    def __init__(self):
        self.player_id = str(uuid.uuid4())  # Unique player ID
        self.player_tag = ""
        self.online_status = False
        self.active_challenges = []
        self.offline_mode = True  # Start in offline mode
        self.sync_timer = None
        self.device_id = str(uuid.uuid4())  # Unique device identifier
        
    def connect(self):
        """Connect to server and sync data"""
        try:
            response = requests.post(f"{SERVER_URL}/connect", 
                                  json={"player_id": self.player_id})
            if response.status_code == 200:
                self.online_status = True
                self.offline_mode = False
                return True
        except:
            self.online_status = False
            self.offline_mode = True
        return False
    
    def update_profile(self, profile_name, tag, stats):
        """Update online profile"""
        if self.offline_mode:
            return False  # Silently fail in offline mode
        elif not self.online_status:
            self.connect()  # Try to reconnect
            if not self.online_status:
                return False
        try:
            data = {
                "player_id": self.player_id,
                "name": profile_name,
                "tag": tag,
                "stats": stats
            }
            response = requests.post(f"{SERVER_URL}/update_profile", json=data)
            return response.status_code == 200
        except:
            return False
            
    def get_rankings(self, timeframe="weekly"):
        """Get weekly/monthly rankings"""
        if self.offline_mode:
            return {"message": "Offline mode - Rankings unavailable"}
        try:
            response = requests.get(f"{SERVER_URL}/rankings/{timeframe}")
            if response.status_code == 200:
                return response.json()
        except:
            return []
        return []
        
    def send_challenge(self, target_tag):
        """Send challenge to another player"""
        if self.offline_mode:
            return False
        if not target_tag:
            return False
        data = {
            "from_id": self.player_id,
            "target_tag": target_tag,
            "timestamp": datetime.datetime.now().isoformat()
        }
        response = requests.post(f"{SERVER_URL}/challenge", json=data)
        return response.status_code == 200
    
    def check_challenges(self):
        """Check for incoming challenges"""
        try:
            response = requests.get(f"{SERVER_URL}/challenges/{self.player_id}")
            if response.status_code == 200:
                self.active_challenges = response.json()
                return self.active_challenges
        except Exception as e:
            logging.error(f"Error checking challenges: {e}")
        return []
        
    def check_challenges(self):
        """Check for incoming challenges"""
        try:
            response = requests.get(f"{SERVER_URL}/challenges/{self.player_id}")
            if response.status_code == 200:
                self.active_challenges = response.json()
                return self.active_challenges
        except Exception as e:
            logging.error(f"Error checking challenges: {e}")
        return []
    
    def start_sync(self):
        """Start automatic profile syncing"""
        if not self.sync_timer and not self.offline_mode:
            self._sync_profiles()  # Initial sync
            self.sync_timer = threading.Timer(SYNC_INTERVAL, self._periodic_sync)
            self.sync_timer.daemon = True
            self.sync_timer.start()
    
    def stop_sync(self):
        """Stop automatic profile syncing"""
        if self.sync_timer:
            self.sync_timer.cancel()
            self.sync_timer = None
    
    def _periodic_sync(self):
        """Internal method for periodic sync"""
        self._sync_profiles()
        # Schedule next sync
        self.sync_timer = threading.Timer(SYNC_INTERVAL, self._periodic_sync)
        self.sync_timer.daemon = True
        self.sync_timer.start()
    
    def _sync_profiles(self):
        """Sync profiles with the server"""
        if self.offline_mode:
            return
        
        try:
            # Load local profiles
            local_profiles = load_profiles()
            
            # Get last sync timestamp
            last_sync = self._get_last_sync()
            
            # Upload local changes
            sync_data = {
                "player_id": self.player_id,
                "device_id": self.device_id,
                "profiles": local_profiles,
                "last_sync": last_sync
            }
            
            response = requests.post(f"{SERVER_URL}/sync", json=sync_data)
            if response.status_code == 200:
                server_data = response.json()
                
                # Merge server profiles with local profiles
                merged_profiles = self._merge_profiles(local_profiles, server_data.get("profiles", {}))
                
                # Save merged profiles
                with open('math_blast_profiles.json', 'w') as f:
                    json.dump(merged_profiles, f)
                
                # Update last sync timestamp
                self._save_last_sync(server_data.get("sync_timestamp"))
                
                # Trigger UI updates if needed
                if hasattr(self, 'on_sync_complete'):
                    self.on_sync_complete()
        
        except Exception as e:
            print(f"Sync error: {e}")
    
    def _get_last_sync(self):
        """Get the timestamp of the last successful sync"""
        try:
            with open('sync_info.json', 'r') as f:
                sync_info = json.load(f)
                return sync_info.get(LAST_SYNC_KEY)
        except:
            return None
    
    def _save_last_sync(self, timestamp):
        """Save the timestamp of the last successful sync"""
        try:
            sync_info = {}
            try:
                with open('sync_info.json', 'r') as f:
                    sync_info = json.load(f)
            except:
                pass
            
            sync_info[LAST_SYNC_KEY] = timestamp
            
            with open('sync_info.json', 'w') as f:
                json.dump(sync_info, f)
        except Exception as e:
            logging.error(f"Error saving last sync timestamp: {e}")
    
    def _merge_profiles(self, local_profiles, server_profiles):
        """Merge local and server profiles, keeping the most recent data"""
        merged = local_profiles.copy()
        
        for name, server_profile in server_profiles.items():
            if name not in merged:
                # New profile from server
                merged[name] = server_profile
            else:
                # Profile exists locally, merge data
                local_profile = merged[name]
                server_timestamp = server_profile.get('last_modified', 0)
                local_timestamp = local_profile.get('last_modified', 0)
                
                if server_timestamp > local_timestamp:
                    # Server has newer data
                    merged[name] = server_profile
                elif server_timestamp == local_timestamp:
                    # Same timestamp, merge achievements and stats
                    merged[name]['achievements'] = list(set(
                        local_profile.get('achievements', []) +
                        server_profile.get('achievements', [])
                    ))
                    
                    # Take highest values for numerical stats
                    for key in ['highest_level', 'total_correct', 'games_played', 'games_won']:
                        merged[name][key] = max(
                            local_profile.get(key, 0),
                            server_profile.get(key, 0)
                        )
        
        return merged

# Initialize online manager
online_mgr = OnlineManager()

# Profile and high score functions
def load_profiles():
    try:
        if os.path.exists('math_blast_profiles.json'):
            with open('math_blast_profiles.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def check_achievements(profile):
    """Check and award achievements based on profile stats"""
    achievements = profile.get('achievements', [])
    stats = profile.get('stats', {})
    
    # Check each achievement condition
    if 'beginner' not in achievements and stats.get('games_played', 0) > 0:
        achievements.append('beginner')
        
    if 'perfect_10' not in achievements and stats.get('max_streak', 0) >= 10:
        achievements.append('perfect_10')
        
    if 'level_master' not in achievements and profile['highest_level'] >= 5:
        achievements.append('level_master')
        
    if 'challenge_king' not in achievements and stats.get('challenges_won', 0) >= 5:
        achievements.append('challenge_king')
        
    if 'math_wizard' not in achievements and profile['total_correct'] >= 100:
        achievements.append('math_wizard')
        
    if 'no_mistake' not in achievements and stats.get('perfect_levels', 0) > 0:
        achievements.append('no_mistake')
        
    return achievements

def save_profile(name, highest_level, total_correct, game_result=None, game_stats=None):
    profiles = load_profiles()
    if name in profiles:
        # Update existing profile with highest values and stats
        profile = profiles[name]
        profile['highest_level'] = max(highest_level, profile['highest_level'])
        profile['total_correct'] = total_correct + profile.get('total_correct', 0)
        profile['games_played'] = profile.get('games_played', 0) + (1 if game_result else 0)
        profile['last_modified'] = int(datetime.datetime.now().timestamp())
        
        # Update game stats
        if game_result:
            profile['games_won'] = profile.get('games_won', 0) + (1 if game_result == 'win' else 0)
            profile['games_lost'] = profile.get('games_lost', 0) + (1 if game_result == 'lose' else 0)
        
        # Update detailed stats
        if game_stats:
            stats = profile.get('stats', {})
            stats['max_streak'] = max(stats.get('max_streak', 0), game_stats.get('streak', 0))
            stats['perfect_levels'] = stats.get('perfect_levels', 0) + (1 if game_stats.get('no_mistakes', False) else 0)
            stats['fastest_level'] = min(stats.get('fastest_level', float('inf')), game_stats.get('level_time', float('inf')))
            stats['total_time'] = stats.get('total_time', 0) + game_stats.get('total_time', 0)
            profile['stats'] = stats
        
        # Check and award achievements
        profile['achievements'] = check_achievements(profile)
    else:
        # Create new profile with default values
        profiles[name] = {
            'highest_level': highest_level,
            'total_correct': total_correct,
            'games_played': 0,
            'games_won': 0,
            'games_lost': 0,
            'avatar': random.choice(AVATARS)  # assign random avatar
        }
    with open('math_blast_profiles.json', 'w') as f:
        json.dump(profiles, f)
    # After saving locally, attempt to push update to server in background
    try:
        profile = profiles.get(name, {})
        tag = profile.get('tag', '')
        stats = {
            'highest_level': profile.get('highest_level', highest_level),
            'total_correct': profile.get('total_correct', total_correct),
            'games_played': profile.get('games_played', 0),
            'games_won': profile.get('games_won', 0)
        }
        # Fire-and-forget background update so UI isn't blocked
        if 'online_mgr' in globals():
            try:
                threading.Thread(target=online_mgr.update_profile, args=(name, tag, stats), daemon=True).start()
            except Exception:
                pass
    except Exception:
        pass

def delete_profile(name):
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        with open('math_blast_profiles.json', 'w') as f:
            json.dump(profiles, f)
        return True
    return False

def get_leaderboard():
    """Get sorted leaderboard data"""
    profiles = load_profiles()
    # Sort by highest level first, then total correct
    return sorted(
        [(name, data) for name, data in profiles.items()],
        key=lambda x: (x[1]['highest_level'], x[1]['total_correct']),
        reverse=True
    )


# Profile manager to centralize profile I/O and merging logic
class ProfileManager:
    def __init__(self, filename='math_blast_profiles.json'):
        self.filename = filename

    def load_profiles(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading profiles: {e}")
        return {}

    def save_profiles(self, profiles):
        try:
            with open(self.filename, 'w') as f:
                json.dump(profiles, f)
        except Exception as e:
            logging.error(f"Error saving profiles: {e}")

    def save_profile(self, name, highest_level, total_correct, game_result=None, game_stats=None):
        profiles = self.load_profiles()
        if name in profiles:
            profile = profiles[name]
            profile['highest_level'] = max(highest_level, profile.get('highest_level', 1))
            profile['total_correct'] = total_correct + profile.get('total_correct', 0)
            profile['games_played'] = profile.get('games_played', 0) + (1 if game_result else 0)
            profile['last_modified'] = int(datetime.datetime.now().timestamp())

            if game_result:
                profile['games_won'] = profile.get('games_won', 0) + (1 if game_result == 'win' else 0)
                profile['games_lost'] = profile.get('games_lost', 0) + (1 if game_result == 'lose' else 0)

            if game_stats:
                stats = profile.get('stats', {})
                stats['max_streak'] = max(stats.get('max_streak', 0), game_stats.get('streak', 0))
                stats['perfect_levels'] = stats.get('perfect_levels', 0) + (1 if game_stats.get('no_mistakes', False) else 0)
                stats['fastest_level'] = min(stats.get('fastest_level', float('inf')), game_stats.get('level_time', float('inf')))
                stats['total_time'] = stats.get('total_time', 0) + game_stats.get('total_time', 0)
                profile['stats'] = stats

            profile['achievements'] = check_achievements(profile)
        else:
            profiles[name] = {
                'highest_level': highest_level,
                'total_correct': total_correct,
                'games_played': 0,
                'games_won': 0,
                'games_lost': 0,
                'avatar': random.choice(AVATARS)
            }

        self.save_profiles(profiles)

    def delete_profile(self, name):
        profiles = self.load_profiles()
        if name in profiles:
            del profiles[name]
            self.save_profiles(profiles)
            return True
        return False

    def get_leaderboard(self):
        profiles = self.load_profiles()
        return sorted(
            [(name, data) for name, data in profiles.items()],
            key=lambda x: (x[1].get('highest_level', 1), x[1].get('total_correct', 0)),
            reverse=True
        )

# instantiate manager
profile_mgr = ProfileManager()

def generate_unique_tag(existing_profiles_func=None, prefix='P'):
    """Generate a short unique player tag not present in existing profiles.

    existing_profiles_func: optional callable returning dict of profiles (name->data).
    prefix: short prefix string for readability.
    """
    existing = {}
    try:
        if existing_profiles_func:
            existing = existing_profiles_func()
        else:
            existing = load_profiles()
        used = {p.get('tag') for p in existing.values() if isinstance(p, dict) and p.get('tag')}
    except Exception:
        used = set()

    # try a few readable formats first
    for _ in range(10):
        tag = f"{prefix}{random.randint(1000, 9999)}"
        if tag not in used:
            return tag

    # fallback to uuid-based short tag
    t = uuid.uuid4().hex[:8].upper()
    while t in used:
        t = uuid.uuid4().hex[:8].upper()
    return t

def create_profile_screen():
    global root, profile_window, main_container
    # Ensure `button_style` exists. Some initialization paths define it later
    # in the file; add a safe fallback to avoid NameError when this function
    # is called earlier (for example during certain test runs).
    if 'button_style' not in globals():
        globals()['button_style'] = {
            'relief': 'raised',
            'bd': 4,
            'bg': '#4a90e2',
            'fg': 'white',
            'font': ('Arial', 12, 'bold'),
            'padx': 10,
            'pady': 6
        }
    
    profile_window = tk.Toplevel(root)
    profile_window.title("Select Profile")
    
    # Create a layout manager for this window
    win_layout = LayoutManager(profile_window)
    
    # Configure minimum size and responsive scaling
    profile_window.minsize(win_layout.min_width, win_layout.min_height)
    
    # For foldables/tablets in portrait, use 90% of screen
    if win_layout.is_foldable and win_layout.current_orientation == "portrait":
        width = int(win_layout.screen_width * 0.9)
        height = int(win_layout.screen_height * 0.9)
        profile_window.geometry(f"{width}x{height}")
    else:
        # On desktop/landscape, maximize
        profile_window.state('zoomed')
    
    # Configure window
    profile_window.configure(bg=THEME['background'])
    
    # Load existing profiles
    profiles = load_profiles()
    
    # Use scaled font sizes
    title_font_size = win_layout.get_font_size(20)
    tk.Label(profile_window, 
             text="Math Blast Profiles", 
             font=("Arial", title_font_size, "bold"),
             bg=THEME['background']).pack(pady=win_layout.get_widget_size(20)[1])
    
    # Main container with padding
    main_container = tk.Frame(profile_window, bg=THEME['background'], padx=40, pady=20)
    main_container.pack(fill="both", expand=True)
    
    # Title with larger font
    title_label = tk.Label(main_container, text="Math Blast Profiles", 
                          font=("Arial", 32, "bold"))
    title_label.pack(pady=30)
    
    # Profile creation with tag
    create_frame = tk.Frame(main_container)
    create_frame.pack(pady=20, fill="x")
    
    tk.Label(create_frame, text="Create New Profile:", 
             font=("Arial", 18, "bold")).pack()
             
    name_frame = tk.Frame(create_frame)
    name_frame.pack(fill="x", pady=5)
    
    tk.Label(name_frame, text="Name:", 
             font=("Arial", 14)).pack(side=tk.LEFT, padx=5)
    new_name = tk.Entry(name_frame, font=("Arial", 16))
    new_name.pack(side=tk.LEFT, expand=True, fill="x", padx=5)
    
    tag_frame = tk.Frame(create_frame)
    tag_frame.pack(fill="x", pady=5)
    
    tk.Label(tag_frame, text="Player Tag:", 
             font=("Arial", 14)).pack(side=tk.LEFT, padx=5)
    new_tag = tk.Entry(tag_frame, font=("Arial", 16))
    # pre-fill with a generated unique tag but allow user edit
    try:
        new_tag.insert(0, generate_unique_tag())
    except Exception:
        pass
    new_tag.pack(side=tk.LEFT, expand=True, fill="x", padx=5)
    def randomize_tag():
        try:
            new_tag.delete(0, tk.END)
            new_tag.insert(0, generate_unique_tag())
            check_tag_availability()
        except Exception:
            pass
    tk.Button(tag_frame, text="Randomize Tag", command=randomize_tag).pack(side=tk.LEFT, padx=6)
    # Inline tag availability indicator
    tag_status = tk.Label(tag_frame, text="", font=("Arial", 12))
    tag_status.pack(side=tk.LEFT, padx=8)

    def check_tag_availability(event=None):
        try:
            entered = new_tag.get().strip()
            profiles = load_profiles()
            used = {p.get('tag') for p in profiles.values() if isinstance(p, dict) and p.get('tag')}
            if not entered:
                tag_status.config(text="No tag", fg='orange')
                return False
            if entered in used:
                tag_status.config(text="Taken", fg='red')
                return False
            # basic validation: alnum and limited length
            if len(entered) > 16 or not all(c.isalnum() or c in ('-', '_') for c in entered):
                tag_status.config(text="Invalid", fg='red')
                return False
            tag_status.config(text="Available", fg='green')
            return True
        except Exception:
            tag_status.config(text="?", fg='gray')
            return False

    new_tag.bind('<KeyRelease>', check_tag_availability)
    tk.Label(tag_frame, text="(for online play)", 
             font=("Arial", 12, "italic")).pack(side=tk.LEFT, padx=5)
             
    # Online status indicator
    online_status = tk.Label(create_frame, text="⭕ Offline", 
                            font=("Arial", 12))
    online_status.pack(pady=5)
    
    def check_online_status():
        if online_mgr.connect():
            online_status.config(text="✅ Online", fg="green")
            # Enable online-only buttons and features
            challenge_tag.config(state='normal')
            send_challenge_btn.config(state='normal')
            weekly_text.config(state='normal')
            monthly_text.config(state='normal')
        else:
            online_status.config(text="⭕ Offline - Online features disabled", fg="red")
            # Disable online-only features
            challenge_tag.config(state='disabled')
            send_challenge_btn.config(state='disabled')
            weekly_text.config(state='disabled')
            monthly_text.config(state='disabled')
            
            # Show offline message in online-only areas
            weekly_text.insert('1.0', "Online features unavailable in offline mode")
            monthly_text.insert('1.0', "Online features unavailable in offline mode")
            weekly_text.config(state='disabled')
            monthly_text.config(state='disabled')
    
    threading.Thread(target=check_online_status, daemon=True).start()
    
    # Avatar selection
    avatar_frame = tk.Frame(create_frame)
    avatar_frame.pack(pady=15)
    selected_avatar = tk.StringVar(value=AVATARS[0])
    
    def update_avatar(avatar):
        selected_avatar.set(avatar)
        # Update visual feedback for selected avatar
        for btn in avatar_buttons.winfo_children():
            if btn.cget('text') == avatar:
                btn.config(bg='#90EE90')  # Light green for selected
            else:
                btn.config(bg='#e6e6e6')  # Default color
    
    tk.Label(avatar_frame, text="Choose Avatar:", 
             font=("Arial", 16, "bold")).pack(pady=5)
    avatar_buttons = tk.Frame(avatar_frame)
    avatar_buttons.pack()
    
    for avatar in AVATARS:
        btn = tk.Button(avatar_buttons, text=avatar, font=("Arial", 24),
                       width=2, height=1,
                       command=lambda a=avatar: update_avatar(a))
        btn.pack(side=tk.LEFT, padx=4)
    update_avatar(AVATARS[0])  # Set initial selection
    
    def add_profile():
        name = new_name.get().strip()
        if name:
            profiles = load_profiles()
            if name in profiles:
                tk.messagebox.showerror("Error", "Profile name already exists")
                return

            # Validate tag before creating
            tag = new_tag.get().strip()
            if not tag:
                tag = generate_unique_tag()
            if not check_tag_availability():
                tk.messagebox.showerror("Error", "Tag is invalid or already taken")
                return

            # create the profile then set avatar and tag
            save_profile(name, 1, 0)
            profiles = load_profiles()  # reload to get saved profile
            profiles[name]['avatar'] = selected_avatar.get()  # Save chosen avatar
            profiles[name]['tag'] = tag
            with open('math_blast_profiles.json', 'w') as f:
                json.dump(profiles, f)
            new_name.delete(0, tk.END)
            update_profile_list()
            update_leaderboard()
            
    tk.Button(create_frame, text="Create Profile", command=add_profile, **button_style).pack(pady=5)
    
    # Profile selection and leaderboard
    bottom_frame = tk.Frame(main_container)
    bottom_frame.pack(pady=20, fill="both", expand=True)
    
    # Split into left (selection) and right (leaderboard) sections
    select_frame = tk.Frame(bottom_frame)
    select_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=20)
    
    leaderboard_frame = tk.Frame(bottom_frame)
    leaderboard_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=20)
    
    # Profile selection with larger fonts and better spacing
    tk.Label(select_frame, text="Select Profile:", 
             font=("Arial", 24, "bold")).pack(pady=10)
    # Use a Treeview to show multiple columns (Name/avatar, Tag, Level, Score, Games)
    columns = ('tag', 'acct_level', 'level', 'score', 'games')
    profile_tree = ttk.Treeview(select_frame, columns=columns, show='tree headings', height=12)
    profile_tree.heading('#0', text='Player')
    profile_tree.column('#0', width=220)
    profile_tree.heading('tag', text='Tag')
    profile_tree.column('tag', width=100)
    profile_tree.heading('acct_level', text='Acct Lvl')
    profile_tree.column('acct_level', width=80, anchor='center')
    profile_tree.heading('level', text='Level')
    profile_tree.column('level', width=80, anchor='center')
    profile_tree.heading('score', text='Score')
    profile_tree.column('score', width=100, anchor='center')
    profile_tree.heading('games', text='Games')
    profile_tree.column('games', width=100, anchor='center')
    profile_tree.pack(pady=10, fill="both", expand=True)
    
    def update_profile_list():
        try:
            # clear tree
            for iid in profile_tree.get_children():
                profile_tree.delete(iid)
            profiles = load_profiles()
            
            if not profiles:
                profile_tree.insert('', 'end', text='No profiles yet - Create one!', values=('', '', '', ''))
                return
                
            for name in profiles:
                try:
                    profile = profiles[name]
                    avatar = profile.get('avatar', '👤')
                    lvl = profile.get('highest_level', 1)
                    score_val = profile.get('total_correct', 0)
                    games = profile.get('games_played', 0)
                    tag = profile.get('tag', '')
                    acct_lvl = profile.get('account_level', profile.get('xp', 0) // 100 + 1 if profile.get('xp') is not None else 1)
                    # Use profile name as item id (iids must be unique)
                    profile_tree.insert('', 'end', iid=name, text=f"{avatar} {name}", values=(tag, acct_lvl, lvl, score_val, games))
                except Exception as e:
                    logging.error(f"Error formatting profile {name}: {e}")
                    continue
        except Exception as e:
            logging.error(f"Error updating profile list: {e}")
            # clear and show error
            try:
                for iid in profile_tree.get_children():
                    profile_tree.delete(iid)
                profile_tree.insert('', 'end', text='Error loading profiles', values=('', '', '', ''))
            except Exception:
                pass
            
    def update_leaderboard():
            try:
                # populate leaderboard_tree
                try:
                    for iid in leaderboard_tree.get_children():
                        leaderboard_tree.delete(iid)
                except Exception:
                    pass

                all_leaders = get_leaderboard()
                leaders = all_leaders[:5] if all_leaders else []

                if not leaders:
                    leaderboard_tree.insert('', 'end', values=('No scores yet', '', '', ''))
                    return

                medals = ["🥇", "🥈", "🥉"]
                for i, (name, data) in enumerate(leaders, 1):
                    try:
                        avatar = data.get('avatar', '👤')
                        level = data.get('highest_level', 1)
                        score_val = data.get('total_correct', 0)
                        games = data.get('games_played', 0)
                        wins = data.get('games_won', 0)
                        win_rate = (wins / games * 100) if games > 0 else 0
                        acct_lvl = data.get('account_level', data.get('xp', 0) // 100 + 1 if data.get('xp') is not None else 1)
                        display_name = f"{medals[i-1] if i<=3 else '  '} {avatar} {name}"
                        # include account level in the name column for visibility
                        display_name = f"{display_name} [Lvl {acct_lvl}]"
                        leaderboard_tree.insert('', 'end', values=(display_name, level, score_val, f"{win_rate:.1f}%"))
                    except Exception as e:
                        logging.error(f"Error formatting leaderboard entry: {e}")
                        continue
            except Exception as e:
                logging.error(f"Unable to load leaderboard data: {e}")
    
    def delete_selected_profile():
        sel = profile_tree.selection()
        if not sel:
            return
        # profile_tree iids are profile names
        name = sel[0]
        try:
            if delete_profile(name):
                update_profile_list()
                update_leaderboard()
        except Exception as e:
            logging.error(f"Error deleting selected profile: {e}")
            return
    
    # Delete button
    del_btn = tk.Button(select_frame, text="Delete Profile", command=delete_selected_profile, 
              **button_style)
    del_btn.config(bg='#ff9999')
    del_btn.pack(pady=5)
    
    # Rankings and Challenges section
    right_frame = tk.Frame(leaderboard_frame)
    right_frame.pack(fill="both", expand=True)
    
    # Tabs for different rankings
    rankings_notebook = ttk.Notebook(right_frame)
    rankings_notebook.pack(fill="both", expand=True, pady=10)
    
    # All-time leaderboard
    alltime_frame = tk.Frame(rankings_notebook)
    rankings_notebook.add(alltime_frame, text="All Time")
    
    tk.Label(alltime_frame, text="🏆 Top Players 🏆", 
             font=("Arial", 24, "bold")).pack(pady=10)
    # Leaderboard as Treeview (Name, Level, Score, Win Rate)
    lb_columns = ('name', 'level', 'score', 'winrate')
    leaderboard_tree = ttk.Treeview(alltime_frame, columns=lb_columns, show='headings')
    leaderboard_tree.heading('name', text='Player')
    leaderboard_tree.column('name', width=200)
    leaderboard_tree.heading('level', text='Level')
    leaderboard_tree.column('level', width=80, anchor='center')
    leaderboard_tree.heading('score', text='Score')
    leaderboard_tree.column('score', width=120, anchor='center')
    leaderboard_tree.heading('winrate', text='Win Rate')
    leaderboard_tree.column('winrate', width=100, anchor='center')
    leaderboard_tree.pack(pady=5, fill="both", expand=True)
    
    # Weekly rankings
    weekly_frame = tk.Frame(rankings_notebook)
    rankings_notebook.add(weekly_frame, text="Weekly")
    
    tk.Label(weekly_frame, text="📅 This Week's Best 📅", 
             font=("Arial", 24, "bold")).pack(pady=10)
    weekly_text = tk.Text(weekly_frame, 
                         font=("Arial", 16),
                         height=8, width=35,
                         bg='#f8f8f8',
                         relief='ridge',
                         padx=10, pady=10)
    weekly_text.pack(pady=5, fill="both", expand=True)
    weekly_text.config(state='disabled')  # Make read-only initially
    
    # Monthly rankings
    monthly_frame = tk.Frame(rankings_notebook)
    rankings_notebook.add(monthly_frame, text="Monthly")
    
    tk.Label(monthly_frame, text="📆 Monthly Champions 📆", 
             font=("Arial", 24, "bold")).pack(pady=10)
    monthly_text = tk.Text(monthly_frame, 
                          font=("Arial", 16),
                          height=8, width=35,
                          bg='#f8f8f8',
                          relief='ridge',
                          padx=10, pady=10)
    monthly_text.pack(pady=5, fill="both", expand=True)
    monthly_text.config(state='disabled')  # Make read-only initially
    
    # Challenges section
    challenge_frame = tk.Frame(right_frame)
    challenge_frame.pack(fill="x", pady=10)
    
    tk.Label(challenge_frame, text="⚔️ Player Challenges ⚔️", 
             font=("Arial", 18, "bold")).pack(pady=5)
             
    challenge_controls = tk.Frame(challenge_frame)
    challenge_controls.pack(fill="x", pady=5)
    
    # Challenge input
    tk.Label(challenge_controls, text="Player Tag:", 
             font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
    challenge_tag = tk.Entry(challenge_controls, font=("Arial", 12))
    challenge_tag.pack(side=tk.LEFT, padx=5)
    challenge_tag.config(state='disabled')  # Start disabled until online check
    
    
    
    def send_player_challenge():
        tag = challenge_tag.get().strip()
        if tag:
            if online_mgr.send_challenge(tag):
                tk.messagebox.showinfo("Challenge Sent", 
                    f"Challenge sent to player {tag}!")
            else:
                tk.messagebox.showerror("Error", 
                    "Couldn't send challenge. Check the tag and try again.")
    
    send_challenge_btn = tk.Button(challenge_controls, text="Send Challenge", 
                          command=send_player_challenge,
                          **button_style, state='disabled')  # Start disabled until online check
    send_challenge_btn.pack(side=tk.LEFT, padx=5)
    
    
    def select_profile():
        sel = profile_tree.selection()
        if not sel:
            return
        name = sel[0]
        global current_profile
        current_profile = name
        # Set online manager player tag from profile if available
        try:
            profiles = load_profiles()
            online_mgr.player_tag = profiles.get(name, {}).get('tag', '')
        except Exception:
            pass

        # Start profile syncing if online
        if online_mgr.online_status:
            online_mgr.start_sync()

        # Start analytics session
        analytics.start_session(name)

        # Create progress tracker for the profile
        global current_progress_tracker
        current_progress_tracker = ProgressTracker(name)
        current_progress_tracker.load_progress()

        # Reset game stats
        global game_stats
        game_stats = {
            'streak': 0,
            'max_streak': 0,
            'current_problem': None,
            'problem_success_rate': {
                '+': 1.0,
                '-': 1.0,
                '*': 1.0,
                '/': 1.0
            },
            'problems_by_type': {
                'addition': 0,
                'subtraction': 0,
                'multiplication': 0,
                'division': 0
            },
            'no_mistakes': True,
            'level_start_time': datetime.datetime.now(),
            'total_time': 0
        }

        profile_window.destroy()
        show_main_menu()

class ProgressTracker:
    def __init__(self, profile_name):
        self.profile_name = profile_name
        self.progress_file = f"progress_{profile_name}.json"
        self.progress_data = {
            'learning_curve': [],  # Track improvement over time
            'problem_history': [],  # Recent problem performance
            'skill_levels': {
                'addition': 1.0,
                'subtraction': 1.0,
                'multiplication': 1.0,
                'division': 1.0
            },
            'achievements_progress': {},  # Track progress towards achievements
            'daily_goals': {
                'problems_solved': 0,
                'streak_days': 0,
                'last_played': None
            }
        }
    
    def load_progress(self):
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    saved_data = json.load(f)
                    self.progress_data.update(saved_data)
                    
                # Check daily streak
                if self.progress_data['daily_goals']['last_played']:
                    last_played = datetime.datetime.fromisoformat(
                        self.progress_data['daily_goals']['last_played']
                    )
                    today = datetime.datetime.now()
                    days_diff = (today - last_played).days
                    
                    if days_diff > 1:  # Streak broken
                        self.progress_data['daily_goals']['streak_days'] = 0
                    elif days_diff == 1:  # Continued streak
                        self.progress_data['daily_goals']['streak_days'] += 1
                        
                # Update last played
                self.progress_data['daily_goals']['last_played'] = datetime.datetime.now().isoformat()
                self.save_progress()
                    
        except Exception as e:
            logging.error(f"Error loading progress for {self.profile_name}: {e}")
    
    def save_progress(self):
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f)
        except Exception as e:
            logging.error(f"Error saving progress for {self.profile_name}: {e}")
    
    def update_skill_level(self, problem_type, success, time_taken):
        """Update skill level based on performance"""
        current_level = self.progress_data['skill_levels'][problem_type]
        
        # Adjust based on success and time
        if success:
            # Faster solutions give more skill increase
            time_factor = max(0.5, min(1.5, 10 / time_taken))
            skill_change = 0.1 * time_factor
        else:
            skill_change = -0.05
        
        # Update skill level with bounds
        new_level = max(0.1, min(5.0, current_level + skill_change))
        self.progress_data['skill_levels'][problem_type] = new_level
        
        # Record in learning curve
        self.progress_data['learning_curve'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'problem_type': problem_type,
            'success': success,
            'time_taken': time_taken,
            'skill_level': new_level
        })
        
        # Keep learning curve manageable
        if len(self.progress_data['learning_curve']) > 1000:
            self.progress_data['learning_curve'] = self.progress_data['learning_curve'][-1000:]
        
        self.save_progress()
    
    def get_recommended_problem_type(self):
        """Suggest problem type based on skill levels"""
        skills = self.progress_data['skill_levels']
        # Favor problems types with lower skill levels
        weights = {k: 1/v for k, v in skills.items()}
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        return random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        
    def check_achievement_progress(self, stats):
        """Update progress towards achievements"""
        achievements_data = self.progress_data['achievements_progress']
        
        # Example achievement checks
        if stats['streak'] > achievements_data.get('best_streak', 0):
            achievements_data['best_streak'] = stats['streak']
            
        if stats.get('no_mistakes', False):
            achievements_data['perfect_levels'] = achievements_data.get('perfect_levels', 0) + 1
            
        self.save_progress()
    
    

def show_main_menu():
    root.deiconify()
    # Update title to show current profile and tag (if available)
    try:
        profiles = load_profiles()
        profile = profiles.get(current_profile, {}) if current_profile else {}
        tag = profile.get('tag', '') if isinstance(profile, dict) else ''
        acct_lvl = profile.get('account_level', profile.get('xp', 0) // 100 + 1 if isinstance(profile, dict) else 1)
        title = f"Math Blast - Profile: {current_profile}" if current_profile else "Math Blast"
        if tag:
            title = f"{title} [{tag}]"
        if acct_lvl:
            title = f"{title} (Account Lvl {acct_lvl})"
        root.title(title)
    except Exception:
        root.title(f"Math Blast - Profile: {current_profile}")

# Create the main window
root = tk.Tk()
root.title("Math Blast")

# Initialize managers
layout_mgr, touch_mgr = init_managers(root)
root.minsize(layout_mgr.min_width, layout_mgr.min_height)

# Increase touch targets if touch is enabled
# Ensure a default button_style exists before we attempt to update it.
if 'button_style' not in globals():
    button_style = {
        'relief': 'raised',
        'bd': 4,
        'bg': '#4a90e2',
        'fg': 'white',
        'font': ('Arial', 12, 'bold'),
        'padx': 10,
        'pady': 6
    }

if touch_mgr.touch_enabled:
    # Make buttons bigger for touch
    button_style.update({
        'padx': 20,
        'pady': 12
    })

# Initialize current profile and trackers
current_profile = None
current_progress_tracker = None
game_stats = {
    'streak': 0,
    'max_streak': 0,
    'current_problem': None,
    'problem_success_rate': {
        '+': 1.0,
        '-': 1.0,
        '*': 1.0,
        '/': 1.0
    },
    'problems_by_type': {
        'addition': 0,
        'subtraction': 0,
        'multiplication': 0,
        'division': 0
    },
    'no_mistakes': True,
    'level_start_time': datetime.datetime.now(),
    'total_time': 0
}

# Theme configuration
THEME = {
    'primary': '#4a90e2',  # Blue
    'secondary': '#43c59e',  # Mint green
    'accent': '#ff6b6b',  # Coral
    'background': '#f8f9fa',  # Light gray
    'text': '#212529',  # Dark gray
    'success': '#28a745',  # Green
    'error': '#dc3545',  # Red
    'warning': '#ffc107'  # Yellow
}

# reusable button style for a 3D / raised appearance
button_style = {
    'relief': 'raised',  # raised appearance
    'bd': 8,  # thicker border for more depth
    'activebackground': '#b3b3b3',  # darker when pressed
    'highlightthickness': 3,  # thicker highlight border
    'highlightbackground': THEME['secondary'],  # themed outline
    'bg': THEME['primary'],  # themed background
    'fg': 'white',  # white text
    'font': ('Arial', 12, 'bold'),  # bold font
    'padx': 15,  # horizontal padding
    'pady': 8   # vertical padding
}

# Configure custom styles for ttk widgets
style = ttk.Style()
style.configure('GameProgress.Horizontal.TProgressbar',
                troughcolor=THEME['background'],
                background=THEME['secondary'],
                thickness=25)

# Create and configure the main window
root.configure(bg=THEME['background'])
root.option_add('*Font', 'Arial 12')
root.option_add('*Background', THEME['background'])
root.option_add('*Foreground', THEME['text'])

# Initialize layout manager
layout_mgr = init_layout_manager(root)

# Create title with custom styling using scaled sizes
title_frame = tk.Frame(root, bg=THEME['background'])
title_frame.pack(pady=layout_mgr.get_widget_size(20)[1])

logo_label = tk.Label(title_frame, 
                     text="🎯", 
                     font=("Arial", layout_mgr.get_font_size(48)),
                     bg=THEME['background'])
logo_label.pack()

Title_screen = tk.Label(title_frame, 
                       text="Welcome to Math Blast",
                       font=("Arial", layout_mgr.get_font_size(32), "bold"),
                       bg=THEME['background'],
                       fg=THEME['primary'])
Title_screen.pack(pady=layout_mgr.get_widget_size(10)[1])

# Update button style with scaled sizes
button_width, button_height = layout_mgr.get_widget_size(30, 2)
scaled_button_style = button_style.copy()
scaled_button_style.update({
    'font': ('Arial', layout_mgr.get_font_size(12), 'bold'),
    'width': button_width,
    'height': button_height
})

START = tk.Button(root, text="START", **scaled_button_style)
START.config(bg='#00C621')
PROFILE = tk.Button(root, text="Change Profile", **scaled_button_style, command=create_profile_screen)

Title_screen.pack(pady=20)
START.pack(pady=10)
PROFILE.pack(pady=10)

AUTO_TEST = '--auto-test' in sys.argv

# Show profile selection at startup (skip if running automated test)
if not AUTO_TEST:
    # ensure profile list and leaderboard are populated when screen opens
    # (create_profile_screen will call update_profile_list/update_leaderboard internally)
    create_profile_screen()
else:
    # Automated test mode: ensure there is a test profile and open the game
    TEST_PROFILE = 'AUTOTEST'
    profiles = load_profiles()
    if TEST_PROFILE not in profiles:
        # create a lightweight profile
        save_profile(TEST_PROFILE, 1, 0)
        profiles = load_profiles()
        profiles[TEST_PROFILE]['avatar'] = AVATARS[0]
        try:
            profiles[TEST_PROFILE]['tag'] = generate_unique_tag()
        except Exception:
            profiles[TEST_PROFILE]['tag'] = f"AUT{random.randint(1000,9999)}"
        with open('math_blast_profiles.json', 'w') as f:
            json.dump(profiles, f)

    # Programmatically select the profile and start the game after mainloop starts
    def _auto_start():
        global current_profile, current_progress_tracker
        current_profile = TEST_PROFILE
        analytics.start_session(current_profile)
        current_progress_tracker = ProgressTracker(current_profile)
        current_progress_tracker.load_progress()
        show_main_menu()
        try:
            online_mgr.player_tag = load_profiles().get(current_profile, {}).get('tag', '')
        except Exception:
            pass
        # open game window
        START_press()
        # Automated gameplay: submit correct answers until level advances twice or max iterations
        def _auto_play_step(iteration=[0], max_iter=100):
            try:
                iteration[0] += 1
                if iteration[0] > max_iter:
                    return
                # Read the correct answer from AUT_problem_answer (StringVar)
                aut_ans_var = globals().get('AUT_problem_answer')
                aut_entry = globals().get('AUT_answer_entry')
                aut_btn = globals().get('AUT_submit_btn')
                if aut_ans_var and aut_entry and aut_btn:
                    try:
                        ans = aut_ans_var.get()
                        if ans:
                            aut_entry.delete(0, tk.END)
                            aut_entry.insert(0, str(ans))
                            # Click submit
                            aut_btn.invoke()
                    except Exception:
                        pass
                # Continue after short delay
                root.after(200, _auto_play_step)
            except Exception:
                return

        # Start automated play after a short delay to let the UI settle
        root.after(500, _auto_play_step)

    # schedule after a short delay so Tk is ready
    root.after(200, _auto_start)

# define function
def START_press():
    # open a new window (Toplevel) and hide the main window
    window = tk.Toplevel(root)
    window.title("Math Blast — Game")
    root.withdraw()
    
    # Create layout manager for game window
    game_layout = LayoutManager(window)
    window.minsize(game_layout.min_width, game_layout.min_height)
    
    # Handle orientation changes for the game window
    def handle_game_orientation(orientation):
        if orientation == "portrait" and game_layout.is_foldable:
            # Stack frames vertically in portrait mode on foldables
            game_frame.pack(side=tk.TOP, fill="both", expand=True)
            play_frame.pack(side=tk.TOP, fill="both", expand=True)
        else:
            # Side by side in landscape
            game_frame.pack(side=tk.LEFT, fill="both", expand=True)
            play_frame.pack(side=tk.RIGHT, fill="both", expand=True)
    
    game_layout.on_orientation_change = handle_game_orientation
    
    # create two frames inside the game window and swap between them
    game_frame = tk.Frame(window, bg=THEME['background'])
    play_frame = tk.Frame(window, bg=THEME['background'])  # renamed from blank_frame to play_frame
    
    # Initial layout based on current orientation
    handle_game_orientation(game_layout.current_orientation)

    # Game variables
    score = tk.IntVar(value=0)
    wrong_answers = tk.IntVar(value=0)
    current_level = tk.IntVar(value=1)
    goal = tk.IntVar(value=10)  # starts at 10, increases by 5 each level
    problem_answer = tk.StringVar()
    current_answer = tk.DoubleVar()
    total_correct = tk.IntVar(value=0)  # track total correct answers this session
    
    # Stats tracking
    game_stats = {
        'start_time': datetime.datetime.now(),
        'level_start_time': datetime.datetime.now(),
        'streak': 0,
        'max_streak': 0,
        'no_mistakes': True,
        'problems_by_type': {'addition': 0, 'subtraction': 0, 'multiplication': 0, 'division': 0},
        'total_time': 0,
        'level_time': 0
    }

    def generate_problem():
        """Generate a random math problem with dynamic difficulty"""
        current_score = score.get()
        level = current_level.get()
        streak = game_stats['streak']
        
        # Dynamic difficulty adjustment
        difficulty = min(1.0, 0.5 + (level * 0.1) + (streak * 0.05))
        
        # Select operator based on level and performance
        operators = ['+', '-']
        if level >= 2:
            operators.append('*')
        if level >= 3:
            operators.append('/')
            
        # Favor operators the player struggles with
        if 'problem_success_rate' in game_stats:
            rates = game_stats['problem_success_rate']
            # Add more instances of operators with lower success rates
            for op, rate in rates.items():
                if op in operators and rate < 0.7:  # Below 70% success rate
                    operators.extend([op] * 2)  # Add extra instances
        
        op = random.choice(operators)
        
        # Generate numbers based on difficulty
        if op in ['+', '-']:
            max_num = int(50 * difficulty)
            a = random.randint(1, max_num)
            b = random.randint(1, max_num)
            if op == '-' and difficulty < 0.7:  # Ensure positive results for lower difficulties
                a, b = max(a, b), min(a, b)
        else:  # multiplication and division
            max_num = int(12 * difficulty)
            a = random.randint(1, max_num)
            b = random.randint(1, max_num)
            if op == '/':  # ensure clean division
                a = a * b  # This guarantees clean division
        
        # Calculate answer and update stats
        if op == '+': 
            answer = a + b
            game_stats['problems_by_type']['addition'] += 1
        elif op == '-': 
            answer = a - b
            game_stats['problems_by_type']['subtraction'] += 1
        elif op == '*': 
            answer = a * b
            game_stats['problems_by_type']['multiplication'] += 1
        else: 
            answer = a / b
            game_stats['problems_by_type']['division'] += 1
        
        # Track problem for analytics
        problem_start_time = datetime.datetime.now()
        game_stats['current_problem'] = {
            'type': op,
            'start_time': problem_start_time,
            'numbers': (a, b),
            'answer': answer
        }
        
        problem_answer.set(str(answer))
        return f"{a} {op} {b} = ?"
        
def get_hint():
    """Generate a helpful hint for the current problem"""
    if 'current_problem' not in game_stats:
        return "Solve the problem step by step!"
        
    problem = game_stats['current_problem']
    op = problem['type']
    a, b = problem['numbers']
    
    hints = {
        '+': [
            f"Try counting up from {min(a, b)}",
            "Break it into smaller parts",
            f"Think: {min(a, b)} + 10 would be {min(a, b) + 10}"
        ],
        '-': [
            "Count down from the larger number",
            f"What number plus {b} equals {a}?",
            f"Try counting up from {b} to {a}"
        ],
        '*': [
            f"Think of it as adding {a}, {b} times",
            f"If {a}×5={a*5}, what's {a}×{b}?",
            "Break into easier multiplication and add"
        ],
        '/': [
            f"What times {b} equals {a}?",
            f"This is the same as {a} ÷ {b}",
            "Think of it as fair sharing"
        ]
    }
    
    # Use player's history to give more specific hints
    if 'problem_success_rate' in game_stats:
        success_rate = game_stats['problem_success_rate'].get(op, 1.0)
        if success_rate < 0.5:  # If player struggles with this operator
            if op == '+':
                return f"Try adding tens first: {a} = {(a//10)*10} + {a%10}"
            elif op == '-':
                return f"Start from {a} and count down {b} numbers"
            elif op == '*':
                return f"Break it down: {a}×{b} = {a}×{b//2} + {a}×{b//2}"
            elif op == '/':
                return f"What number times {b} gives you {a}?"
    
    return random.choice(hints[op])

    def check_answer():
        """Check if the answer is correct"""
        try:
            user_answer = float(answer_entry.get())
            correct_answer = float(problem_answer.get())
            if abs(user_answer - correct_answer) < 0.01:  # allow small rounding errors for division
                # Update streak and stats
                game_stats['streak'] += 1
                game_stats['max_streak'] = max(game_stats['max_streak'], game_stats['streak'])
                
                # Correct answer
                score.set(score.get() + 1)
                total_correct.set(total_correct.get() + 1)  # increment total correct
                result_label.config(text="✓", fg="green")
                # Play correct sound (high beep)
                winsound.Beep(1000, 200)  # 1000 Hz for 200ms
                if score.get() >= goal.get():
                    next_level()
                else:
                    problem_label.config(text=generate_problem())
            else:
                # Wrong answer
                game_stats['streak'] = 0  # Reset streak on wrong answer
                game_stats['no_mistakes'] = False  # Mark that there was a mistake
                wrong_answers.set(wrong_answers.get() + 1)
                result_label.config(text="X", fg="red")
                # Play wrong sound (low beep)
                winsound.Beep(250, 300)  # 250 Hz for 300ms
                if wrong_answers.get() >= 3:
                    game_over()
                else:
                    problem_label.config(text=generate_problem())
            answer_entry.delete(0, tk.END)
            update_status()
            # Clear the result after 1 second
            window.after(1000, lambda: result_label.config(text=""))
        except ValueError:
            # Invalid input - do nothing
            pass

    def next_level():
        """Advance to next level"""
        new_level = current_level.get() + 1
        current_level.set(new_level)
        goal.set(goal.get() + 5)
        score.set(0)
        wrong_answers.set(0)
        
        # Update level time
        now = datetime.datetime.now()
        game_stats['level_time'] = (now - game_stats['level_start_time']).total_seconds()
        game_stats['total_time'] += game_stats['level_time']
        game_stats['level_start_time'] = now
        
        # Save profile progress when advancing levels with win result
        save_profile(current_profile, new_level, total_correct.get(), 'win', game_stats)
        update_status()
        problem_label.config(text=generate_problem())
        level_label.config(text=f"Level {new_level}")
        # Play victory sound for level up
        winsound.Beep(1500, 150)
        winsound.Beep(2000, 150)

    def game_over(reason="mistakes"):
        """Handle game over state"""
        # Update final timing stats
        now = datetime.datetime.now()
        game_stats['level_time'] = (now - game_stats['level_start_time']).total_seconds()
        game_stats['total_time'] += game_stats['level_time']
        
        # Save final scores to profile with game result
        save_profile(current_profile, current_level.get(), total_correct.get(), 'lose', game_stats)
        problem_label.config(text="Game Over!")
        answer_entry.config(state='disabled')
        submit_btn.config(state='disabled')
        # Play game over sound
        winsound.Beep(500, 200)
        winsound.Beep(350, 400)

    def update_achievements_display():
        """Update the achievements display"""
        profiles = load_profiles()
        profile = profiles.get(current_profile, {})
        achievements = profile.get('achievements', [])
        
        achievements_text.config(state='normal')
        achievements_text.delete('1.0', tk.END)
        
        for achievement_id in achievements:
            if achievement_id in ACHIEVEMENTS:
                achievement = ACHIEVEMENTS[achievement_id]
                achievements_text.insert(tk.END, 
                    f"{achievement['icon']} {achievement['name']}\n")
        
        achievements_text.config(state='disabled')

    def update_status():
        """Update the status display"""
        profiles = load_profiles()
        profile = profiles.get(current_profile, {
            'highest_level': 1, 
            'total_correct': 0,
            'games_played': 0,
            'games_won': 0,
            'avatar': '👤'
        })
        
        # Calculate win rate
        games_played = profile.get('games_played', 0)
        win_rate = (profile.get('games_won', 0) / games_played * 100) if games_played > 0 else 0
        
        status_label.config(
            text=f"{profile['avatar']} Profile: {current_profile}\n" +
                 f"Score: {score.get()}/{goal.get()} | Wrong: {wrong_answers.get()}/3 | Level: {current_level.get()}\n" +
                 f"Best Level: {profile['highest_level']} | Total Correct: {profile['total_correct'] + total_correct.get()}\n" +
                 f"Games Played: {games_played} | Win Rate: {win_rate:.1f}%"
        )

    def back_to_menu():
        window.destroy()
        root.deiconify()

    def start_game(challenge_type=None):
        global game_stats
        # Reset game statistics
        game_stats.update({
            'start_time': datetime.datetime.now(),
            'level_start_time': datetime.datetime.now(),
            'streak': 0,
            'max_streak': 0,
            'no_mistakes': True,
            'problems_by_type': {'addition': 0, 'subtraction': 0, 'multiplication': 0, 'division': 0},
            'total_time': 0,
            'level_time': 0
        })
        
        # hide game_frame and show play_frame
        game_frame.pack_forget()
        play_frame.pack(fill="both", expand=True)
        
        # Reset game state
        score.set(0)
        wrong_answers.set(0)
        current_level.set(1)
        goal.set(10)
        total_correct.set(0)  # reset total correct for this session
        
        # Set up challenge mode if specified
        if challenge_type:
            challenge_label.config(text=f"Challenge Mode: {CHALLENGE_TYPES[challenge_type]['name']}")
            challenge_label.pack(pady=5)
            if challenge_type == 'speed':
                goal.set(10)  # First to 10 problems
            elif challenge_type == 'endurance':
                start_timer(300)  # 5 minutes
            elif challenge_type == 'precision':
                wrong_answers.set(0)
                max_wrong.set(3)  # 3 mistakes limit
        
        problem_label.config(text=generate_problem())
        result_label.config(text="")  # clear any previous result
        answer_entry.config(state='normal')
        submit_btn.config(state='normal')
        update_status()

    # Game frame content (instructions)
    scaled_font = ("Arial", game_layout.get_font_size(16))
    scaled_bold = ("Arial", game_layout.get_font_size(16), "bold")
    scaled_large = ("Arial", game_layout.get_font_size(20), "bold")
    
    instructions = tk.Label(game_frame, 
                          text="Solve math problems to advance levels!\nGet 3 wrong and it's game over.\nReach the goal to win each level!", 
                          font=scaled_font,
                          bg=THEME['background'])
    instructions.pack(padx=game_layout.get_widget_size(20)[0], 
                     pady=game_layout.get_widget_size(20)[1])
    
    # Update button style with scaled sizes
    game_button_style = button_style.copy()
    btn_width, btn_height = game_layout.get_widget_size(20, 2)
    game_button_style.update({
        'font': scaled_bold,
        'width': btn_width,
        'height': btn_height
    })
    
    tk.Button(game_frame, text="Start Game", command=start_game, 
              **game_button_style).pack(pady=game_layout.get_widget_size(6)[1])
    tk.Button(game_frame, text="Back to Menu", command=back_to_menu, 
              **game_button_style).pack(pady=game_layout.get_widget_size(6)[1])

    # Play frame content (game interface)
    level_label = tk.Label(play_frame, text="Level 1", 
                          font=scaled_large,
                          bg=THEME['background'])
    level_label.pack(pady=game_layout.get_widget_size(10)[1])
    
    # Challenge mode label
    challenge_label = tk.Label(play_frame, text="", 
                              font=scaled_bold, 
                              fg="purple",
                              bg=THEME['background'])
    
    # Timer label for timed challenges
    timer_label = tk.Label(play_frame, text="", 
                          font=scaled_font,
                          bg=THEME['background'])
    timer_var = tk.StringVar(value="")
    timer_active = False
    max_wrong = tk.IntVar(value=3)
    
    def start_timer(seconds):
        nonlocal timer_active
        timer_active = True
        timer_label.pack(pady=5)
        
        def update_timer():
            if timer_active and seconds > 0:
                mins, secs = divmod(seconds, 60)
                timer_var.set(f"Time: {mins:02d}:{secs:02d}")
                timer_label.config(text=timer_var.get())
                window.after(1000, update_timer)
            elif seconds <= 0:
                game_over("time")
        
        update_timer()
    
    status_label = tk.Label(play_frame, text="", 
                          font=scaled_font,
                          bg=THEME['background'])
    status_label.pack(pady=game_layout.get_widget_size(5)[1])
    
    # Achievements display with responsive layout
    achievements_frame = tk.Frame(play_frame, bg=THEME['background'])
    
    # Pack achievements on right in landscape, bottom in portrait
    def update_achievements_layout(orientation):
        achievements_frame.pack_forget()
        if orientation == "portrait":
            achievements_frame.pack(side=tk.BOTTOM, fill="x", 
                                 padx=game_layout.get_widget_size(10)[0])
        else:
            achievements_frame.pack(side=tk.RIGHT, fill="y",
                                 padx=game_layout.get_widget_size(10)[0])
    
    update_achievements_layout(game_layout.current_orientation)
    game_layout.on_orientation_change = update_achievements_layout
    
    tk.Label(achievements_frame, text="🏅 Achievements 🏅", 
             font=scaled_bold,
             bg=THEME['background']).pack(pady=game_layout.get_widget_size(5)[1])
    
    # Scale text widget size based on orientation
    def get_achievement_size():
        if game_layout.current_orientation == "portrait":
            return game_layout.get_widget_size(60, 6)  # wider, shorter in portrait
        return game_layout.get_widget_size(25, 8)  # narrower, taller in landscape
    
    width, height = get_achievement_size()
    achievements_text = tk.Text(achievements_frame, 
                              font=scaled_font,
                              width=width, height=height,
                              bg='#f0f0f0',
                              relief='ridge')
    achievements_text.pack(pady=game_layout.get_widget_size(5)[1])
    achievements_text.config(state='disabled')
    
    # Frame to hold problem and result side by side
    problem_frame = tk.Frame(play_frame, bg=THEME['background'])
    problem_frame.pack(pady=game_layout.get_widget_size(20)[1])
    
    # Use larger font for math problem
    problem_font = ("Arial", game_layout.get_font_size(24))
    problem_font_bold = ("Arial", game_layout.get_font_size(24), "bold")
    
    problem_label = tk.Label(problem_frame, text="", 
                           font=problem_font,
                           bg=THEME['background'])
    problem_label.pack(side=tk.LEFT, padx=game_layout.get_widget_size(5)[0])
    
    # Label for showing ✓ or X
    result_label = tk.Label(problem_frame, text="", 
                          font=problem_font_bold,
                          bg=THEME['background'])
    result_label.pack(side=tk.LEFT, padx=game_layout.get_widget_size(5)[0])
    
    answer_frame = tk.Frame(play_frame, bg=THEME['background'])
    answer_frame.pack(pady=game_layout.get_widget_size(10)[1])
    
    # Scale entry width based on screen size
    entry_width = game_layout.get_widget_size(10)[0]
    answer_entry = tk.Entry(answer_frame, 
                          font=("Arial", game_layout.get_font_size(18)),
                          width=min(20, max(8, entry_width // 20)))  # scale width but keep reasonable
    answer_entry.pack(side=tk.LEFT, padx=game_layout.get_widget_size(5)[0])
    answer_entry.bind('<Return>', lambda e: check_answer())
    
    # Enable touch keyboard for answer entry (numeric only)
    if touch_mgr and touch_mgr.touch_enabled:
        touch_mgr.bind_touch_events(answer_entry)
        # Configure as numeric entry
        answer_entry.configure(validate='numeric')
    
    # Update button style with game-scaled sizes
    submit_btn_style = game_button_style.copy()
    submit_btn_style.update({
        'font': ("Arial", game_layout.get_font_size(14), "bold")
    })
    submit_btn = tk.Button(answer_frame, text="Submit", 
                         command=check_answer, 
                         **submit_btn_style)
    submit_btn.pack(side=tk.LEFT, padx=game_layout.get_widget_size(5)[0])
    
    tk.Button(play_frame, text="Back to Menu", command=back_to_menu, **button_style).pack(pady=10)

    # show the game frame initially
    game_frame.pack(fill="both", expand=True)

    # Expose key widgets/vars for automated tests or external control
    try:
        globals().update({
            'AUT_window': window,
            'AUT_answer_entry': answer_entry,
            'AUT_submit_btn': submit_btn,
            'AUT_problem_label': problem_label,
            'AUT_problem_answer': problem_answer,
            'AUT_score_var': score,
            'AUT_goal_var': goal,
            'AUT_current_level_var': current_level,
            'AUT_wrong_answers_var': wrong_answers
        })
    except Exception:
        pass

# wire the button after the function is defined
START.config(command=START_press)

# start the Tk event loop
root.mainloop()
