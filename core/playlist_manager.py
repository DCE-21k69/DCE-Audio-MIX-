import os
import json
import shutil
import uuid
import subprocess

PLAYLIST_DIR = ".playlist"
METADATA_FILE = os.path.join(PLAYLIST_DIR, "playlist_data.json")

def init_playlist():
    if not os.path.exists(PLAYLIST_DIR):
        os.makedirs(PLAYLIST_DIR, exist_ok=True)
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w") as f:
            json.dump([], f)

def get_playlist():
    init_playlist()
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

def save_playlist(data):
    init_playlist()
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_to_playlist(title, duration, source_wav_path, thumbnail="", is_local=False):
    playlist = get_playlist()
    song_id = str(uuid.uuid4())
    dest_wav = os.path.join(PLAYLIST_DIR, f"{song_id}.wav")
    
    shutil.copy2(source_wav_path, dest_wav)
    
    new_song = {
        "id": song_id,
        "title": title,
        "duration": duration,
        "thumbnail": thumbnail,
        "file": dest_wav,
        "is_local": is_local
    }
    playlist.append(new_song)
    save_playlist(playlist)
    return new_song

def remove_from_playlist(song_id):
    playlist = get_playlist()
    new_playlist = []
    for s in playlist:
        if s["id"] == song_id:
            if os.path.exists(s["file"]):
                os.remove(s["file"])
        else:
            new_playlist.append(s)
    save_playlist(new_playlist)

def import_local_file(file_path):
    # Convertir MP3/WAV a formato L4D2 y añadir a playlist
    title = os.path.basename(file_path)
    temp_wav = os.path.join(PLAYLIST_DIR, "temp_local.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", file_path,
        "-ac", "1",
        "-ar", "22050",
        "-acodec", "pcm_s16le",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        temp_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Obtener duracion aproximada con ffprobe si es posible (simplificado a 0 aqui)
    add_to_playlist(title, 0, temp_wav, thumbnail="", is_local=True)
    if os.path.exists(temp_wav):
        os.remove(temp_wav)
