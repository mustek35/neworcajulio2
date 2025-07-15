# Sistema de Visualización con Soporte de GStreamer

Este proyecto incluye utilidades para visualizar cámaras RTSP.

## Backend de decodificación

El archivo `config.json` posee ahora el parámetro `decoder_backend` para
seleccionar el método de decodificación preferido:

```json
"decoder_backend": "ffmpeg"  // o "gstreamer"
```

- **ffmpeg**: usa `FFmpegRTSPReader` como antes.
- **gstreamer**: usa `GStreamerRTSPReader` si GStreamer está disponible.
- Cualquier valor distinto o ausencia del parámetro implica modo `auto`,
  que intentará GStreamer y luego FFmpeg.

## Instalación de GStreamer

Para utilizar el backend GStreamer es necesario instalar GStreamer junto
con los plugins de vídeo (por ejemplo `gstreamer1.0-plugins-bad` y
`gstreamer1.0-libav`). En un sistema basado en Debian esto puede lograrse
con:

```bash
sudo apt-get install python3-gi gstreamer1.0-tools \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-libav
```

Asegúrese de que las bindings de Python (`gi`) estén disponibles.

