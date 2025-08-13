import os
import time
import csv
import threading
from datetime import datetime

# platform / Android cache handling
from kivy.utils import platform as kivy_platform
if kivy_platform == 'android':
    # Import Android permissions classes
    from android.permissions import request_permissions, Permission
    try:
        from android.storage import app_storage_path
        cache_dir = os.path.join(app_storage_path(), '.cache')
        os.environ['HF_HOME'] = cache_dir
        os.environ['XDG_CACHE_HOME'] = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning setting Android cache path: {e}")

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.utils.set_bars_colors import set_bars_colors
# --- Refactored UI Imports ---
# Import modern KivyMD components based on the reference code
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)
from kivymd.uix.appbar import (
    MDTopAppBar,
    MDTopAppBarLeadingButtonContainer,
    MDActionTopAppBarButton,
    MDTopAppBarTitle,
)
# --- Added missing button imports ---
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.divider import MDDivider
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList
from kivymd.uix.boxlayout import MDBoxLayout


# Try PyJNIus for Android memory APIs; fallback to /proc parsing
try:
    from jnius import autoclass
    _HAS_JNIUS = True
except Exception:
    _HAS_JNIUS = False

import os as _os

# ------------------ Memory helpers ------------------
def get_pid():
    """Get the current process ID."""
    try:
        if _HAS_JNIUS:
            Process = autoclass('android.os.Process')
            return int(Process.myPid())
    except Exception:
        pass
    return _os.getpid()

def read_proc_meminfo():
    """Read /proc/meminfo for system memory details."""
    out = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                k, v = line.split(':', 1)
                out[k.strip()] = int(v.strip().split()[0])
    except Exception:
        pass
    return out

def read_proc_status(pid):
    """Read /proc/{pid}/status for process memory details."""
    path = f'/proc/{pid}/status'
    res = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                if line.startswith(('VmRSS:', 'VmSize:', 'VmPeak:')):
                    k, v = line.split(':', 1)
                    res[k.strip()] = int(v.strip().split()[0])
    except Exception:
        pass
    return res

def get_memory_info_jnius(pid):
    """Get detailed memory info on Android using JNIus."""
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        ActivityManager = autoclass('android.app.ActivityManager')

        activity = PythonActivity.mActivity
        am = activity.getSystemService(Context.ACTIVITY_SERVICE)
        mi = ActivityManager.MemoryInfo()
        am.getMemoryInfo(mi)

        pinfo = am.getProcessMemoryInfo([int(pid)])[0]
        return {
            'totalMem_kb': int(mi.totalMem / 1024),
            'availMem_kb': int(mi.availMem / 1024),
            'lowMemory': bool(mi.lowMemory),
            'pss_kb': int(pinfo.getTotalPss()),
            'private_dirty_kb': int(pinfo.getTotalPrivateDirty())
        }
    except Exception:
        return None

def get_memory_snapshot(pid):
    """Get a snapshot of memory usage, using JNIus if available."""
    if _HAS_JNIUS:
        jinfo = get_memory_info_jnius(pid)
        if jinfo:
            return jinfo
    sysinfo = read_proc_meminfo()
    procinfo = read_proc_status(pid)
    return {
        'totalMem_kb': sysinfo.get('MemTotal', -1),
        'availMem_kb': sysinfo.get('MemAvailable', sysinfo.get('MemFree', -1)),
        'lowMemory': False,
        'pss_kb': procinfo.get('VmRSS', -1),
        'private_dirty_kb': -1
    }

def kb_to_mb(kb):
    """Convert kilobytes to megabytes."""
    try:
        return kb / 1024.0
    except Exception:
        return -1.0

# ------------------ Demo complex operation ------------------
def demo_complex_operation(stop_event, duration_sec=180):
    """A function that simulates a memory and CPU intensive task."""
    end_time = time.time() + duration_sec
    allocated = []
    try:
        while time.time() < end_time and not stop_event.is_set():
            try:
                # Allocate memory in chunks
                for _ in range(6):
                    # MODIFIED: Changed allocation from 5MB to 100KB
                    allocated.append(bytearray(100 * 1024)) # 100KB
                # Release old memory to keep usage fluctuating
                if len(allocated) > 40:
                    allocated = allocated[10:]
            except MemoryError:
                allocated = []
            # Simulate CPU work
            s = 0
            for i in range(50000):
                s += (i ^ (i << 1)) & 0xFF
            time.sleep(0.25)
    finally:
        allocated = None

