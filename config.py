import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"devices": {}}
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {"devices": {}}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def ensure_device_in_config(config, device_name, is_sink=True):
    changed = False
    if device_name not in config["devices"]:
        # We auto-assign priority based on device type guesses
        if "ROG DELTA II" in device_name.upper():
            device_type = "special_rog"
            priority = 100
            icon = "audio-headset"
        else:
            device_type = "generic"
            priority = 50
            icon = "audio-card"
            
        config["devices"][device_name] = {
            "type": device_type,
            "priority": priority,
            "icon": icon,
            "is_sink": is_sink
        }
        changed = True
    return changed