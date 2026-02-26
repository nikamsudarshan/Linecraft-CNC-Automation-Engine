import os
import subprocess
import time
import threading
import json
import uuid
import datetime
import signal

# CONFIG
AXICLI_PATH = "/path/to/your/env/bin/axicli"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_FILE = os.path.join(BASE_DIR, "pen_inventory.json")
SESSION_FILE = os.path.join(BASE_DIR, "session_state.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.py") # <--- TARGET THE SINGLE FILE

class PlotManager:
    def __init__(self):
        # QUEUE & STATE
        self.queue = []
        self.current_index = 0
        self.state = "IDLE"
        self.status_message = "Ready"

        # PREVIEWS
        self.current_project_path = None
        self.current_file = None
        self.next_file = None

        # PEN SYSTEM
        self.pens = {}
        self.current_pen_id = None

        # STATS
        self.start_time = 0
        self.session_ink_meters = 0.0

        # INIT
        self.load_inventory()
        self.load_session_state()

    # --- RECOVERY SYSTEM ---
    def save_session_state(self):
        data = {
            "project_path": self.current_project_path,
            "current_index": self.current_index,
            "session_ink": self.session_ink_meters,
            "start_time": self.start_time
        }
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def load_session_state(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r') as f:
                    data = json.load(f)
                    path = data.get("project_path")
                    if path and os.path.exists(path):
                        self.load_batch(path)
                        self.current_index = data.get("current_index", 0)
                        self.session_ink_meters = data.get("session_ink", 0.0)
                        self.start_time = data.get("start_time", 0)
                        self.update_file_pointers()
                        self.status_message = f"Recovered session at Card {self.current_index + 1}"
            except: pass

    def clear_session_state(self):
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)

    # --- QUEUE NAVIGATION ---
    def skip_forward(self):
        if self.state in ["PLOTTING"]: return False, "Cannot skip while plotting"
        if self.current_index < len(self.queue) - 1:
            self.current_index += 1
            self.update_file_pointers()
            self.save_session_state()
            self.status_message = f"Skipped to Card {self.current_index + 1}"
            return True, "Skipped Forward"
        return False, "End of Queue"

    def skip_backward(self):
        if self.state in ["PLOTTING"]: return False, "Cannot skip while plotting"
        if self.current_index > 0:
            self.current_index -= 1
            self.update_file_pointers()
            self.save_session_state()
            self.status_message = f"Rewound to Card {self.current_index + 1}"
            return True, "Skipped Backward"
        return False, "Start of Queue"

    def toggle_pause(self):
        if self.state == "PAUSED":
            self.state = "IDLE"
            self.status_message = "Resumed. Ready to start."
            return "RESUMED"
        else:
            self.state = "PAUSED"
            self.status_message = "⏸️ Queue PAUSED. Finish current card."
            return "PAUSED"

    # --- PEN INVENTORY ---
    def load_inventory(self):
        if os.path.exists(INVENTORY_FILE):
            try:
                with open(INVENTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.pens = data.get('pens', {})
                    self.current_pen_id = data.get('current_pen_id')
            except: self.create_default_inventory()
        else: self.create_default_inventory()

    def create_default_inventory(self):
        default_id = "default_pen"
        self.pens = {default_id: {"name": "Standard Black (200m)", "capacity": 200.0, "used": 0.0}}
        self.current_pen_id = default_id
        self.save_inventory()

    def save_inventory(self):
        data = {"current_pen_id": self.current_pen_id, "pens": self.pens}
        with open(INVENTORY_FILE, 'w') as f: json.dump(data, f, indent=4)

    def add_pen(self, name, capacity_meters):
        pen_id = str(uuid.uuid4())[:8]
        self.pens[pen_id] = {"name": name, "capacity": float(capacity_meters), "used": 0.0}
        self.current_pen_id = pen_id
        self.save_inventory()
        return pen_id

    def set_active_pen(self, pen_id):
        if pen_id in self.pens:
            self.current_pen_id = pen_id
            self.save_inventory()
            return True
        return False

    def deduct_ink(self, meters):
        if self.current_pen_id and self.current_pen_id in self.pens:
            self.pens[self.current_pen_id]['used'] += meters
            self.session_ink_meters += meters
            self.save_inventory()
            self.save_session_state()

    # --- QUEUE LOGIC ---
    def load_batch(self, project_path):
        self.current_project_path = project_path
        batch_dir = os.path.join(project_path, "generated_batch")
        if not os.path.exists(batch_dir): return False, "No batch folder"
        files = sorted([f for f in os.listdir(batch_dir) if f.endswith(".svg")])
        if not files: return False, "No SVGs found"

        self.batch_ink_stats = {}
        try:
            with open(os.path.join(batch_dir, "batch_stats.json"), 'r') as f: self.batch_ink_stats = json.load(f)
        except: pass

        self.queue = [os.path.join(batch_dir, f) for f in files]
        self.current_index = 0
        self.session_ink_meters = 0.0
        self.update_file_pointers()
        self.state = "IDLE"
        self.status_message = f"Loaded {len(self.queue)} files."
        self.save_session_state()
        return True, f"Loaded {len(self.queue)} files."

    def update_file_pointers(self):
        self.current_file = os.path.basename(self.queue[self.current_index]) if 0 <= self.current_index < len(self.queue) else None
        self.next_file = os.path.basename(self.queue[self.current_index + 1]) if 0 <= self.current_index + 1 < len(self.queue) else None

    def start_queue(self):
        if not self.queue: return False, "Queue empty"
        if self.state == "PAUSED": return False, "Queue is Paused"

        self.state = "PLOTTING"
        if self.start_time == 0: self.start_time = time.time()
        self.process_current_file()
        return True, "Batch Started"

    def process_current_file(self):
        if self.current_index >= len(self.queue):
            self.state = "COMPLETED"
            self.status_message = "Order Complete!"
            self.clear_session_state()
            return

        file_path = self.queue[self.current_index]
        self.status_message = f"Plotting {self.current_index + 1}/{len(self.queue)}..."
        t = threading.Thread(target=self._run_plot_thread, args=(file_path,))
        t.start()

    def _run_plot_thread(self, file_path):
        try:
            # 1. COMMAND CONSTRUCTION
            cmd = [AXICLI_PATH, file_path]

            # 2. CHECK FOR CONFIG FILE
            if os.path.exists(CONFIG_FILE):
                cmd += ['--config', CONFIG_FILE]
            else:
                # Safe Fallback if you delete the file by accident
                cmd += ['--speed_pendown', '25', '--speed_penup', '75']

            # 3. RUN PLOT
            subprocess.run(
                cmd,
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # 4. DEDUCT INK & CLEANUP
            fname = os.path.basename(file_path)
            self.deduct_ink(self.batch_ink_stats.get(fname, 0.5))

            subprocess.run([AXICLI_PATH, '--mode', 'manual', '--manual_cmd', 'disable_xy'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 5. NEXT STEP
            if self.state == "PAUSED":
                self.save_session_state()
                self.status_message = "⏸️ Paused. Check Quality. Resume to Reprint or Next to Skip."
            elif self.current_index + 1 < len(self.queue):
                self.state = "WAITING_FOR_PAPER"
                self.status_message = "⚠️ Change Paper -> Click Continue"
                self.save_session_state()
            else:
                self.state = "COMPLETED"
                self.status_message = "All done!"
                self.clear_session_state()

        except Exception as e:
            self.state = "ERROR"
            self.status_message = f"Error: {str(e)}"

    def user_continue(self):
        if self.state == "WAITING_FOR_PAPER":
            self.current_index += 1
            self.update_file_pointers()
            self.state = "PLOTTING"
            self.process_current_file()
            return True
        return False

manager = PlotManager()
