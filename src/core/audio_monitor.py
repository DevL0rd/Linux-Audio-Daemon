import subprocess
import threading
import re
import time

class AudioMonitor:
    def __init__(self, on_change_callback):
        self.on_change = on_change_callback
        
    def start(self):
        t = threading.Thread(target=self._listen_pactl, daemon=True)
        t.start()
        
    def _listen_pactl(self):
        try:
            # pactl subscribe prints live events whenever an audio device is added/removed
            process = subprocess.Popen(["pactl", "subscribe"], stdout=subprocess.PIPE, text=True)
            for line in process.stdout:
                if "sink" in line.lower() or "source" in line.lower():
                    if "new" in line.lower() or "remove" in line.lower() or "change" in line.lower():
                        # Give wireplumber a split second to settle before parsing
                        time.sleep(0.1)
                        self.on_change()
        except Exception as e:
            print(f"[Audio Monitor] Error starting pactl subscribe: {e}")

    def get_current_devices(self):
        devices = []
        try:
            out = subprocess.check_output(["wpctl", "status"]).decode()
        except Exception as e:
            print(f"[Audio Monitor] Error running wpctl: {e}")
            return devices
            
        current_section = None
        for line in out.splitlines():
            # Detect sections like " ├─ Sinks:"
            match = re.search(r'[├└]─\s+([A-Za-z]+):', line)
            if match:
                current_section = match.group(1)
                continue
                
            if current_section in ["Sinks", "Sources"]:
                clean_line = line.replace("*", "").strip(' │\t\n\r')
                if not clean_line: continue
                if clean_line.startswith("├─") or clean_line.startswith("└─"): continue
                
                # Extract ID and Name, ignoring the [vol: X] at the end
                m = re.search(r'^(\d+)\.\s+(.*?)(?:\s+\[.*\])?$', clean_line)
                if m:
                    node_id = m.group(1)
                    name = m.group(2).strip()
                    is_sink = (current_section == "Sinks")
                    devices.append({
                        "id": node_id,
                        "name": name,
                        "is_sink": is_sink
                    })
        return devices