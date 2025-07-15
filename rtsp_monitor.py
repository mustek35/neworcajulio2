# ========================================================================================
# ARCHIVO: test_ffmpeg_bridge_simple.py
# Test simple del FFmpeg Bridge para verificar que funciona
# ========================================================================================

import subprocess
import cv2
import numpy as np
import threading
import queue
import time

class FFmpegRTSPReader:
    """
    Lector RTSP usando FFmpeg como backend cuando OpenCV falla con H.264
    """
    
    def __init__(self, rtsp_url, width=1920, height=1080):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.process = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.running = False
        self.thread = None
        
    def start(self):
        """Iniciar captura de video"""
        if self.running:
            return
            
        # Comando FFmpeg para convertir RTSP a raw frames
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', self.rtsp_url,
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-an',  # Sin audio
            '-sn',  # Sin subtítulos  
            '-'     # Output a stdout
        ]
        
        try:
            print(f"🚀 Iniciando FFmpeg con comando:")
            print(f"   {' '.join(cmd[:6])}... {self.rtsp_url}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
            
            self.running = True
            self.thread = threading.Thread(target=self._read_frames)
            self.thread.daemon = True
            self.thread.start()
            
            print(f"✅ FFmpeg bridge iniciado")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando FFmpeg: {e}")
            return False
    
    def _read_frames(self):
        """Thread para leer frames desde FFmpeg"""
        frame_size = self.width * self.height * 3  # BGR = 3 bytes por pixel
        
        print(f"📐 Esperando frames de {self.width}x{self.height} ({frame_size} bytes cada uno)")
        
        frame_count = 0
        while self.running:
            try:
                # Leer frame raw desde FFmpeg
                raw_frame = self.process.stdout.read(frame_size)
                
                if len(raw_frame) != frame_size:
                    if len(raw_frame) == 0:
                        print(f"📡 FFmpeg terminó o sin datos")
                    else:
                        print(f"⚠️ Frame incompleto: {len(raw_frame)}/{frame_size}")
                    break
                
                # Convertir a numpy array
                frame = np.frombuffer(raw_frame, dtype=np.uint8)
                frame = frame.reshape((self.height, self.width, 3))
                
                frame_count += 1
                if frame_count % 30 == 0:  # Log cada 30 frames (~1 segundo)
                    print(f"📷 Frame {frame_count} recibido correctamente")
                
                # Agregar a queue (eliminar frame viejo si está lleno)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()  # Eliminar frame viejo
                        self.frame_queue.put_nowait(frame)  # Agregar nuevo
                    except queue.Empty:
                        pass
                        
            except Exception as e:
                print(f"❌ Error leyendo frame: {e}")
                break
        
        print(f"🏁 Thread de lectura terminado. Total frames: {frame_count}")
    
    def read(self):
        """Leer frame (compatible con cv2.VideoCapture)"""
        if not self.running:
            return False, None
            
        try:
            frame = self.frame_queue.get(timeout=2.0)
            return True, frame
        except queue.Empty:
            return False, None
    
    def isOpened(self):
        """Verificar si está abierto"""
        return self.running and self.process is not None
    
    def release(self):
        """Liberar recursos"""
        print(f"🛑 Liberando recursos FFmpeg...")
        self.running = False
        
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        
        if self.thread:
            self.thread.join(timeout=3)
        
        # Limpiar queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        print(f"✅ Recursos liberados")

def test_ffmpeg_bridge():
    """Probar el puente FFmpeg"""
    print("🔍 PROBANDO FFMPEG BRIDGE")
    print("=" * 50)
    
    rtsp_url = "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live"
    print(f"🎯 URL: {rtsp_url}")
    
    # Crear lector FFmpeg
    cap = FFmpegRTSPReader(rtsp_url)
    
    if not cap.start():
        print("❌ No se pudo iniciar FFmpeg bridge")
        return False
    
    print("✅ FFmpeg bridge iniciado, esperando frames...")
    
    frames_received = 0
    start_time = time.time()
    max_duration = 30  # 30 segundos máximo
    
    try:
        # Leer frames
        while time.time() - start_time < max_duration:
            ret, frame = cap.read()
            
            if ret and frame is not None:
                frames_received += 1
                
                # Log progreso cada 10 frames
                if frames_received % 10 == 0:
                    elapsed = time.time() - start_time
                    fps = frames_received / elapsed
                    print(f"📊 Frame {frames_received}: {frame.shape} ({fps:.1f} FPS)")
                
                # Guardar primer frame como prueba
                if frames_received == 1:
                    try:
                        cv2.imwrite("primer_frame_ffmpeg.jpg", frame)
                        print(f"💾 Primer frame guardado: primer_frame_ffmpeg.jpg")
                    except Exception as e:
                        print(f"⚠️ No se pudo guardar frame: {e}")
                
                # Si ya recibimos suficientes frames para confirmar que funciona
                if frames_received >= 30:
                    print(f"🎉 ¡Suficientes frames recibidos! Test exitoso")
                    break
            else:
                print(f"⚠️ No frame recibido")
                time.sleep(0.1)
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrumpido por usuario")
    except Exception as e:
        print(f"❌ Error durante test: {e}")
    finally:
        cap.release()
    
    total_time = time.time() - start_time
    fps_promedio = frames_received / total_time if total_time > 0 else 0
    
    print(f"\n📊 RESULTADOS:")
    print(f"   ⏱️ Tiempo total: {total_time:.1f} segundos")
    print(f"   📷 Frames recibidos: {frames_received}")
    print(f"   📈 FPS promedio: {fps_promedio:.1f}")
    
    if frames_received > 0:
        print(f"\n🎉 ¡FFMPEG BRIDGE FUNCIONA PERFECTAMENTE!")
        print(f"💡 Tu stream H.264 se puede leer usando este bridge")
        return True
    else:
        print(f"\n❌ FFmpeg Bridge no recibió frames")
        print(f"🔧 Verificar instalación de FFmpeg")
        return False

def check_ffmpeg_installation():
    """Verificar que FFmpeg está instalado y accesible"""
    print("🔍 VERIFICANDO INSTALACIÓN DE FFMPEG")
    print("=" * 40)
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Extraer versión
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else "Versión desconocida"
            print(f"✅ FFmpeg instalado: {version_line}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout verificando FFmpeg")
        return False
    except FileNotFoundError:
        print(f"❌ FFmpeg no encontrado en PATH")
        print(f"💡 Instalar FFmpeg desde: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"❌ Error verificando FFmpeg: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 TEST FFMPEG BRIDGE - SOLUCIÓN DEFINITIVA")
    print("=" * 60)
    
    # Verificar FFmpeg primero
    if not check_ffmpeg_installation():
        print(f"\n❌ FFmpeg no está disponible")
        print(f"📥 INSTRUCCIONES DE INSTALACIÓN:")
        print(f"   1. Descargar FFmpeg desde: https://ffmpeg.org/download.html")
        print(f"   2. Extraer y agregar al PATH del sistema")
        print(f"   3. Reiniciar terminal y probar: ffmpeg -version")
        return
    
    # Probar bridge
    if test_ffmpeg_bridge():
        print(f"\n🎉 ¡ÉXITO TOTAL!")
        print(f"✅ Tu cámara ahora funciona con FFmpeg Bridge")
        print(f"📁 Usar: ffmpeg_rtsp_bridge.py en tu proyecto")
        print(f"💡 Reemplazar cv2.VideoCapture con FFmpegRTSPReader")
        
        print(f"\n📋 CÓDIGO DE EJEMPLO:")
        print(f"```python")
        print(f"from ffmpeg_rtsp_bridge import FFmpegRTSPReader")
        print(f"")
        print(f"# En lugar de:")
        print(f"# cap = cv2.VideoCapture(rtsp_url)")
        print(f"")
        print(f"# Usar:")
        print(f"cap = FFmpegRTSPReader(rtsp_url)")
        print(f"cap.start()")
        print(f"")
        print(f"# Luego usar normalmente:")
        print(f"ret, frame = cap.read()")
        print(f"```")
    else:
        print(f"\n❌ Bridge no funcionó correctamente")
        print(f"🔧 Verificar configuración de red y FFmpeg")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⏹️ Test cancelado por usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()