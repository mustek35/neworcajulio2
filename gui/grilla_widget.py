# ========================================================================================
# gui/grilla_widget.py - CÓDIGO COMPLETO CON OVERLAY CORREGIDO
# ========================================================================================

from PyQt6.QtWidgets import QWidget, QSizePolicy, QMenu, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QGroupBox, QFormLayout
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QFont, QImage
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QSizeF, QSize, QPointF, QTimer
from PyQt6.QtMultimedia import QVideoFrame, QVideoFrameFormat

# Importaciones del sistema existente
from gui.visualizador_detector import VisualizadorDetector
from core.gestor_alertas import GestorAlertas
from core.rtsp_builder import generar_rtsp
from core.analytics_processor import AnalyticsProcessor
from gui.video_saver import VideoSaverThread
from core.cross_line_counter import CrossLineCounter
from core.ptz_control import PTZCameraONVIF
from collections import defaultdict, deque
import numpy as np
from datetime import datetime
import uuid
import json
import os
import time

# Importar módulos refactorizados OPCIONALMENTE
try:
    from gui.components.cell_manager import CellManager
    CELL_MANAGER_AVAILABLE = True
except ImportError:
    CELL_MANAGER_AVAILABLE = False

try:
    from gui.components.ptz_manager import PTZManager
    PTZ_MANAGER_AVAILABLE = True
except ImportError:
    PTZ_MANAGER_AVAILABLE = False

try:
    from gui.components.detection_handler import DetectionHandler
    DETECTION_HANDLER_AVAILABLE = True
except ImportError:
    DETECTION_HANDLER_AVAILABLE = False

try:
    from gui.components.grid_renderer import GridRenderer
    GRID_RENDERER_AVAILABLE = True
except ImportError:
    GRID_RENDERER_AVAILABLE = False

try:
    from gui.components.context_menu import ContextMenuManager
    CONTEXT_MENU_AVAILABLE = True
except ImportError:
    CONTEXT_MENU_AVAILABLE = False

try:
    from gui.components.config_manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Sistema modular
MODULAR_SYSTEM_AVAILABLE = CELL_MANAGER_AVAILABLE
if MODULAR_SYSTEM_AVAILABLE:
    print("✅ Sistema modular disponible")
else:
    print("⚠️ Sistema modular no disponible, usando legacy")

# Constantes
DEBUG_LOGS = False
CONFIG_FILE_PATH = "config.json"


