import subprocess
import threading
import json
import time

class AudioMonitor:
    def __init__(self, on_change_callback):
        self.on_change = on_change_callback
        self.last_snapshot = None

    def start(self):
        t = threading.Thread(target=self._listen_pactl, daemon=True)
        t.start()

    def _snapshot(self):
        # Identity of the current device set, ignoring transient state (volume, etc.)
        return frozenset(
            (d["id"], d["name"], d["is_sink"]) for d in self.get_current_devices()
        )

    def _listen_pactl(self):
        try:
            # Establish a baseline so a volume/port "change" event that leaves the
            # device set untouched does not look like a change on the first event.
            self.last_snapshot = self._snapshot()

            # pactl subscribe prints live events whenever an audio device is added/removed
            process = subprocess.Popen(["pactl", "subscribe"], stdout=subprocess.PIPE, text=True)
            for line in process.stdout:
                low = line.lower()
                # Match only real device objects, not playback streams: "sink-input"
                # contains "sink" and "source-output" contains "source", and both
                # spam 'change' events constantly during playback.
                if " on sink #" not in low and " on source #" not in low:
                    continue

                # Give wireplumber a split second to settle before parsing
                time.sleep(0.1)

                # Authoritative gate: only act when the actual device set changed.
                # pactl emits 'change' on a sink for every volume/port/state tweak,
                # which must NOT be treated as a device-list change.
                snapshot = self._snapshot()
                if snapshot != self.last_snapshot:
                    self.last_snapshot = snapshot
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