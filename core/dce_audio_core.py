import os
import subprocess
import yt_dlp

def search_youtube(query: str, max_results: int = 5):
    """Busca canciones en YouTube o procesa un enlace directo."""
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    
    results = []
    
    # Verificar si es un enlace directo
    if "youtube.com" in query or "youtu.be" in query:
        search_url = query
    else:
        search_url = f"ytsearch{max_results}:{query}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            if info:
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            video_id = entry.get('id')
                            results.append({
                                'id': video_id,
                                'title': entry.get('title', 'Sin titulo'),
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'duration': entry.get('duration', 0),
                                'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                            })
                else:
                    video_id = info.get('id')
                    results.append({
                        'id': video_id,
                        'title': info.get('title', 'Sin titulo'),
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'duration': info.get('duration', 0),
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    })
    except Exception as e:
        print(f"Error en busqueda de YouTube: {e}")
        
    return results

def download_and_convert(youtube_url: str, output_path: str):
    """Descarga audio de YouTube y lo convierte a WAV (16-bit, Mono, 22050Hz) usando FFmpeg."""
    temp_audio = output_path + ".temp.webm"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
        
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
