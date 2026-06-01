import time
import sys
from audio_switcher import AudioSwitcher
from rog_delta_ii import RogDeltaII

def main():
    print("Starting Headset Auto Switcher Daemon...")
    switcher = AudioSwitcher()
    
    def on_connect():
        print("\n--- Headset Connected ---")
        switcher.save_defaults()
        switcher.switch_to("ROG DELTA II")
        
    def on_disconnect():
        print("\n--- Headset Disconnected ---")
        switcher.restore_defaults()
        
    def on_battery(level):
        print(f"[Status] Battery level: {level}%")

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
