#!/bin/bash
echo "Iniciando compilacion Flatpak para Linux..."
mkdir -p dist/linux
cp main.py dist/linux/dce_audio_mix
chmod +x dist/linux/dce_audio_mix
echo "Para construir el Flatpak ejecuta: flatpak-builder build-dir flatpak/com.github.dce21k69.dceaudiomix.yaml --force-clean"
