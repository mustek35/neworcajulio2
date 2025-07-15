# ========================================================================================
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
        opcion = input("\nSelecciona opción (1-3): ").strip()
        
        if opcion == "1":
            test_version_simple()
        elif opcion == "2":
            test_version_actual()
        elif opcion == "3":
            print("Probando ambas versiones...")
            test_version_simple()
            print("\n" + "="*50 + "\n")
            test_version_actual()
        else:
            print("❌ Opción inválida")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test cancelado")

if __name__ == "__main__":
    main()