# ------------------ KV Language UI Definition (Refactored) ------------------
KV = '''
# Root layout is now a vertical MDBoxLayout to ensure the top bar is at the top.
MDBoxLayout:
    orientation: "vertical"

    MDTopAppBar:
        # Using the declarative style from the reference app for a modern look
        MDTopAppBarLeadingButtonContainer:
            MDActionTopAppBarButton:
                icon: "menu"
                on_release: app.on_menu()
        MDTopAppBarTitle:
            text: "Memory Monitor"
            pos_hint: {"center_x": 0.5}
        MDActionTopAppBarButton:
            icon: "theme-light-dark"
            on_release: app.toggle_theme()

    MDScreen:
        # Content layout is now vertical and responsive.
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(12)

            # Control Panel Card: spans width, height is adaptive to content.
            MDCard:
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                orientation: "vertical"
                elevation: 2
                radius: [12,]

                MDLabel:
                    id: pid_label
                    text: "PID: --"
                    halign: "left"
                    adaptive_height: True

                MDLabel:
                    id: status_label
                    text: "Status: idle"
                    halign: "left"
                    adaptive_height: True

                MDDivider:
                    height: dp(12)

                MDLabel:
                    text: "Live Memory"
                    adaptive_height: True
                    font_style: "Title"
                    role: "medium"

                MDLabel:
                    id: pss_label
                    text: "PSS: -- MB"
                    halign: "left"
                    adaptive_height: True

                MDLabel:
                    id: avail_label
                    text: "Available RAM: -- MB"
                    halign: "left"
                    adaptive_height: True

                MDLabel:
                    id: low_label
                    text: "Low memory: --"
                    halign: "left"
                    adaptive_height: True
                
                MDBoxLayout: # Spacer
                    adaptive_height: True
                    padding: dp(8)

                # --- Buttons ---
                MDBoxLayout:
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(8)
                    adaptive_size: True
                    pos_hint: {"center_x": 0.5}

                    MDButton:
                        id: start_btn
                        on_release: app.start_test()
                        MDButtonText:
                            text: "Start"

                    MDButton:
                        id: stop_btn
                        disabled: True
                        on_release: app.stop_test()
                        MDButtonText:
                            text: "Stop"

                    MDButton:
                        id: save_btn
                        on_release: app.save_csv()
                        MDButtonText:
                            text: "Save CSV"

            # Log Card: fills remaining vertical space.
            MDCard:
                padding: dp(12)
                orientation: "vertical"
                elevation: 2
                radius: [12,]

                MDLabel:
                    text: "Live Log"
                    adaptive_height: True
                    font_style: "Title"
                    role: "medium"

                MDScrollView:
                    id: scroll
                    MDList:
                        id: log_grid
                        
        MDBoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(12)
            MDLabel:
                id: footer_label
                text: "Ready."
                halign: "left"
'''

