# ========================================================================================
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
        print("\n⏹️ Detenido por usuario")
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
        print("\n⏹️ Detenido por usuario")
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
        opcion = input("\nSelecciona opción (1-2): ").strip()
        
        if opcion == "1":
            ejemplo_simple()
        elif opcion == "2":
            ejemplo_con_deteccion()
        else:
            print("❌ Opción inválida")
            
    except KeyboardInterrupt:
        print("\n⏹️ Cancelado por usuario")
