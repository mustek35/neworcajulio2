# ========================================================================================
# gui/visualizador_detector.py - CÓDIGO COMPLETO CORREGIDO
# ========================================================================================

import time

# ✅ IMPORT FFMPEG BRIDGE PARA TODAS LAS CÁMARAS
try:
    from ffmpeg_rtsp_bridge import FFmpegRTSPReader
    FFMPEG_BRIDGE_AVAILABLE = True
    print("✅ FFmpeg Bridge disponible para todas las cámaras")
except ImportError:
    FFMPEG_BRIDGE_AVAILABLE = False
    print("⚠️ FFmpeg Bridge no disponible - usando QMediaPlayer")

# Detectar soporte GStreamer
try:
    from gstreamer_rtsp_bridge import GStreamerRTSPReader
    GST_BRIDGE_AVAILABLE = True
    print("✅ GStreamer Bridge disponible")
except Exception:
    GST_BRIDGE_AVAILABLE = False
    print("⚠️ GStreamer Bridge no disponible")

from PyQt6.QtMultimedia import QMediaPlayer, QVideoSink, QVideoFrameFormat, QVideoFrame
from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QImage, QPixmap
import numpy as np
import cv2

from core.detector_worker import DetectorWorker, iou
from core.advanced_tracker import AdvancedTracker

from logging_utils import get_logger

logger = get_logger(__name__)

