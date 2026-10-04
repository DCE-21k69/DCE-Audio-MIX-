import os
import subprocess
import yt_dlp

def search_youtube(query: str, max_results: int = 5):
    """Busca canciones en YouTube y devuelve titulo, url, duracion y miniatura."""
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    results = []
    search_url = f"ytsearch{max_results}:{query}"
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)
        if info and 'entries' in info:
            for entry in info['entries']:
                results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                    'duration': entry.get('duration'),
                    'thumbnail': f"https://img.youtube.com/vi/{entry.get('id')}/hqdefault.jpg"
                })
    return results

def download_and_convert(youtube_url: str, output_path: str):
    """Descarga audio de YouTube y lo convierte a WAV (16-bit, Mono, 22050Hz) usando FFmpeg."""
    temp_audio = output_path + ".temp.webm"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
        
    # Convertir con FFmpeg a 16-bit PCM (s16), Mono (-ac 1), 22050Hz (-ar 22050)
    # y aplicar filtro loudnorm para normalizar el volumen
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_audio,
        "-ac", "1",
        "-ar", "22050",
        "-acodec", "pcm_s16le",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        output_path
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    return output_path

if __name__ == "__main__":
    print("Probando buscador de YouTube...")
    res = search_youtube("linkin park numb", 3)
    for r in res:
        print(f"- {r['title']} ({r['duration']}s) -> {r['url']}")
