"""
HotkeyManager usando evdev — funciona en X11 y Wayland sin root.
Requisito: el usuario debe estar en el grupo 'input'.
    sudo usermod -aG input $USER  (luego cerrar sesión y volver a entrar)
"""

import threading
import asyncio
import glob
import os
from evdev import InputDevice, categorize, ecodes, list_devices


# Mapa de evdev KEY_* a la cadena que usamos internamente
EVDEV_TO_NAME: dict[int, str] = {
    # Función
    ecodes.KEY_F1:  "f1",  ecodes.KEY_F2:  "f2",  ecodes.KEY_F3:  "f3",
    ecodes.KEY_F4:  "f4",  ecodes.KEY_F5:  "f5",  ecodes.KEY_F6:  "f6",
    ecodes.KEY_F7:  "f7",  ecodes.KEY_F8:  "f8",  ecodes.KEY_F9:  "f9",
    ecodes.KEY_F10: "f10", ecodes.KEY_F11: "f11", ecodes.KEY_F12: "f12",
    # Flechas
    ecodes.KEY_LEFT:  "leftarrow",
    ecodes.KEY_RIGHT: "rightarrow",
    ecodes.KEY_UP:    "uparrow",
    ecodes.KEY_DOWN:  "downarrow",
    # Numpad
    ecodes.KEY_KPPLUS:  "kp_plus",
    ecodes.KEY_KPMINUS: "kp_minus",
    ecodes.KEY_KPENTER: "kp_enter",
    ecodes.KEY_KP0: "kp_ins",    ecodes.KEY_KP1: "kp_end",
    ecodes.KEY_KP2: "kp_downarrow", ecodes.KEY_KP3: "kp_pgdn",
    ecodes.KEY_KP4: "kp_leftarrow", ecodes.KEY_KP5: "kp_5",
    ecodes.KEY_KP6: "kp_rightarrow", ecodes.KEY_KP7: "kp_home",
    ecodes.KEY_KP8: "kp_uparrow", ecodes.KEY_KP9: "kp_pgup",
    # Comunes y puntuación
    ecodes.KEY_SPACE:       "space",
    ecodes.KEY_ENTER:       "enter",
    ecodes.KEY_ESC:         "escape",
    ecodes.KEY_TAB:         "tab",
    ecodes.KEY_EQUAL:       "+",
    ecodes.KEY_SEMICOLON:   "semicolon",
    ecodes.KEY_APOSTROPHE:  "apostrophe",
    ecodes.KEY_GRAVE:       "grave",
    ecodes.KEY_COMMA:       "comma",
    ecodes.KEY_DOT:         "period",
    ecodes.KEY_SLASH:       "slash",
    ecodes.KEY_BACKSLASH:   "backslash",
    ecodes.KEY_MINUS:       "-",
    ecodes.KEY_LEFTBRACE:   "[",
    ecodes.KEY_RIGHTBRACE:  "]",
}

# También guardamos letras/numeros por su char
for code in range(ecodes.KEY_A, ecodes.KEY_Z + 1):
    char = chr(ord('a') + (code - ecodes.KEY_A))
    EVDEV_TO_NAME[code] = char

for i, code in enumerate([
    ecodes.KEY_0, ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_3, ecodes.KEY_4,
    ecodes.KEY_5, ecodes.KEY_6, ecodes.KEY_7, ecodes.KEY_8, ecodes.KEY_9,
]):
    EVDEV_TO_NAME[code] = str(i)


def _find_keyboards() -> list[InputDevice]:
    """Devuelve todos los dispositivos de teclado disponibles."""
    devices = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            caps = dev.capabilities()
            # Si tiene teclas de teclado (KEY_A etc.) lo consideramos teclado
            if ecodes.EV_KEY in caps and ecodes.KEY_A in caps[ecodes.EV_KEY]:
                devices.append(dev)
        except Exception:
            pass
    return devices


class HotkeyManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._hotkeys: dict[str, callable] = {}
        self._threads: list[threading.Thread] = []
        self._running = False
        self._start()

    # ------------------------------------------------------------------ #
    #  API pública
    # ------------------------------------------------------------------ #

    def set_hotkey(self, key_str: str, callback):
        """Asigna o reemplaza un hotkey (thread-safe)."""
        with self._lock:
            self._hotkeys[key_str.lower()] = callback

    def remove_hotkey(self, key_str: str):
        with self._lock:
            self._hotkeys.pop(key_str.lower(), None)

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------ #
    #  Internos
    # ------------------------------------------------------------------ #

    def _start(self):
        keyboards = _find_keyboards()
        if not keyboards:
            print("[HotkeyManager] No se encontraron teclados en /dev/input. "
                  "Ejecuta: sudo usermod -aG input $USER  y reinicia sesión.")
            return

        self._running = True
        for dev in keyboards:
            t = threading.Thread(target=self._listen, args=(dev,), daemon=True)
            t.start()
            self._threads.append(t)

    def _listen(self, dev: InputDevice):
        try:
            for event in dev.read_loop():
                if not self._running:
                    break
                if event.type != ecodes.EV_KEY:
                    continue
                key_event = categorize(event)
                if key_event.keystate != key_event.key_down:
                    continue
                key_code = key_event.scancode
                name = EVDEV_TO_NAME.get(key_code)
                if name is None:
                    continue
                with self._lock:
                    cb = self._hotkeys.get(name)
                if cb is not None:
                    threading.Thread(target=cb, daemon=True).start()
        except Exception as e:
            # El dispositivo puede desconectarse — simplemente termina
            pass


hotkey_manager = HotkeyManager()
