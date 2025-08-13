# main.py
import os
import time
import csv
import threading
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

# Try to import PyJNIus (Android). If unavailable (desktop), fall back to /proc parsing.
try:
    from jnius import autoclass
    _HAS_JNIUS = True
except Exception:
    _HAS_JNIUS = False

import os as _os

# ---------- helpers to fetch PID & memory ----------
def get_pid():
    """Return current process PID (int)."""
    try:
        # Prefer android.os.Process.myPid() if JNI available
        if _HAS_JNIUS:
            Process = autoclass('android.os.Process')
            return int(Process.myPid())
    except Exception:
        pass
    # fallback to Python
    return _os.getpid()

def read_proc_meminfo():
    out = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                k, v = line.split(':', 1)
                out[k.strip()] = int(v.strip().split()[0])  # kB
    except Exception:
        pass
    return out

def read_proc_status(pid):
    """Parse /proc/<pid>/status for VmRSS / VmSize (kB)"""
    path = f'/proc/{pid}/status'
    res = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                if line.startswith('VmRSS:') or line.startswith('VmSize:') or line.startswith('VmPeak:'):
                    k, v = line.split(':', 1)
                    res[k.strip()] = int(v.strip().split()[0])
    except Exception:
        pass
    return res

def get_memory_info_jnius(pid):
    """
    Returns dict with:
      totalMem_kb, availMem_kb, lowMemory (bool),
      pss_kb (getTotalPss), private_dirty_kb (getTotalPrivateDirty)
    """
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        ActivityManager = autoclass('android.app.ActivityManager')
        Process = autoclass('android.os.Process')

        activity = PythonActivity.mActivity
        am = activity.getSystemService(Context.ACTIVITY_SERVICE)
        mi = ActivityManager.MemoryInfo()
        am.getMemoryInfo(mi)

        # getProcessMemoryInfo expects an int[]; passing [pid] works with pyjnius
        pinfo = am.getProcessMemoryInfo([int(pid)])[0]  # Debug.MemoryInfo
        return {
            'totalMem_kb': int(mi.totalMem / 1024),  # convert bytes -> kB
            'availMem_kb': int(mi.availMem / 1024),
            'lowMemory': bool(mi.lowMemory),
            'pss_kb': int(pinfo.getTotalPss()),  # already kB
            'private_dirty_kb': int(pinfo.getTotalPrivateDirty())
        }
    except Exception:
        return None

def get_memory_snapshot(pid):
    """
    Try priority:
      1) PyJNIus ActivityManager + getProcessMemoryInfo -> best (PSS)
      2) fallback -> parse /proc/meminfo and /proc/<pid>/status
    """
    if _HAS_JNIUS:
        jinfo = get_memory_info_jnius(pid)
        if jinfo:
            return jinfo

    # fallback: /proc parsing (kB)
    sysinfo = read_proc_meminfo()
    procinfo = read_proc_status(pid)
    return {
        'totalMem_kb': sysinfo.get('MemTotal', -1),
        'availMem_kb': sysinfo.get('MemAvailable', sysinfo.get('MemFree', -1)),
        'lowMemory': False,
        'pss_kb': procinfo.get('VmRSS', -1),  # RSS used as fallback for PSS
        'private_dirty_kb': -1
    }

def kb_to_mb(kb):
    try:
        return kb / 1024.0
    except Exception:
        return -1.0

# ---------- Complex operation (demo) ----------
def demo_complex_operation(stop_event, duration_sec=180):
    """
    Simulate a memory- and CPU-heavy operation for `duration_sec`.
    This creates and releases bytearrays to simulate allocations and churn.
    Runs until time is up or stop_event is set.
    """
    print("[demo] complex operation started for", duration_sec, "seconds")
    end_time = time.time() + duration_sec
    allocated = []
    try:
        while time.time() < end_time and not stop_event.is_set():
            # Allocate several 5 MB chunks to create pressure, then sleep shortly.
            try:
                for _ in range(6):
                    # allocate ~5 MB
                    allocated.append(bytearray(5 * 1024 * 1024))
                # occasionally free half of them to allow GC / freeing
                if len(allocated) > 30:
                    # drop some references (allow GC)
                    allocated = allocated[10:]
            except MemoryError:
                # if device hits OOM, clear allocated list and continue carefully
                allocated = []
            # small compute to simulate CPU work
            s = 0
            for i in range(100000):
                s += (i ^ (i << 1)) & 0xFF
            # small pause
            time.sleep(0.25)
    finally:
        # free memory references and hint GC
        allocated = None
        print("[demo] complex operation finished or stopped")

