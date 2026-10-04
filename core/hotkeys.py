import threading
from pynput import keyboard


class HotkeyManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.listener = None
        self.hotkeys = {}

    def set_hotkey(self, key_str, callback):
        with self._lock:
            self.hotkeys[key_str] = callback
        self._restart_listener()

    def remove_hotkey(self, key_str):
        with self._lock:
            if key_str in self.hotkeys:
                del self.hotkeys[key_str]
        self._restart_listener()

    def _restart_listener(self):
        # Stop old listener in a safe way
        old = self.listener
        self.listener = None
        if old is not None:
            try:
                # Use a thread to avoid blocking the calling thread
                t = threading.Thread(target=old.stop, daemon=True)
                t.start()
                t.join(timeout=1.0)  # Max 1s to stop old listener
            except Exception:
                pass

        with self._lock:
            hotkeys_copy = dict(self.hotkeys)

        if not hotkeys_copy:
            return

        try:
            new_listener = keyboard.GlobalHotKeys(hotkeys_copy)
            new_listener.daemon = True
            self.listener = new_listener
            new_listener.start()
        except Exception as e:
            print(f"Error iniciando GlobalHotKeys: {e}")

    def stop(self):
        old = self.listener
        self.listener = None
        if old is not None:
            try:
                t = threading.Thread(target=old.stop, daemon=True)
                t.start()
                t.join(timeout=1.0)
            except Exception:
                pass


hotkey_manager = HotkeyManager()