class GrillaWidget(QWidget):
    """Widget de grilla con overlay de detecciones corregido"""
    
    log_signal = pyqtSignal(str)

    def __init__(self, filas=18, columnas=22, area=None, parent=None, fps_config=None):
        super().__init__(parent)
        
        # === CONFIGURACIÓN BÁSICA ===
        self.filas = filas
        self.columnas = columnas
        self.area = area if area else [0] * (filas * columnas)
        self.temporal = set()
        self.pixmap = None
        self.last_frame = None 
        self.original_frame_size = None 
        self.latest_tracked_boxes = []
        
        # Estados de celdas (API original)
        self.selected_cells = set()
        self.discarded_cells = set()
        self.cell_presets = {}
        self.cell_ptz_map = {}
        self.ptz_objects = {}
        self.credentials_cache = {}
        self.ptz_cameras = []

        # 🔥 VARIABLES CRÍTICAS PARA STREAM
        self.cam_data = None
        self.visualizador = None
        self.video_label = None
        
        # Contadores de debug
        self._frame_debug_count = 0
        self._detection_debug_count = 0
        self._last_stats_log = 0

        # Datos de cámara y alertas
        self.alertas = None
        self.objetos_previos = {}
        self.umbral_movimiento = 20
        self.detectors = None 
        self.analytics_processor = AnalyticsProcessor(self)

        # Configuración de FPS
        if fps_config is None:
            fps_config = {"visual_fps": 15, "detection_fps": 5, "ai_fps": 2}
        self.fps_config = fps_config

        # Sistema de línea de conteo
        self.cross_counter = CrossLineCounter()
        self.cross_line_enabled = False
        self.cross_line_edit_mode = False
        self._dragging_line = None
        self._temp_line_start = None
        self._last_mouse_pos = None
        
        # === INICIALIZACIÓN DE UI ===
        self.setupUi()
        
        # === INICIALIZACIÓN DEL SISTEMA ===
        self.modular_system_enabled = MODULAR_SYSTEM_AVAILABLE
        if self.modular_system_enabled:
            try:
                self._initialize_modular_system()
            except Exception as e:
                print(f"❌ Error inicializando sistema modular: {e}")
                self.modular_system_enabled = False
                self._initialize_legacy_system()
        else:
            self._initialize_legacy_system()
        
        self.registrar_log("✅ GrillaWidget inicializado (modo: {})".format(
            "modular" if self.modular_system_enabled else "legacy"
        ))

    def setupUi(self):
        """Configurar interfaz de usuario"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Widget principal de video
        self.video_label = QLabel("📺 Esperando señal...")
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #333;
                background-color: #1a1a1a;
                color: white;
                font-size: 14px;
                text-align: center;
            }
        """)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setScaledContents(True)
        
        layout.addWidget(self.video_label)
        
        # Widget de información
        self.info_label = QLabel("Sin información")
        self.info_label.setMaximumHeight(30)
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.info_label)

    def _initialize_modular_system(self):
        """Inicializa el sistema modular"""
        # ConfigManager
        if CONFIG_MANAGER_AVAILABLE:
            self.config_manager = ConfigManager(parent=self)
        
        # CellManager
        if CELL_MANAGER_AVAILABLE:
            self.cell_manager = CellManager(
                self.filas, self.columnas, parent=self
            )
            
        # PTZManager  
        if PTZ_MANAGER_AVAILABLE:
            self.ptz_manager = PTZManager(parent=self)
            
        # DetectionHandler
        if DETECTION_HANDLER_AVAILABLE:
            self.detection_handler = DetectionHandler(parent=self)
            
        # GridRenderer
        if GRID_RENDERER_AVAILABLE:
            self.grid_renderer = GridRenderer(parent=self)
            
        # ContextMenuManager
        if CONTEXT_MENU_AVAILABLE:
            self.context_menu_manager = ContextMenuManager(parent=self)

    def _initialize_legacy_system(self):
        """Inicializa el sistema legacy"""
        self.ptz_enabled = False
        self.detection_count = 0
        self.frame_count = 0

    # ========================================================================================
    # 🔥 MÉTODOS CRÍTICOS PARA STREAM
    # ========================================================================================

    def set_cam_data(self, cam_data):
        """Configurar datos de cámara y crear visualizador"""
        try:
            self.cam_data = cam_data
            ip = cam_data.get('ip', 'unknown') if cam_data else 'unknown'
            
            self.registrar_log(f"🔧 [{ip}] Configurando cam_data")
            self.info_label.setText(f"Cámara: {ip}")
            
            # Crear visualizador inmediatamente
            self.crear_visualizador()
            
            # Iniciar stream automáticamente si tenemos datos
            if self.cam_data and self.cam_data.get('rtsp'):
                self.iniciar_stream()
            
        except Exception as e:
            self.registrar_log(f"❌ Error configurando cam_data: {e}")

    def crear_visualizador(self):
        """Crear VisualizadorDetector"""
        try:
            if not hasattr(self, 'cam_data') or not self.cam_data:
                self.registrar_log("❌ No se puede crear visualizador sin cam_data")
                return
            
            ip = self.cam_data.get('ip', 'unknown')
            self.registrar_log(f"🔧 [{ip}] Creando VisualizadorDetector...")
            
            # Crear visualizador
            self.visualizador = VisualizadorDetector(self.cam_data, parent=self)
            
            # Conectar señales INMEDIATAMENTE
            self.conectar_senales_visualizador()
            
            self.registrar_log(f"✅ [{ip}] VisualizadorDetector creado exitosamente")
            
        except Exception as e:
            self.registrar_log(f"❌ Error creando VisualizadorDetector: {e}")
            import traceback
            traceback.print_exc()

    def conectar_senales_visualizador(self):
        """Conectar señales del visualizador"""
        if not self.visualizador:
            return
        
        try:
            ip = self.cam_data.get('ip', 'unknown')
            self.registrar_log(f"🔌 [{ip}] Conectando señales del visualizador...")
            
            # Conexiones críticas
            self.visualizador.result_ready.connect(self.procesar_detecciones)
            self.registrar_log(f"   ✅ result_ready conectado")
            
            self.visualizador.log_signal.connect(self.registrar_log)
            self.registrar_log(f"   ✅ log_signal conectado")
            
            if hasattr(self.visualizador, 'frame_ready'):
                self.visualizador.frame_ready.connect(self.mostrar_frame)
                self.registrar_log(f"   ✅ frame_ready conectado")
            
            if hasattr(self.visualizador, 'stats_ready'):
                self.visualizador.stats_ready.connect(self.mostrar_stats_debug)
                self.registrar_log(f"   ✅ stats_ready conectado")
            
            self.registrar_log(f"🔌 [{ip}] Todas las señales conectadas exitosamente")
            
        except Exception as e:
            self.registrar_log(f"❌ Error conectando señales: {e}")

    def iniciar_stream(self):
        """🔥 MÉTODO CRÍTICO: Iniciar stream"""
        try:
            if not hasattr(self, 'cam_data') or not self.cam_data:
                self.registrar_log("❌ ERROR: cam_data no configurado")
                return

            ip = self.cam_data.get('ip', 'unknown')
            rtsp_url = self.cam_data.get('rtsp')

            self.registrar_log(f"🚀 [{ip}] === INICIANDO STREAM ===")
            self.registrar_log(f"📝 [{ip}] URL: {rtsp_url}")

            if not rtsp_url:
                self.registrar_log(f"❌ [{ip}] URL RTSP no configurada")
                self.mostrar_error("URL RTSP no configurada")
                return

            # Crear visualizador si no existe
            if not hasattr(self, 'visualizador') or not self.visualizador:
                self.registrar_log(f"🔧 [{ip}] Creando VisualizadorDetector...")
                self.crear_visualizador()
                
                if not self.visualizador:
                    self.registrar_log(f"❌ [{ip}] ERROR: No se pudo crear VisualizadorDetector")
                    self.mostrar_error("Error creando visualizador")
                    return

            # 🔥 INICIAR STREAM EN EL VISUALIZADOR
            try:
                self.registrar_log(f"🎬 [{ip}] Llamando a visualizador.start_stream()")
                self.visualizador.start_stream(rtsp_url)
                self.registrar_log(f"✅ [{ip}] start_stream() ejecutado correctamente")
                
                # Actualizar UI
                self.info_label.setText(f"Conectando a {ip}...")
                
            except Exception as e:
                self.registrar_log(f"❌ [{ip}] ERROR en start_stream(): {e}")
                self.mostrar_error(f"Error iniciando stream: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            self.registrar_log(f"❌ ERROR GENERAL en iniciar_stream(): {e}")
            import traceback
            traceback.print_exc()

    def mostrar_frame(self, pixmap):
        """Mostrar frame en el widget de video"""
        try:
            if not pixmap or pixmap.isNull():
                return
                
            ip = self.cam_data.get('ip', 'unknown') if self.cam_data else 'unknown'
            
            # Mostrar frame escalado
            if hasattr(self, 'video_label') and self.video_label:
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.video_label.setPixmap(scaled_pixmap)
                
                # Actualizar información
                self.info_label.setText(f"🟢 {ip} - Activo")
                
                # Log ocasional
                self._frame_debug_count += 1
                if self._frame_debug_count % 100 == 0:
                    self.registrar_log(f"📺 [{ip}] Frame #{self._frame_debug_count} mostrado")
        
        except Exception as e:
            self.registrar_log(f"❌ Error mostrando frame: {e}")

    def procesar_detecciones(self, detecciones):
        """Procesar detecciones recibidas"""
        try:
            ip = self.cam_data.get('ip', 'unknown') if self.cam_data else 'unknown'
            
            if not detecciones:
                return
            
            # Actualizar contador
            self._detection_debug_count += 1
            
            # Log ocasional
            if self._detection_debug_count % 50 == 0:
                self.registrar_log(
                    f"🎯 [{ip}] Detección #{self._detection_debug_count}: "
                    f"{len(detecciones)} objetos detectados"
                )
            
            # Procesar detecciones
            if hasattr(self, 'actualizar_boxes'):
                self.actualizar_boxes(detecciones)
            else:
                self.latest_tracked_boxes = detecciones
                self.update()  # Forzar repaint para mostrar overlay
        
        except Exception as e:
            self.registrar_log(f"❌ Error procesando detecciones: {e}")

    def mostrar_stats_debug(self, stats):
        """Mostrar estadísticas de debug"""
        try:
            ip = stats.get('camera_ip', 'unknown')
            
            import time
            current_time = time.time()
            
            if current_time - self._last_stats_log > 10:  # Cada 10 segundos
                fps = stats.get('current_fps', 0)
                total_frames = stats.get('total_frames', 0)
                source = "FFmpeg" if stats.get('using_ffmpeg', False) else "Qt"
                errors = stats.get('errors', 0)
                
                self.registrar_log(
                    f"📊 [{ip}] Stats: {total_frames} frames | {fps:.1f} FPS | "
                    f"Source: {source} | Errors: {errors}"
                )
                
                self._last_stats_log = current_time
        
        except Exception as e:
            self.registrar_log(f"❌ Error mostrando stats: {e}")

    def mostrar_error(self, mensaje):
        """Mostrar error en la UI"""
        try:
            if hasattr(self, 'video_label') and self.video_label:
                pixmap = QPixmap(640, 360)
                pixmap.fill(QColor(50, 50, 50))
                
                painter = QPainter(pixmap)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont('Arial', 14))
                
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, 
                               f"❌ ERROR\n{mensaje}")
                
                painter.end()
                
                self.video_label.setPixmap(pixmap)
                self.info_label.setText(f"❌ Error: {mensaje}")
    
        except Exception as e:
            print(f"Error mostrando error en UI: {e}")

    # ========================================================================================
    # 🔥 MÉTODO FALTANTE Y COMPATIBILIDAD
    # ========================================================================================

    def mostrar_vista(self, camera_data):
        """🔥 MÉTODO CRÍTICO: Mostrar vista de cámara (llamado desde main_window)"""
        try:
            self.registrar_log(f"🎬 mostrar_vista() llamado con: {camera_data.get('ip', 'unknown')}")
            
            # Configurar datos de cámara
            self.set_cam_data(camera_data)
            
            # El stream se inicia automáticamente en set_cam_data()
            if not self.is_stream_active():
                self.registrar_log("🔄 Stream no activo, forzando inicio...")
                self.iniciar_stream()
            
            self.registrar_log(f"✅ mostrar_vista() completado para {camera_data.get('ip', 'unknown')}")
            
        except Exception as e:
            self.registrar_log(f"❌ Error en mostrar_vista(): {e}")
            import traceback
            traceback.print_exc()

    def iniciar(self):
        """Método de compatibilidad"""
        self.registrar_log("🔄 iniciar() llamado - redirigiendo a iniciar_stream()")
        self.iniciar_stream()

    def reproducir(self, camera_data=None):
        """Método de compatibilidad"""
        if camera_data:
            self.mostrar_vista(camera_data)
        else:
            self.iniciar_stream()

    def configurar_camara(self, camera_data):
        """Método de compatibilidad"""
        self.set_cam_data(camera_data)

    def is_stream_active(self):
        """Verificar si el stream está activo"""
        return (hasattr(self, 'visualizador') and 
                self.visualizador and 
                hasattr(self.visualizador, 'using_ffmpeg'))

    # ========================================================================================
    # 🔥 PAINTEVENTS CORREGIDOS PARA OVERLAY
    # ========================================================================================

    def paintEvent(self, event):
        """🔥 CORREGIDO: Evento de pintura con overlay correcto"""
        super().paintEvent(event)
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 1. DIBUJAR CELDAS DE LA GRILLA (PRIMERO)
            self._draw_grid_cells(painter)
            
            # 2. DIBUJAR DETECCIONES SOBRE TODO (SEGUNDO)
            self._draw_detections_overlay(painter)
            
            painter.end()
            
        except Exception as e:
            print(f"❌ Error en paintEvent: {e}")

    def _draw_grid_cells(self, painter):
        """Dibujar celdas de la grilla"""
        try:
            if not hasattr(self, 'filas') or not hasattr(self, 'columnas'):
                return
                
            widget_width = self.width()
            widget_height = self.height()
            
            if widget_width <= 0 or widget_height <= 0:
                return
            
            # Calcular tamaño de celda
            cell_width = widget_width / self.columnas
            cell_height = widget_height / self.filas
            
            # Configurar estilos
            grid_pen = QPen(QColor(100, 100, 100, 100), 1)  # Líneas tenues
            selected_brush = QBrush(QColor(0, 255, 0, 50))   # Verde transparente
            
            painter.setPen(grid_pen)
            
            # Dibujar líneas horizontales
            for i in range(self.filas + 1):
                y = i * cell_height
                painter.drawLine(0, int(y), widget_width, int(y))
            
            # Dibujar líneas verticales
            for j in range(self.columnas + 1):
                x = j * cell_width
                painter.drawLine(int(x), 0, int(x), widget_height)
            
            # Dibujar celdas seleccionadas
            if hasattr(self, 'selected_cells') and self.selected_cells:
                painter.setBrush(selected_brush)
                for cell_index in self.selected_cells:
                    row = cell_index // self.columnas
                    col = cell_index % self.columnas
                    
                    x = col * cell_width
                    y = row * cell_height
                    
                    painter.drawRect(int(x), int(y), int(cell_width), int(cell_height))
        
        except Exception as e:
            print(f"❌ Error dibujando celdas: {e}")

    def _draw_detections_overlay(self, painter):
        """🔥 CORREGIDO: Dibujar detecciones SOBRE el video"""
        try:
            if not hasattr(self, 'latest_tracked_boxes') or not self.latest_tracked_boxes:
                return
            
            # Configurar estilos para detecciones
            detection_pen = QPen(QColor(0, 255, 0), 3)  # Verde brillante
            text_pen = QPen(QColor(255, 255, 255), 2)   # Texto blanco
            bg_brush = QBrush(QColor(0, 0, 0, 180))     # Fondo semi-transparente
            
            font = QFont('Arial', 12, QFont.Weight.Bold)
            painter.setFont(font)
            
            widget_width = self.width()
            widget_height = self.height()
            
            for i, box in enumerate(self.latest_tracked_boxes):
                if not isinstance(box, dict):
                    continue
                    
                bbox = box.get('bbox', [])
                if len(bbox) < 4:
                    continue
                
                # Extraer coordenadas
                x, y, w, h = bbox[:4]
                
                # 🔥 ESCALAR COORDENADAS AL TAMAÑO DEL WIDGET
                # Asumiendo que las detecciones vienen en coordenadas de video original
                if hasattr(self, 'original_frame_size') and self.original_frame_size:
                    orig_w, orig_h = self.original_frame_size
                    scale_x = widget_width / orig_w
                    scale_y = widget_height / orig_h
                    
                    x = int(x * scale_x)
                    y = int(y * scale_y)
                    w = int(w * scale_x)
                    h = int(h * scale_y)
                
                # Asegurar que las coordenadas estén dentro del widget
                x = max(0, min(x, widget_width - w))
                y = max(0, min(y, widget_height - h))
                w = min(w, widget_width - x)
                h = min(h, widget_height - y)
                
                # Dibujar rectángulo de detección
                painter.setPen(detection_pen)
                painter.setBrush(QBrush())  # Sin relleno
                painter.drawRect(int(x), int(y), int(w), int(h))
                
                # Preparar texto de etiqueta
                class_name = box.get('class_name', 'obj')
                confidence = box.get('conf', 0.0)
                track_id = box.get('track_id', -1)
                
                if track_id >= 0:
                    label = f"{class_name} #{track_id} {confidence:.2f}"
                else:
                    label = f"{class_name} {confidence:.2f}"
                
                # Dibujar fondo para el texto
                text_rect = painter.fontMetrics().boundingRect(label)
                bg_rect = text_rect.adjusted(-4, -2, 4, 2)
                bg_rect.moveTopLeft(QPointF(x, y - text_rect.height() - 5))
                
                painter.setBrush(bg_brush)
                painter.setPen(QPen())
                painter.drawRect(bg_rect)
                
                # Dibujar texto
                painter.setPen(text_pen)
                painter.drawText(int(x), int(y - 5), label)
        
        except Exception as e:
            print(f"❌ Error dibujando detecciones: {e}")

    # ========================================================================================
    # MÉTODOS DE COMPATIBILIDAD Y FUNCIONALIDAD ORIGINAL
    # ========================================================================================

    def actualizar_boxes(self, boxes):
        """Actualizar cajas de detección (método original)"""
        try:
            if not boxes:
                return
            
            self.latest_tracked_boxes = boxes
            self.detection_count = getattr(self, 'detection_count', 0) + 1
            
            # Procesar cada detección
            for box in boxes:
                if isinstance(box, dict):
                    bbox = box.get('bbox', [])
                    confidence = box.get('conf', 0.0)
                    class_name = box.get('class_name', 'unknown')
                    track_id = box.get('track_id', -1)
                    
                    # Log ocasional de detecciones
                    if self.detection_count % 100 == 0:
                        self.registrar_log(
                            f"🔍 Detección #{self.detection_count}: {class_name} "
                            f"(conf: {confidence:.2f}, track: {track_id})"
                        )
            
            # 🔥 FORZAR ACTUALIZACIÓN VISUAL
            self.update()
            
            # Integración PTZ si está disponible
            self._try_ptz_integration(boxes)
            
        except Exception as e:
            self.registrar_log(f"❌ Error actualizando boxes: {e}")

    def _try_ptz_integration(self, boxes):
        """Intentar integración PTZ"""
        try:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'send_detections_to_ptz'):
                camera_id = self.cam_data.get('ip', 'unknown') if self.cam_data else 'unknown'
                ptz_detections = self._convert_boxes_for_ptz(boxes)
                if ptz_detections:
                    success = main_window.send_detections_to_ptz(camera_id, ptz_detections)
                    if success and self.detection_count <= 10:
                        self.registrar_log(f"🎯 PTZ: {len(ptz_detections)} detecciones enviadas a {camera_id}")
        except Exception as e:
            if not hasattr(self, '_ptz_error_logged'):
                self.registrar_log(f"⚠️ Error integración PTZ: {e}")
                self._ptz_error_logged = True

    def _get_main_window(self):
        """Obtener referencia a la ventana principal"""
        widget = self
        while widget:
            if hasattr(widget, 'send_detections_to_ptz'):
                return widget
            widget = widget.parent()
        return None

    def _convert_boxes_for_ptz(self, boxes):
        """Convertir detecciones para PTZ"""
        ptz_detections = []
        frame_size = getattr(self, 'original_frame_size', (640, 480))
        
        for box in boxes:
            if isinstance(box, dict):
                bbox = box.get('bbox', [])
                if len(bbox) >= 4:
                    ptz_detections.append({
                        'bbox': bbox,
                        'confidence': box.get('conf', 0.0),
                        'class_name': box.get('class_name', 'object'),
                        'track_id': box.get('track_id', -1)
                    })
        
        return ptz_detections

    def request_paint_update(self):
        """Solicitar actualización de pintura"""
        self.update()

    def detener(self):
        """Detener el widget y limpiar recursos"""
        try:
            ip = self.cam_data.get('ip', 'unknown') if self.cam_data else 'unknown'
            self.registrar_log(f"🛑 [{ip}] Deteniendo GrillaWidget...")
            
            # Detener visualizador
            if hasattr(self, 'visualizador') and self.visualizador:
                self.visualizador.stop()
                self.visualizador = None
            
            # Limpiar datos
            self.cam_data = None
            self.latest_tracked_boxes = []
            
            # Actualizar UI
            if hasattr(self, 'video_label'):
                self.video_label.setText("📺 Desconectado")
            if hasattr(self, 'info_label'):
                self.info_label.setText("Cámara desconectada")
            
            self.registrar_log(f"✅ [{ip}] GrillaWidget detenido correctamente")
            
        except Exception as e:
            self.registrar_log(f"❌ Error deteniendo widget: {e}")

    def registrar_log(self, mensaje):
        """Registrar mensaje de log con timestamp"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            log_msg = f"[{timestamp}] {mensaje}"
            print(log_msg)
            
            # Emitir señal si está disponible
            if hasattr(self, 'log_signal'):
                try:
                    self.log_signal.emit(log_msg)
                except:
                    pass
        except:
            print(mensaje)

    # ========================================================================================
    # MÉTODOS DE COMPATIBILIDAD CON LA API ORIGINAL
    # ========================================================================================

    def set_area(self, area):
        """Establecer área de detección"""
        self.area = area

    def get_area(self):
        """Obtener área de detección"""
        return self.area

    def clear_selection(self):
        """Limpiar selección de celdas"""
        self.selected_cells.clear()
        self.update()

    def select_all(self):
        """Seleccionar todas las celdas"""
        self.selected_cells = set(range(self.filas * self.columnas))
        self.update()

    def toggle_cell(self, row, col):
        """Alternar estado de celda"""
        index = row * self.columnas + col
        if index in self.selected_cells:
            self.selected_cells.remove(index)
        else:
            self.selected_cells.add(index)
        self.update()

    def configurar_alertas(self, gestor_alertas):
        """Configurar gestor de alertas"""
        self.alertas = gestor_alertas

    def configurar_ptz(self, ptz_config):
        """Configurar sistema PTZ"""
        if hasattr(self, 'ptz_manager'):
            self.ptz_manager.configure(ptz_config)

    def get_detection_count(self):
        """Obtener contador de detecciones"""
        return getattr(self, 'detection_count', 0)

    def reset_detection_count(self):
        """Resetear contador de detecciones"""
        self.detection_count = 0

    def __del__(self):
        """Destructor para limpiar recursos"""
        try:
            self.detener()
        except:
            pass