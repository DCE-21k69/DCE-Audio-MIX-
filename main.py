import flet as ft
import os

def main(page: ft.Page):
    page.title = "DCE Audio Mix"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080808"
    
    # Intentar usar el icono oficial
    icon_path = os.path.abspath(os.path.join("assets", "logoapp.png"))
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    page.add(
        ft.Column(
            [
                ft.Image(src=icon_path, width=150, height=150) if os.path.exists(icon_path) else ft.Icon(ft.icons.MUSIC_NOTE, size=150),
                ft.Text("DCE AUDIO MIX", size=30, weight=ft.FontWeight.BOLD, color="#ffaa00"),
                ft.Text("Bienvenido al gestor de audio definitivo para Source Engine.", color=ft.Colors.WHITE_70),
                ft.ElevatedButton("Buscar Canción (WIP)", icon=ft.icons.SEARCH)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.run(main)
