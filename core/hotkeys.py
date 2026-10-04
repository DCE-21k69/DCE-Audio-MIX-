import threading
from pynput import keyboard


class HotkeyManager:
    """
    Single persistent keyboard listener. Hotkeys are stored in a dict and
    checked on every key press - no restart needed, no X11 display_record crash.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._hotkeys = {}   # {normalized_key_str: callback}
        self._listener = None
        self._start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_hotkey(self, key_str, callback):
        """Add or replace a hotkey (thread-safe)."""
        norm = self._normalize(key_str)
        with self._lock:
            self._hotkeys[norm] = callback

    def remove_hotkey(self, key_str):
        """Remove a hotkey (thread-safe)."""
        norm = self._normalize(key_str)
        with self._lock:
            self._hotkeys.pop(norm, None)

    def stop(self):
        """Stop the listener permanently (call on app exit)."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _normalize(self, key_str: str) -> str:
        """Turn a pynput key string into a consistent lowercase form."""
        # pynput represents special keys like <f9>, <left>, +, etc.
        return key_str.lower().strip()

    def _key_to_str(self, key) -> str:
        """Convert a pynput Key object / KeyCode to our normalized string."""
        try:
            # Special keys: Key.f9 -> '<f9>', Key.left -> '<left>'
            name = key.name  # e.g. 'f9', 'left', 'space'
            return f"<{name}>"
        except AttributeError:
            # Regular character keys: KeyCode(char='a') -> 'a'
            try:
                return key.char.lower() if key.char else ""
            except AttributeError:
                return ""

    def _on_press(self, key):
        key_str = self._key_to_str(key)
        if not key_str:
            return
        with self._lock:
            cb = self._hotkeys.get(key_str)
        if cb is not None:
            threading.Thread(target=cb, daemon=True).start()

    def _start(self):
        try:
            self._listener = keyboard.Listener(on_press=self._on_press)
            self._listener.daemon = True
            self._listener.start()
        except Exception as e:
            print(f"[HotkeyManager] Error starting listener: {e}")


hotkey_manager = HotkeyManager()
