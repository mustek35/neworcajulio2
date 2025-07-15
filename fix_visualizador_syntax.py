# ========================================================================================
# ARCHIVO: fix_visualizador_syntax.py
# Corrección del error de sintaxis en visualizador_detector.py
# ========================================================================================

import os
import shutil
from datetime import datetime

def fix_visualizador_syntax():
    """
    Corregir error de sintaxis en visualizador_detector.py
    """
    print("🔧 CORRIGIENDO ERROR DE SINTAXIS")
    print("=" * 50)
    
    archivo = "gui/visualizador_detector.py"
    
    if not os.path.exists(archivo):
        print(f"❌ {archivo} no encontrado")
        return False
    
    # Crear backup
    backup_file = f"{archivo}.backup_syntax_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(archivo, backup_file)
    print(f"💾 Backup creado: {backup_file}")
    
    try:
        # Leer contenido
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar el error específico en la línea 229
        # El error es que falta salto de línea antes de "def iniciar"
        error_pattern = 'self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame FFmpeg: {e}")    def iniciar(self):'
        
        if error_pattern in contenido:
            # Corregir agregando salto de línea
            contenido_corregido = contenido.replace(
                error_pattern,
                'self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame FFmpeg: {e}")\n\n    def iniciar(self):'
            )
            print("✅ Error específico encontrado y corregido")
        else:
            # Buscar patrón más general
            import re
            # Buscar líneas que terminan con ")    def " 
            patron = r'(\)[ ]*def )'
            matches = re.findall(patron, contenido)
            
            if matches:
                print(f"🔍 Encontrados {len(matches)} problemas de formato")
                # Corregir todos los casos
                contenido_corregido = re.sub(r'(\))[ ]*def ', r'\1\n\n    def ', contenido)
            else:
                print("🔍 Buscando otros problemas de sintaxis...")
                contenido_corregido = fix_general_syntax_issues(contenido)
        
        # Verificar sintaxis
        try:
            compile(contenido_corregido, archivo, 'exec')
            print("✅ Sintaxis verificada correctamente")
        except SyntaxError as e:
            print(f"❌ Aún hay errores de sintaxis:")
            print(f"   Línea {e.lineno}: {e.text}")
            print(f"   Error: {e.msg}")
            
            # Intentar corrección adicional
            contenido_corregido = fix_specific_syntax_error(contenido_corregido, e)
        
        # Guardar archivo corregido
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(contenido_corregido)
        
        print(f"✅ Archivo corregido: {archivo}")
        return True
        
    except Exception as e:
        print(f"❌ Error durante corrección: {e}")
        return False

def fix_general_syntax_issues(contenido):
    """
    Corregir problemas generales de sintaxis
    """
    print("🔧 Aplicando correcciones generales...")
    
    # 1. Asegurar saltos de línea antes de def
    import re
    contenido = re.sub(r'([^\\n])[ ]*def ', r'\1\n\n    def ', contenido)
    
    # 2. Corregir indentación de métodos
    contenido = re.sub(r'\\n[ ]*def ([^_])', r'\n\n    def \1', contenido)
    
    # 3. Asegurar que los métodos empiecen con indentación correcta
    lines = contenido.split('\n')
    corrected_lines = []
    
    for i, line in enumerate(lines):
        # Si es una línea def que no está bien indentada
        if line.strip().startswith('def ') and not line.startswith('    def '):
            if i > 0 and not corrected_lines[-1].strip() == '':
                corrected_lines.append('')  # Agregar línea vacía
            corrected_lines.append('    ' + line.strip())  # Indentar correctamente
        else:
            corrected_lines.append(line)
    
    return '\n'.join(corrected_lines)

