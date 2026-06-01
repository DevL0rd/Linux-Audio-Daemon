import subprocess
import threading
import time
import re

class BluetoothBatteryMonitor:
    def __init__(self, on_battery_callback):
        self.on_battery = on_battery_callback
        self.last_levels = {}
        
    def start(self):
        t = threading.Thread(target=self._poll_upower, daemon=True)
        t.start()
        
    def _poll_upower(self):
        while True:
            try:
                out = subprocess.check_output(["upower", "-d"]).decode()
                current_device = None
                current_name = None
                
                for line in out.splitlines():
                    line = line.strip()
                    
                    if line.startswith("Device:"):
                        current_device = line.split(":", 1)[1].strip()
                        current_name = "Bluetooth Headset" # fallback
                    elif current_device and line.startswith("model:"):
                        current_name = line.split(":", 1)[1].strip()
                    elif current_device and line.startswith("percentage:"):
                        m = re.search(r'(\d+)%', line)
                        if m:
                            level = int(m.group(1))
                            # Filter for bluetooth audio devices
                            if "headset_dev" in current_device or "bluez" in current_device:
                                self._evaluate(current_name, current_device, level)
            except Exception as e:
                print(f"[BT Battery] Error polling upower: {e}")
                
            # Check every 60 seconds
            time.sleep(60)

    def _evaluate(self, name, device_path, level):
        last = self.last_levels.get(device_path)
        if last != level:
            self.last_levels[device_path] = level
            self.on_battery(name, level)