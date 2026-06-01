import time
import sys
import subprocess
from audio_switcher import AudioSwitcher
from rog_delta_ii import RogDeltaII

def send_notification(title, message, icon="audio-headset", urgency="normal"):
    try:
        # Uses standard Linux desktop notifications
        subprocess.run([
            "notify-send", 
            "-a", "Headset Manager", 
            "-i", icon, 
            "-u", urgency, 
            title, 
            message
        ])
    except Exception as e:
        print(f"[Notify] Failed to send notification: {e}")

def main():
    print("Starting Headset Auto Switcher Daemon...")
    switcher = AudioSwitcher()
    
    # State tracking to prevent battery notification spam
    battery_state = {"last_notified": None}
    
    def on_connect():
        print("\n--- Headset Connected ---")
        switcher.save_defaults()
        switcher.switch_to("ROG DELTA II")
        battery_state["last_notified"] = None  # Reset battery tracking
        send_notification("Headset Connected", "ROG Delta II is now active.", "audio-headset")
        
    def on_disconnect():
        print("\n--- Headset Disconnected ---")
        switcher.restore_defaults()
        battery_state["last_notified"] = None
        send_notification("Headset Disconnected", "Restored previous audio devices.", "audio-headset")
        
    def on_battery(level):
        print(f"[Status] Battery level: {level}%")
        
        # Determine battery thresholds
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
            
        # Only notify if we crossed a new threshold downwards to avoid spam
        if threshold and battery_state["last_notified"] != threshold:
            battery_state["last_notified"] = threshold
            send_notification(title, f"ROG Delta II is at {level}%", icon, urgency)

    callbacks = {
        'on_connect': on_connect,
        'on_disconnect': on_disconnect,
        'on_battery': on_battery
    }
    
    headset = RogDeltaII(callbacks)
    
    # Listens indefinitely for hardware packets
    headset.listen()
    
    # Fallback to keep alive if listen exits instantly
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