def fix_specific_syntax_error(contenido, error):
    """
    Corregir error específico de sintaxis
    """
    print(f"🔧 Corrigiendo error específico en línea {error.lineno}...")
    
    lines = contenido.split('\n')
    
    if error.lineno <= len(lines):
        error_line = lines[error.lineno - 1]
        print(f"   Línea problemática: {error_line}")
        
        # Corregir problemas comunes
        if 'def ' in error_line and not error_line.strip().startswith('def '):
            # Problema de indentación de método
            lines[error.lineno - 1] = '    ' + error_line.strip()
            print("   ✅ Indentación de método corregida")
            
        elif ')    def ' in error_line:
            # Falta salto de línea antes de def
            parts = error_line.split(')    def ')
            if len(parts) == 2:
                lines[error.lineno - 1] = parts[0] + ')'
                lines.insert(error.lineno, '')
                lines.insert(error.lineno + 1, '    def ' + parts[1])
                print("   ✅ Salto de línea agregado antes de def")
    
    return '\n'.join(lines)

def restore_from_backup():
    """
    Restaurar desde backup más reciente si la corrección falla
    """
    print("\n🔄 OPCIÓN: RESTAURAR DESDE BACKUP")
    
    # Buscar backups
    backups = []
    for file in os.listdir("."):
        if "visualizador_detector.py.backup" in file:
            backups.append(file)
    
    if not backups:
        print("❌ No se encontraron backups")
        return False
    
    # Ordenar por fecha (más reciente primero)
    backups.sort(reverse=True)
    
    print("📁 Backups encontrados:")
    for i, backup in enumerate(backups[:3], 1):
        print(f"   {i}. {backup}")
    
    try:
        selection = input(f"\n¿Restaurar desde {backups[0]}? (s/N): ").strip().lower()
        
        if selection in ['s', 'si', 'sí', 'y', 'yes']:
            shutil.copy2(backups[0], "gui/visualizador_detector.py")
            print(f"✅ Restaurado desde {backups[0]}")
            return True
    except Exception as e:
        print(f"❌ Error restaurando: {e}")
    
    return False

