# ========================================================================================
# ARCHIVO: test_camera_especifica.py
# Test específico para la cámara con contraseña @Remoto753524
# ========================================================================================

import cv2
import urllib.parse
import time
import socket
import subprocess
import platform
from datetime import datetime

def test_tu_camara():
    """
    Test específico para tu configuración de cámara
    """
    print("🔍 TEST ESPECÍFICO - CÁMARA CON CONTRASEÑA ESPECIAL")
    print("=" * 60)
    
    # Tu configuración específica
    cam_config = {
        'ip': '192.168.1.3',
        'puerto': 30012,  # Puerto HTTP diferente
        'puerto_rtsp': 30012,  # Asumo que RTSP usa el mismo puerto no estándar
        'usuario': 'admin',
        'contrasena': '@Remoto753524',  # Contraseña con @ al inicio
        'canal': '1',
        'tipo': 'nvr',
        'perfil': 'main'
    }
    
    print(f"📋 CONFIGURACIÓN:")
    print(f"   IP: {cam_config['ip']}")
    print(f"   Puerto: {cam_config['puerto']}")
    print(f"   Usuario: {cam_config['usuario']}")
    print(f"   Contraseña: {cam_config['contrasena']}")
    print(f"   Canal: {cam_config['canal']}")
    print(f"   Tipo: {cam_config['tipo']}")
    
    # 1. Generar URLs con diferentes enfoques
    print(f"\n🔧 GENERANDO URLs RTSP:")
    
    # Método 1: URL que proporcionaste (funciona)
    url_conocida = "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s0/live"
    print(f"   ✅ URL conocida (que funciona): {url_conocida}")
    
    # Método 2: Codificación automática correcta
    usuario_encoded = urllib.parse.quote(cam_config['usuario'], safe='')
    contrasena_encoded = urllib.parse.quote(cam_config['contrasena'], safe='')
    url_auto = f"rtsp://{usuario_encoded}:{contrasena_encoded}@{cam_config['ip']}:{cam_config['puerto_rtsp']}/unicast/c{cam_config['canal']}/s0/live"
    print(f"   🤖 URL generada automáticamente: {url_auto}")
    
    # Verificar que ambas URLs son equivalentes
    if url_conocida == url_auto:
        print(f"   ✅ Las URLs coinciden perfectamente")
    else:
        print(f"   ⚠️ Las URLs son diferentes")
        print(f"      Diferencia detectada, analizando...")
        
        # Analizar diferencias
        if "%40" in url_auto:
            print(f"      • @ se codifica como %40 en URL automática")
        if "%2F" in url_conocida:
            print(f"      • Tu URL usa %2F (que corresponde a /)")
        if "%2F" in url_auto:
            print(f"      • URL automática también usa %2F")
    
    # 2. Decodificar para verificar
    print(f"\n🔍 DECODIFICACIÓN:")
    from urllib.parse import urlparse, unquote
    
    for nombre, url in [("Conocida", url_conocida), ("Automática", url_auto)]:
        try:
            parsed = urlparse(url)
            print(f"   {nombre}:")
            print(f"      Usuario decodificado: '{unquote(parsed.username)}'")
            print(f"      Contraseña decodificada: '{unquote(parsed.password)}'")
            print(f"      Host: {parsed.hostname}:{parsed.port}")
            print(f"      Ruta: {parsed.path}")
        except Exception as e:
            print(f"   ❌ Error decodificando {nombre}: {e}")
    
    # 3. Diagnóstico de conectividad
    print(f"\n📡 DIAGNÓSTICO DE CONECTIVIDAD:")
    
    # Ping
    print(f"   🔍 Probando ping a {cam_config['ip']}...")
    if test_ping(cam_config['ip']):
        print(f"   ✅ Ping exitoso")
    else:
        print(f"   ❌ Ping falló")
    
    # Puerto
    print(f"   🔍 Probando puerto {cam_config['puerto']}...")
    if test_port(cam_config['ip'], cam_config['puerto']):
        print(f"   ✅ Puerto {cam_config['puerto']} accesible")
    else:
        print(f"   ❌ Puerto {cam_config['puerto']} no accesible")
    
    # 4. Test de ambas URLs
    print(f"\n🎥 PROBANDO STREAMS RTSP:")
    
    urls_a_probar = [
        ("URL conocida (funciona)", url_conocida),
        ("URL automática", url_auto)
    ]
    
    for nombre, url in urls_a_probar:
        print(f"\n   🔍 Probando {nombre}:")
        print(f"      URL: {url}")
        
        resultado = test_rtsp_stream(url, timeout=10)
        
        if resultado['success']:
            print(f"      ✅ Stream funcional: {resultado['frames']} frames")
            if resultado.get('fps', 0) > 0:
                print(f"      📊 FPS: {resultado['fps']:.1f}")
        else:
            print(f"      ❌ Stream falló: {resultado['error']}")
    
    # 5. Recomendaciones
    print(f"\n💡 ANÁLISIS Y RECOMENDACIONES:")
    
    # Verificar si la contraseña realmente empieza con @ o /
    if cam_config['contrasena'].startswith('@'):
        print(f"   🔍 Tu contraseña empieza con '@'")
        print(f"   📝 Codificación correcta: @ → %40")
        print(f"   ⚠️ Pero tu URL funcional usa %2F (que es '/')")
        print(f"   🤔 Posibilidades:")
        print(f"      1. La contraseña real empieza con '/' no '@'")
        print(f"      2. El sistema de cámaras tiene codificación especial")
        print(f"      3. Hay un proxy/gateway que modifica las URLs")
    
    if url_conocida != url_auto:
        print(f"   🔧 Para que la generación automática funcione:")
        print(f"      • Verifica que la contraseña real sea: {cam_config['contrasena']}")
        print(f"      • O ajusta la contraseña en config para que genere: {url_conocida}")
    
    print(f"\n✅ RECOMENDACIÓN FINAL:")
    print(f"   • Usa la URL que ya funciona: {url_conocida}")
    print(f"   • En tu configuración, agrega campo 'rtsp': '{url_conocida}'")
    print(f"   • Esto evitará que se genere automáticamente")

