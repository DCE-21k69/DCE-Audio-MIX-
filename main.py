import flet as ft
import os
import asyncio
import webbrowser
from core.dce_audio_core import search_youtube, download_and_convert
from core.l4d2_manager import L4D2Manager
from core.playlist_manager import get_playlist, add_to_playlist, remove_from_playlist, import_local_file

def main(page: ft.Page):
    page.title = "DCE Audio Mix"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080808"
    page.window.width = 950
    page.window.height = 750

    icon_path = os.path.abspath(os.path.join("assets", "logoapp.png"))
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    l4d2 = L4D2Manager()

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
        success, msg = l4d2.generate_cfg()
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN_800 if success else ft.Colors.RED_800)
        page.snack_bar.open = True
        check_l4d2_status()

    btn_connect = ft.Button("Conectar / Inyectar CFG", icon=ft.Icons.CABLE, on_click=do_connect_l4d2, color="#ffaa00")

    top_bar = ft.Container(
        content=ft.Row([
            ft.Image(src=icon_path, width=40, height=40) if os.path.exists(icon_path) else ft.Icon(ft.Icons.MUSIC_NOTE, color="#ffaa00"),
            ft.Text("DCE AUDIO MIX", size=22, weight=ft.FontWeight.BOLD, color="#ffaa00"),
            ft.Container(expand=True),
            l4d2_status_icon,
            l4d2_status_text,
            btn_connect
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=10,
        bgcolor="#121212",
        border_radius=8
    )

    # --- PESTAÑA 1: BUSCADOR ---
    search_state = {"query": "", "loaded_count": 0, "is_loading_more": False, "has_more": True, "is_direct_link": False}
    search_input = ft.TextField(hint_text="Escribe el nombre o pega enlace de YouTube...", expand=True, bgcolor="#101010")
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
            success, msg = l4d2.set_voice_input(out_wav)
            status_text.value = f"✅ {msg}"
        except Exception as err:
            status_text.value = f"❌ Error: {err}"
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
            load_playlist_view()
        except Exception as err:
            status_text.value = f"❌ Error: {err}"
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

    def inject_playlist_song(song):
        success, msg = l4d2.set_voice_input(song['file'])
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN_800 if success else ft.Colors.RED_800)
        page.snack_bar.open = True
        page.update()

    def delete_playlist_song(song_id):
        remove_from_playlist(song_id)
        load_playlist_view()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                page.snack_bar = ft.SnackBar(ft.Text(f"Procesando {f.name}..."))
                page.snack_bar.open = True; page.update()
                import_local_file(f.path)
            load_playlist_view()

    file_picker = ft.FilePicker(on_result=on_file_picked)

    async def open_file_picker(e):
        await file_picker.pick_files(allow_multiple=True, allowed_extensions=["mp3", "wav", "m4a", "ogg"])

    page.services.append(file_picker)

    playlist_column = ft.Column([
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

    page.add(ft.Column([top_bar, tabs_layout], expand=True))
    
    check_l4d2_status()
    load_playlist_view()

if __name__ == "__main__":
    ft.run(main)
