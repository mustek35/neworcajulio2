# ========================================================================================
# DIAGNÓSTICO: Problemas después de refactorización de grilla_widget
# Si funcionaba antes, el problema está en los cambios de código, no en H.264
# ========================================================================================

import os
import json
from datetime import datetime

def diagnosticar_cambios_refactorizacion():
    """
    Diagnosticar qué cambió después de la refactorización que rompió QMediaPlayer
    """
    print("🔍 DIAGNÓSTICO POST-REFACTORIZACIÓN")
    print("=" * 60)
    
    print("📋 SITUACIÓN CONFIRMADA:")
    print("   ✅ ANTES: QMediaPlayer funcionaba perfectamente")
    print("   ❌ DESPUÉS: Problemas de 'sin señal' tras refactorizar grilla_widget")
    print("   🎯 CONCLUSIÓN: El problema está en cambios de código, NO en codec")
    
    # Problemas comunes post-refactorización
    problemas_comunes = [
        {
            "problema": "Imports Rotos",
            "descripcion": "Cambios en imports rompieron dependencias",
            "sintomas": ["ImportError", "ModuleNotFoundError", "AttributeError"],
            "solucion": "Verificar y corregir imports"
        },
        {
            "problema": "Inicialización de QMediaPlayer",
            "descripcion": "Cambios en orden de inicialización",
            "sintomas": ["QMediaPlayer no inicia", "VideoSink no conecta"],
            "solucion": "Revisar orden de setup"
        },
        {
            "problema": "Callbacks Desconectados",
            "descripcion": "Señales Qt no conectadas correctamente",
            "sintomas": ["on_frame no se llama", "Sin eventos de video"],
            "solucion": "Reconectar señales"
        },
        {
            "problema": "Referencias de Objeto",
            "descripcion": "Objetos se destruyen prematuramente",
            "sintomas": ["C++ object deleted", "Crashes intermitentes"],
            "solucion": "Mantener referencias activas"
        },
        {
            "problema": "Threading Issues",
            "descripcion": "Problemas de concurrencia tras refactorización",
            "sintomas": ["Timeouts", "Deadlocks", "Comportamiento errático"],
            "solucion": "Revisar manejo de threads"
        }
    ]
    
    for i, problema in enumerate(problemas_comunes, 1):
        print(f"\n{i}. 🔧 {problema['problema']}")
        print(f"   📝 {problema['descripcion']}")
        print(f"   🚨 Síntomas: {', '.join(problema['sintomas'])}")
        print(f"   💡 Solución: {problema['solucion']}")

def crear_version_pre_refactorizacion():
    """
    Crear una versión simplificada basada en cómo funcionaba antes
    """
    print("\n🔄 CREANDO VERSIÓN PRE-REFACTORIZACIÓN")
    print("=" * 50)
    
    # VisualizadorDetector simple y funcional (como antes)
    visualizador_simple = '''# ========================================================================================
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
'''
    
    # Escribir versión simple
    with open("gui/visualizador_detector_simple.py", 'w', encoding='utf-8') as f:
        f.write(visualizador_simple)
    
    print("✅ Versión simple creada: gui/visualizador_detector_simple.py")

def identificar_cambios_problematicos():
    """
    Identificar qué cambios específicos pueden haber causado el problema
    """
    print("\n🔍 IDENTIFICANDO CAMBIOS PROBLEMÁTICOS")
    print("=" * 50)
    
    cambios_problematicos = [
        {
            "area": "Orden de Inicialización",
            "problema": "QMediaPlayer/QVideoSink configurados en orden incorrecto",
            "solucion": "Crear QMediaPlayer → QVideoSink → setVideoSink → conectar señales"
        },
        {
            "area": "Conexión de Señales",
            "problema": "videoFrameChanged.connect() llamado después de play()",
            "solucion": "Conectar TODAS las señales ANTES de setSource/play"
        },
        {
            "area": "Referencias de Objeto",
            "problema": "QVideoSink se destruye prematuramente",
            "solucion": "Mantener referencia activa en self.video_sink"
        },
        {
            "area": "Threading",
            "problema": "DetectorWorker interfiere con QMediaPlayer",
            "solucion": "Asegurar que on_frame procese rápidamente"
        },
        {
            "area": "Callbacks Complejos",
            "problema": "Demasiados callbacks agregados tras refactorización",
            "solucion": "Simplificar callbacks, mantener solo los esenciales"
        }
    ]
    
    for cambio in cambios_problematicos:
        print(f"\n🔧 {cambio['area']}:")
        print(f"   ❌ Problema: {cambio['problema']}")
        print(f"   ✅ Solución: {cambio['solucion']}")

