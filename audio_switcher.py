import subprocess
import re

class AudioSwitcher:
    def __init__(self):
        self.saved_sink = None
        self.saved_source = None

    def _parse_wpctl(self, section_target, find_default=True, search_name=None):
        try:
            out = subprocess.check_output(["wpctl", "status"]).decode()
        except Exception as e:
            print(f"[Audio] Error running wpctl: {e}")
            return None

        current_section = None
        for line in out.splitlines():
            # Detect section header like " ├─ Sinks:"
            match = re.search(r'[├└]─\s+([A-Za-z]+):', line)
            if match:
                current_section = match.group(1)
                continue
                
            if current_section == section_target:
                if find_default and "*" in line:
                    m = re.search(r'(\d+)\.', line)
                    if m: return m.group(1)
                if search_name and search_name.lower() in line.lower():
                    m = re.search(r'(\d+)\.', line)
                    if m: return m.group(1)
        return None

    def save_defaults(self):
        self.saved_sink = self._parse_wpctl("Sinks", find_default=True)
        self.saved_source = self._parse_wpctl("Sources", find_default=True)
        print(f"[Audio] Saved defaults - Sink: {self.saved_sink}, Source: {self.saved_source}")

    def switch_to(self, name_part):
        sink = self._parse_wpctl("Sinks", find_default=False, search_name=name_part)
        source = self._parse_wpctl("Sources", find_default=False, search_name=name_part)
        
        if sink:
            print(f"[Audio] Switching sink to {sink} ({name_part})")
            subprocess.run(["wpctl", "set-default", sink])
        if source:
            print(f"[Audio] Switching source to {source} ({name_part})")
            subprocess.run(["wpctl", "set-default", source])

    def restore_defaults(self):
        if self.saved_sink:
            print(f"[Audio] Restoring sink to {self.saved_sink}")
            subprocess.run(["wpctl", "set-default", self.saved_sink])
        if self.saved_source:
            print(f"[Audio] Restoring source to {self.saved_source}")
            subprocess.run(["wpctl", "set-default", self.saved_source])