def create_clean_visualizador():
    """
    Crear una versión limpia del visualizador sin FFmpeg bridge
    """
    print("\n🆕 CREANDO VERSIÓN LIMPIA SIN FFMPEG BRIDGE")
    
    visualizador_limpio = '''# ========================================================================================
# ARCHIVO: gui/visualizador_detector.py
# Versión limpia sin FFmpeg Bridge (funcionará con OpenCV normal)
# ========================================================================================

from PyQt6.QtMultimedia import QMediaPlayer, QVideoSink, QVideoFrameFormat, QVideoFrame
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QImage
import numpy as np
import time

from core.detector_worker import DetectorWorker, iou
from core.advanced_tracker import AdvancedTracker

from logging_utils import get_logger

logger = get_logger(__name__)

class VisualizadorDetector(QObject):
    result_ready = pyqtSignal(list) 
    log_signal = pyqtSignal(str)

    def __init__(self, cam_data, parent=None):
        super().__init__(parent)
        self.cam_data = cam_data
        cam_ip_for_name = self.cam_data.get('ip', str(id(self))) 
        self.setObjectName(f"Visualizador_{cam_ip_for_name}")

        self.video_player = QMediaPlayer()
        self.video_sink = QVideoSink()
        self.video_player.setVideoSink(self.video_sink)

        self.video_sink.videoFrameChanged.connect(self.on_frame)
        self.video_player.errorOccurred.connect(
            lambda e: logger.error(
                "MediaPlayer error (%s): %s", self.objectName(), self.video_player.errorString()
            )
        )

        # Configuración de FPS mejorada
        fps_config = cam_data.get("fps_config", {})
        self.visual_fps = fps_config.get("visual_fps", 25)
        self.detection_fps = fps_config.get("detection_fps", cam_data.get("detection_fps", 8))
        
        # Calcular intervalo de detección basado en FPS
        base_fps = 30  # Asumimos que el stream llega a ~30 FPS
        self.detector_frame_interval = max(1, int(base_fps / self.detection_fps))
        
        self.frame_counter = 0

        imgsz_default = cam_data.get("imgsz", 416)
        device = cam_data.get("device", "cpu")
        logger.debug("%s: Inicializando DetectorWorker en %s", self.objectName(), device)

        # Tracker compartido para todas las detecciones
        self.tracker = AdvancedTracker(
            conf_threshold=cam_data.get("confianza", 0.5),
            device=device,
            lost_ttl=cam_data.get("lost_ttl", 5),
        )
        self._pending_detections = {}
        self._last_frame = None
        self._current_frame_id = 0

        modelos = cam_data.get("modelos")
        if not modelos:
            modelo_single = cam_data.get("modelo", "Personas")
            modelos = [modelo_single] if modelo_single else []

        self.detectors = []
        for m in modelos:
            detector = DetectorWorker(
                model_key=m,
                confidence=cam_data.get("confianza", 0.5),
                frame_interval=1,
                imgsz=imgsz_default,
                device=device,
                track=False,
            )
            detector.result_ready.connect(
                lambda res, _mk, fid, mk=m: self._procesar_resultados_detector_worker(res, mk, fid)
            )
            detector.start()
            self.detectors.append(detector)
        logger.debug("%s: %d DetectorWorker(s) started", self.objectName(), len(self.detectors))

    def update_fps_config(self, visual_fps=25, detection_fps=8):
        """Actualizar configuración de FPS en tiempo real"""
        self.visual_fps = visual_fps
        self.detection_fps = detection_fps
        
        base_fps = 30
        self.detector_frame_interval = max(1, int(base_fps / detection_fps))
        
        logger.info("%s: FPS actualizado - Visual: %d, Detección: %d (intervalo: %d)", 
                   self.objectName(), visual_fps, detection_fps, self.detector_frame_interval)

    def _procesar_resultados_detector_worker(self, output_for_signal, model_key, frame_id):
        logger.debug(
            "%s: _procesar_resultados_detector_worker received results for model %s",
            self.objectName(),
            model_key,
        )
        if frame_id != self._current_frame_id:
            logger.debug(
                "%s: Ignoring results for old frame %s (current %s)",
                self.objectName(),
                frame_id,
                self._current_frame_id,
            )
            return

        self._pending_detections[model_key] = output_for_signal
        if len(self._pending_detections) == len(self.detectors):
            merged = []
            for dets in self._pending_detections.values():
                for det in dets:
                    duplicate = False
                    for mdet in merged:
                        # Merge if boxes overlap significantly regardless of class
                        if iou(det['bbox'], mdet['bbox']) > 0.5:
                            if det.get('conf', 0) > mdet.get('conf', 0):
                                mdet.update(det)
                            duplicate = True
                            break
                    if not duplicate:
                        merged.append(det.copy())

            tracks = self.tracker.update(merged, frame=self._last_frame)
            self.result_ready.emit(tracks)
            self._pending_detections = {}

    def iniciar(self):
        rtsp_url = self.cam_data.get("rtsp")
        if rtsp_url:
            logger.info("%s: Reproduciendo RTSP %s", self.objectName(), rtsp_url)
            self.log_signal.emit(f"🎥 [{self.objectName()}] Streaming iniciado: {rtsp_url}")
            
            # Configurar callbacks del media player
            self.video_player.playbackStateChanged.connect(self._on_playback_state_changed)
            self.video_player.mediaStatusChanged.connect(self._on_media_status_changed)
            
            self.video_player.setSource(QUrl(rtsp_url))
            self.video_player.play()
        else:
            logger.warning("%s: No se encontró URL RTSP para iniciar", self.objectName())
            self.log_signal.emit(f"⚠️ [{self.objectName()}] No se encontró URL RTSP.")
    
    def _on_playback_state_changed(self, state):
        """Callback para cambios en el estado de reproducción"""
        state_names = {0: "StoppedState", 1: "PlayingState", 2: "PausedState"}
        state_name = state_names.get(state, f"Unknown({state})")
        self.log_signal.emit(f"🎬 [{self.objectName()}] Estado reproducción: {state_name}")
        
        if state == 0:  # Stopped
            self.log_signal.emit(f"⛔ [{self.objectName()}] STREAM DETENIDO - Verificar conexión")
            
    def _on_media_status_changed(self, status):
        """Callback para cambios en el estado del media"""
        status_names = {
            0: "NoMedia", 1: "LoadingMedia", 2: "LoadedMedia", 3: "StalledMedia",
            4: "BufferingMedia", 5: "BufferedMedia", 6: "EndOfMedia", 7: "InvalidMedia"
        }
        status_name = status_names.get(status, f"Unknown({status})")
        self.log_signal.emit(f"📺 [{self.objectName()}] Estado media: {status_name}")
        
        if status == 7:  # InvalidMedia
            self.log_signal.emit(f"❌ [{self.objectName()}] MEDIA INVÁLIDO - URL incorrecta o stream no disponible")
        elif status == 3:  # StalledMedia  
            self.log_signal.emit(f"⚠️ [{self.objectName()}] STREAM INTERRUMPIDO - Problemas de red")
        elif status == 5:  # BufferedMedia
            self.log_signal.emit(f"✅ [{self.objectName()}] STREAM ACTIVO - Recibiendo datos")

    def detener(self):
        logger.info("%s: Deteniendo VisualizadorDetector", self.objectName())
        
        if hasattr(self, 'detectors'):
            for det in self.detectors:
                if det:
                    logger.info("%s: Deteniendo %s", self.objectName(), det.objectName())
                    det.stop()
                    
        if hasattr(self, 'video_player') and self.video_player:
            player_state = self.video_player.playbackState()
            if player_state != QMediaPlayer.PlaybackState.StoppedState:
                logger.info("%s: Deteniendo QMediaPlayer estado %s", self.objectName(), player_state)
                self.video_player.stop()
            logger.info("%s: Desvinculando salida de video del QMediaPlayer", self.objectName())
            self.video_player.setVideoSink(None)
            logger.info("%s: Agendando QMediaPlayer para deleteLater", self.objectName())
            self.video_player.deleteLater()
            self.video_player = None
            
        if hasattr(self, 'video_sink') and self.video_sink:
            self.video_sink = None
            
        logger.info("%s: VisualizadorDetector detenido", self.objectName())

    def on_frame(self, frame):
        logger.debug(
            "%s: on_frame called %d (interval %d)",
            self.objectName(),
            self.frame_counter,
            self.detector_frame_interval,
        )
        
        if not frame.isValid():
            self.log_signal.emit(f"❌ [{self.objectName()}] Frame inválido recibido")
            return

        # Debug: Información del frame cada 100 frames
        if self.frame_counter % 100 == 0:
            self.log_signal.emit(f"📷 [{self.objectName()}] Frame #{self.frame_counter}: {frame.width()}x{frame.height()}")
        
        handle_type = frame.handleType()
        logger.debug("%s: frame handle type %s", self.objectName(), handle_type)

        self.frame_counter += 1
        
        # Procesar frames para detección según la configuración de FPS
        if self.frame_counter % self.detector_frame_interval == 0:
            try:
                qimg = self._qimage_from_frame(frame)
                if qimg is None:
                    if self.frame_counter % 50 == 0:
                        self.log_signal.emit(f"⚠️ [{self.objectName()}] No se pudo convertir frame a QImage")
                    return
                    
                if qimg.format() != QImage.Format.Format_RGB888:
                    img_converted = qimg.convertToFormat(QImage.Format.Format_RGB888)
                else:
                    img_converted = qimg

                buffer = img_converted.constBits()
                bytes_per_pixel = img_converted.depth() // 8
                buffer.setsize(img_converted.height() * img_converted.width() * bytes_per_pixel)

                arr = (
                    np.frombuffer(buffer, dtype=np.uint8)
                    .reshape((img_converted.height(), img_converted.width(), bytes_per_pixel))
                    .copy()
                )

                self._last_frame = arr
                self._pending_detections = {}
                self._current_frame_id += 1

                if hasattr(self, 'detectors'):
                    detectores_activos = sum(1 for det in self.detectors if det and det.isRunning())
                    if self.frame_counter % 200 == 0:
                        self.log_signal.emit(f"🤖 [{self.objectName()}] Detectores activos: {detectores_activos}/{len(self.detectors)}")
                    
                    for det in self.detectors:
                        if det and det.isRunning():
                            det.set_frame(arr, self._current_frame_id)
                else:
                    if self.frame_counter % 100 == 0:
                        self.log_signal.emit(f"⚠️ [{self.objectName()}] No hay detectores configurados")

            except Exception as e:
                logger.error("%s: error procesando frame en on_frame: %s", self.objectName(), e)
                self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame: {e}")

    def _qimage_from_frame(self, frame: QVideoFrame) -> QImage | None:
        if frame.map(QVideoFrame.MapMode.ReadOnly):
            try:
                pf = frame.pixelFormat()
                rgb_formats = {
                    getattr(QVideoFrameFormat.PixelFormat, name)
                    for name in [
                        "Format_RGB24", "Format_RGB32", "Format_BGR24", "Format_BGR32",
                        "Format_RGBX8888", "Format_RGBA8888", "Format_BGRX8888", "Format_BGRA8888", "Format_ARGB32",
                    ]
                    if hasattr(QVideoFrameFormat.PixelFormat, name)
                }
                if pf in rgb_formats:
                    img_format = QVideoFrameFormat.imageFormatFromPixelFormat(pf)
                    if img_format != QImage.Format.Format_Invalid:
                        return QImage(
                            frame.bits(),
                            frame.width(),
                            frame.height(),
                            frame.bytesPerLine(),
                            img_format,
                        ).copy()
            finally:
                frame.unmap()
        image = frame.toImage()
        return image if not image.isNull() else None
'''
    
    # Escribir versión limpia
    with open("gui/visualizador_detector_clean.py", 'w', encoding='utf-8') as f:
        f.write(visualizador_limpio)
    
    print("✅ Versión limpia creada: gui/visualizador_detector_clean.py")
    
    # Preguntar si reemplazar
    try:
        replace = input("¿Reemplazar archivo problemático con versión limpia? (s/N): ").strip().lower()
        if replace in ['s', 'si', 'sí', 'y', 'yes']:
            shutil.copy2("gui/visualizador_detector_clean.py", "gui/visualizador_detector.py")
            print("✅ Archivo reemplazado con versión limpia")
            return True
    except:
        pass
    
    return False