def script_comparacion_funcional():
    """
    Script para probar versión simple vs actual
    """
    print("\n🧪 CREANDO SCRIPT DE COMPARACIÓN")
    print("=" * 40)
    
    script_test = '''# ========================================================================================
# test_versiones.py - Comparar versión simple vs actual
# ========================================================================================

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_version_simple():
    """Probar versión simple del visualizador"""
    print("🧪 PROBANDO VERSIÓN SIMPLE")
    
    # Datos de cámara de prueba
    cam_data = {
        "ip": "192.168.1.3",
        "rtsp": "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live",
        "modelos": ["Personas"],
        "confianza": 0.5,
        "detection_fps": 8
    }
    
    try:
        from gui.visualizador_detector_simple import VisualizadorDetector
        
        app = QApplication(sys.argv)
        
        # Crear visualizador
        visualizador = VisualizadorDetector(cam_data)
        
        # Conectar log signal
        visualizador.log_signal.connect(lambda msg: print(f"[SIMPLE] {msg}"))
        
        # Iniciar stream
        visualizador.iniciar()
        
        # Timer para detener después de 30 segundos
        timer = QTimer()
        timer.timeout.connect(lambda: [visualizador.detener(), app.quit()])
        timer.start(30000)
        
        print("✅ Versión simple iniciada, probando por 30 segundos...")
        app.exec()
        
    except Exception as e:
        print(f"❌ Error en versión simple: {e}")
        import traceback
        traceback.print_exc()

def test_version_actual():
    """Probar versión actual del visualizador"""
    print("🧪 PROBANDO VERSIÓN ACTUAL")
    
    cam_data = {
        "ip": "192.168.1.3", 
        "rtsp": "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live",
        "modelos": ["Personas"],
        "confianza": 0.5,
        "detection_fps": 8
    }
    
    try:
        from gui.visualizador_detector import VisualizadorDetector
        
        app = QApplication(sys.argv)
        
        visualizador = VisualizadorDetector(cam_data)
        visualizador.log_signal.connect(lambda msg: print(f"[ACTUAL] {msg}"))
        visualizador.iniciar()
        
        timer = QTimer()
        timer.timeout.connect(lambda: [visualizador.detener(), app.quit()])
        timer.start(30000)
        
        print("✅ Versión actual iniciada, probando por 30 segundos...")
        app.exec()
        
    except Exception as e:
        print(f"❌ Error en versión actual: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔄 COMPARACIÓN DE VERSIONES")
    print("=" * 40)
    
    print("1. Versión Simple (pre-refactorización)")
    print("2. Versión Actual (post-refactorización)")
    print("3. Ambas versiones")
    
    try:
        opcion = input("\\nSelecciona opción (1-3): ").strip()
        
        if opcion == "1":
            test_version_simple()
        elif opcion == "2":
            test_version_actual()
        elif opcion == "3":
            print("Probando ambas versiones...")
            test_version_simple()
            print("\\n" + "="*50 + "\\n")
            test_version_actual()
        else:
            print("❌ Opción inválida")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Test cancelado")

if __name__ == "__main__":
    main()
'''
    
    with open("test_versiones.py", 'w', encoding='utf-8') as f:
        f.write(script_test)
    
    print("✅ Script de comparación creado: test_versiones.py")

def solucion_inmediata():
    """
    Solución inmediata para restaurar funcionalidad
    """
    print("\n🚀 SOLUCIÓN INMEDIATA")
    print("=" * 30)
    
    print("📋 PASOS PARA RESTAURAR FUNCIONALIDAD:")
    print("1. 📁 Usar versión simple: gui/visualizador_detector_simple.py")
    print("2. 🔄 Reemplazar archivo actual")
    print("3. 🧪 Probar con: python test_versiones.py")
    print("4. ✅ Si funciona → identificar diferencias específicas")
    
    try:
        replace = input("\\n¿Reemplazar visualizador actual con versión simple? (s/N): ").strip().lower()
        
        if replace in ['s', 'si', 'sí', 'y', 'yes']:
            import shutil
            
            # Backup del actual
            backup_file = f"gui/visualizador_detector.py.backup_antes_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists("gui/visualizador_detector.py"):
                shutil.copy2("gui/visualizador_detector.py", backup_file)
                print(f"💾 Backup creado: {backup_file}")
            
            # Reemplazar con versión simple
            shutil.copy2("gui/visualizador_detector_simple.py", "gui/visualizador_detector.py")
            print("✅ Archivo reemplazado con versión simple")
            
            print("\\n🎯 PRÓXIMOS PASOS:")
            print("   1. Ejecuta: python app.py")
            print("   2. Si funciona → el problema estaba en la refactorización")
            print("   3. Si no funciona → hay otros problemas")
            
        else:
            print("⚠️ Reemplazo cancelado")
            print("💡 Puedes usar: python test_versiones.py para comparar")
    
    except Exception as e:
        print(f"❌ Error en reemplazo: {e}")

def main():
    """
    Función principal del diagnóstico
    """
    print("🔍 DIAGNÓSTICO POST-REFACTORIZACIÓN")
    print("=" * 60)
    
    print("🎯 HIPÓTESIS CONFIRMADA:")
    print("Si funcionaba antes y falló después de refactorizar,")
    print("el problema está en cambios de código, NO en codec H.264")
    
    diagnosticar_cambios_refactorizacion()
    crear_version_pre_refactorizacion()
    identificar_cambios_problematicos()
    script_comparacion_funcional()
    solucion_inmediata()
    
    print("\n💡 CONCLUSIÓN:")
    print("Tu instinto es correcto - QMediaPlayer debería funcionar.")
    print("El problema está en qué se rompió durante la refactorización.")

if __name__ == "__main__":
    main()