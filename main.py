import flet as ft
import os
import asyncio
from core.dce_audio_core import search_youtube, download_and_convert

def main(page: ft.Page):
    page.title = "DCE Audio Mix"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080808"
    page.window.width = 900
    page.window.height = 650

    icon_path = os.path.abspath(os.path.join("assets", "logoapp.png"))
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    search_input = ft.TextField(
        hint_text="Escribe el nombre de una canción o pega un enlace de YouTube...",
        expand=True,
        bgcolor="#101010"
    )

    results_list = ft.ListView(expand=True, spacing=10, padding=10)
    status_text = ft.Text("", color="#ffaa00", size=14)
    loading_ring = ft.ProgressRing(visible=False, width=20, height=20, color="#ffaa00")

    def create_result_card(item):
        duration_sec = item.get('duration', 0) or 0
        duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}" if duration_sec else "--:--"
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Image(src=item['thumbnail'], width=120, height=70, fit=ft.BoxFit.COVER, border_radius=6),
                    ft.Column(
                        [
                            ft.Text(item['title'], weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"Duración: {duration_min}", size=12, color=ft.Colors.WHITE_54)
                        ],
                        expand=True,
                        spacing=4
                    ),
                    ft.Button(
                        "Usar en L4D2",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda e: page.run_task(process_song_download, item['url'], item['title'])
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor="#141414",
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, "#222222")
        )

    async def process_song_download(url, title):
        status_text.value = f"Descargando y convirtiendo: {title}..."
        loading_ring.visible = True
        page.update()

        try:
            out_dir = os.path.join(os.getcwd(), "downloads")
            os.makedirs(out_dir, exist_ok=True)
            out_wav = os.path.join(out_dir, "voice_input.wav")
            
            # Ejecutar tarea pesada en un hilo para no bloquear la UI
            await asyncio.to_thread(download_and_convert, url, out_wav)
            
            loading_ring.visible = False
            status_text.value = f"✅ ¡Listo! Audio procesado y guardado como voice_input.wav en /downloads/"
        except Exception as err:
            loading_ring.visible = False
            status_text.value = f"❌ Error al procesar audio: {err}"
        
        page.update()

    async def perform_search(e):
        query = search_input.value.strip()
        if not query:
            return

        results_list.controls.clear()
        loading_ring.visible = True
        status_text.value = "Buscando en YouTube..."
        page.update()

        try:
            # Ejecutar yt-dlp en un hilo paralelo
            results = await asyncio.to_thread(search_youtube, query, 6)
            loading_ring.visible = False
            
            if not results:
                status_text.value = "No se encontraron resultados."
            else:
                status_text.value = f"Se encontraron {len(results)} resultados:"
                for item in results:
                    results_list.controls.append(create_result_card(item))
        except Exception as err:
            loading_ring.visible = False
            status_text.value = f"Error al buscar: {err}"
            
        page.update()

    search_button = ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=lambda e: page.run_task(perform_search, e))
    search_input.on_submit = lambda e: page.run_task(perform_search, e)

    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Image(src=icon_path, width=40, height=40) if os.path.exists(icon_path) else ft.Icon(ft.Icons.MUSIC_NOTE, color="#ffaa00"),
                        ft.Text("DCE AUDIO MIX", size=22, weight=ft.FontWeight.BOLD, color="#ffaa00"),
                    ],
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Divider(color="#222222"),
                ft.Row([search_input, search_button]),
                ft.Row([loading_ring, status_text], alignment=ft.MainAxisAlignment.START),
                results_list
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    ft.run(main)
