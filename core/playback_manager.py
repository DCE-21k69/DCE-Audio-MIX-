import os
import time
import struct
import shutil
import threading

class PlaybackManager:
    def __init__(self, l4d2_manager):
        self.l4d2 = l4d2_manager
        self.lock = threading.Lock()
        
        self.master_wav_path = None
        self.current_title = "Ninguna canción cargada"
        self.is_playing = False
        self.playback_start_time = 0.0
        self.accumulated_time = 0.0
        self.total_duration = 0.0
        self.last_toggle_time = 0.0
        
        # Callback opcional para notificar a la UI sobre cambios de estado
        self.on_state_change = None

        # Si ya hay un voice_input.wav en L4D2, lo tomamos como master inicial
        self._init_existing_audio()

    def _init_existing_audio(self):
        if not self.l4d2.game_path:
            return
        v1 = os.path.join(self.l4d2.game_path, "left4dead2", "voice_input.wav")
        if os.path.exists(v1):
            master_cache = os.path.abspath(os.path.join(".downloads", "current_master.wav"))
            os.makedirs(os.path.dirname(master_cache), exist_ok=True)
            if not os.path.exists(master_cache):
                try:
                    shutil.copy2(v1, master_cache)
                except Exception:
                    pass
            if os.path.exists(master_cache):
                self.master_wav_path = master_cache
                self.current_title = "Audio activo en L4D2"
                self.total_duration = self._get_wav_duration(master_cache)

    def _get_wav_duration(self, wav_path):
        try:
            with open(wav_path, "rb") as f:
                data = f.read(44)
            if len(data) >= 44 and data[:4] == b'RIFF':
                channels = struct.unpack('<H', data[22:24])[0]
                sample_rate = struct.unpack('<I', data[24:28])[0]
                bits_per_sample = struct.unpack('<H', data[34:36])[0]
                bytes_per_sec = sample_rate * channels * (bits_per_sample // 8)
                file_size = os.path.getsize(wav_path)
                data_size = file_size - 44
                if bytes_per_sec > 0:
                    return max(0.0, data_size / bytes_per_sec)
        except Exception:
            pass
        return 0.0

    def load_track(self, source_wav_path, title=""):
        with self.lock:
            os.makedirs(".downloads", exist_ok=True)
            master_cache = os.path.abspath(os.path.join(".downloads", "current_master.wav"))
            try:
                shutil.copy2(source_wav_path, master_cache)
                self.master_wav_path = master_cache
            except Exception:
                self.master_wav_path = os.path.abspath(source_wav_path)

            self.current_title = title or os.path.basename(source_wav_path)
            self.accumulated_time = 0.0
            self.is_playing = False
            self.playback_start_time = 0.0
            self.total_duration = self._get_wav_duration(self.master_wav_path)
            
            # Inyectar el archivo original completo en L4D2
            success, msg = self.l4d2.set_voice_input(self.master_wav_path)
            
            if self.on_state_change:
                try:
                    self.on_state_change(self.get_status())
                except Exception:
                    pass
                
            return success, msg

    def toggle_pause_resume(self, check_game_running=True):
        with self.lock:
            # Si se llama desde hotkey global, verificar si el juego está abierto
            if check_game_running and not self.l4d2.is_game_running():
                return False, "L4D2 no está corriendo"

            now = time.time()
            # Debounce de 250ms para evitar pulsaciones dobles fantasma
            if now - self.last_toggle_time < 0.25:
                return False, "Debounce"
            self.last_toggle_time = now

            if not self.master_wav_path or not os.path.exists(self.master_wav_path):
                return False, "No hay canción cargada."

            if self.is_playing:
                # Transición de REPRODUCIENDO a PAUSADO
                elapsed = now - self.playback_start_time
                self.is_playing = False
                self.accumulated_time += elapsed
                
                # Si superó la duración total, reiniciar a 0
                if self.total_duration > 0 and self.accumulated_time >= self.total_duration:
                    self.accumulated_time = 0.0

                # Rebanar archivo y sobrescribir voice_input.wav en tiempo real
                t0 = time.time()
                self._slice_and_update(self.accumulated_time)
                t1 = time.time()
                
                pos_str = self.format_time(self.accumulated_time)
                tot_str = self.format_time(self.total_duration)
                print(f"[DCE Playback] ⏸️ PAUSA en {pos_str} / {tot_str} (Rebanado en {(t1-t0)*1000:.1f}ms)")
                
                if self.on_state_change:
                    try:
                        self.on_state_change(self.get_status())
                    except Exception:
                        pass
                        
                return True, f"Pausado en {pos_str}"
            else:
                # Transición de PAUSADO a REPRODUCIENDO (PLAY / RESUME)
                self.is_playing = True
                self.playback_start_time = now
                
                pos_str = self.format_time(self.accumulated_time)
                print(f"[DCE Playback] ▶️ REANUDAR desde {pos_str}")
                
                if self.on_state_change:
                    try:
                        self.on_state_change(self.get_status())
                    except Exception:
                        pass
                        
                return True, f"Reanudando desde {pos_str}"

    def restart_track(self):
        with self.lock:
            self.is_playing = False
            self.accumulated_time = 0.0
            self.playback_start_time = 0.0
            if self.master_wav_path and os.path.exists(self.master_wav_path):
                self.l4d2.set_voice_input(self.master_wav_path)
            if self.on_state_change:
                try:
                    self.on_state_change(self.get_status())
                except Exception:
                    pass
            print(f"[DCE Playback] 🔄 Reiniciado desde 0:00")
            return True, "Reiniciado desde 0:00"

    def _slice_and_update(self, start_sec):
        if not self.master_wav_path or not os.path.exists(self.master_wav_path):
            return False
            
        try:
            with open(self.master_wav_path, "rb") as f:
                data = f.read()
        except Exception as e:
            print(f"[DCE Playback] Error leyendo master WAV: {e}")
            return False

        if len(data) < 44 or data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            return False

        # Parsear chunks fmt y data de forma robusta
        idx = 12
        fmt_found = False
        data_found = False
        data_start = 0
        data_size = 0
        
        channels = 1
        sample_rate = 11025
        bits_per_sample = 16

        while idx + 8 <= len(data):
            chunk_id = data[idx:idx+4]
            chunk_len = struct.unpack('<I', data[idx+4:idx+8])[0]
            chunk_data_start = idx + 8

            if chunk_id == b'fmt ':
                fmt_found = True
                channels = struct.unpack('<H', data[chunk_data_start+2:chunk_data_start+4])[0]
                sample_rate = struct.unpack('<I', data[chunk_data_start+4:chunk_data_start+8])[0]
                bits_per_sample = struct.unpack('<H', data[chunk_data_start+14:chunk_data_start+16])[0]
            elif chunk_id == b'data':
                data_found = True
                data_start = chunk_data_start
                data_size = chunk_len
                break

            idx += 8 + chunk_len
            if chunk_len % 2 != 0:
                idx += 1

        if not fmt_found or not data_found:
            return False

        bytes_per_sample = bits_per_sample // 8
        frame_size = channels * bytes_per_sample
        bytes_per_sec = sample_rate * frame_size

        audio_bytes = data[data_start:data_start+data_size]
        byte_offset = int(start_sec * bytes_per_sec)
        byte_offset = (byte_offset // frame_size) * frame_size

        if byte_offset >= len(audio_bytes):
            byte_offset = 0

        sliced_audio = audio_bytes[byte_offset:]
        
        # Construir cabecera canónica WAV de 44 bytes sin metadata extra
        riff_header = bytearray()
        riff_header.extend(b'RIFF')
        riff_header.extend(struct.pack('<I', 36 + len(sliced_audio)))
        riff_header.extend(b'WAVE')
        riff_header.extend(b'fmt ')
        riff_header.extend(struct.pack('<I', 16))
        riff_header.extend(struct.pack('<H', 1))
        riff_header.extend(struct.pack('<H', channels))
        riff_header.extend(struct.pack('<I', sample_rate))
        riff_header.extend(struct.pack('<I', bytes_per_sec))
        riff_header.extend(struct.pack('<H', frame_size))
        riff_header.extend(struct.pack('<H', bits_per_sample))
        riff_header.extend(b'data')
        riff_header.extend(struct.pack('<I', len(sliced_audio)))

        full_sliced = riff_header + sliced_audio

        # Inyectar inmediatamente en las rutas de L4D2
        if self.l4d2.game_path:
            v1 = os.path.join(self.l4d2.game_path, "left4dead2", "voice_input.wav")
            v2 = os.path.join(self.l4d2.game_path, "voice_input.wav")
            for target_path in (v1, v2):
                try:
                    with open(target_path, "wb") as f:
                        f.write(full_sliced)
                except Exception as e:
                    print(f"[DCE Playback] Error escribiendo en {target_path}: {e}")
        return True

    def get_status(self):
        with self.lock:
            cur = self.accumulated_time
            if self.is_playing:
                cur += (time.time() - self.playback_start_time)
            return {
                "title": self.current_title,
                "is_playing": self.is_playing,
                "current_time": cur,
                "total_duration": self.total_duration,
                "current_str": self.format_time(cur),
                "total_str": self.format_time(self.total_duration)
            }

    @staticmethod
    def format_time(seconds):
        sec = int(max(0, seconds))
        m = sec // 60
        s = sec % 60
        return f"{m:02d}:{s:02d}"
