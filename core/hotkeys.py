from pynput import keyboard

class HotkeyManager:
    def __init__(self):
        self.listener = None
        self.hotkeys = {}
        
    def set_hotkey(self, key_str, callback):
        self.hotkeys[key_str] = callback
        self.restart_listener()
        
    def remove_hotkey(self, key_str):
        if key_str in self.hotkeys:
            del self.hotkeys[key_str]
            self.restart_listener()

    def restart_listener(self):
        if self.listener:
            self.listener.stop()
            
        if not self.hotkeys:
            return
            
        try:
            self.listener = keyboard.GlobalHotKeys(self.hotkeys)
            self.listener.start()
        except Exception as e:
            print(f"Error iniciando GlobalHotKeys: {e}")

    def stop(self):
        if self.listener:
            self.listener.stop()

hotkey_manager = HotkeyManager()
