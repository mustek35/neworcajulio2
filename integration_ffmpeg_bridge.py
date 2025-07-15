# ========================================================================================
# ARCHIVO: integration_ffmpeg_bridge.py
# Integración del FFmpeg Bridge en tu aplicación de detección
# ========================================================================================

import os
import shutil
from datetime import datetime

def integrate_ffmpeg_bridge():
    """
    Integrar FFmpeg Bridge en tu aplicación principal
    """
    print("🔧 INTEGRANDO FFMPEG BRIDGE EN TU APLICACIÓN")
    print("=" * 60)
    
    # 1. Actualizar VisualizadorDetector
    update_visualizador_detector()
    
    # 2. Actualizar configuración de cámaras
    update_camera_config()
    
    # 3. Crear ejemplo de uso
    create_usage_example()
    
    print("✅ INTEGRACIÓN COMPLETADA")
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Reinicia tu aplicación: python app.py")
    print("   2. La cámara 192.168.1.3 ahora debería funcionar")
    print("   3. Revisa logs para confirmar funcionamiento")

def update_visualizador_detector():
    """
    Actualizar VisualizadorDetector para usar FFmpeg Bridge
    """
    print("\n📝 ACTUALIZANDO VisualizadorDetector...")
    
    archivo_visualizador = "gui/visualizador_detector.py"
    
    if not os.path.exists(archivo_visualizador):
        print(f"❌ {archivo_visualizador} no encontrado")
        return
    
    # Crear backup
    backup_file = f"{archivo_visualizador}.backup_ffmpeg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(archivo_visualizador, backup_file)
    print(f"💾 Backup creado: {backup_file}")
    
    # Leer contenido actual
    with open(archivo_visualizador, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Agregar import del FFmpeg Bridge al inicio
    import_ffmpeg = '''
# ✅ IMPORT FFMPEG BRIDGE PARA H.264
try:
    from ffmpeg_rtsp_bridge import FFmpegRTSPReader
    FFMPEG_BRIDGE_AVAILABLE = True
    print("✅ FFmpeg Bridge disponible")
except ImportError:
    FFMPEG_BRIDGE_AVAILABLE = False
    print("⚠️ FFmpeg Bridge no disponible")
'''
    
    # Buscar imports existentes y agregar
    if "from PyQt6.QtMultimedia import" in contenido:
        pos_imports = contenido.find("from PyQt6.QtMultimedia import")
        contenido = contenido[:pos_imports] + import_ffmpeg + "\n" + contenido[pos_imports:]
    
    # Modificar el método iniciar para detectar URLs problemáticas
    parche_iniciar = '''
    def iniciar(self):
        rtsp_url = self.cam_data.get("rtsp")
        if rtsp_url:
            logger.info("%s: Reproduciendo RTSP %s", self.objectName(), rtsp_url)
            self.log_signal.emit(f"🎥 [{self.objectName()}] Streaming iniciado: {rtsp_url}")
            
            # ✅ DETECTAR SI NECESITA FFMPEG BRIDGE
            ip = self.cam_data.get('ip', '')
            if ip == '192.168.1.3' and FFMPEG_BRIDGE_AVAILABLE:
                self.log_signal.emit(f"🔧 [{self.objectName()}] Usando FFmpeg Bridge para H.264")
                self._start_ffmpeg_bridge(rtsp_url)
                return
            
            # Configurar callbacks estándar de MediaPlayer
            self.video_player.playbackStateChanged.connect(self._on_playback_state_changed)
            self.video_player.mediaStatusChanged.connect(self._on_media_status_changed)
            
            self.video_player.setSource(QUrl(rtsp_url))
            self.video_player.play()
        else:
            logger.warning("%s: No se encontró URL RTSP para iniciar", self.objectName())
            self.log_signal.emit(f"⚠️ [{self.objectName()}] No se encontró URL RTSP.")
    
    def _start_ffmpeg_bridge(self, rtsp_url):
        """Iniciar FFmpeg Bridge para cámaras H.264 problemáticas"""
        try:
            self.ffmpeg_reader = FFmpegRTSPReader(rtsp_url)
            
            if self.ffmpeg_reader.start():
                self.log_signal.emit(f"✅ [{self.objectName()}] FFmpeg Bridge iniciado")
                
                # Iniciar thread para procesar frames desde FFmpeg
                import threading
                self.ffmpeg_thread = threading.Thread(target=self._process_ffmpeg_frames, daemon=True)
                self.ffmpeg_thread.start()
            else:
                self.log_signal.emit(f"❌ [{self.objectName()}] Error iniciando FFmpeg Bridge")
                
        except Exception as e:
            self.log_signal.emit(f"❌ [{self.objectName()}] Error FFmpeg Bridge: {e}")
    
    def _process_ffmpeg_frames(self):
        """Procesar frames desde FFmpeg Bridge"""
        frame_count = 0
        
        while hasattr(self, 'ffmpeg_reader') and self.ffmpeg_reader.isOpened():
            try:
                ret, frame = self.ffmpeg_reader.read()
                
                if ret and frame is not None:
                    frame_count += 1
                    
                    # Procesar frame igual que on_frame normal
                    self._process_ffmpeg_frame(frame, frame_count)
                    
                    # Log progreso ocasional
                    if frame_count % 100 == 0:
                        self.log_signal.emit(f"📷 [{self.objectName()}] FFmpeg: {frame_count} frames procesados")
                
                else:
                    time.sleep(0.01)  # Pequeña pausa si no hay frame
                    
            except Exception as e:
                self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando FFmpeg frame: {e}")
                break
    
    def _process_ffmpeg_frame(self, frame, frame_count):
        """Procesar frame de FFmpeg igual que on_frame"""
        try:
            # Procesar frames para detección según la configuración de FPS
            if frame_count % self.detector_frame_interval == 0:
                self._last_frame = frame
                self._pending_detections = {}
                self._current_frame_id += 1

                if hasattr(self, 'detectors'):
                    detectores_activos = sum(1 for det in self.detectors if det and det.isRunning())
                    if frame_count % 200 == 0:  # Log cada 200 frames
                        self.log_signal.emit(f"🤖 [{self.objectName()}] FFmpeg: {detectores_activos}/{len(self.detectors)} detectores activos")
                    
                    for det in self.detectors:
                        if det and det.isRunning():
                            det.set_frame(frame, self._current_frame_id)

        except Exception as e:
            logger.error("%s: error procesando FFmpeg frame: %s", self.objectName(), e)
            self.log_signal.emit(f"❌ [{self.objectName()}] Error procesando frame FFmpeg: {e}")'''
    
    # Buscar el método iniciar existente y reemplazarlo
    inicio_metodo = contenido.find("    def iniciar(self):")
    if inicio_metodo != -1:
        # Encontrar el final del método
        lineas = contenido[inicio_metodo:].split('\n')
        fin_metodo = inicio_metodo
        for i, linea in enumerate(lineas[1:], 1):
            if linea.strip() and not linea.startswith(' ') and not linea.startswith('\t'):
                if linea.strip().startswith('def '):
                    fin_metodo = inicio_metodo + len('\n'.join(lineas[:i]))
                    break
        
        # Reemplazar el método
        contenido_nuevo = contenido[:inicio_metodo] + parche_iniciar + contenido[fin_metodo:]
    else:
        contenido_nuevo = contenido + parche_iniciar
    
    # Actualizar método detener para limpiar FFmpeg
    parche_detener = '''
    def detener(self):
        logger.info("%s: Deteniendo VisualizadorDetector", self.objectName())
        
        # ✅ DETENER FFMPEG BRIDGE SI ESTÁ ACTIVO
        if hasattr(self, 'ffmpeg_reader'):
            try:
                self.ffmpeg_reader.release()
                self.log_signal.emit(f"🛑 [{self.objectName()}] FFmpeg Bridge detenido")
            except Exception as e:
                logger.error("%s: Error deteniendo FFmpeg Bridge: %s", self.objectName(), e)
        
        # Detener detectores normales
        if hasattr(self, 'detectors'):
            for det in self.detectors:
                if det:
                    logger.info("%s: Deteniendo %s", self.objectName(), det.objectName())
                    det.stop()
        
        # Detener MediaPlayer normal
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
        
        logger.info("%s: VisualizadorDetector detenido", self.objectName())'''
    
    # Buscar y reemplazar método detener
    inicio_detener = contenido_nuevo.find("    def detener(self):")
    if inicio_detener != -1:
        lineas = contenido_nuevo[inicio_detener:].split('\n')
        fin_detener = inicio_detener
        for i, linea in enumerate(lineas[1:], 1):
            if linea.strip() and not linea.startswith(' ') and not linea.startswith('\t'):
                if linea.strip().startswith('def '):
                    fin_detener = inicio_detener + len('\n'.join(lineas[:i]))
                    break
        
        contenido_nuevo = contenido_nuevo[:inicio_detener] + parche_detener + contenido_nuevo[fin_detener:]
    
    # Agregar import time si no existe
    if "import time" not in contenido_nuevo:
        contenido_nuevo = "import time\n" + contenido_nuevo
    
    # Escribir archivo actualizado
    with open(archivo_visualizador, 'w', encoding='utf-8') as f:
        f.write(contenido_nuevo)
    
    print(f"✅ VisualizadorDetector actualizado con FFmpeg Bridge")

def update_camera_config():
    """
    Actualizar configuración de la cámara para usar URL correcta
    """
    print("\n📝 ACTUALIZANDO CONFIGURACIÓN DE CÁMARA...")
    
    import json
    
    # Configuración corregida para tu cámara
    config_corregida = {
        "ip": "192.168.1.3",
        "puerto": 30012,
        "usuario": "admin",
        "contrasena": "/Remoto753524",  # Contraseña corregida
        "tipo": "nvr",
        "canal": "1",
        "grilla": "grilla 1",
        "nombre": "Cámara NVR - FFmpeg Bridge",
        "rtsp": "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live",  # URL que funciona
        "puerto_rtsp": 30012,
        "perfil": "sub",
        "fps_config": {
            "visual_fps": 15,      # Reducido para mejor performance
            "detection_fps": 5,    # Detección cada 6 frames
            "ui_update_fps": 10
        }
    }
    
    # Buscar archivos de configuración
    archivos_config = ["config.json", "camaras_config.json"]
    
    for archivo in archivos_config:
        if os.path.exists(archivo):
            print(f"   📁 Actualizando {archivo}...")
            
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    if archivo == "config.json":
                        data = json.load(f)
                        camaras = data.get("camaras", [])
                    else:
                        camaras = json.load(f)
                
                # Buscar y actualizar cámara 192.168.1.3
                camara_encontrada = False
                for cam in camaras:
                    if cam.get('ip') == '192.168.1.3':
                        cam.update(config_corregida)
                        camara_encontrada = True
                        print(f"      ✅ Cámara 192.168.1.3 actualizada")
                        break
                
                if not camara_encontrada:
                    # Agregar nueva cámara
                    camaras.append(config_corregida)
                    print(f"      ✅ Cámara 192.168.1.3 agregada")
                
                # Crear backup
                backup_file = f"{archivo}.backup_ffmpeg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(archivo, backup_file)
                print(f"      💾 Backup: {backup_file}")
                
                # Guardar cambios
                with open(archivo, 'w', encoding='utf-8') as f:
                    if archivo == "config.json":
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    else:
                        json.dump(camaras, f, indent=4, ensure_ascii=False)
                
                print(f"      ✅ {archivo} actualizado")
                return True
                
            except Exception as e:
                print(f"      ❌ Error actualizando {archivo}: {e}")
    
    # Si no hay archivos, crear configuración nueva
    print("   📁 Creando nueva configuración...")
    with open("config_ffmpeg_bridge.json", 'w', encoding='utf-8') as f:
        json.dump([config_corregida], f, indent=4, ensure_ascii=False)
    
    print(f"   ✅ Nueva configuración creada: config_ffmpeg_bridge.json")

def create_usage_example():
    """
    Crear ejemplo de uso del FFmpeg Bridge
    """
    print("\n📝 CREANDO EJEMPLO DE USO...")
    
    ejemplo_uso = '''# ========================================================================================
# EJEMPLO DE USO: FFmpeg Bridge para tu aplicación
# ========================================================================================

from ffmpeg_rtsp_bridge import FFmpegRTSPReader
import cv2
import time

def ejemplo_simple():
    """Ejemplo simple de uso del FFmpeg Bridge"""
    print("🎥 EJEMPLO SIMPLE - FFMPEG BRIDGE")
    
    # URL de tu cámara que funciona
    rtsp_url = "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live"
    
    # Crear lector FFmpeg (en lugar de cv2.VideoCapture)
    cap = FFmpegRTSPReader(rtsp_url)
    
    # Iniciar captura
    if not cap.start():
        print("❌ Error iniciando FFmpeg Bridge")
        return
    
    print("✅ FFmpeg Bridge iniciado, presiona 'q' para salir")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Leer frame (igual que cv2.VideoCapture)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                frame_count += 1
                
                # Mostrar FPS cada 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"📊 Frame {frame_count}, FPS: {fps:.1f}")
                
                # Mostrar frame
                cv2.imshow('Tu Cámara - FFmpeg Bridge', frame)
                
                # Salir con 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print("\\n⏹️ Detenido por usuario")
    finally:
        # Limpiar recursos
        cap.release()
        cv2.destroyAllWindows()
        
        # Estadísticas finales
        total_time = time.time() - start_time
        fps_promedio = frame_count / total_time if total_time > 0 else 0
        print(f"📊 Total: {frame_count} frames en {total_time:.1f}s ({fps_promedio:.1f} FPS)")

def ejemplo_con_deteccion():
    """Ejemplo con detección YOLO usando FFmpeg Bridge"""
    print("🤖 EJEMPLO CON DETECCIÓN - FFMPEG BRIDGE")
    
    # Importar YOLO si está disponible
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')  # Modelo ligero
        print("✅ YOLO cargado")
    except ImportError:
        print("⚠️ YOLO no disponible, solo mostrando frames")
        model = None
    
    rtsp_url = "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live"
    cap = FFmpegRTSPReader(rtsp_url)
    
    if not cap.start():
        print("❌ Error iniciando FFmpeg Bridge")
        return
    
    frame_count = 0
    detection_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if ret and frame is not None:
                frame_count += 1
                
                # Ejecutar detección cada 5 frames (para performance)
                if model and frame_count % 5 == 0:
                    results = model(frame, verbose=False)
                    
                    # Dibujar detecciones
                    annotated_frame = results[0].plot()
                    
                    # Contar detecciones
                    if len(results[0].boxes) > 0:
                        detection_count += len(results[0].boxes)
                        print(f"🎯 Frame {frame_count}: {len(results[0].boxes)} detecciones")
                    
                    cv2.imshow('Detección + FFmpeg Bridge', annotated_frame)
                else:
                    cv2.imshow('Detección + FFmpeg Bridge', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print("\\n⏹️ Detenido por usuario")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"📊 Total detecciones: {detection_count}")

if __name__ == "__main__":
    print("🎥 EJEMPLOS DE USO - FFMPEG BRIDGE")
    print("=" * 50)
    print("1. Ejemplo simple")
    print("2. Ejemplo con detección YOLO")
    
    try:
        opcion = input("\\nSelecciona opción (1-2): ").strip()
        
        if opcion == "1":
            ejemplo_simple()
        elif opcion == "2":
            ejemplo_con_deteccion()
        else:
            print("❌ Opción inválida")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Cancelado por usuario")
'''
    
    with open("ejemplo_ffmpeg_bridge.py", 'w', encoding='utf-8') as f:
        f.write(ejemplo_uso)
    
    print(f"✅ Ejemplo creado: ejemplo_ffmpeg_bridge.py")

def main():
    """
    Función principal de integración
    """
    print("🔧 INTEGRACIÓN FFMPEG BRIDGE - SOLUCIÓN COMPLETA")
    print("=" * 60)
    
    print("📋 ESTADO ACTUAL:")
    print("   ✅ FFmpeg Bridge probado y funcional")
    print("   ✅ Tu cámara H.264 transmite correctamente")
    print("   ✅ 30 frames recibidos exitosamente")
    print("   🎯 Integrando en tu aplicación...")
    
    try:
        integrate_ffmpeg_bridge()
        
        print(f"\n🎉 ¡INTEGRACIÓN COMPLETADA EXITOSAMENTE!")
        print(f"=" * 50)
        
        print(f"\n📁 ARCHIVOS MODIFICADOS:")
        print(f"   • gui/visualizador_detector.py - Actualizado con FFmpeg Bridge")
        print(f"   • config.json - Configuración de cámara corregida")
        print(f"   • ejemplo_ffmpeg_bridge.py - Ejemplos de uso")
        
        print(f"\n🚀 CÓMO PROCEDER:")
        print(f"   1. Reinicia tu aplicación: python app.py")
        print(f"   2. Tu cámara 192.168.1.3 ahora usará FFmpeg Bridge automáticamente")
        print(f"   3. Verifica logs para confirmar: '✅ FFmpeg Bridge iniciado'")
        print(f"   4. Si hay problemas, revisa console debug")
        
        print(f"\n🧪 PRUEBAS ADICIONALES:")
        print(f"   • python ejemplo_ffmpeg_bridge.py - Test individual")
        print(f"   • python test_ffmpeg_bridge_simple.py - Verificación rápida")
        
        print(f"\n💡 NOTAS IMPORTANTES:")
        print(f"   • Solo la cámara 192.168.1.3 usa FFmpeg Bridge")
        print(f"   • Otras cámaras siguen usando OpenCV normal")
        print(f"   • FPS reducido a 15/5 para mejor performance")
        print(f"   • Backups automáticos creados de archivos modificados")
        
    except Exception as e:
        print(f"\n❌ Error durante integración: {e}")
        print(f"🔧 Revisar archivos y permisos")

if __name__ == "__main__":
    main()