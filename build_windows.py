import os
import subprocess

print("Iniciando compilacion para Windows...")

cmd = [
    "flet", "pack", "main.py",
    "--name", "DCE_Audio_Mix",
    "--icon", "assets/logoapp.png",
    "--add-data", "assets;assets"
]

subprocess.run(cmd)
print("Compilacion terminada. Verifica la carpeta /dist/")
