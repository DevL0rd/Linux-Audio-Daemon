# Linux-Audio-Daemon

A modular daemon that automatically switches audio output and microphone input based on customizable rules. Also supports reading usb packets from dongles for devices that are always available even when headset is disconnected, so that we can switch to a headset when it actually connects.

This is mostly for myself, but in case my friends use it, here is the instructions:

## Installation
```bash
./install.sh
```

## Uninstallation
To disable the daemon and clean up the systemd services and udev rules, run:
```bash
./uninstall.sh
```

## Configuration (`config.json`)
Devices are **automatically added** to `config.json` the moment you plug them in or turn them on. You do not need to manually type out exact PipeWire device names! Simply connect a new monitor, TV, or Bluetooth headset, and the daemon will immediately generate an entry for it.

Once a device appears in the config file, you can tweak its behavior:
* **`priority`**: The core routing rule. Higher numbers mean higher priority (e.g., `100` > `50`). The daemon will always auto-route your audio to the highest priority device that is currently available.
* **`icon`**: The icon used in the desktop popup notifications (e.g., `audio-headset`, `audio-card`, `video-display`).
* **`type`**: Set to `"generic"` for normal devices (TVs, Bluetooth earbuds). Set to a custom string for special hardware (see below).

## Adding a New "Special" Device
Standard audio devices disappear from Linux when disconnected, making them easy to track. However, some 2.4GHz wireless dongles act as a permanent sound card even when the headset itself is turned off. 

To fix this, you can write a "Special Device" hardware watcher. The **ROG Delta II** is included in the source code as an example.

### 1. Write the Hardware Watcher
Create a new Python script in `src/devices/`. Your class should listen to raw USB packets (or another hardware indicator) and trigger callbacks when the actual hardware state changes:
```python
# src/devices/my_custom_headset.py
class MyCustomHeadset:
    def __init__(self, callbacks):
        self.callbacks = callbacks
        
    def listen(self):
        # ... block and listen to /dev/hidrawX ...
        # When turned on: self.callbacks['on_connect']()
        # When turned off: self.callbacks['on_disconnect']()
```

### 2. Register it in the Daemon
Open `src/daemon.py` and hook your new watcher into the `PriorityRouter`:
* Import your class and start its `.listen()` method in a background thread inside `start()`.
* Add a state variable (e.g., `self.my_headset_connected = False`).
* Update that state variable in your callbacks and immediately call `self.evaluate_routing()`.

### 3. Update the Routing Logic
In `src/daemon.py` inside `evaluate_routing()`, tell the router to ignore the device's generic PipeWire presence if your custom hardware logic says it is actually turned off:
```python
if c_info["type"] == "special_myheadset":
    if not self.my_headset_connected:
        continue # Skip this device, the hardware is turned off!
```

### 4. Tag the Config
Finally, open your `config.json` and change the `"type"` of your headset's audio sink to `"special_myheadset"` so the daemon knows to apply your custom rules.
