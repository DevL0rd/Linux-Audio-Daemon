import subprocess
import threading
import json
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

    def _get_devices_from_pactl(self, device_type):
        devices = []
        try:
            out = subprocess.check_output(["pactl", "-f", "json", "list", device_type]).decode()
            data = json.loads(out)
            for item in data:
                name = item.get("description")
                # PipeWire exposes its native WirePlumber ID inside PulseAudio properties
                props = item.get("properties", {})
                node_id = props.get("object.id")
                
                if name and node_id:
                    # Ignore loopback monitor devices to keep the config clean
                    if name.startswith("Monitor of "):
                        continue
                        
                    devices.append({
                        "id": str(node_id),
                        "name": name,
                        "is_sink": (device_type == "sinks")
                    })
        except Exception as e:
            print(f"[Audio Monitor] Error parsing JSON for {device_type}: {e}")
        return devices

    def get_current_devices(self):
        sinks = self._get_devices_from_pactl("sinks")
        sources = self._get_devices_from_pactl("sources")
        return sinks + sources