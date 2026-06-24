import os
import glob
import time

class RogDeltaII:
    def __init__(self, callbacks):
        self.callbacks = callbacks
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
        while True:
            hidraw_device = self._find_hidraw("0b05", "1afa")
            
            if not hidraw_device:
                time.sleep(5)
                continue

            print(f"[ROG Delta II] Listening on {hidraw_device}...")
            try:
                # Open with O_RDWR so we can ping it
                fd = os.open(hidraw_device, os.O_RDWR)
                
                # Proactively ping the dongle for battery status. 
                # This forces it to respond if the headset is currently turned on.
                try:
                    os.write(fd, bytearray([0xcc, 0x12, 0x09] + [0] * 61))
                except Exception as e:
                    print(f"[ROG Delta II] Failed to send startup ping: {e}")

                while True:
                    data = os.read(fd, 64)
                    if not data:
                        break # EOF
                    
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
                            # 0xFF/255 is the "headset off/unknown" sentinel; a value
                            # in 0..100 means the headset is actually on.
                            if battery <= 100:
                                if not self.is_connected:
                                    self.is_connected = True
                                    if 'on_connect' in self.callbacks:
                                        self.callbacks['on_connect']()
                                if 'on_battery' in self.callbacks:
                                    self.callbacks['on_battery'](battery)
            except PermissionError:
                print(f"[ROG Delta II] Permission denied opening {hidraw_device}. Check udev rules.")
                time.sleep(5)
            except Exception as e:
                print(f"[ROG Delta II] Connection lost or error: {e}")
                if self.is_connected:
                    self.is_connected = False
                    if 'on_disconnect' in self.callbacks:
                        self.callbacks['on_disconnect']()
                
            finally:
                try:
                    os.close(fd)
                except Exception:
                    pass
                
            time.sleep(2)
