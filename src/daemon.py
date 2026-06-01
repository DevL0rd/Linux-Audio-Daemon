import time
import subprocess
from core.config import load_config, save_config, ensure_device_in_config
from core.audio_monitor import AudioMonitor
from devices.rog_delta_ii import RogDeltaII

def send_notification(title, message, icon="audio-card", urgency="normal"):
    try:
        subprocess.run([
            "notify-send", 
            "-a", "Smart Audio Manager", 
            "-i", icon, 
            "-u", urgency, 
            title, 
            message
        ])
    except Exception as e:
        print(f"[Notify] Failed to send notification: {e}")

class PriorityRouter:
    def __init__(self):
        self.config = load_config()
        self.audio_monitor = AudioMonitor(self.on_system_audio_change)
        
        # State
        self.rog_connected = False
        self.current_sink_name = None
        self.current_source_name = None
        self.battery_last_notified = None
        
        self.rog_watcher = RogDeltaII({
            'on_connect': self.on_rog_connect,
            'on_disconnect': self.on_rog_disconnect,
            'on_battery': self.on_rog_battery
        })
        
    def start(self):
        print("Starting Smart Audio Manager...")
        self.audio_monitor.start()
        
        import threading
        t = threading.Thread(target=self.rog_watcher.listen, daemon=True)
        t.start()
        
        # Trigger initial evaluation
        self.evaluate_routing()
        
        # Keep daemon alive
        while True:
            time.sleep(1)
            
    def on_rog_connect(self):
        print("\n[Event] ROG Delta II Connected")
        self.rog_connected = True
        self.battery_last_notified = None
        self.evaluate_routing()
        
    def on_rog_disconnect(self):
        print("\n[Event] ROG Delta II Disconnected")
        self.rog_connected = False
        self.battery_last_notified = None
        self.evaluate_routing()
        
    def on_rog_battery(self, level):
        print(f"[Status] ROG Delta II Battery: {level}%")
        threshold = None
        urgency = "normal"
        icon = "battery-good"
        title = ""
        
        if level <= 10:
            threshold = "critical"
            urgency = "critical"
            icon = "battery-empty"
            title = "Headset Battery Critical"
        elif level <= 20:
            threshold = "low"
            urgency = "normal"
            icon = "battery-low"
            title = "Headset Battery Low"
            
        if threshold and self.battery_last_notified != threshold:
            self.battery_last_notified = threshold
            send_notification(title, f"ROG Delta II is at {level}%", icon, urgency)

    def on_system_audio_change(self):
        print("\n[Event] System Audio Devices Changed")
        self.evaluate_routing()
        
    def evaluate_routing(self):
        system_devices = self.audio_monitor.get_current_devices()
        config_changed = False
        
        # Auto-fill new devices into config
        for dev in system_devices:
            if ensure_device_in_config(self.config, dev["name"], dev["is_sink"]):
                config_changed = True
                
        if config_changed:
            save_config(self.config)
            
        # Determine available devices based on config and hardware status
        available_sinks = []
        available_sources = []
        
        for dev in system_devices:
            c_info = self.config["devices"].get(dev["name"])
            if not c_info: continue
            
            # Special hardware logic: Is the headset actually turned on?
            if c_info["type"] == "special_rog":
                if not self.rog_connected:
                    continue 
                    
            node = {
                "id": dev["id"],
                "name": dev["name"],
                "priority": c_info.get("priority", 0),
                "icon": c_info.get("icon", "audio-card")
            }
            
            if dev["is_sink"]:
                available_sinks.append(node)
            else:
                available_sources.append(node)
            
        # Sort highest priority first
        available_sinks.sort(key=lambda x: x["priority"], reverse=True)
        available_sources.sort(key=lambda x: x["priority"], reverse=True)
        
        # 1. Route Sink (Output)
        if available_sinks:
            best_sink = available_sinks[0]
            if self.current_sink_name != best_sink["name"]:
                print(f"[Router] Switching output to: {best_sink['name']} (Priority: {best_sink['priority']})")
                subprocess.run(["wpctl", "set-default", best_sink["id"]])
                
                if self.config["devices"][best_sink["name"]]["type"] == "special_rog":
                     send_notification("Headset Connected", f"Audio out: {best_sink['name']}", best_sink["icon"])
                elif self.current_sink_name and self.config["devices"].get(self.current_sink_name, {}).get("type") == "special_rog":
                     send_notification("Headset Disconnected", f"Audio fell back to {best_sink['name']}", best_sink["icon"])
                else:
                     send_notification("Audio Output Routed", f"Switched to {best_sink['name']}", best_sink["icon"])
                     
                self.current_sink_name = best_sink["name"]

        # 2. Route Source (Input)
        if available_sources:
            best_source = available_sources[0]
            if self.current_source_name != best_source["name"]:
                print(f"[Router] Switching input to: {best_source['name']} (Priority: {best_source['priority']})")
                subprocess.run(["wpctl", "set-default", best_source["id"]])
                
                # Avoid double-notifying if it's the ROG headset (since sink usually triggers it)
                if self.config["devices"][best_source["name"]]["type"] != "special_rog":
                    send_notification("Microphone Routed", f"Switched to {best_source['name']}", "audio-input-microphone")
                    
                self.current_source_name = best_source["name"]

if __name__ == "__main__":
    router = PriorityRouter()
    router.start()
