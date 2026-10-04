import os
import psutil
import platform
import shutil

class L4D2Manager:
    def __init__(self):
        self.game_path = self._find_l4d2_path()
        
    def _find_l4d2_path(self):
        system = platform.system()
        paths_to_check = []
        if system == "Windows":
            paths_to_check = [
                r"C:\Program Files (x86)\Steam\steamapps\common\Left 4 Dead 2",
                r"D:\SteamLibrary\steamapps\common\Left 4 Dead 2",
                r"E:\SteamLibrary\steamapps\common\Left 4 Dead 2",
            ]
        elif system == "Linux":
            home = os.path.expanduser("~")
            paths_to_check = [
                os.path.join(home, ".local/share/Steam/steamapps/common/Left 4 Dead 2"),
                os.path.join(home, ".steam/steam/steamapps/common/Left 4 Dead 2"),
                os.path.join(home, ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Left 4 Dead 2")
            ]
        for p in paths_to_check:
            if os.path.exists(p) and os.path.isdir(p):
                return p
        return None

    def is_game_running(self):
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if "left4dead2" in name or "hl2.exe" in name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def generate_cfg(self, hotkey="x"):
        if not self.game_path:
            return False, "Ruta de L4D2 no encontrada."
        cfg_dir = os.path.join(self.game_path, "left4dead2", "cfg")
        if not os.path.exists(cfg_dir):
            return False, "Carpeta cfg de L4D2 no encontrada."
        cfg_content = f"""// Generado por DCE Audio Mix
alias dce_play "voice_inputfromfile 1; +voicerecord; alias dce_toggle dce_stop"
alias dce_stop "-voicerecord; voice_inputfromfile 0; alias dce_toggle dce_play"
alias dce_toggle "dce_play"
bind "{hotkey}" "dce_toggle"
echo "DCE Audio Mix cargado con exito. Presiona {hotkey} para reproducir."
"""
        try:
            cfg_path = os.path.join(cfg_dir, "dce_audio.cfg")
            with open(cfg_path, "w") as f:
                f.write(cfg_content)
            
            # Ocultar archivo en Windows
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(cfg_path, 2)
                
            return True, f"¡Conectado! Ejecuta 'exec dce_audio.cfg' en consola L4D2."
        except Exception as e:
            return False, f"Error CFG: {e}"
            
    def set_voice_input(self, source_wav_path):
        if not self.game_path:
            return False, "Juego no encontrado."
        target_wav = os.path.join(self.game_path, "left4dead2", "voice_input.wav")
        try:
            shutil.copy2(source_wav_path, target_wav)
            
            # Ocultar en Windows
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(target_wav, 2)
                
            return True, "Audio inyectado en L4D2."
        except Exception as e:
            return False, f"Error inyectando audio: {e}"
