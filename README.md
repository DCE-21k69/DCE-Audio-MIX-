# 🎵 DCE Audio MIX - Left 4 Dead 2

<p align="center">
  <img src="assets/logoapp.png" alt="DCE Audio MIX Logo" width="160"/>
  <br>
  <b>Gestor e Inyector de Audio en Tiempo Real con Modo Ninja para Left 4 Dead 2</b>
  <br>
  <i>Compatible con Windows y Linux (X11 & Wayland / Steam Deck)</i>
</p>

---

## 📖 ¿Qué es DCE Audio MIX?

**DCE Audio MIX** es una herramienta complementaria diseñada para la comunidad de Left 4 Dead 2 (especialmente jugadores de Versus y Modders). Permite buscar, descargar, convertir y reproducir cualquier canción o clip de audio a través del canal de voz del juego (`voice_input.wav`) sin interrumpir la partida.

Con su **Modo Ninja**, puedes cambiar canciones o pausar directamente con el teclado mientras juegas a pantalla completa, con detección automática de conflictos para no sobreescribir tus binds de `autoexec.cfg`.

---

## ✨ Características Principales

- 🔍 **Buscador de YouTube Integrado:**
  - Búsqueda por palabras clave o enlaces directos de YouTube.
  - Carga rápida con scroll infinito y apertura de enlace en navegador.
  - Conversión automática en tiempo real al formato exacto de Source Engine: **22050 Hz, 16-bit Mono PCM (.wav)**.
- 🎵 **Mi Playlist Local:**
  - Guarda canciones descargadas en una carpeta oculta (`.playlist`).
  - Importación directa de archivos de música locales (`.mp3`, `.wav`, etc.) desde tu equipo.
  - Inyección instantánea al juego con un solo clic.
- 🥷 **Modo Ninja (Hotkeys Globales en Partida):**
  - Controla la música (**Siguiente**, **Anterior**, **Pausar/Play**) con teclas de acceso rápido globales.
  - Capturador automático de teclas: haz clic y presiona cualquier tecla (flechas, teclado numérico, F1-F12, etc.).
  - Funciona con el juego a pantalla completa sin minimizar.
- 🛡️ **Detector de Binds y Conflictos CFG:**
  - Escanea tus archivos de configuración de L4D2 (`config.cfg`, `autoexec.cfg`, etc.).
  - Si intentas asignar una tecla que ya está en uso por tus macros o acciones del juego, la app te avisa y te protege.
  - Previene asignar la misma tecla a dos acciones distintas.
- 🐧 **Compatibilidad Total en Linux & Steam Deck:**
  - Soporte para **X11 y Wayland** mediante el subsistema de eventos del kernel (`evdev`).
  - Asistente de permisos integrado con `pkexec` (solicita contraseña gráficamente sin tocar la terminal).
- 🪟 **Modo Frameless y Diseño Oscuro:**
  - Ventana personalizada sin barra blanca del sistema operativo.
  - Diseño moderno, oscuro y optimizado.

---

## 🛠️ Requisitos del Sistema

1. **Python 3.10 o superior**
2. **FFmpeg instalado en el sistema:**
   - **Arch Linux / Manjaro:** `sudo pacman -S ffmpeg`
   - **Ubuntu / Debian / Linux Mint:** `sudo apt install ffmpeg`
   - **Fedora:** `sudo dnf install ffmpeg`
   - **Windows:** Descargar de [ffmpeg.org](https://ffmpeg.org/download.html) y agregarlo al PATH.
3. *(Solo en Linux)* Pertenecer al grupo `input` para que el Modo Ninja pueda leer teclas globales:
   - La app incluye un botón automático en la interfaz para activar estos permisos (`pkexec`).

---

## 🚀 Instalación y Puesta en Marcha

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/DCE-21k69/DCE-Audio-MIX-.git
   cd DCE-Audio-MIX-
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   *(En Windows CMD: `venv\Scripts\activate`)*

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python3 main.py
   ```

---

## 🎮 Cómo Usar Dentro de Left 4 Dead 2

1. Abre **DCE Audio MIX** y haz clic en **"Conectar"** en la barra superior.
   - La app generará automáticamente el archivo `dce_audio.cfg` en la carpeta `cfg` de tu juego y verificará la ruta.
2. Abre tu **Left 4 Dead 2**.
3. Abre la consola del juego (tecla `~` o la que tengas asignada) y escribe:
   ```cfg
   exec dce_audio.cfg
   ```
   *(Solo necesitas ejecutar este comando una vez al entrar al juego).*
4. **Reproducir música:**
   - Presiona la tecla asignada en la app para Pausa/Play (por defecto `x`).
   - La música sonará por tu micrófono en el juego para que todo el servidor la escuche.
5. **Modo Ninja en plena partida:**
   - Presiona tus teclas de **Siguiente** o **Anterior** configuradas en la app para pasar de canción sin salir del juego.

---

## 📁 Estructura del Proyecto

```
DCE Audio MIX/
├── assets/                  # Logos, iconos y recursos gráficos
├── core/
│   ├── l4d2_manager.py      # Detección de proceso, generación de CFG y parseo de binds
│   ├── playlist_manager.py  # Gestión de playlist local y conversiones FFmpeg
│   └── hotkeys.py           # Capturador de hotkeys globales del kernel (evdev)
├── main.py                  # Interfaz gráfica Flet y orquestación
├── requirements.txt         # Dependencias de Python fijadas
└── README.md                # Documentación oficial
```

---

## 👤 Créditos y Comunidad

- **Desarrollador Principal:** [DCE-21k69](https://github.com/DCE-21k69)
- **Ecosistema:** DCE Mods Loader Versus L4D2
- **Licencia:** MIT License - Libre para la comunidad.