def main():
    """
    Función principal para corregir sintaxis
    """
    print("🔧 CORRECCIÓN DE SINTAXIS - VISUALIZADOR DETECTOR")
    print("=" * 60)
    
    print("📋 ERROR DETECTADO:")
    print("   Línea 229: Falta salto de línea antes de 'def iniciar'")
    print("   Causa: Error en integración FFmpeg Bridge")
    
    print("\n🛠️ OPCIONES DE CORRECCIÓN:")
    print("1. 🔧 Corregir sintaxis automáticamente")
    print("2. 🔄 Restaurar desde backup")
    print("3. 🆕 Usar versión limpia (sin FFmpeg Bridge)")
    
    try:
        opcion = input("\nSelecciona opción (1-3): ").strip()
        
        if opcion == "1":
            if fix_visualizador_syntax():
                print("\n✅ Sintaxis corregida exitosamente")
                print("💡 Prueba ejecutar: python app.py")
            else:
                print("\n❌ No se pudo corregir automáticamente")
                print("💡 Prueba opción 2 o 3")
                
        elif opcion == "2":
            if restore_from_backup():
                print("\n✅ Restaurado desde backup")
                print("💡 Prueba ejecutar: python app.py")
            else:
                print("\n❌ No se pudo restaurar")
                
        elif opcion == "3":
            if create_clean_visualizador():
                print("\n✅ Versión limpia instalada")
                print("💡 Tu aplicación debería funcionar ahora")
                print("⚠️ Nota: Cámara 192.168.1.3 seguirá con timeout (sin FFmpeg)")
            else:
                print("\n⚠️ Versión limpia creada pero no instalada")
                
        else:
            print("❌ Opción inválida")
    
    except KeyboardInterrupt:
        print("\n⏹️ Cancelado por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()