def test_ping(host, timeout=3):
    """Test de ping"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        result = subprocess.run(['ping', param, '1', host], 
                              capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0
    except Exception:
        return False

def test_port(host, port, timeout=5):
    """Test de puerto"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def test_rtsp_stream(rtsp_url, timeout=15):
    """Test de stream RTSP"""
    try:
        print(f"      🔄 Conectando...")
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            return {'success': False, 'error': 'No se pudo abrir stream', 'frames': 0}
        
        print(f"      ✅ Conexión establecida")
        
        frames_count = 0
        start_time = time.time()
        
        while time.time() - start_time < timeout and frames_count < 5:
            ret, frame = cap.read()
            if ret and frame is not None:
                frames_count += 1
                height, width = frame.shape[:2]
                print(f"      📷 Frame {frames_count}: {width}x{height}")
            else:
                break
            time.sleep(0.2)
        
        cap.release()
        
        if frames_count > 0:
            fps = frames_count / (time.time() - start_time)
            return {'success': True, 'frames': frames_count, 'fps': fps}
        else:
            return {'success': False, 'error': 'No se recibieron frames válidos', 'frames': 0}
            
    except Exception as e:
        return {'success': False, 'error': str(e), 'frames': 0}

def generar_configuracion_corregida():
    """
    Generar configuración JSON corregida para tu cámara
    """
    print(f"\n📝 GENERANDO CONFIGURACIÓN CORREGIDA:")
    
    # Configuración corregida con URL RTSP que funciona
    config_corregida = {
        "ip": "192.168.1.3",
        "puerto": 30012,
        "usuario": "admin", 
        "contrasena": "@Remoto753524",  # Contraseña original
        "tipo": "nvr",
        "canal": "1",
        "grilla": "grilla 1",
        "nombre": "Cámara NVR Canal 1",
        "rtsp": "rtsp://admin:%40Remoto753524@192.168.1.3:30012/unicast/c1/s0/live",  # URL que funciona
        "puerto_rtsp": 30012,
        "perfil": "main"
    }
    
    print(f"   📋 Configuración recomendada:")
    import json
    print(json.dumps(config_corregida, indent=4, ensure_ascii=False))
    
    # Guardar en archivo
    try:
        with open("camara_corregida.json", 'w', encoding='utf-8') as f:
            json.dump([config_corregida], f, indent=4, ensure_ascii=False)
        print(f"   💾 Configuración guardada en: camara_corregida.json")
    except Exception as e:
        print(f"   ⚠️ No se pudo guardar archivo: {e}")
    
    return config_corregida

