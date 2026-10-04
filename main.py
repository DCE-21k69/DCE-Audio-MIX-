import flet as ft
import os
import json
import asyncio
import webbrowser
from core.dce_audio_core import search_youtube, download_and_convert
from core.l4d2_manager import L4D2Manager
from core.hotkeys import hotkey_manager
from core.playlist_manager import get_playlist, add_to_playlist, remove_from_playlist, import_local_file
from core.playback_manager import PlaybackManager

CONFIG_FILE = os.path.abspath("hotkeys_config.json")

def load_hotkeys_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"pause": "x", "prev": "", "next": ""}

def save_hotkeys_config(pause, prev, next_k):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"pause": pause, "prev": prev, "next": next_k}, f, indent=2)
    except Exception as e:
        print(f"Error guardando hotkeys: {e}")

def fix_linux_audio_ducking():
    try:
        import subprocess, shutil
        if shutil.which("wpctl"):
            subprocess.run(["wpctl", "settings", "bluetooth.autoswitch-to-headset-profile", "false"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["wpctl", "settings", "linking.role-based.duck-level", "1.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def main(page: ft.Page):
    fix_linux_audio_ducking()
    page.title = "DCE Audio Mix"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080808"
    page.window.width = 950
    page.window.height = 750
    page.window.frameless = True

    icon_path = os.path.abspath(os.path.join("assets", "logoapp.png"))
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    l4d2 = L4D2Manager()

    # --- HELPER NOTIFICACIONES (SNACKBAR FLET 1.0) ---
    def show_notify(msg, is_error=False, is_warning=False):
        color = ft.Colors.RED_800 if is_error else (ft.Colors.ORANGE_800 if is_warning else ft.Colors.GREEN_800)
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(str(msg), color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                bgcolor=color,
                open=True
            )
        )

    # --- TOP BAR (STATUS L4D2) ---
    l4d2_status_icon = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.RED_500, size=16)
    l4d2_status_text = ft.Text("L4D2 No Detectado", color=ft.Colors.RED_500, weight=ft.FontWeight.BOLD)
    
    def check_l4d2_status():
        is_running = l4d2.is_game_running()
        if l4d2.game_path:
            if is_running:
                l4d2_status_icon.color = ft.Colors.GREEN_500
                l4d2_status_text.value = "L4D2 Conectado y Corriendo"
                l4d2_status_text.color = ft.Colors.GREEN_500
            else:
                l4d2_status_icon.color = ft.Colors.ORANGE_500
                l4d2_status_text.value = "L4D2 Detectado (Cerrado)"
                l4d2_status_text.color = ft.Colors.ORANGE_500
        else:
            l4d2_status_icon.color = ft.Colors.RED_500
            l4d2_status_text.value = "Carpeta L4D2 No Encontrada"
            l4d2_status_text.color = ft.Colors.RED_500
        page.update()

    def do_connect_l4d2(e):
        cfg = load_hotkeys_config()
        pause_key = cfg.get("pause") or "x"
        success, msg = l4d2.generate_cfg(pause_key)
        show_notify(msg, is_error=not success)
        check_l4d2_status()

    btn_connect = ft.Button("Conectar", icon=ft.Icons.CABLE, on_click=do_connect_l4d2, color="#ffaa00")

    # Botones de ventana
    async def do_close(*args):
        hotkey_manager.stop()
        await page.window.close()
        
    async def do_minimize(*args):
        page.window.minimized = True
        page.update()

    btn_min = ft.IconButton(ft.Icons.MINIMIZE, on_click=lambda e: page.run_task(do_minimize), icon_color=ft.Colors.WHITE_54)
    btn_close = ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: page.run_task(do_close), icon_color=ft.Colors.RED_400)

    top_bar = ft.WindowDragArea(
        content=ft.Container(
            content=ft.Row([
                ft.Image(src=icon_path, width=40, height=40) if os.path.exists(icon_path) else ft.Icon(ft.Icons.MUSIC_NOTE, color="#ffaa00"),
                ft.Text("DCE AUDIO MIX", size=16, weight=ft.FontWeight.BOLD, color="#ffaa00"),
                ft.Container(expand=True),
                l4d2_status_icon,
                l4d2_status_text,
                btn_connect,
                ft.Container(width=10),
                btn_min,
                btn_close
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            bgcolor="#121212",
            border_radius=8
        )
    )

    playback = PlaybackManager(l4d2)

    # --- BARRA DE CONTROL Y REPRODUCCIÓN (PLAY / PAUSA / REANUDAR / REINICIAR) ---
    lbl_now_playing_title = ft.Text(
        playback.current_title,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS
    )
    lbl_now_playing_time = ft.Text("⏸️ Pausado (00:00 / 00:00)", color=ft.Colors.WHITE_54, size=12)
    btn_toggle_play_ui = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        icon_color="#ffaa00",
        tooltip="Pausar / Continuar (o presiona tu hotkey en juego)",
        on_click=lambda e: (playback.toggle_pause_resume(check_game_running=False), update_playback_ui())
    )
    btn_restart_ui = ft.IconButton(
        icon=ft.Icons.REPLAY_ROUNDED,
        icon_color=ft.Colors.WHITE_54,
        tooltip="Reiniciar canción desde el inicio (0:00)",
        on_click=lambda e: (playback.restart_track(), show_notify("🔄 Canción reiniciada a 0:00"), update_playback_ui())
    )

    def update_playback_ui(status=None):
        if not status:
            status = playback.get_status()
        lbl_now_playing_title.value = status["title"]
        icon_stat = "▶️" if status["is_playing"] else "⏸️"
        txt_stat = "En reproducción" if status["is_playing"] else "Pausado"
        lbl_now_playing_time.value = f"{icon_stat} {txt_stat} ({status['current_str']} / {status['total_str']})"
        lbl_now_playing_time.color = ft.Colors.GREEN_400 if status["is_playing"] else ft.Colors.WHITE_54
        btn_toggle_play_ui.icon = ft.Icons.PAUSE_ROUNDED if status["is_playing"] else ft.Icons.PLAY_ARROW_ROUNDED
        btn_toggle_play_ui.icon_color = ft.Colors.GREEN_400 if status["is_playing"] else "#ffaa00"
        try:
            page.update()
        except Exception:
            pass

    playback.on_state_change = lambda st: update_playback_ui(st)

    playback_bar = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.MUSIC_NOTE, color="#ffaa00", size=24),
            ft.Column([
                lbl_now_playing_title,
                lbl_now_playing_time
            ], expand=True, spacing=2),
            btn_toggle_play_ui,
            btn_restart_ui
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=14, vertical=6),
        bgcolor="#161616",
        border_radius=8,
        border=ft.Border.all(1, "#262626")
    )

    # --- PESTAÑA 1: BUSCADOR ---
    search_state = {"query": "", "loaded_count": 0, "is_loading_more": False, "has_more": True, "is_direct_link": False}
    search_input = ft.TextField(hint_text="Escribe el nombre o pega enlace de YouTube...", expand=True, bgcolor="#101010", on_submit=lambda e: page.run_task(perform_search, e))
    results_list = ft.ListView(expand=True, spacing=10, padding=10)
    status_text = ft.Text("", color="#ffaa00", size=14)
    loading_ring = ft.ProgressRing(visible=False, width=20, height=20, color="#ffaa00")
    bottom_loading = ft.Container(content=ft.ProgressRing(width=30, height=30, color="#00ffaa"), alignment=ft.Alignment.CENTER, padding=20, visible=False)

    def create_search_card(item, is_direct_link=False):
        duration_sec = item.get('duration', 0) or 0
        duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}" if duration_sec else "--:--"
        
        btn_use = ft.Button("Usar Directo", icon=ft.Icons.PLAY_ARROW, on_click=lambda e: page.run_task(download_and_inject, item['url'], item['title']))
        btn_save = ft.Button("Descargar a Playlist", icon=ft.Icons.PLAYLIST_ADD, on_click=lambda e: page.run_task(download_to_playlist, item['url'], item['title'], duration_sec, item['thumbnail']))
        btn_browser = ft.IconButton(icon=ft.Icons.OPEN_IN_BROWSER, tooltip="Abrir en YouTube", icon_color=ft.Colors.WHITE_54, on_click=lambda e: webbrowser.open(item['url']))

        buttons_row = ft.Row([btn_use, btn_save])
        if not is_direct_link: buttons_row.controls.append(btn_browser)
        
        return ft.Container(
            content=ft.Row([
                ft.Image(src=item['thumbnail'], width=120, height=70, fit=ft.BoxFit.COVER, border_radius=6),
                ft.Column([
                    ft.Text(item['title'], weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"Duración: {duration_min}", size=12, color=ft.Colors.WHITE_54)
                ], expand=True, spacing=4),
                buttons_row
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#141414", padding=10, border_radius=8, border=ft.Border.all(1, "#222222")
        )

    async def download_and_inject(url, title):
        status_text.value = f"Inyectando temporal: {title}..."
        loading_ring.visible = True
        page.update()
        try:
            os.makedirs(".downloads", exist_ok=True)
            out_wav = os.path.abspath(os.path.join(".downloads", "voice_input_temp.wav"))
            await asyncio.to_thread(download_and_convert, url, out_wav)
            success, msg = playback.load_track(out_wav, title=title)
            status_text.value = f"✅ Inyectado en L4D2: {title}"
            show_notify(f"✅ Inyectado en L4D2: {title}")
            update_playback_ui()
        except Exception as err:
            status_text.value = f"❌ Error: {err}"
            show_notify(f"❌ Error al inyectar: {err}", is_error=True)
        loading_ring.visible = False
        page.update()

    async def download_to_playlist(url, title, duration, thumbnail):
        status_text.value = f"Guardando en playlist: {title}..."
        loading_ring.visible = True
        page.update()
        try:
            os.makedirs(".downloads", exist_ok=True)
            out_wav = os.path.abspath(os.path.join(".downloads", "temp_to_playlist.wav"))
            await asyncio.to_thread(download_and_convert, url, out_wav)
            await asyncio.to_thread(add_to_playlist, title, duration, out_wav, thumbnail, False)
            status_text.value = f"✅ Añadido a Playlist local!"
            show_notify(f"✅ Guardado en Playlist: {title}")
            load_playlist_view()
        except Exception as err:
            status_text.value = f"❌ Error: {err}"
            show_notify(f"❌ Error al guardar: {err}", is_error=True)
        loading_ring.visible = False
        page.update()

    async def perform_search(e):
        query = search_input.value.strip()
        if not query: return
        is_direct = "youtube.com" in query or "youtu.be" in query
        search_state.update({"query": query, "loaded_count": 15, "is_loading_more": False, "has_more": True, "is_direct_link": is_direct})
        results_list.controls.clear()
        loading_ring.visible = True
        status_text.value = "Buscando en YouTube..."
        page.update()
        try:
            results = await asyncio.to_thread(search_youtube, query, search_state["loaded_count"])
            loading_ring.visible = False
            if not results:
                status_text.value = "No se encontraron resultados."; search_state["has_more"] = False
            else:
                status_text.value = f"Mostrando {len(results)} resultados:"
                for item in results: results_list.controls.append(create_search_card(item, is_direct))
                results_list.controls.append(bottom_loading)
        except Exception as err:
            loading_ring.visible = False; status_text.value = f"Error al buscar: {err}"
        page.update()

    async def load_more_results():
        if search_state["is_loading_more"] or not search_state["has_more"]: return
        search_state["is_loading_more"] = True; bottom_loading.visible = True; page.update()
        target_count = search_state["loaded_count"] + 15
        try:
            results = await asyncio.to_thread(search_youtube, search_state["query"], target_count)
            new_results = results[search_state["loaded_count"]:]
            if not new_results:
                search_state["has_more"] = False
            else:
                for item in new_results: results_list.controls.insert(-1, create_search_card(item, search_state["is_direct_link"]))
                search_state["loaded_count"] += len(new_results)
                status_text.value = f"Mostrando {search_state['loaded_count']} resultados:"
        except Exception: pass
        search_state["is_loading_more"] = False; bottom_loading.visible = search_state["has_more"]; page.update()

    results_list.on_scroll = lambda e: page.run_task(load_more_results) if e.pixels >= e.max_scroll_extent - 150 else None

    search_column = ft.Column([
        ft.Row([search_input, ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=lambda e: page.run_task(perform_search, e))]),
        ft.Row([loading_ring, status_text]),
        results_list
    ], expand=True)

    # --- PESTAÑA 2: PLAYLIST ---
    playlist_list = ft.ListView(expand=True, spacing=10)
    current_song_index = [0]
    
    def play_next_song():
        data = get_playlist()
        if not data: return
        current_song_index[0] = (current_song_index[0] + 1) % len(data)
        song = data[current_song_index[0]]
        playback.load_track(song['file'], title=song['title'])
        print(f"Modo Ninja: Siguiente -> {song['title']}")
        update_playback_ui()

    def play_prev_song():
        data = get_playlist()
        if not data: return
        current_song_index[0] = (current_song_index[0] - 1) % len(data)
        song = data[current_song_index[0]]
        playback.load_track(song['file'], title=song['title'])
        print(f"Modo Ninja: Anterior -> {song['title']}")
        update_playback_ui()

    def inject_playlist_song(song):
        data = get_playlist()
        for i, s in enumerate(data):
            if s['id'] == song['id']:
                current_song_index[0] = i
                break
        success, msg = playback.load_track(song['file'], title=song['title'])
        show_notify(f"✅ Inyectado en L4D2: {song['title']}" if success else f"❌ Error: {msg}", is_error=not success)
        update_playback_ui()

    def delete_playlist_song(song_id):
        remove_from_playlist(song_id)
        load_playlist_view()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                show_notify(f"Procesando {f.name}...")
                import_local_file(f.path)
            load_playlist_view()

    file_picker = ft.FilePicker(on_result=on_file_picked)

    async def open_file_picker(e):
        await file_picker.pick_files(allow_multiple=True, allowed_extensions=["mp3", "wav", "m4a", "ogg"])

    page.services.append(file_picker)

    def load_playlist_view():
        playlist_list.controls.clear()
        data = get_playlist()
        if not data:
            playlist_list.controls.append(ft.Text("Tu playlist está vacía. Busca en YouTube o añade un archivo local.", color=ft.Colors.WHITE_54))
        for song in data:
            dur_min = f"{song['duration'] // 60}:{song['duration'] % 60:02d}" if song.get('duration') else "--:--"
            src_tag = "📂 Local" if song.get('is_local') else "🔴 YouTube"
            
            btn_use = ft.Button("Inyectar", icon=ft.Icons.PLAY_ARROW, on_click=lambda e, s=song: inject_playlist_song(s))
            btn_del = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=lambda e, s=song: delete_playlist_song(s['id']))
            
            card = ft.Container(
                content=ft.Row([
                    ft.Image(src=song.get('thumbnail') or icon_path, width=80, height=50, fit=ft.BoxFit.COVER, border_radius=6),
                    ft.Column([
                        ft.Text(song['title'], weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row([ft.Text(f"Duración: {dur_min}", size=12, color=ft.Colors.WHITE_54), ft.Text(src_tag, size=12, color="#ffaa00")])
                    ], expand=True),
                    ft.Row([btn_use, btn_del])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#181818", padding=10, border_radius=8, border=ft.Border.all(1, "#333333")
            )
            playlist_list.controls.append(card)
        page.update()

    # --- MODO NINJA Y HOTKEYS ---
    saved_cfg = load_hotkeys_config()
    saved_pause = saved_cfg.get("pause") or "x"
    saved_prev = saved_cfg.get("prev") or ""
    saved_next = saved_cfg.get("next") or ""

    def on_hotkey_pause():
        playback.toggle_pause_resume()
        update_playback_ui()

    # Pre-registrar hotkeys guardadas al iniciar
    if saved_pause:
        hotkey_manager.set_hotkey(saved_pause, on_hotkey_pause)
    if saved_prev:
        hotkey_manager.set_hotkey(saved_prev, play_prev_song)
    if saved_next:
        hotkey_manager.set_hotkey(saved_next, play_next_song)

    FLET_TO_L4D2 = {
        "ñ": "semicolon",
        "Ñ": "semicolon",
        "ç": "backslash",
        "Ç": "backslash",
        "Arrow Left": "leftarrow",
        "Arrow Right": "rightarrow",
        "Arrow Up": "uparrow",
        "Arrow Down": "downarrow",
        " ": "space",
        "Enter": "enter",
        "Escape": "escape",
        "Numpad Add": "kp_plus",
        "Numpad Subtract": "kp_minus",
        "+": "+",
        "-": "-",
        ",": "comma",
        ".": "period",
        ";": "semicolon",
        ":": "semicolon",
        "Tab": "tab",
        "Shift Left": "shift",
        "Shift Right": "shift",
        "Control Left": "ctrl",
        "Control Right": "ctrl",
        "Alt Left": "alt",
        "Alt Right": "alt",
    }

    def flet_key_to_l4d2(flet_key: str):
        if flet_key in FLET_TO_L4D2:
            return FLET_TO_L4D2[flet_key]
        return flet_key.lower()

    def clean_engine_key(k: str):
        k_clean = str(k).strip()
        if "semicolon" in k_clean.lower() or "ñ" in k_clean.lower():
            return "semicolon"
        return k_clean

    recording_state = {"active": None}

    # Labels de estado de teclas
    init_pause_disp = "semicolon (tecla Ñ)" if saved_pause == "semicolon" else saved_pause
    init_prev_disp = "semicolon (tecla Ñ)" if saved_prev == "semicolon" else (saved_prev if saved_prev else "Clic para asignar...")
    init_next_disp = "semicolon (tecla Ñ)" if saved_next == "semicolon" else (saved_next if saved_next else "Clic para asignar...")

    lbl_pause = ft.Text(init_pause_disp, color=ft.Colors.WHITE_38, size=13)
    lbl_prev = ft.Text(init_prev_disp, color=ft.Colors.WHITE_38 if saved_prev else ft.Colors.WHITE_54, size=13)
    lbl_next = ft.Text(init_next_disp, color=ft.Colors.WHITE_38 if saved_next else ft.Colors.WHITE_54, size=13)

    def mark_applied(lbl):
        lbl.color = ft.Colors.WHITE_38
        lbl.update()
    
    def set_aplicar_btn_state(has_pending: bool):
        if has_pending:
            btn_aplicar_hotkeys.color = ft.Colors.GREEN_400
            btn_aplicar_hotkeys.bgcolor = "#1a2e1a"
        else:
            btn_aplicar_hotkeys.color = ft.Colors.WHITE_38
            btn_aplicar_hotkeys.bgcolor = "#1a1a1a"
        btn_aplicar_hotkeys.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if not recording_state["active"]: return
        
        target = recording_state["active"]
        l4d2_key = flet_key_to_l4d2(e.key)
        disp_key = "semicolon (tecla Ñ)" if l4d2_key == "semicolon" else l4d2_key
        
        def update_label(lbl):
            same = (lbl.color == ft.Colors.WHITE_38 and clean_engine_key(lbl.value) == clean_engine_key(disp_key))
            lbl.value = disp_key
            lbl.color = ft.Colors.WHITE_38 if same else ft.Colors.GREEN_400
            lbl.update()
            return same

        if target == "pause":
            already = update_label(lbl_pause)
        elif target == "prev":
            already = update_label(lbl_prev)
        elif target == "next":
            already = update_label(lbl_next)
        else:
            already = False

        recording_state["active"] = None
        if not already:
            set_aplicar_btn_state(True)
        page.update()
        
    page.on_keyboard_event = on_keyboard

    def start_record(e, target):
        recording_state["active"] = target
        if target == "pause": 
            lbl_pause.value = "⌨️ Presiona una tecla..."
            lbl_pause.color = "#ffaa00"
            lbl_pause.update()
        if target == "prev": 
            lbl_prev.value = "⌨️ Presiona una tecla..."
            lbl_prev.color = "#ffaa00"
            lbl_prev.update()
        if target == "next": 
            lbl_next.value = "⌨️ Presiona una tecla..."
            lbl_next.color = "#ffaa00"
            lbl_next.update()

    btn_pause_rec = ft.OutlinedButton(content=ft.Text("🎵 Pausa/Play"), on_click=lambda e: start_record(e, "pause"))
    btn_prev_rec = ft.OutlinedButton(content=ft.Text("⏮ Anterior"), on_click=lambda e: start_record(e, "prev"))
    btn_next_rec = ft.OutlinedButton(content=ft.Text("⏭ Siguiente"), on_click=lambda e: start_record(e, "next"))

    def aplicar_hotkeys(e):
        pause_k = lbl_pause.value.strip()
        prev_k = lbl_prev.value.strip()
        next_k = lbl_next.value.strip()

        if "Presiona" in pause_k or "Presiona" in prev_k or "Presiona" in next_k:
            show_notify("Presiona una tecla en el teclado primero.", is_warning=True)
            return

        raw_pause = pause_k if pause_k != "Clic para asignar..." else "x"
        raw_prev = prev_k if prev_k != "Clic para asignar..." else ""
        raw_next = next_k if next_k != "Clic para asignar..." else ""

        pause_val = clean_engine_key(raw_pause)
        prev_val = clean_engine_key(raw_prev) if raw_prev else ""
        next_val = clean_engine_key(raw_next) if raw_next else ""

        # Verificar duplicados entre nuestras propias teclas
        chosen = [k for k in [pause_val, prev_val, next_val] if k]
        if len(chosen) != len(set(chosen)):
            show_notify("⚠️ No puedes usar la misma tecla para dos funciones diferentes.", is_warning=True)
            return

        # Verificar colisiones con CFGs de L4D2
        bound = l4d2.get_bound_keys()
        for label, val in [("Pausa/Play", pause_val), ("Anterior", prev_val), ("Siguiente", next_val)]:
            if val and val.lower() in bound:
                show_notify(f"⚠️ Tecla '{val}' ({label}) en uso en L4D2: {bound[val.lower()][0]}", is_error=True)
                return

        # Aplicar CFG en L4D2 con la tecla de pausa
        if pause_val:
            l4d2.generate_cfg(pause_val)
            hotkey_manager.set_hotkey(pause_val, on_hotkey_pause)
        
        # Registrar listeners de hotkeys
        if prev_val:
            hotkey_manager.set_hotkey(prev_val, play_prev_song)
        if next_val:
            hotkey_manager.set_hotkey(next_val, play_next_song)

        # Guardar configuración en archivo persistente
        save_hotkeys_config(pause_val, prev_val, next_val)

        # Actualizar visuales
        if pause_val: mark_applied(lbl_pause)
        if prev_val: mark_applied(lbl_prev)
        if next_val: mark_applied(lbl_next)
        set_aplicar_btn_state(False)

        show_notify("✅ ¡Teclas guardadas y aplicadas con éxito!")

    btn_aplicar_hotkeys = ft.Button("Aplicar Teclas", icon=ft.Icons.CHECK_CIRCLE, on_click=aplicar_hotkeys, color=ft.Colors.WHITE_38, bgcolor="#1a1a1a")

    # --- CHECK GRUPO INPUT para evdev ---
    import grp
    def _user_in_input_group():
        try:
            members = grp.getgrnam("input").gr_mem
            import pwd
            username = pwd.getpwuid(os.getuid()).pw_name
            return username in members
        except Exception:
            return False

    def _try_add_to_input_group(e):
        import subprocess, pwd
        username = pwd.getpwuid(os.getuid()).pw_name
        try:
            subprocess.run(["pkexec", "usermod", "-aG", "input", username], check=True)
            show_notify("✅ ¡Listo! Cierra sesión y vuelve a entrar para activar los hotkeys.")
            btn_fix_input.visible = False
            lbl_input_warning.visible = False
            page.update()
        except Exception as ex:
            show_notify(f"❌ Error: {ex}", is_error=True)

    _in_input = _user_in_input_group()
    btn_fix_input = ft.Button(
        "Activar Hotkeys (requiere contraseña)",
        icon=ft.Icons.LOCK_OPEN,
        on_click=_try_add_to_input_group,
        color=ft.Colors.ORANGE_400,
        visible=not _in_input
    )
    lbl_input_warning = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_400),
            ft.Text(
                "Necesitas permisos para usar hotkeys globales. Haz clic en el botón para activarlos.",
                color=ft.Colors.ORANGE_400, size=12
            )
        ]),
        visible=not _in_input
    )

    ninja_panel = ft.Container(
        content=ft.Column([
            ft.Text("🥷 Modo Ninja (Captura automática de teclado)", size=16, weight=ft.FontWeight.BOLD, color="#ffaa00"),
            lbl_input_warning,
            btn_fix_input,
            ft.Text("Haz clic en los botones y presiona la tecla que desees asignar.", size=12, color=ft.Colors.WHITE_54),
            ft.Row([
                ft.Column([btn_pause_rec, lbl_pause]),
                ft.Column([btn_prev_rec, lbl_prev]),
                ft.Column([btn_next_rec, lbl_next]),
            ]),
            ft.Row([btn_aplicar_hotkeys], alignment=ft.MainAxisAlignment.END)
        ]),
        bgcolor="#121212", padding=10, border_radius=8, border=ft.Border.all(1, "#333333")
    )

    playlist_column = ft.Column([
        ninja_panel,
        ft.Row([
            ft.Text("Canciones Guardadas", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Container(expand=True),
            ft.Button("Añadir Archivo Local", icon=ft.Icons.FOLDER_OPEN, on_click=open_file_picker)
        ]),
        ft.Divider(color="#222222"),
        playlist_list
    ], expand=True)

    # --- ENSAMBLE PRINCIPAL ---
    tabs_layout = ft.Tabs(
        length=2,
        selected_index=0,
        expand=True,
        content=ft.Column([
            ft.TabBar(
                tabs=[
                    ft.Tab(label="🔍 Buscador YouTube"),
                    ft.Tab(label="🎵 Mi Playlist"),
                ]
            ),
            ft.TabBarView(
                expand=True,
                controls=[
                    ft.Container(content=search_column, padding=10),
                    ft.Container(content=playlist_column, padding=10)
                ]
            )
        ], expand=True)
    )

    page.add(ft.Column([top_bar, playback_bar, tabs_layout], expand=True))
    
    check_l4d2_status()
    load_playlist_view()
    update_playback_ui()
    page.window.visible = True
    page.update()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