# ------------------ App Class ------------------
class MemMonitorApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.sample_interval = 1.0
        self.duration_sec = 180
        self.pid = get_pid()
        self.sampling = False
        self.samples = []
        self.stop_event = threading.Event()
        self.task_thread = None

    def build(self):
        """Builds the app from the KV string."""
        self.root = Builder.load_string(KV)
        # Style application is moved to on_start for robustness
        return self.root
    
    def on_start(self):
        """Called on app startup. Handles permissions and initial styling."""
        if kivy_platform == 'android':
            try:
                # Request storage permissions for saving files publicly
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            except Exception as e:
                print(f"Failed to request permissions: {e}")
        
        # Apply theme and status bar colors once the app window is ready
        self.apply_styles(self.theme_cls.theme_style)
        self.root.ids.pid_label.text = f"PID: {self.pid}"

    def apply_styles(self, style: str) -> None:
        """Applies the color and icon styles for the app."""
        self.theme_cls.theme_style = style
        icon_style = "Dark" if style == "Light" else "Light"
        self.set_bars_colors(self.theme_cls.surfaceColor, self.theme_cls.surfaceColor, icon_style)
        Window.clearcolor = self.theme_cls.backgroundColor

    def set_bars_colors(self, status_color, nav_color, style):
        """A helper to set the system bar colors."""
        try:
            set_bars_colors(status_color, nav_color, style)
        except Exception as e:
            print(f"Could not set bar colors: {e}")

    def toggle_theme(self):
        """Switches the theme between Light and Dark."""
        new_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        self.apply_styles(new_style)

    def on_menu(self):
        """Callback for the menu button press."""
        self.root.ids.footer_label.text = "Menu pressed"

    # ---- Test controls ----
    def start_test(self):
        """Starts the memory sampling and the background task."""
        if self.sampling:
            return
        self.sampling = True
        self.samples = []
        self.stop_event.clear()
        self.root.ids.status_label.text = "Status: running"
        self.root.ids.start_btn.disabled = True
        self.root.ids.stop_btn.disabled = False
        self.root.ids.log_grid.clear_widgets()
        self._start_time = time.time()
        
        self.task_thread = threading.Thread(target=demo_complex_operation, args=(self.stop_event, self.duration_sec), daemon=True)
        self.task_thread.start()
        
        Clock.schedule_interval(self._sample_tick, self.sample_interval)

    def stop_test(self, finished=False):
        """Stops the memory sampling and the background task."""
        if not self.sampling:
            return
        self.sampling = False
        self.stop_event.set()
        Clock.unschedule(self._sample_tick)
        
        self.root.ids.status_label.text = "Status: finished" if finished else "Status: stopped"
        self.root.ids.start_btn.disabled = False
        self.root.ids.stop_btn.disabled = True
        
        Clock.schedule_once(lambda dt: self.save_csv(), 0.5)

    def _sample_tick(self, dt):
        """Called by the clock to take a memory sample. Now uses MDListItem."""
        if not self.sampling:
            return False
            
        now = datetime.utcnow()
        info = get_memory_snapshot(self.pid)
        sample = {
            'timestamp': now.isoformat(),
            'pid': self.pid,
            'pss_kb': info.get('pss_kb', -1),
            'private_dirty_kb': info.get('private_dirty_kb', -1),
            'totalMem_kb': info.get('totalMem_kb', -1),
            'availMem_kb': info.get('availMem_kb', -1),
            'lowMemory': info.get('lowMemory', False)
        }
        self.samples.append(sample)

        # Update UI labels
        self.root.ids.pss_label.text = f"PSS: {kb_to_mb(sample['pss_kb']):.2f} MB"
        self.root.ids.avail_label.text = f"Available RAM: {kb_to_mb(sample['availMem_kb']):.2f} MB"
        self.root.ids.low_label.text = f"Low memory: {sample['lowMemory']}"

        # Add a new entry to the log using the structured MDListItem
        headline = f"[{now.strftime('%H:%M:%S')}] PSS: {kb_to_mb(sample['pss_kb']):.1f}MB"
        supporting = f"Avail: {kb_to_mb(sample['availMem_kb']):.1f}MB | Low Mem: {sample['lowMemory']}"
        
        list_item = MDListItem(
            MDListItemHeadlineText(text=headline),
            MDListItemSupportingText(text=supporting),
        )
        self.root.ids.log_grid.add_widget(list_item)
        
        # Auto-scroll to the bottom to show the latest log entry
        Clock.schedule_once(lambda dt, scroll_to=list_item: self.root.ids.scroll.scroll_to(scroll_to), 0.05)

        # Check if the test duration has elapsed
        elapsed = time.time() - self._start_time
        if elapsed >= self.duration_sec:
            self.stop_test(finished=True)
            return False
        return True

    def save_csv(self):
        """Saves the collected samples to a CSV file in the public Downloads folder."""
        if not self.samples:
            self.root.ids.footer_label.text = "No samples to save."
            return

        def get_save_path():
            """Helper to determine the correct cross-platform save directory."""
            filename = f"mem_samples_{int(time.time())}.csv"
            
            if kivy_platform == 'android':
                try:
                    from jnius import autoclass
                    # Get the public downloads directory path
                    Environment = autoclass('android.os.Environment')
                    downloads_dir = Environment.getExternalStoragePublicDirectory(
                        Environment.DIRECTORY_DOWNLOADS
                    ).getAbsolutePath()
                    
                    # Ensure the directory exists
                    os.makedirs(downloads_dir, exist_ok=True)
                    return os.path.join(downloads_dir, filename)
                except Exception as e:
                    print(f"Could not access public Downloads folder: {e}. Falling back to private storage.")
                    # Fallback to app-specific external storage which is always writable without special permissions
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    context = PythonActivity.mActivity
                    fallback_dir = context.getExternalFilesDir(None).getAbsolutePath()
                    os.makedirs(fallback_dir, exist_ok=True)
                    return os.path.join(fallback_dir, filename)
            else:
                # For desktop (Windows, macOS, Linux), save to user's Downloads folder
                home_dir = os.path.expanduser('~')
                downloads_dir = os.path.join(home_dir, 'Downloads')
                os.makedirs(downloads_dir, exist_ok=True)
                return os.path.join(downloads_dir, filename)

        try:
            path = get_save_path()
            with open(path, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'pid', 'pss_kb', 'private_dirty_kb', 'totalMem_kb', 'availMem_kb', 'lowMemory']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.samples)
            
            # Update the footer with a more user-friendly message
            self.root.ids.footer_label.text = f"Saved to Downloads"
            print(f"CSV saved to: {path}")
        except Exception as e:
            error_msg = f"Error saving CSV: {e}"
            self.root.ids.footer_label.text = error_msg
            print(error_msg)


if __name__ == "__main__":
    MemMonitorApp().run()
