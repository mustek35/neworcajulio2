# ========================================================================================
# VisualizadorDetector - Versión Simple Pre-Refactorización
# Basado en funcionamiento previo exitoso con QMediaPlayer
# ========================================================================================

from PyQt6.QtMultimedia import QMediaPlayer, QVideoSink, QVideoFrameFormat, QVideoFrame
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QImage
import numpy as np

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

        # ✅ CONFIGURACIÓN SIMPLE Y DIRECTA (COMO ANTES)
        self.video_player = QMediaPlayer()
        self.video_sink = QVideoSink()
        self.video_player.setVideoSink(self.video_sink)

        # ✅ CONECTAR SEÑALES INMEDIATAMENTE (ORDEN IMPORTANTE)
        self.video_sink.videoFrameChanged.connect(self.on_frame)
        self.video_player.errorOccurred.connect(self.on_error)

        # Configuración básica de FPS
        self.detection_fps = cam_data.get("detection_fps", 8)
        base_fps = 30
        self.detector_frame_interval = max(1, int(base_fps / self.detection_fps))
        self.frame_counter = 0

        # Configuración del tracker
        device = cam_data.get("device", "cpu")
        self.tracker = AdvancedTracker(
            conf_threshold=cam_data.get("confianza", 0.5),
            device=device,
            lost_ttl=cam_data.get("lost_ttl", 5),
        )
        self._pending_detections = {}
        self._last_frame = None
        self._current_frame_id = 0

        # ✅ CONFIGURAR DETECTORES SIMPLE
        self._setup_detectores(cam_data, device)

    def _setup_detectores(self, cam_data, device):
        """Configurar detectores de forma simple"""
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
                imgsz=cam_data.get("imgsz", 416),
                device=device,
                track=False,
            )
            # ✅ CONECTAR SEÑALES CORRECTAMENTE
            detector.result_ready.connect(
                lambda res, _mk, fid, mk=m: self._procesar_resultados_detector_worker(res, mk, fid)
            )
            detector.start()
            self.detectors.append(detector)
        
        logger.info("%s: %d DetectorWorker(s) iniciados", self.objectName(), len(self.detectors))

    def iniciar(self):
        """Iniciar reproducción RTSP - VERSIÓN SIMPLE"""
        rtsp_url = self.cam_data.get("rtsp")
        if not rtsp_url:
            logger.warning("%s: No se encontró URL RTSP", self.objectName())
            self.log_signal.emit(f"⚠️ [{self.objectName()}] No se encontró URL RTSP")
            return

        logger.info("%s: Iniciando RTSP %s", self.objectName(), rtsp_url)
        self.log_signal.emit(f"🎥 [{self.objectName()}] Iniciando stream: {rtsp_url}")
        
        # ✅ CONFIGURACIÓN SIMPLE Y DIRECTA
        try:
            self.video_player.setSource(QUrl(rtsp_url))
            self.video_player.play()
            self.log_signal.emit(f"▶️ [{self.objectName()}] Comando play enviado")
        except Exception as e:
            logger.error("%s: Error iniciando stream: %s", self.objectName(), e)
            self.log_signal.emit(f"❌ [{self.objectName()}] Error iniciando: {e}")

    def on_error(self, error):
        """Manejar errores del QMediaPlayer"""
        error_string = self.video_player.errorString()
        logger.error("%s: QMediaPlayer error: %s", self.objectName(), error_string)
        self.log_signal.emit(f"❌ [{self.objectName()}] Error QMediaPlayer: {error_string}")

    def on_frame(self, frame):
        """Procesar frame de video - VERSIÓN SIMPLE"""
        if not frame.isValid():
            return

        self.frame_counter += 1
        
        # Log cada 100 frames para confirmar que llegan
        if self.frame_counter % 100 == 0:
            self.log_signal.emit(f"📷 [{self.objectName()}] Frame #{self.frame_counter}: {frame.width()}x{frame.height()}")
        
        # Procesar para detección según intervalo
        if self.frame_counter % self.detector_frame_interval == 0:
            try:
                self._procesar_frame_para_deteccion(frame)
            except Exception as e:
                logger.error("%s: Error procesando frame: %s", self.objectName(), e)

    def _procesar_frame_para_deteccion(self, frame):
        """Procesar frame para detección"""
        # Convertir QVideoFrame a QImage
        qimg = self._qimage_from_frame(frame)
        if qimg is None:
            return
            
        # Convertir a formato RGB
        if qimg.format() != QImage.Format.Format_RGB888:
            img_converted = qimg.convertToFormat(QImage.Format.Format_RGB888)
        else:
            img_converted = qimg

        # Convertir a numpy array
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

        # Enviar a detectores
        for det in self.detectors:
            if det and det.isRunning():
                det.set_frame(arr, self._current_frame_id)

    def _qimage_from_frame(self, frame: QVideoFrame):
        """Convertir QVideoFrame a QImage - MÉTODO SIMPLE"""
        if frame.map(QVideoFrame.MapMode.ReadOnly):
            try:
                pf = frame.pixelFormat()
                
                # Formatos RGB compatibles
                rgb_formats = {
                    getattr(QVideoFrameFormat.PixelFormat, name)
                    for name in [
                        "Format_RGB24", "Format_RGB32", "Format_BGR24", "Format_BGR32",
                        "Format_RGBX8888", "Format_RGBA8888", "Format_BGRX8888", 
                        "Format_BGRA8888", "Format_ARGB32",
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
        
        # Fallback: usar toImage()
        image = frame.toImage()
        return image if not image.isNull() else None

    def _procesar_resultados_detector_worker(self, output_for_signal, model_key, frame_id):
        """Procesar resultados de detectores"""
        if frame_id != self._current_frame_id:
            return

        self._pending_detections[model_key] = output_for_signal
        
        # Cuando tenemos resultados de todos los detectores
        if len(self._pending_detections) == len(self.detectors):
            merged = []
            for dets in self._pending_detections.values():
                for det in dets:
                    duplicate = False
                    for mdet in merged:
                        if iou(det['bbox'], mdet['bbox']) > 0.5:
                            if det.get('conf', 0) > mdet.get('conf', 0):
                                mdet.update(det)
                            duplicate = True
                            break
                    if not duplicate:
                        merged.append(det.copy())

            # Actualizar tracker y emitir resultados
            tracks = self.tracker.update(merged, frame=self._last_frame)
            self.result_ready.emit(tracks)
            self._pending_detections = {}

    def detener(self):
        """Detener visualizador"""
        logger.info("%s: Deteniendo VisualizadorDetector", self.objectName())
        
        # Detener detectores
        if hasattr(self, 'detectors'):
            for det in self.detectors:
                if det:
                    det.stop()
        
        # Detener QMediaPlayer
        if hasattr(self, 'video_player') and self.video_player:
            try:
                self.video_player.stop()
                self.video_player.setVideoSink(None)
                self.video_player = None
            except Exception as e:
                logger.error("%s: Error deteniendo player: %s", self.objectName(), e)
        
        logger.info("%s: VisualizadorDetector detenido", self.objectName())

    def update_fps_config(self, visual_fps=25, detection_fps=8):
        """Actualizar configuración de FPS"""
        self.detection_fps = detection_fps
        base_fps = 30
        self.detector_frame_interval = max(1, int(base_fps / detection_fps))
        logger.info("%s: FPS actualizado - Detección: %d", self.objectName(), detection_fps)
