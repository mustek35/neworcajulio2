# ========================================================================================
# ARCHIVO: main_window_rtsp_debug_patch.py
# Parche para agregar monitoreo RTSP integrado a MainWindow
# ========================================================================================

import os
import shutil
from datetime import datetime

def aplicar_parche_main_window():
    """
    Aplica parche a main_window.py para agregar funcionalidad de debug RTSP
    """
    print("🔧 Aplicando parche de debug RTSP a MainWindow...")
    
    archivo_main = "ui/main_window.py"
    
    if not os.path.exists(archivo_main):
        print(f"❌ No se encontró {archivo_main}")
        return False
    
    # Crear backup
    backup_file = f"{archivo_main}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(archivo_main, backup_file)
    print(f"💾 Backup creado: {backup_file}")
    
    # Leer contenido actual
    with open(archivo_main, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # ================================
    # PARCHE 1: Agregar imports
    # ================================
    imports_nuevos = '''
# ✅ IMPORTS PARA DEBUG RTSP
try:
    from rtsp_monitor import RTSPMonitor, RTSPMonitorWidget
    RTSP_MONITOR_AVAILABLE = True
except ImportError:
    RTSP_MONITOR_AVAILABLE = False
    print("⚠️ rtsp_monitor no disponible")

import cv2
import threading
import socket
'''
    
    # Buscar imports existentes y agregar los nuevos
    if "from PyQt6.QtWidgets import" in contenido:
        pos_imports = contenido.find("from PyQt6.QtWidgets import")
        contenido = contenido[:pos_imports] + imports_nuevos + "\n" + contenido[pos_imports:]
    
    # ================================
    # PARCHE 2: Agregar método debug_camera_connection
    # ================================
    metodo_debug_connection = '''
    def debug_camera_connection(self, cam_data):
        """Ejecutar diagnóstico detallado de una cámara específica"""
        ip = cam_data.get('ip', 'N/A')
        rtsp_url = cam_data.get('rtsp', '')
        
        self.append_debug(f"🔍 Iniciando diagnóstico para {ip}...")
        
        # Verificar datos básicos
        self.append_debug(f"📝 IP: {ip}")
        self.append_debug(f"👤 Usuario: {cam_data.get('usuario', 'N/A')}")
        self.append_debug(f"📺 Canal: {cam_data.get('canal', 'N/A')}")
        self.append_debug(f"🔗 URL: {rtsp_url}")
        
        # Thread para no bloquear la UI
        def run_diagnosis():
            try:
                # 1. Ping test
                self.append_debug(f"📡 Probando conectividad...")
                if self._test_ping(ip):
                    self.append_debug(f"✅ Ping exitoso a {ip}")
                else:
                    self.append_debug(f"❌ No se puede hacer ping a {ip}")
                
                # 2. Puerto RTSP
                puerto = int(cam_data.get('puerto', 554))
                self.append_debug(f"🔌 Probando puerto {puerto}...")
                if self._test_port(ip, puerto):
                    self.append_debug(f"✅ Puerto {puerto} accesible")
                else:
                    self.append_debug(f"❌ Puerto {puerto} no accesible")
                
                # 3. Test RTSP con OpenCV
                if rtsp_url:
                    self.append_debug(f"📹 Probando stream RTSP...")
                    success, frames, error = self._test_rtsp_stream(rtsp_url)
                    if success:
                        self.append_debug(f"✅ Stream RTSP funcional - {frames} frames recibidos")
                    else:
                        self.append_debug(f"❌ Error en stream RTSP: {error}")
                else:
                    self.append_debug(f"⚠️ URL RTSP no configurada")
                    
            except Exception as e:
                self.append_debug(f"❌ Error en diagnóstico: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_diagnosis, daemon=True)
        thread.start()
    
    def _test_ping(self, host, timeout=3):
        """Test de ping básico"""
        try:
            import subprocess
            import platform
            
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            result = subprocess.run(['ping', param, '1', host], 
                                  capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0
        except Exception:
            return False
    
    def _test_port(self, host, port, timeout=5):
        """Test de conectividad de puerto"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _test_rtsp_stream(self, rtsp_url, timeout=10):
        """Test de stream RTSP con OpenCV"""
        try:
            cap = cv2.VideoCapture(rtsp_url)
            
            if not cap.isOpened():
                return False, 0, "No se pudo abrir el stream"
            
            frames_count = 0
            start_time = time.time()
            
            while time.time() - start_time < timeout and frames_count < 10:
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames_count += 1
                else:
                    break
                time.sleep(0.1)
            
            cap.release()
            
            if frames_count > 0:
                return True, frames_count, None
            else:
                return False, 0, "No se recibieron frames válidos"
                
        except Exception as e:
            return False, 0, str(e)
'''
    
    # Buscar lugar para insertar el método (antes del último método o al final de la clase)
    if "def closeEvent(self, event):" in contenido:
        pos_insert = contenido.find("def closeEvent(self, event):")
        contenido = contenido[:pos_insert] + metodo_debug_connection + "\n    " + contenido[pos_insert:]
    else:
        # Buscar el final de la clase MainWindow
        pos_class_end = contenido.rfind("class MainWindow")
        if pos_class_end != -1:
            # Encontrar el final de la clase
            lines = contenido[pos_class_end:].split('\n')
            insert_pos = pos_class_end
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith(' ') and not line.startswith('\t') and i > 10:
                    insert_pos = pos_class_end + len('\n'.join(lines[:i]))
                    break
            contenido = contenido[:insert_pos] + metodo_debug_connection + "\n" + contenido[insert_pos:]
    
    # ================================
    # PARCHE 3: Modificar setup_menu para agregar debug
    # ================================
    menu_debug_patch = '''
        # ✅ MENU DEBUG RTSP
        debug_menu = menubar.addMenu("🔍 Debug")
        
        test_all_action = debug_menu.addAction("📊 Probar Todas las Cámaras")
        test_all_action.triggered.connect(self.test_all_cameras)
        
        monitor_action = debug_menu.addAction("📺 Monitor RTSP en Vivo")
        monitor_action.triggered.connect(self.open_rtsp_monitor)
        
        debug_menu.addSeparator()
        
        connection_action = debug_menu.addAction("🔍 Diagnóstico de Conexión")
        connection_action.triggered.connect(self.open_connection_diagnostics)
'''
    
    # Buscar el final de setup_menu y agregar el menú debug
    if "def setup_menu(self):" in contenido:
        # Encontrar el final del método setup_menu
        pos_setup_menu = contenido.find("def setup_menu(self):")
        lines = contenido[pos_setup_menu:].split('\n')
        
        # Buscar el final del método (siguiente def o final del contenido)
        method_end = pos_setup_menu
        for i, line in enumerate(lines[1:], 1):
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if line.strip().startswith('def '):
                    method_end = pos_setup_menu + len('\n'.join(lines[:i]))
                    break
        
        # Insertar el menú debug antes del final del método
        contenido = contenido[:method_end-1] + menu_debug_patch + "\n" + contenido[method_end:]
    
    # ================================
    # PARCHE 4: Agregar métodos para el menú debug
    # ================================
    metodos_debug_menu = '''
    def test_all_cameras(self):
        """Probar conectividad de todas las cámaras"""
        self.append_debug("🚀 Iniciando test de todas las cámaras...")
        
        if not self.camera_data_list:
            self.append_debug("❌ No hay cámaras configuradas")
            return
        
        def run_tests():
            success_count = 0
            total_count = len(self.camera_data_list)
            
            for i, cam_data in enumerate(self.camera_data_list, 1):
                ip = cam_data.get('ip', f'cam_{i}')
                self.append_debug(f"🔍 [{i}/{total_count}] Probando {ip}...")
                
                try:
                    # Test básico de conectividad
                    if self._test_ping(ip):
                        self.append_debug(f"  ✅ Ping OK")
                        
                        # Test puerto RTSP
                        puerto = int(cam_data.get('puerto', 554))
                        if self._test_port(ip, puerto):
                            self.append_debug(f"  ✅ Puerto {puerto} OK")
                            
                            # Test stream RTSP
                            rtsp_url = cam_data.get('rtsp')
                            if rtsp_url:
                                success, frames, error = self._test_rtsp_stream(rtsp_url, timeout=5)
                                if success:
                                    self.append_debug(f"  ✅ Stream OK ({frames} frames)")
                                    success_count += 1
                                else:
                                    self.append_debug(f"  ❌ Stream Error: {error}")
                            else:
                                self.append_debug(f"  ⚠️ URL RTSP no configurada")
                        else:
                            self.append_debug(f"  ❌ Puerto {puerto} no accesible")
                    else:
                        self.append_debug(f"  ❌ No hay conectividad de red")
                        
                except Exception as e:
                    self.append_debug(f"  ❌ Error: {e}")
                
                time.sleep(0.5)  # Pausa entre tests
            
            self.append_debug(f"📊 RESULTADO: {success_count}/{total_count} cámaras funcionando")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_tests, daemon=True)
        thread.start()
    
    def open_rtsp_monitor(self):
        """Abrir monitor RTSP en tiempo real"""
        if not RTSP_MONITOR_AVAILABLE:
            self.append_debug("❌ Monitor RTSP no disponible - falta rtsp_monitor.py")
            return
        
        try:
            if not hasattr(self, 'rtsp_monitor_widget'):
                self.rtsp_monitor_widget = RTSPMonitorWidget(self.camera_data_list, self)
            
            self.rtsp_monitor_widget.show()
            self.rtsp_monitor_widget.raise_()
            self.append_debug("📺 Monitor RTSP abierto")
            
        except Exception as e:
            self.append_debug(f"❌ Error abriendo monitor RTSP: {e}")
    
    def open_connection_diagnostics(self):
        """Abrir diálogo de diagnósticos de conexión"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QTextEdit, QLabel
            
            class ConnectionDiagDialog(QDialog):
                def __init__(self, camera_list, parent=None):
                    super().__init__(parent)
                    self.camera_list = camera_list
                    self.parent_window = parent
                    self.setWindowTitle("🔍 Diagnóstico de Conexión")
                    self.setFixedSize(600, 400)
                    self.setup_ui()
                
                def setup_ui(self):
                    layout = QVBoxLayout(self)
                    
                    # Selector de cámara
                    selector_layout = QHBoxLayout()
                    selector_layout.addWidget(QLabel("Cámara:"))
                    
                    self.camera_combo = QComboBox()
                    for i, cam in enumerate(self.camera_list):
                        ip = cam.get('ip', f'Cámara {i+1}')
                        name = cam.get('nombre', ip)
                        self.camera_combo.addItem(f"{name} ({ip})")
                    
                    selector_layout.addWidget(self.camera_combo)
                    
                    self.diagnose_btn = QPushButton("🔍 Diagnosticar")
                    self.diagnose_btn.clicked.connect(self.run_diagnosis)
                    selector_layout.addWidget(self.diagnose_btn)
                    
                    layout.addLayout(selector_layout)
                    
                    # Área de resultados
                    self.result_text = QTextEdit()
                    self.result_text.setReadOnly(True)
                    layout.addWidget(self.result_text)
                    
                    # Botones
                    button_layout = QHBoxLayout()
                    button_layout.addStretch()
                    
                    close_btn = QPushButton("Cerrar")
                    close_btn.clicked.connect(self.close)
                    button_layout.addWidget(close_btn)
                    
                    layout.addLayout(button_layout)
                
                def run_diagnosis(self):
                    selected_index = self.camera_combo.currentIndex()
                    if selected_index < 0:
                        return
                    
                    cam_data = self.camera_list[selected_index]
                    self.result_text.clear()
                    self.result_text.append("🔍 Iniciando diagnóstico...\n")
                    
                    # Ejecutar diagnóstico en la ventana principal
                    if self.parent_window:
                        self.parent_window.debug_camera_connection(cam_data)
                        self.result_text.append("📋 Revisa la consola de debug para resultados detallados")
            
            dialog = ConnectionDiagDialog(self.camera_data_list, self)
            dialog.exec()
            
        except Exception as e:
            self.append_debug(f"❌ Error abriendo diagnósticos: {e}")
'''
    
    # Insertar métodos al final de la clase
    if "def closeEvent(self, event):" in contenido:
        pos_insert = contenido.find("def closeEvent(self, event):")
        contenido = contenido[:pos_insert] + metodos_debug_menu + "\n    " + contenido[pos_insert:]
    
    # ================================
    # PARCHE 5: Agregar import time al inicio
    # ================================
    if "import time" not in contenido:
        contenido = "import time\n" + contenido
    
    # Escribir archivo modificado
    with open(archivo_main, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ MainWindow actualizado con debug RTSP")
    return True


def crear_script_aplicar_debug():
    """Crear script principal para aplicar todos los parches de debug"""
    
    script_content = '''#!/usr/bin/env python3
# ========================================================================================
# SCRIPT PRINCIPAL: aplicar_debug_completo.py
# Aplica todos los parches de debug para diagnóstico de cámaras
# ========================================================================================

import os
import sys
from datetime import datetime

def main():
    """Función principal para aplicar debug completo"""
    print("🚀 APLICANDO DEBUG COMPLETO PARA CÁMARAS")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    archivos_requeridos = [
        "ui/main_window.py",
        "gui/visualizador_detector.py", 
        "gui/grilla_widget.py"
    ]
    
    missing_files = [f for f in archivos_requeridos if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Error: No se encontraron archivos requeridos:")
        for f in missing_files:
            print(f"   • {f}")
        print("\\nAsegúrate de ejecutar este script desde el directorio raíz del proyecto.")
        return False
    
    success_count = 0
    
    # 1. Aplicar debug mejorado para cámaras
    print("\\n🔧 1. Aplicando debug mejorado para cámaras...")
    try:
        from debug_camera_enhanced import aplicar_debug_camara
        aplicar_debug_camara()
        success_count += 1
        print("   ✅ Debug de cámaras aplicado")
    except Exception as e:
        print(f"   ❌ Error aplicando debug de cámaras: {e}")
    
    # 2. Aplicar parche a MainWindow
    print("\\n🔧 2. Aplicando parche a MainWindow...")
    try:
        from main_window_rtsp_debug_patch import aplicar_parche_main_window
        if aplicar_parche_main_window():
            success_count += 1
            print("   ✅ MainWindow actualizado")
        else:
            print("   ❌ Error aplicando parche a MainWindow")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Verificar archivos creados
    print("\\n🔧 3. Verificando archivos de debug...")
    archivos_debug = [
        "rtsp_monitor.py",
        "diagnostico_camaras.py", 
        "debug_camera_enhanced.py",
        "main_window_rtsp_debug_patch.py"
    ]
    
    for archivo in archivos_debug:
        if os.path.exists(archivo):
            print(f"   ✅ {archivo}")
        else:
            print(f"   ⚠️ {archivo} no encontrado")
    
    # 4. Resultados finales
    print("\\n" + "=" * 60)
    print("📊 RESUMEN DE APLICACIÓN:")
    print(f"   ✅ Parches aplicados: {success_count}/2")
    
    if success_count == 2:
        print("\\n🎉 DEBUG APLICADO EXITOSAMENTE")
        print("\\n📋 PRÓXIMOS PASOS:")
        print("   1. Reinicia la aplicación principal")
        print("   2. Ve al menú '🔍 Debug' para nuevas opciones")
        print("   3. Usa 'Probar Todas las Cámaras' para test rápido")
        print("   4. Usa 'Monitor RTSP en Vivo' para monitoreo continuo")
        print("   5. Revisa la consola para mensajes de debug detallados")
        print("\\n🔍 DIAGNÓSTICO MANUAL:")
        print("   • Ejecuta: python diagnostico_camaras.py")
        print("   • Ejecuta: python rtsp_monitor.py")
        print("\\n📝 LOGS MEJORADOS:")
        print("   • Información de conexión RTSP detallada")
        print("   • Estado de frames en tiempo real")
        print("   • Diagnóstico automático de errores")
        
    else:
        print("\\n⚠️ APLICACIÓN PARCIAL")
        print("Algunos parches no se pudieron aplicar completamente.")
        print("Revisa los errores anteriores y ejecuta manualmente si es necesario.")
    
    return success_count == 2

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⏹️ Cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Error inesperado: {e}")
        sys.exit(1)
'''
    
    with open("aplicar_debug_completo.py", 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script principal creado: aplicar_debug_completo.py")


def crear_guia_uso():
    """Crear guía de uso para el debug de cámaras"""
    
    guia_content = '''# 🔍 GUÍA DE USO - DEBUG DE CÁMARAS

## 📋 Resumen
Esta guía explica cómo usar las nuevas herramientas de debug para diagnosticar problemas de cámaras que muestran "sin señal".

## 🚀 Aplicación Rápida

### 1. Aplicar Debug Automáticamente
```bash
python aplicar_debug_completo.py
```

### 2. Reiniciar la Aplicación
Después de aplicar los parches, reinicia tu aplicación principal.

## 🔍 Herramientas de Diagnóstico

### A. Menú Debug en la Aplicación
Después de aplicar los parches, encontrarás un nuevo menú "🔍 Debug" con:

1. **📊 Probar Todas las Cámaras**
   - Test rápido de conectividad
   - Verifica ping, puertos y streams RTSP
   - Resultados en la consola de debug

2. **📺 Monitor RTSP en Vivo**
   - Monitoreo continuo de streams
   - Estadísticas de FPS en tiempo real
   - Detección automática de desconexiones

3. **🔍 Diagnóstico de Conexión**
   - Diagnóstico individual por cámara
   - Análisis detallado de problemas

### B. Herramientas de Línea de Comandos

#### 1. Diagnóstico Completo
```bash
python diagnostico_camaras.py
```
- Analiza todas las cámaras configuradas
- Verifica conectividad de red
- Prueba autenticación y streams RTSP

#### 2. Monitor RTSP Individual
```bash
python rtsp_monitor.py rtsp://usuario:pass@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0 30
```
- Monitorea una cámara específica por 30 segundos
- Muestra estadísticas de frames y FPS

#### 3. Monitor Interactivo
```bash
python rtsp_monitor.py
```
- Interfaz interactiva para seleccionar modo
- Opción para probar todas las cámaras

## 📊 Interpretación de Resultados

### ✅ Señales Positivas
- `✅ Ping exitoso`: Red funcionando
- `✅ Puerto 554 accesible`: Servicio RTSP activo
- `✅ Stream RTSP funcional`: Cámara transmitiendo
- `✅ X frames recibidos`: Stream estable

### ❌ Señales de Problema
- `❌ No se puede hacer ping`: Problema de red o IP incorrecta
- `❌ Puerto 554 no accesible`: Servicio RTSP apagado/bloqueado
- `❌ No se pudo abrir stream`: URL incorrecta o credenciales inválidas
- `❌ No se recibieron frames`: Stream conecta pero no transmite

### ⚠️ Señales de Advertencia
- `⚠️ URL RTSP no configurada`: Falta configuración
- `⚠️ Stream interrumpido`: Conexión inestable
- `⚠️ FPS bajo`: Possible problema de ancho de banda

## 🔧 Debug Mejorado en Logs

Los nuevos logs incluyen:

### Estados de Conexión
```
🎬 [Visualizador_192.168.1.100] Estado reproducción: PlayingState
📺 [Visualizador_192.168.1.100] Estado media: BufferedMedia
✅ [Visualizador_192.168.1.100] STREAM ACTIVO - Recibiendo datos
```

### Información de Frames
```
📷 [Visualizador_192.168.1.100] Frame #100: 1920x1080, Formato: 25
🤖 [Visualizador_192.168.1.100] Detectores activos: 2/2
```

### Errores Detallados
```
❌ [Visualizador_192.168.1.100] MEDIA INVÁLIDO - URL incorrecta o stream no disponible
⛔ [Visualizador_192.168.1.100] STREAM DETENIDO - Verificar conexión
```

## 🛠️ Solución de Problemas Comunes

### Problema: "Sin señal" en cámaras
1. Ejecutar `python diagnostico_camaras.py`
2. Verificar resultados del ping y puerto
3. Si el ping falla: verificar IP y conectividad de red
4. Si el puerto falla: verificar que el servicio RTSP esté activo
5. Si el stream falla: verificar URL y credenciales

### Problema: Stream se conecta pero no muestra video
1. Usar monitor RTSP para verificar frames
2. Verificar que el canal y perfil sean correctos
3. Probar diferentes perfiles (main/sub)
4. Verificar ancho de banda de red

### Problema: Conexión intermitente
1. Usar "Monitor RTSP en Vivo" para monitoreo continuo
2. Verificar estabilidad de red
3. Ajustar configuración de FPS
4. Verificar carga del servidor de cámaras

## 📋 Checklist de Verificación

### Antes de Reportar Problemas
- [ ] Aplicado debug completo con `aplicar_debug_completo.py`
- [ ] Ejecutado `diagnostico_camaras.py`
- [ ] Revisado logs de debug en la aplicación
- [ ] Probado monitor RTSP individual
- [ ] Verificado conectividad de red básica
- [ ] Confirmado credenciales de cámara

### Información para Soporte
Cuando reportes problemas, incluye:
1. Resultado completo de `diagnostico_camaras.py`
2. Logs de debug de la aplicación
3. Modelo de cámara y configuración de red
4. Información del servidor/NVR si aplica

## 🎯 Próximos Pasos

Después de aplicar el debug:
1. Reinicia la aplicación
2. Prueba las nuevas herramientas de debug
3. Identifica patrones en los errores
4. Ajusta configuración según los resultados
5. Monitorea estabilidad con las nuevas herramientas

---
📞 **¿Necesitas ayuda?** Comparte los resultados del diagnóstico para análisis detallado.
'''
    
    with open("GUIA_DEBUG_CAMARAS.md", 'w', encoding='utf-8') as f:
        f.write(guia_content)
    
    print("✅ Guía de uso creada: GUIA_DEBUG_CAMARAS.md")


if __name__ == "__main__":
    print("🔧 Creando herramientas de debug para MainWindow...")
    
    try:
        # Aplicar parche a MainWindow
        if aplicar_parche_main_window():
            print("✅ Parche aplicado exitosamente")
        else:
            print("❌ Error aplicando parche")
        
        # Crear script principal
        crear_script_aplicar_debug()
        
        # Crear guía de uso
        crear_guia_uso()
        
        print("\n🎉 HERRAMIENTAS DE DEBUG CREADAS")
        print("📋 Archivos generados:")
        print("   • aplicar_debug_completo.py - Script principal")
        print("   • GUIA_DEBUG_CAMARAS.md - Guía de uso")
        print("\n🚀 Ejecuta: python aplicar_debug_completo.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()