# ---------- Kivy UI App ----------
class MemMonitorApp(App):
    def build(self):
        self.pid = get_pid()
        self.sampling = False
        self.samples = []  # list of dicts
        self.stop_event = threading.Event()
        self.task_thread = None
        self.sample_interval = 1.0  # seconds
        self.duration_sec = 180  # 3 minutes

        root = BoxLayout(orientation='vertical', padding=8, spacing=8)

        # Info row (PID + buttons)
        info_row = BoxLayout(size_hint_y=None, height='48dp', spacing=8)
        self.pid_label = Label(text=f"PID: {self.pid}", size_hint_x=0.4)
        self.status_label = Label(text="Status: idle", size_hint_x=0.6)
        info_row.add_widget(self.pid_label)
        info_row.add_widget(self.status_label)
        root.add_widget(info_row)

        # Buttons
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing=8)
        self.start_btn = Button(text="Start 3-min test", on_press=self.start_test)
        self.stop_btn = Button(text="Stop", on_press=self.stop_test, disabled=True)
        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.stop_btn)
        root.add_widget(btn_row)

        # Scrollable grid for live stats
        scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        # Summary / path label
        self.out_label = Label(text="No log saved yet.", size_hint_y=None, height='40dp')
        root.add_widget(self.out_label)

        return root

    def add_line(self, text):
        lbl = Label(text=text, size_hint_y=None, height='28dp', halign='left', valign='middle')
        lbl.text_size = (self.grid.width - 50, None)
        self.grid.add_widget(lbl)
        # keep scroll to bottom by scheduling an adjustment
        Clock.schedule_once(lambda dt: self.grid.canvas.ask_update())

    def start_test(self, _btn):
        if self.sampling:
            return
        self.sampling = True
        self.samples = []
        self.stop_event.clear()
        self.status_label.text = "Status: running"
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.grid.clear_widgets()
        self.add_line(f"Starting 3-minute memory test at {datetime.utcnow().isoformat()} UTC")
        # launch heavy background task
        self.task_thread = threading.Thread(target=demo_complex_operation, args=(self.stop_event, self.duration_sec), daemon=True)
        self.task_thread.start()
        # start sampling (Clock runs on main thread)
        self._samples_taken = 0
        self._max_samples = int(self.duration_sec / self.sample_interval)
        self._start_time = time.time()
        Clock.schedule_interval(self._sample_tick, self.sample_interval)

    def stop_test(self, _btn=None):
        if not self.sampling:
            return
        self.sampling = False
        self.stop_event.set()
        self.status_label.text = "Status: stopping..."
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        # ensure clock unscheduled next tick by setting sampling false; also write file
        self._write_csv()

    def _sample_tick(self, dt):
        if not self.sampling:
            return False  # unschedule
        now = datetime.utcnow()
        pid = self.pid
        info = get_memory_snapshot(pid)
        sample = {
            'timestamp': now.isoformat(),
            'pid': pid,
            'pss_kb': info.get('pss_kb'),
            'private_dirty_kb': info.get('private_dirty_kb'),
            'totalMem_kb': info.get('totalMem_kb'),
            'availMem_kb': info.get('availMem_kb'),
            'lowMemory': info.get('lowMemory')
        }
        self.samples.append(sample)
        self._samples_taken += 1

        # Update UI
        line = (f"[{sample['timestamp']}] PSS={kb_to_mb(sample['pss_kb']):.2f} MB, "
                f"Avail={kb_to_mb(sample['availMem_kb']):.2f} MB, Low={sample['lowMemory']}")
        self.add_line(line)

        # stop if duration reached
        elapsed = time.time() - self._start_time
        if elapsed >= self.duration_sec:
            # mark finished
            self.sampling = False
            self.stop_event.set()
            self.status_label.text = "Status: finished"
            self.start_btn.disabled = False
            self.stop_btn.disabled = True
            self._write_csv()
            return False  # unschedule
        return True  # schedule again

    def _write_csv(self):
        if not self.samples:
            self.out_label.text = "No samples to save."
            return

        # save to app user data dir
        try:
            user_dir = self.user_data_dir
        except Exception:
            user_dir = os.getcwd()
        filename = f"mem_samples_{int(time.time())}.csv"
        path = os.path.join(user_dir, filename)
        try:
            with open(path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['timestamp', 'pid', 'pss_kb', 'private_dirty_kb', 'totalMem_kb', 'availMem_kb', 'lowMemory'])
                for s in self.samples:
                    writer.writerow([s['timestamp'], s['pid'], s['pss_kb'], s['private_dirty_kb'], s['totalMem_kb'], s['availMem_kb'], s['lowMemory']])
            self.out_label.text = f"Saved CSV: {path}"
            self.add_line(f"Saved CSV: {path}")
        except Exception as e:
            self.out_label.text = f"Failed to save CSV: {e}"
            self.add_line(f"Failed to save CSV: {e}")

if __name__ == '__main__':
    MemMonitorApp().run()
