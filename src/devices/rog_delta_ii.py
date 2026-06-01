import os
import glob

class RogDeltaII:
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.hidraw_device = self._find_hidraw("0b05", "1afa")
        self.is_connected = False
        
    def _find_hidraw(self, vendor_id, product_id):
        v_id = int(vendor_id, 16)
        p_id = int(product_id, 16)
        
        for path in glob.glob("/sys/class/hidraw/*"):
            uevent_path = os.path.join(path, "device", "uevent")
            if os.path.exists(uevent_path):
                with open(uevent_path, "r") as f:
                    for line in f:
                        if line.startswith("HID_ID="):
                            parts = line.strip().split("=")[1].split(":")
                            if len(parts) == 3:
                                if int(parts[1], 16) == v_id and int(parts[2], 16) == p_id:
                                    return f"/dev/{os.path.basename(path)}"
        return None

    def listen(self):
        if not self.hidraw_device:
            print("[ROG Delta II] Dongle not found (no hidraw device matched).")
            return

        print(f"[ROG Delta II] Listening on {self.hidraw_device}...")
        try:
            fd = os.open(self.hidraw_device, os.O_RDONLY)
            while True:
                data = os.read(fd, 64)
                if len(data) >= 6 and data[0:2] == b'\xcc\x12':
                    if data[2:6] == b'\x00\x00\x01\x01':
                        if not self.is_connected:
                            self.is_connected = True
                            if 'on_connect' in self.callbacks:
                                self.callbacks['on_connect']()
                    elif data[2:6] == b'\x00\x00\x01\x00':
                        if self.is_connected:
                            self.is_connected = False
                            if 'on_disconnect' in self.callbacks:
                                self.callbacks['on_disconnect']()
                    elif data[2:4] == b'\x09\x00':
                        battery = data[5]
                        if 'on_battery' in self.callbacks:
                            self.callbacks['on_battery'](battery)
        except PermissionError:
            print(f"[ROG Delta II] Permission denied opening {self.hidraw_device}. Check udev rules.")
        except Exception as e:
            print(f"[ROG Delta II] Error: {e}")