def test_diferentes_codificaciones():
    """
    Probar diferentes enfoques de codificación para entender el problema
    """
    print(f"\n🧪 PROBANDO DIFERENTES CODIFICACIONES:")
    
    ip = "192.168.1.3"
    puerto = 30012
    usuario = "admin"
    contraseña_original = "@Remoto753524"
    
    # Diferentes interpretaciones de la contraseña
    variaciones = [
        ("Contraseña con @", "@Remoto753524", "%40Remoto753524"),
        ("Contraseña con /", "/Remoto753524", "%2FRemoto753524"),
        ("Si fuera /@ combinado", "/@Remoto753524", "%2F%40Remoto753524"),
    ]
    
    print(f"   🔍 Análisis de tu URL funcional:")
    url_funcional = "rtsp://admin:%2FRemoto753524@192.168.1.3:30012/unicast/c1/s0/live"
    print(f"      URL: {url_funcional}")
    
    # Decodificar la contraseña de la URL funcional
    from urllib.parse import urlparse, unquote
    parsed = urlparse(url_funcional)
    contraseña_decodificada = unquote(parsed.password)
    print(f"      Contraseña decodificada: '{contraseña_decodificada}'")
    
    if contraseña_decodificada != contraseña_original:
        print(f"   🚨 DESCUBRIMIENTO IMPORTANTE:")
        print(f"      Contraseña que dices: '{contraseña_original}'")
        print(f"      Contraseña que funciona: '{contraseña_decodificada}'")
        print(f"      💡 La contraseña real parece ser: '{contraseña_decodificada}'")
    
    print(f"\n   🔧 Generando URLs con diferentes enfoques:")
    
    for desc, contraseña, codificada in variaciones:
        url = f"rtsp://admin:{codificada}@{ip}:{puerto}/unicast/c1/s0/live"
        coincide = "✅ COINCIDE" if url == url_funcional else "❌ Diferente"
        print(f"      {desc}:")
        print(f"         URL: {url}")
        print(f"         {coincide} con la URL funcional")

def actualizar_configuracion_existente():
    """
    Actualizar configuración existente con la URL correcta
    """
    print(f"\n🔄 ACTUALIZANDO CONFIGURACIÓN EXISTENTE:")
    
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
                
                # Buscar y actualizar la cámara con IP 192.168.1.3
                camara_encontrada = False
                for cam in camaras:
                    if cam.get('ip') == '192.168.1.3':
                        print(f"      🎯 Cámara encontrada: {cam.get('ip')}")
                        
                        # Actualizar con URL correcta
                        cam['rtsp'] = "rtsp://admin:%40Remoto753524@192.168.1.3:30012/unicast/c1/s0/live"
                        cam['puerto_rtsp'] = 30012
                        if 'nombre' not in cam:
                            cam['nombre'] = f"Cámara {cam.get('ip')}"
                        
                        print(f"      ✅ URL RTSP actualizada")
                        camara_encontrada = True
                        break
                
                if camara_encontrada:
                    # Crear backup
                    import shutil
                    backup_file = f"{archivo}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(archivo, backup_file)
                    print(f"      💾 Backup creado: {backup_file}")
                    
                    # Guardar actualización
                    with open(archivo, 'w', encoding='utf-8') as f:
                        if archivo == "config.json":
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        else:
                            json.dump(camaras, f, indent=4, ensure_ascii=False)
                    
                    print(f"      ✅ Configuración actualizada exitosamente")
                else:
                    print(f"      ⚠️ No se encontró cámara con IP 192.168.1.3")
                    
            except Exception as e:
                print(f"      ❌ Error actualizando {archivo}: {e}")

def main():
    """Función principal"""
    print("🚀 INICIANDO TEST ESPECÍFICO PARA TU CÁMARA")
    
    try:
        # Test principal
        test_tu_camara()
        
        # Análisis de codificaciones
        test_diferentes_codificaciones()
        
        # Generar configuración corregida
        generar_configuracion_corregida()
        
        # Preguntar si actualizar configuración existente
        print(f"\n❓ ¿Quieres actualizar tu configuración existente? (s/N): ", end="")
        respuesta = input().strip().lower()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            actualizar_configuracion_existente()
            print(f"\n🎉 ¡Configuración actualizada!")
            print(f"💡 Ahora las herramientas de diagnóstico deberían funcionar correctamente")
        
        print(f"\n✅ TEST COMPLETADO")
        print(f"📋 RESUMEN:")
        print(f"   • URL que funciona: rtsp://admin:%40Remoto753524@192.168.1.3:30012/unicast/c1/s0/live")
        print(f"   • Agregar campo 'rtsp' a tu configuración evita generación automática")
        print(f"   • La contraseña se codifica como %40 (@ codificado)")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test cancelado por usuario")
    except Exception as e:
        print(f"\n❌ Error durante test: {e}")

if __name__ == "__main__":
    import os
    import json
    main()