class VisualizadorDetector(QObject):
    result_ready = pyqtSignal(list) 
    log_signal = pyqtSignal(str)
    frame_ready = pyqtSignal(QImage)  # 🔥 NUEVA SEÑAL PARA VIDEO
    frame_ready = pyqtSignal(QPixmap)
    stats_ready = pyqtSignal(dict)

    def __init__(self, cam_data, parent=None):
        super().__init__(parent)
        self.cam_data = cam_data
        cam_ip_for_name = self.cam_data.get('ip', str(id(self)))
        self.setObjectName(f"Visualizador_{cam_ip_for_name}")

        # Backend de decodificación
        try:
            import json
            with open('config.json', 'r', encoding='utf-8') as f:
                global_cfg = json.load(f)
                global_backend = global_cfg.get('decoder_backend', 'ffmpeg')
        except Exception:
            global_backend = 'ffmpeg'

        self.decoder_backend = cam_data.get('decoder_backend', global_backend)

        # Configuración de debug y rendimiento
        self.debug_visual = cam_data.get('debug_visual', True)
        self.show_fps_overlay = cam_data.get('show_fps_overlay', True)
        self.log_frame_processing = cam_data.get('log_frame_processing', True)
        
        # Detección NVIDIA
        self.nvidia_enabled = self._check_nvidia_support()
        self.ffmpeg_strategy = None
        
        # Log configuración inicial
        self.log_signal.emit(f"🚀 [{self.objectName()}] VisualizadorDetector iniciando...")
        self.log_signal.emit(f"   📍 IP Cámara: {cam_ip_for_name}")
        self.log_signal.emit(f"   🚀 NVIDIA: {'Sí' if self.nvidia_enabled else 'No'}")
        self.log_signal.emit(f"   🎬 FFmpeg: {'Sí' if FFMPEG_BRIDGE_AVAILABLE else 'No'}")
        
        # Configuración QMediaPlayer (fallback)
        self.video_player = QMediaPlayer()
        self.video_sink = QVideoSink()
        self.video_player.setVideoSink(self.video_sink)

        self.video_sink.videoFrameChanged.connect(self.on_frame)
        self.video_player.errorOccurred.connect(self._handle_media_error)

        # Configuración de FPS
        fps_config = cam_data.get("fps_config", {})
        self.visual_fps = fps_config.get("visual_fps", 25)
        self.detection_fps = fps_config.get("detection_fps", cam_data.get("detection_fps", 8))
        
        base_fps = 30
        self.detector_frame_interval = max(1, int(base_fps / self.detection_fps))
        
        self.log_signal.emit(f"   📈 FPS Visual: {self.visual_fps}")
        self.log_signal.emit(f"   🤖 FPS Detección: {self.detection_fps} (intervalo: {self.detector_frame_interval})")
        
        self.frame_counter = 0

        # Variables FFmpeg
        self.ffmpeg_reader = None
        self.ffmpeg_thread = None
        self.using_ffmpeg = False
        # Variables GStreamer
        self.gst_reader = None
        self.gst_thread = None
        self.using_gstreamer = False
        
        # Estadísticas
        self.stats = {
            'start_time': time.time(),
            'total_frames': 0,
            'processed_frames': 0,
            'detection_frames': 0,
            'ffmpeg_frames': 0,
            'gst_frames': 0,
            'qt_frames': 0,
            'dropped_frames': 0,
            'last_fps_calculation': time.time(),
            'fps_window_frames': 0,
            'current_fps': 0.0,
            'avg_processing_time': 0.0,
            'processing_times': [],
            'errors': 0,
            'last_error': None
        }

        # Configuración de detección
        device = self._get_optimal_device()
        imgsz_default = cam_data.get("imgsz", 416)
        
        self.log_signal.emit(f"   🎯 Device: {device}")

        # Tracker
        self.tracker = AdvancedTracker(
            conf_threshold=cam_data.get("confianza", 0.5),
            device=device,
            lost_ttl=cam_data.get("lost_ttl", 5),
        )
        self._pending_detections = {}
        self._last_frame = None
        self._current_frame_id = 0

        # Detectores
        modelos = cam_data.get("modelos")
        if not modelos:
            modelo_single = cam_data.get("modelo", "Personas")
            modelos = [modelo_single] if modelo_single else []

        self.log_signal.emit(f"   🤖 Modelos a cargar: {modelos}")

        self.detectors = []
        for i, modelo in enumerate(modelos):
            detector = DetectorWorker(
                model_key=modelo,
                confidence=cam_data.get("confianza", 0.5),
                frame_interval=1,
                imgsz=imgsz_default,
                device=device,
                track=False,
            )
            detector.result_ready.connect(
                lambda res, _mk, fid, mk=modelo: self._procesar_resultados_detector_worker(res, mk, fid)
            )
            detector.start()
            self.detectors.append(detector)
            self.log_signal.emit(f"      ✅ Detector {i+1}/{len(modelos)}: {modelo}")

        # Timers
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(2000)
        
        self.debug_timer = QTimer()
        self.debug_timer.timeout.connect(self._emit_debug_stats)
        self.debug_timer.start(5000)

        self.log_signal.emit(f"✅ [{self.objectName()}] VisualizadorDetector completamente inicializado")

    def _check_nvidia_support(self):
        """Verificar soporte NVIDIA GPU"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory // (1024**3)
                self.log_signal.emit(f"🚀 NVIDIA GPU: {gpu_name} ({gpu_memory}GB)")
                return True
            else:
                self.log_signal.emit(f"💻 CUDA no disponible, usando CPU")
                return False
        except ImportError:
            self.log_signal.emit(f"⚠️ PyTorch no disponible para detección GPU")
            return False

    def _get_optimal_device(self):
        """Configurar device óptimo"""
        device = self.cam_data.get("device", "auto")
        
        if device == "auto":
            if self.nvidia_enabled:
                device = "cuda:0"
            else:
                device = "cpu"
        
        return device

    def _handle_media_error(self, error):
        """Manejar errores de QMediaPlayer"""
        error_msg = self.video_player.errorString()
        self.log_signal.emit(f"❌ [{self.objectName()}] QMediaPlayer Error: {error_msg}")
        self.stats['errors'] += 1
        self.stats['last_error'] = f"MediaPlayer: {error_msg}"

    def start_stream(self, rtsp_url):
        """Iniciar stream según backend configurado"""
        self.log_signal.emit(f"🎬 [{self.objectName()}] Iniciando stream...")
        self.log_signal.emit(f"   🌐 URL: {rtsp_url[:60]}{'...' if len(rtsp_url) > 60 else ''}")

        backend = (self.decoder_backend or 'auto').lower()

        if backend in ('gstreamer', 'auto') and GST_BRIDGE_AVAILABLE:
            self.log_signal.emit(f"🚀 [{self.objectName()}] Usando GStreamer Bridge")
            if self._start_gstreamer_bridge(rtsp_url):
                return
            self.log_signal.emit(f"⚠️ [{self.objectName()}] GStreamer falló, probando FFmpeg...")
            backend = 'ffmpeg'

        if backend in ('ffmpeg', 'auto') and FFMPEG_BRIDGE_AVAILABLE:
            self.log_signal.emit(f"🚀 [{self.objectName()}] Usando FFmpeg Bridge (alta performance)")
            if self._start_ffmpeg_bridge(rtsp_url):
                return
            self.log_signal.emit(f"⚠️ [{self.objectName()}] FFmpeg falló, probando QMediaPlayer...")

        # Fallback QMediaPlayer
        self.log_signal.emit(f"📺 [{self.objectName()}] Usando QMediaPlayer (compatibilidad)")
        self._start_qmediaplayer(rtsp_url)

    def _start_ffmpeg_bridge(self, rtsp_url):
        """FFmpeg Bridge optimizado"""
        try:
            ip = self.cam_data.get('ip', 'unknown')
            
            # Configuración optimizada por cámara
            if '19.10.10.220' in ip:
                width, height = 640, 360  # Cámara principal
                self.log_signal.emit(f"📐 [{ip}] Configuración: Cámara principal")
            elif '19.10.10.217' in ip:
                width, height = 640, 360  # Cámara secundaria
                self.log_signal.emit(f"📐 [{ip}] Configuración: Cámara secundaria")
            else:
                width, height = 640, 360  # Default
                self.log_signal.emit(f"📐 [{ip}] Configuración: Default")
            
            self.ffmpeg_reader = FFmpegRTSPReader(
                rtsp_url, 
                width=width,
                height=height,
                nvidia_decode=self.nvidia_enabled
            )
            
            if self.ffmpeg_reader.start():
                self.using_ffmpeg = True
                strategy_used = getattr(self.ffmpeg_reader, 'stats', {}).get('command_used', 'Desconocida')
                self.ffmpeg_strategy = strategy_used
                
                self.log_signal.emit(f"✅ [{self.objectName()}] FFmpeg Bridge ACTIVO")
                self.log_signal.emit(f"   📋 Estrategia: {strategy_used}")
                self.log_signal.emit(f"   📐 Resolución: {width}x{height}")
                self.log_signal.emit(f"   🚀 NVIDIA: {self.nvidia_enabled}")
                
                # Thread de procesamiento
                import threading
                self.ffmpeg_thread = threading.Thread(
                    target=self._process_ffmpeg_frames, 
                    daemon=True
                )
                self.ffmpeg_thread.start()
                
                return True
            else:
                self.log_signal.emit(f"❌ [{self.objectName()}] FFmpeg Bridge falló al iniciar")
                return False
                
        except Exception as e:
            self.log_signal.emit(f"❌ [{self.objectName()}] Error FFmpeg Bridge: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = f"FFmpeg: {e}"
            return False

    def _start_gstreamer_bridge(self, rtsp_url):
        """Inicia lector GStreamer"""
        try:
            self.gst_reader = GStreamerRTSPReader(rtsp_url)
            if self.gst_reader.start():
                self.using_gstreamer = True
                import threading
                self.gst_thread = threading.Thread(
                    target=self._process_gstreamer_frames,
                    daemon=True
                )
                self.gst_thread.start()
                self.log_signal.emit(f"✅ [{self.objectName()}] GStreamer Bridge ACTIVO")
                return True
            else:
                return False
        except Exception as e:
            self.log_signal.emit(f"❌ [{self.objectName()}] Error GStreamer Bridge: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = f"GStreamer: {e}"
            return False

    def _start_qmediaplayer(self, rtsp_url):
        """QMediaPlayer como fallback"""
        try:
            self.video_player.setSource(QUrl(rtsp_url))
            self.video_player.play()
            self.using_ffmpeg = False
            self.log_signal.emit(f"✅ [{self.objectName()}] QMediaPlayer iniciado")
        except Exception as e:
            self.log_signal.emit(f"❌ [{self.objectName()}] Error QMediaPlayer: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = f"QMediaPlayer: {e}"
    
    def _process_ffmpeg_frames(self):
        """Procesar frames desde FFmpeg"""
        frame_count = 0
        last_log_time = time.time()
        
        self.log_signal.emit(f"🎬 [{self.objectName()}] Thread FFmpeg iniciado")
        
        while (hasattr(self, 'ffmpeg_reader') and 
               self.ffmpeg_reader and 
               self.ffmpeg_reader.isOpened()):
            
            try:
                ret, frame = self.ffmpeg_reader.read()
                
                if ret and frame is not None:
                    frame_count += 1
                    self.stats['ffmpeg_frames'] += 1
                    self.stats['total_frames'] += 1
                    
                    # Procesar frame
                    processing_time = self._process_frame_universal(
                        frame, frame_count, source="ffmpeg"
                    )
                    
                    # Estadísticas de tiempo
                    if processing_time:
                        self.stats['processing_times'].append(processing_time)
                        if len(self.stats['processing_times']) > 100:
                            self.stats['processing_times'].pop(0)
                        
                        avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
                        self.stats['avg_processing_time'] = avg_time
                    
                    # Debug visual
                    if self.debug_visual and frame_count % 3 == 0:
                        self._emit_debug_frame(frame)
                    
                    # Log cada 100 frames
                    if frame_count % 100 == 0 or time.time() - last_log_time > 10:
                        elapsed = time.time() - self.stats['start_time']
                        fps = self.stats['ffmpeg_frames'] / elapsed if elapsed > 0 else 0
                        
                        self.log_signal.emit(
                            f"📷 [{self.objectName()}] FFmpeg: {frame_count} frames "
                            f"({fps:.1f} FPS) | Proc: {self.stats['avg_processing_time']*1000:.1f}ms"
                        )
                        last_log_time = time.time()
                
                else:
                    time.sleep(0.01)
                    
            except Exception as e:
                self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame FFmpeg: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = f"FFmpeg processing: {e}"
                break
        
        self.log_signal.emit(f"🛑 [{self.objectName()}] Thread FFmpeg terminado")

    def _process_gstreamer_frames(self):
        """Procesar frames desde GStreamer"""
        frame_count = 0
        last_log_time = time.time()

        self.log_signal.emit(f"🎬 [{self.objectName()}] Thread GStreamer iniciado")

        while (hasattr(self, 'gst_reader') and
               self.gst_reader and
               self.gst_reader.isOpened()):

            try:
                ret, frame = self.gst_reader.read()

                if ret and frame is not None:
                    frame_count += 1
                    self.stats['gst_frames'] += 1
                    self.stats['total_frames'] += 1

                    processing_time = self._process_frame_universal(
                        frame, frame_count, source="gstreamer"
                    )

                    if processing_time:
                        self.stats['processing_times'].append(processing_time)
                        if len(self.stats['processing_times']) > 100:
                            self.stats['processing_times'].pop(0)

                        avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
                        self.stats['avg_processing_time'] = avg_time

                    if self.debug_visual and frame_count % 3 == 0:
                        self._emit_debug_frame(frame)

                    if frame_count % 100 == 0 or time.time() - last_log_time > 10:
                        elapsed = time.time() - self.stats['start_time']
                        fps = self.stats['gst_frames'] / elapsed if elapsed > 0 else 0

                        self.log_signal.emit(
                            f"📷 [{self.objectName()}] GStreamer: {frame_count} frames "
                            f"({fps:.1f} FPS) | Proc: {self.stats['avg_processing_time']*1000:.1f}ms"
                        )
                        last_log_time = time.time()

                else:
                    time.sleep(0.01)

            except Exception as e:
                self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame GStreamer: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = f"GStreamer processing: {e}"
                break

        self.log_signal.emit(f"🛑 [{self.objectName()}] Thread GStreamer terminado")

    def _emit_debug_frame(self, frame):
        """Emitir frame para debug visual"""
        try:
            if frame is None or frame.size == 0:
                return
                
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            
            # Convertir BGR a RGB para Qt
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            q_image = QImage(
                rgb_frame.data, 
                width, 
                height, 
                bytes_per_line, 
                QImage.Format.Format_RGB888
            )
            
            pixmap = QPixmap.fromImage(q_image)
            
            # Agregar overlay de FPS
            if self.show_fps_overlay:
                pixmap = self._add_fps_overlay(pixmap)
            
            self.frame_ready.emit(pixmap)
                
        except Exception as e:
            logger.error(f"Error emitiendo debug frame: {e}")
            self.stats['errors'] += 1

    def _add_fps_overlay(self, pixmap):
        """Agregar overlay de FPS"""
        try:
            from PyQt6.QtGui import QPainter, QFont, QColor
            
            painter = QPainter(pixmap)
            painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
            
            # Background semi-transparente
            painter.fillRect(5, 5, 200, 80, QColor(0, 0, 0, 128))
            
            # Texto blanco
            painter.setPen(QColor(255, 255, 255))
            
            fps_text = f"FPS: {self.stats['current_fps']:.1f}"
            if self.using_gstreamer:
                source_lbl = 'GStreamer'
            elif self.using_ffmpeg:
                source_lbl = 'FFmpeg'
            else:
                source_lbl = 'Qt'
            source_text = f"Fuente: {source_lbl}"
            frames_text = f"Frames: {self.stats['total_frames']}"
            proc_text = f"Proc: {self.stats['avg_processing_time']*1000:.1f}ms"
            
            painter.drawText(10, 20, fps_text)
            painter.drawText(10, 35, source_text)
            painter.drawText(10, 50, frames_text)
            painter.drawText(10, 65, proc_text)
            
            painter.end()
            
        except Exception as e:
            logger.error(f"Error adding FPS overlay: {e}")
        
        return pixmap

    def _process_frame_universal(self, frame, frame_count, source="unknown"):
        """Procesar frame universal"""
        processing_start = time.time()
        
        try:
            self.stats['processed_frames'] += 1
            
            if frame_count % self.detector_frame_interval == 0:
                self.stats['detection_frames'] += 1
                
                self._last_frame = frame
                self._pending_detections = {}
                self._current_frame_id += 1

                if self.log_frame_processing and self.stats['detection_frames'] % 50 == 0:
                    self.log_signal.emit(
                        f"🤖 [{self.objectName()}] {source}: Frame {self._current_frame_id} "
                        f"enviado a {len(self.detectors)} detectores"
                    )

                if hasattr(self, 'detectors'):
                    detectores_activos = sum(1 for det in self.detectors if det and det.isRunning())
                    
                    for det in self.detectors:
                        if det and det.isRunning():
                            det.set_frame(frame, self._current_frame_id)
                    
                    if self.stats['detection_frames'] % 100 == 0:
                        self.log_signal.emit(
                            f"🤖 [{self.objectName()}] Detectores: {detectores_activos}/{len(self.detectors)} activos"
                        )

            processing_time = time.time() - processing_start
            return processing_time

        except Exception as e:
            self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame {source}: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = f"Frame processing: {e}"
            return None

    def on_frame(self, frame: QVideoFrame):
        """Callback para QMediaPlayer"""
        if not frame.isValid():
            return
        
        self.stats['qt_frames'] += 1
        self.stats['total_frames'] += 1
        
        try:
            qimg = self._qimage_from_frame(frame)
            if qimg is None:
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
            
            if arr.shape[2] == 3:
                arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

            self.frame_counter += 1
            
            self._process_frame_universal(arr, self.frame_counter, source="qt")
            
            if self.debug_visual and self.frame_counter % 5 == 0:
                self._emit_debug_frame(arr)
                
        except Exception as e:
            self.log_signal.emit(f"❌ [{self.objectName()}] Error en on_frame: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = f"QMediaPlayer frame: {e}"

    def _qimage_from_frame(self, frame: QVideoFrame):
        """Convertir QVideoFrame a QImage"""
        try:
            if frame.surfaceFormat().pixelFormat() == QVideoFrameFormat.PixelFormat.Format_YUV420P:
                return self._qimage_from_yuv420p(frame)
            else:
                img = frame.toImage()
                return img
        except Exception as e:
            logger.error(f"Error converting frame to QImage: {e}")
            self.stats['errors'] += 1
            return None

    def _qimage_from_yuv420p(self, frame: QVideoFrame):
        """Convertir YUV420P a QImage"""
        try:
            frame.map(QVideoFrame.MapMode.ReadOnly)
            
            width = frame.width()
            height = frame.height()
            
            y_data = frame.bits(0)
            u_data = frame.bits(1)
            v_data = frame.bits(2)
            
            y_stride = frame.bytesPerLine(0)
            u_stride = frame.bytesPerLine(1)
            v_stride = frame.bytesPerLine(2)
            
            y_buffer = np.frombuffer(y_data, dtype=np.uint8)[:height * y_stride].reshape(height, y_stride)[:, :width]
            u_buffer = np.frombuffer(u_data, dtype=np.uint8)[:height // 2 * u_stride].reshape(height // 2, u_stride)[:, :width // 2]
            v_buffer = np.frombuffer(v_data, dtype=np.uint8)[:height // 2 * v_stride].reshape(height // 2, v_stride)[:, :width // 2]
            
            u_resized = cv2.resize(u_buffer, (width, height), interpolation=cv2.INTER_LINEAR)
            v_resized = cv2.resize(v_buffer, (width, height), interpolation=cv2.INTER_LINEAR)
            
            yuv = np.zeros((height, width, 3), dtype=np.uint8)
            yuv[:, :, 0] = y_buffer
            yuv[:, :, 1] = u_resized
            yuv[:, :, 2] = v_resized
            
            rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)
            
            bytes_per_line = rgb.shape[1] * 3
            qimg = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            frame.unmap()
            return qimg.copy()
            
        except Exception as e:
            logger.error(f"Error converting YUV420P: {e}")
            frame.unmap()
            self.stats['errors'] += 1
            return None

    def _update_statistics(self):
        """Actualizar estadísticas FPS"""
        try:
            current_time = time.time()
            elapsed = current_time - self.stats['last_fps_calculation']
            
            if elapsed >= 2.0:
                frames_in_window = self.stats['total_frames'] - self.stats['fps_window_frames']
                current_fps = frames_in_window / elapsed if elapsed > 0 else 0
                
                self.stats['current_fps'] = current_fps
                self.stats['last_fps_calculation'] = current_time
                self.stats['fps_window_frames'] = self.stats['total_frames']
        
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")

    def _emit_debug_stats(self):
        """Emitir estadísticas debug"""
        try:
            elapsed = time.time() - self.stats['start_time']
            
            debug_stats = {
                'camera_ip': self.cam_data.get('ip', 'unknown'),
                'total_frames': self.stats['total_frames'],
                'processed_frames': self.stats['processed_frames'],
                'detection_frames': self.stats['detection_frames'],
                'current_fps': self.stats['current_fps'],
                'avg_fps': self.stats['total_frames'] / elapsed if elapsed > 0 else 0,
                'ffmpeg_frames': self.stats['ffmpeg_frames'],
                'gst_frames': self.stats['gst_frames'],
                'qt_frames': self.stats['qt_frames'],
                'using_ffmpeg': self.using_ffmpeg,
                'using_gstreamer': self.using_gstreamer,
                'ffmpeg_strategy': self.ffmpeg_strategy,
                'nvidia_enabled': self.nvidia_enabled,
                'avg_processing_time_ms': self.stats['avg_processing_time'] * 1000,
                'errors': self.stats['errors'],
                'last_error': self.stats['last_error'],
                'uptime_seconds': elapsed
            }
            
            self.stats_ready.emit(debug_stats)
            
            if self.log_frame_processing:
                self.log_signal.emit(
                    f"📊 [{self.objectName()}] "
                    f"Frames: {self.stats['total_frames']} | "
                    f"FPS: {self.stats['current_fps']:.1f} | "
                    f"Source: "
                    f"{'GStreamer' if self.using_gstreamer else ('FFmpeg' if self.using_ffmpeg else 'Qt')} | "
                    f"Errors: {self.stats['errors']}"
                )
        
        except Exception as e:
            logger.error(f"Error emitting debug stats: {e}")

    def update_fps_config(self, visual_fps=25, detection_fps=8):
        """Actualizar FPS"""
        self.visual_fps = visual_fps
        self.detection_fps = detection_fps
        
        base_fps = 30
        self.detector_frame_interval = max(1, int(base_fps / detection_fps))
        
        self.log_signal.emit(
            f"🎯 [{self.objectName()}] FPS actualizado - "
            f"Visual: {visual_fps}, Detección: {detection_fps}, Intervalo: {self.detector_frame_interval}"
        )

    def _procesar_resultados_detector_worker(self, output_for_signal, model_key, frame_id):
        """Procesar resultados detectores"""
        if self.log_frame_processing and frame_id % 100 == 0:
            logger.debug(
                "%s: Resultados recibidos para modelo %s, frame %s",
                self.objectName(), model_key, frame_id
            )
        
        if frame_id != self._current_frame_id:
            if self.log_frame_processing:
                logger.debug(
                    "%s: Ignorando resultados de frame antiguo %s (actual %s)",
                    self.objectName(), frame_id, self._current_frame_id
                )
            return

        self._pending_detections[model_key] = output_for_signal
        
        if len(self._pending_detections) == len(self.detectors):
            merged = []
            total_detections = 0
            
            for model_name, dets in self._pending_detections.items():
                total_detections += len(dets)
                for det in dets:
                    duplicate = False
                    for mdet in merged:
                        if iou(det['bbox'], mdet['bbox']) > 0.5:
                            if det.get('conf', 0) > mdet.get('conf', 0):
                                merged.remove(mdet)
                                merged.append(det)
                            duplicate = True
                            break
                    if not duplicate:
                        merged.append(det)

            if self.log_frame_processing and self._current_frame_id % 50 == 0:
                self.log_signal.emit(
                    f"🔍 [{self.objectName()}] Frame {self._current_frame_id}: "
                    f"{total_detections} detecciones brutas → {len(merged)} fusionadas"
                )

            if hasattr(self, 'tracker'):
                tracked_results = self.tracker.update(merged, frame=self._last_frame)
                
                if self.log_frame_processing and len(tracked_results) > 0 and self._current_frame_id % 100 == 0:
                    active_tracks = len([t for t in tracked_results if t.get('track_id', -1) >= 0])
                    self.log_signal.emit(
                        f"🎯 [{self.objectName()}] Tracking: {active_tracks} objetos activos"
                    )
                
                self.result_ready.emit(tracked_results)
            else:
                self.result_ready.emit(merged)

            self._pending_detections = {}

    def stop(self):
        """🔥 CORREGIDO: Detener con fix del error wait()"""
        self.log_signal.emit(f"🛑 [{self.objectName()}] Deteniendo VisualizadorDetector...")
        
        # Detener timers
        if hasattr(self, 'stats_timer') and self.stats_timer:
            self.stats_timer.stop()
        if hasattr(self, 'debug_timer') and self.debug_timer:
            self.debug_timer.stop()
        
        # Detener FFmpeg Bridge
        if self.ffmpeg_reader:
            try:
                self.log_signal.emit(f"🛑 [{self.objectName()}] Liberando FFmpeg Bridge...")
                self.ffmpeg_reader.release()
            except Exception as e:
                self.log_signal.emit(f"⚠️ [{self.objectName()}] Error liberando FFmpeg: {e}")
            self.ffmpeg_reader = None
        if self.ffmpeg_thread:
            self.ffmpeg_thread.join(timeout=2)
            self.ffmpeg_thread = None

        # Detener GStreamer Bridge
        if self.gst_reader:
            try:
                self.log_signal.emit(f"🛑 [{self.objectName()}] Liberando GStreamer Bridge...")
                self.gst_reader.release()
            except Exception as e:
                self.log_signal.emit(f"⚠️ [{self.objectName()}] Error liberando GStreamer: {e}")
            self.gst_reader = None
        if self.gst_thread:
            self.gst_thread.join(timeout=2)
            self.gst_thread = None
        
        # Detener QMediaPlayer
        if self.video_player:
            try:
                self.video_player.stop()
                self.video_player.setVideoSink(None)
            except Exception as e:
                self.log_signal.emit(f"⚠️ [{self.objectName()}] Error deteniendo QMediaPlayer: {e}")
        
        # 🔥 CORREGIDO: Detener detectores sin error wait()
        self.log_signal.emit(f"🛑 [{self.objectName()}] Deteniendo {len(self.detectors)} detectores...")
        for i, detector in enumerate(self.detectors):
            if detector and detector.isRunning():
                try:
                    detector.quit()
                    detector.wait(3000)  # 🔥 CORRECCIÓN: Solo tiempo en ms, sin timeout=
                    self.log_signal.emit(f"   ✅ Detector {i+1} detenido")
                except Exception as e:
                    self.log_signal.emit(f"   ⚠️ Error deteniendo detector {i+1}: {e}")
        
        # Estadísticas finales
        final_stats = self.get_debug_info()
        self.log_signal.emit(f"📊 [{self.objectName()}] ESTADÍSTICAS FINALES:")
        self.log_signal.emit(f"   ⏱️ Tiempo total: {final_stats['performance']['uptime_seconds']:.1f}s")
        self.log_signal.emit(f"   📷 Frames procesados: {final_stats['performance']['total_frames']}")
        self.log_signal.emit(f"   📈 FPS promedio: {final_stats['performance']['average_fps']:.1f}")
        if self.using_gstreamer:
            source_name = 'GStreamer'
        elif self.using_ffmpeg:
            source_name = 'FFmpeg'
        else:
            source_name = 'QMediaPlayer'
        self.log_signal.emit(f"   🚀 Fuente: {source_name}")
        self.log_signal.emit(f"   ❌ Errores: {final_stats['errors']['total_errors']}")
        
        self.log_signal.emit(f"✅ [{self.objectName()}] VisualizadorDetector detenido completamente")

    def get_debug_info(self):
        """Obtener información completa de debug"""
        elapsed = time.time() - self.stats['start_time']
        
        return {
            'camera_info': {
                'ip': self.cam_data.get('ip', 'unknown'),
                'object_name': self.objectName(),
                'debug_visual': self.debug_visual,
                'show_fps_overlay': self.show_fps_overlay
            },
            'performance': {
                'uptime_seconds': elapsed,
                'total_frames': self.stats['total_frames'],
                'processed_frames': self.stats['processed_frames'],
                'detection_frames': self.stats['detection_frames'],
                'current_fps': self.stats['current_fps'],
                'average_fps': self.stats['total_frames'] / elapsed if elapsed > 0 else 0,
                'avg_processing_time_ms': self.stats['avg_processing_time'] * 1000,
                'dropped_frames': self.stats['dropped_frames']
            },
            'source_info': {
                'using_ffmpeg': self.using_ffmpeg,
                'using_gstreamer': self.using_gstreamer,
                'ffmpeg_strategy': self.ffmpeg_strategy,
                'ffmpeg_frames': self.stats['ffmpeg_frames'],
                'gst_frames': self.stats['gst_frames'],
                'qt_frames': self.stats['qt_frames'],
                'nvidia_enabled': self.nvidia_enabled
            },
            'detection_config': {
                'visual_fps': self.visual_fps,
                'detection_fps': self.detection_fps,
                'detector_frame_interval': self.detector_frame_interval,
                'num_detectors': len(self.detectors),
                'active_detectors': sum(1 for det in self.detectors if det and det.isRunning())
            },
            'errors': {
                'total_errors': self.stats['errors'],
                'last_error': self.stats['last_error']
            }
        }

    def toggle_debug_visual(self, enabled):
        """Activar/desactivar debug visual"""
        self.debug_visual = enabled
        self.log_signal.emit(f"👁️ [{self.objectName()}] Debug visual: {'activado' if enabled else 'desactivado'}")

    def toggle_fps_overlay(self, enabled):
        """Activar/desactivar overlay de FPS"""
        self.show_fps_overlay = enabled
        self.log_signal.emit(f"📊 [{self.objectName()}] FPS overlay: {'activado' if enabled else 'desactivado'}")

    def toggle_frame_logging(self, enabled):
        """Activar/desactivar logging detallado"""
        self.log_frame_processing = enabled
        self.log_signal.emit(f"📝 [{self.objectName()}] Frame logging: {'activado' if enabled else 'desactivado'}")

    def __del__(self):
        """Destructor para limpieza"""
        try:
            self.stop()
        except:
            pass