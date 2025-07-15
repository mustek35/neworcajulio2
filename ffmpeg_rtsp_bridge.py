
# ========================================================================================
# CLASE FFMPEG BRIDGE - Solución cuando OpenCV no puede leer H.264
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
        
        while self.running:
            try:
                # Leer frame raw desde FFmpeg
                raw_frame = self.process.stdout.read(frame_size)
                
                if len(raw_frame) != frame_size:
                    print(f"⚠️ Frame incompleto: {len(raw_frame)}/{frame_size}")
                    break
                
                # Convertir a numpy array
                frame = np.frombuffer(raw_frame, dtype=np.uint8)
                frame = frame.reshape((self.height, self.width, 3))
                
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
    
    def read(self):
        """Leer frame (compatible con cv2.VideoCapture)"""
        if not self.running:
            return False, None
            
        try:
            frame = self.frame_queue.get(timeout=1.0)
            return True, frame
        except queue.Empty:
            return False, None
    
    def isOpened(self):
        """Verificar si está abierto"""
        return self.running and self.process is not None
    
    def release(self):
        """Liberar recursos"""
        self.running = False
        
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        
        if self.thread:
            self.thread.join(timeout=2)
        
        # Limpiar queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

# ========================================================================================
# EJEMPLO DE USO
# ========================================================================================

def test_ffmpeg_bridge():
    """Probar el puente FFmpeg"""
    print("🔍 Probando FFmpeg Bridge...")
    
    # Crear lector FFmpeg
    cap = FFmpegRTSPReader("rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s1/live")
    
    if not cap.start():
        print("❌ No se pudo iniciar FFmpeg bridge")
        return
    
    print("✅ FFmpeg bridge iniciado, leyendo frames...")
    
    frames_received = 0
    start_time = time.time()
    
    # Leer frames por 10 segundos
    while time.time() - start_time < 10:
        ret, frame = cap.read()
        
        if ret and frame is not None:
            frames_received += 1
            if frames_received % 10 == 0:
                print(f"📷 Frame {frames_received}: {frame.shape}")
        
        time.sleep(0.03)  # ~30 FPS
    
    cap.release()
    
    fps = frames_received / (time.time() - start_time)
    print(f"📊 Resultado: {frames_received} frames, {fps:.1f} FPS")
    
    if frames_received > 0:
        print(f"🎉 ¡FFmpeg Bridge funciona perfectamente!")
        return True
    else:
        print(f"❌ FFmpeg Bridge no recibió frames")
        return False

if __name__ == "__main__":
    test_ffmpeg_bridge()
