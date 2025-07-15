# ========================================================================================
# ARCHIVO: diagnostico_camaras_corregido.py
# Diagnóstico completo de cámaras - Compatible con tu estructura de proyecto
# ========================================================================================

import cv2
import json
import os
import requests
from urllib.parse import urlparse
import socket
import threading
import time
import subprocess
import platform

def cargar_camaras():
    """
    Cargar cámaras desde los archivos de configuración disponibles
    """
    camaras = []
    
    # Método 1: Intentar cargar desde config.json (usado por camera_manager.py)
    if os.path.exists("config.json"):
        try:
            with open("config.json", 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                camaras_config = config_data.get("camaras", [])
                if camaras_config:
                    print(f"📁 Cargadas {len(camaras_config)} cámaras desde config.json")
                    return camaras_config
        except Exception as e:
            print(f"⚠️ Error leyendo config.json: {e}")
    
    # Método 2: Intentar cargar desde camaras_config.json 
    if os.path.exists("camaras_config.json"):
        try:
            with open("camaras_config.json", 'r', encoding='utf-8') as f:
                camaras_config = json.load(f)
                if camaras_config:
                    print(f"📁 Cargadas {len(camaras_config)} cámaras desde camaras_config.json")
                    return camaras_config
        except Exception as e:
            print(f"⚠️ Error leyendo camaras_config.json: {e}")
    
    # Método 3: Intentar con el camera_manager del proyecto
    try:
        import sys
        sys.path.insert(0, '.')
        from ui.camera_manager import CONFIG_PATH
        
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                camaras_config = data.get("camaras", [])
                if camaras_config:
                    print(f"📁 Cargadas {len(camaras_config)} cámaras desde {CONFIG_PATH}")
                    return camaras_config
    except Exception as e:
        print(f"⚠️ Error importando camera_manager: {e}")
    
    print("❌ No se encontraron archivos de configuración de cámaras")
    print("💡 Archivos esperados:")
    print("   • config.json")
    print("   • camaras_config.json")
    return []

def generar_rtsp_url(cam_data):
    """
    Generar URL RTSP basada en los datos de la cámara con codificación correcta
    """
    import urllib.parse
    
    ip = cam_data.get('ip')
    usuario = cam_data.get('usuario', 'admin')
    contrasena = cam_data.get('contrasena', '')
    canal = cam_data.get('canal', '1')
    tipo = cam_data.get('tipo', 'fija')
    puerto_rtsp = cam_data.get('puerto_rtsp', cam_data.get('puerto', 554))
    perfil = cam_data.get('perfil', 'main')
    
    # Si ya tiene URL RTSP, usarla
    if 'rtsp' in cam_data and cam_data['rtsp']:
        return cam_data['rtsp']
    
    # ✅ CODIFICAR CREDENCIALES CORRECTAMENTE
    usuario_encoded = urllib.parse.quote(usuario, safe='')
    contrasena_encoded = urllib.parse.quote(contrasena, safe='')
    
    # Construir URL según el tipo
    if tipo == "nvr":
        if perfil == "main":
            perfil_id = "s0"
        elif perfil == "sub":
            perfil_id = "s1"
        elif perfil == "low":
            perfil_id = "s3"
        else:
            perfil_id = "s1"
        return f"rtsp://{usuario_encoded}:{contrasena_encoded}@{ip}:{puerto_rtsp}/unicast/c{canal}/{perfil_id}/live"
    else:
        # Cámara IP estándar
        perfil_suffix = "" if perfil == 'main' else "2"
        return f"rtsp://{usuario_encoded}:{contrasena_encoded}@{ip}:{puerto_rtsp}/Streaming/Channels/{canal}0{perfil_suffix}"

def diagnosticar_camara(cam_data):
    """
    Ejecuta un diagnóstico completo de una cámara
    """
    ip = cam_data.get('ip', 'N/A')
    nombre = cam_data.get('nombre', ip)
    
    print(f"\n🔍 DIAGNÓSTICO PARA: {nombre} ({ip})")
    print("=" * 60)
    
    puerto_http = cam_data.get('puerto', 80)
    puerto_rtsp = cam_data.get('puerto_rtsp', 554)
    usuario = cam_data.get('usuario', 'admin')
    contrasena = cam_data.get('contrasena', '')
    
    # Generar URL RTSP
    rtsp_url = generar_rtsp_url(cam_data)
    
    print(f"📝 Información:")
    print(f"   • IP: {ip}")
    print(f"   • Tipo: {cam_data.get('tipo', 'N/A')}")
    print(f"   • Canal: {cam_data.get('canal', 'N/A')}")
    print(f"   • Usuario: {usuario}")
    print(f"   • Puerto HTTP: {puerto_http}")
    print(f"   • Puerto RTSP: {puerto_rtsp}")
    print(f"   • URL RTSP: {rtsp_url}")
    
    resultados = {}
    
    # 1. Verificar conectividad de red
    print(f"\n📡 1. Verificando conectividad de red...")
    ping_ok = verificar_ping(ip)
    resultados['ping'] = ping_ok
    if ping_ok:
        print(f"   ✅ Ping exitoso a {ip}")
    else:
        print(f"   ❌ No se puede hacer ping a {ip}")
    
    # 2. Verificar puerto HTTP
    print(f"\n🌐 2. Verificando puerto HTTP {puerto_http}...")
    http_ok = verificar_puerto(ip, puerto_http)
    resultados['puerto_http'] = http_ok
    if http_ok:
        print(f"   ✅ Puerto HTTP {puerto_http} accesible")
    else:
        print(f"   ❌ Puerto HTTP {puerto_http} no accesible")
    
    # 3. Verificar puerto RTSP
    print(f"\n📹 3. Verificando puerto RTSP {puerto_rtsp}...")
    rtsp_port_ok = verificar_puerto(ip, puerto_rtsp)
    resultados['puerto_rtsp'] = rtsp_port_ok
    if rtsp_port_ok:
        print(f"   ✅ Puerto RTSP {puerto_rtsp} accesible")
    else:
        print(f"   ❌ Puerto RTSP {puerto_rtsp} no accesible")
    
    # 4. Verificar autenticación HTTP (si disponible)
    print(f"\n🔐 4. Verificando autenticación HTTP...")
    auth_result = verificar_auth_http(ip, puerto_http, usuario, contrasena)
    resultados['auth_http'] = auth_result
    
    # 5. Probar conexión RTSP con OpenCV
    print(f"\n🎥 5. Probando conexión RTSP...")
    rtsp_result = probar_rtsp_opencv(rtsp_url)
    resultados['rtsp_stream'] = rtsp_result
    
    # 6. Verificar formato de URL
    print(f"\n🔗 6. Verificando formato de URL RTSP...")
    verificar_formato_url(rtsp_url)
    
    # Resumen de resultados
    print(f"\n📊 RESUMEN PARA {nombre}:")
    success_count = sum([
        resultados['ping'],
        resultados['puerto_rtsp'],
        resultados['rtsp_stream']['success'] if isinstance(resultados['rtsp_stream'], dict) else False
    ])
    
    if success_count >= 2:
        print(f"   ✅ Estado: FUNCIONAL ({success_count}/3 tests pasados)")
    elif success_count == 1:
        print(f"   ⚠️ Estado: PROBLEMAS ({success_count}/3 tests pasados)")
    else:
        print(f"   ❌ Estado: NO FUNCIONAL ({success_count}/3 tests pasados)")
    
    return resultados

def verificar_ping(host, timeout=3):
    """Verificar si el host responde a ping"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        result = subprocess.run(['ping', param, '1', host], 
                              capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0
    except Exception:
        return False

def verificar_puerto(host, puerto, timeout=5):
    """Verificar si un puerto está abierto"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, puerto))
        sock.close()
        return result == 0
    except Exception:
        return False

def verificar_auth_http(ip, puerto, usuario, contrasena):
    """Verificar autenticación HTTP básica"""
    urls_prueba = [
        f"http://{ip}:{puerto}/",
        f"http://{ip}:{puerto}/cgi-bin/snapshot.cgi",
        f"http://{ip}:{puerto}/web/",
    ]
    
    for url in urls_prueba:
        try:
            response = requests.get(url, auth=(usuario, contrasena), timeout=5)
            print(f"   🌐 {url} → Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Autenticación HTTP exitosa")
                return True
            elif response.status_code == 401:
                print(f"   ⚠️ Credenciales rechazadas (401)")
            elif response.status_code == 404:
                print(f"   ℹ️ Ruta no encontrada (404)")
            else:
                print(f"   ❓ Respuesta inesperada: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout en: {url}")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Error de conexión: {url}")
        except Exception as e:
            print(f"   ❓ Error: {e}")
    
    return False

def probar_rtsp_opencv(rtsp_url, timeout=15):
    """Probar conexión RTSP usando OpenCV"""
    print(f"   🎥 Conectando a: {rtsp_url[:50]}{'...' if len(rtsp_url) > 50 else ''}")
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print(f"   ❌ OpenCV no pudo abrir el stream RTSP")
            return {'success': False, 'error': 'No se pudo abrir stream', 'frames': 0}
        
        print(f"   ✅ Conexión RTSP establecida")
        
        # Intentar leer frames
        frames_leidos = 0
        frames_validos = 0
        inicio = time.time()
        errores_consecutivos = 0
        
        while time.time() - inicio < timeout and frames_leidos < 10 and errores_consecutivos < 5:
            ret, frame = cap.read()
            frames_leidos += 1
            
            if ret and frame is not None:
                frames_validos += 1
                errores_consecutivos = 0
                height, width = frame.shape[:2]
                print(f"   📷 Frame {frames_validos}: {width}x{height}")
            else:
                errores_consecutivos += 1
                print(f"   ⚠️ Error leyendo frame {frames_leidos}")
            
            time.sleep(0.2)
        
        cap.release()
        
        if frames_validos > 0:
            fps_estimado = frames_validos / (time.time() - inicio)
            print(f"   ✅ Stream funcional: {frames_validos} frames válidos ({fps_estimado:.1f} FPS)")
            return {'success': True, 'frames': frames_validos, 'fps': fps_estimado}
        else:
            print(f"   ❌ No se pudieron leer frames válidos del stream")
            return {'success': False, 'error': 'Sin frames válidos', 'frames': 0}
            
    except Exception as e:
        print(f"   ❌ Error en prueba RTSP: {e}")
        return {'success': False, 'error': str(e), 'frames': 0}

def verificar_formato_url(url):
    """Verificar el formato de la URL RTSP"""
    try:
        parsed = urlparse(url)
        print(f"   📝 Análisis de URL:")
        print(f"      • Esquema: {parsed.scheme}")
        print(f"      • Host: {parsed.hostname}")
        print(f"      • Puerto: {parsed.port or 'default'}")
        print(f"      • Ruta: {parsed.path}")
        print(f"      • Usuario: {parsed.username or 'No especificado'}")
        print(f"      • Contraseña: {'***' if parsed.password else 'No especificada'}")
        
        # Validaciones
        if parsed.scheme != 'rtsp':
            print(f"   ⚠️ Esquema debería ser 'rtsp', encontrado: '{parsed.scheme}'")
        
        if not parsed.hostname:
            print(f"   ❌ No se detectó hostname en la URL")
            
        if not parsed.port:
            print(f"   ℹ️ Puerto no especificado, usando 554 por defecto")
            
    except Exception as e:
        print(f"   ❌ Error analizando URL: {e}")

def diagnosticar_todas_camaras():
    """Ejecutar diagnóstico en todas las cámaras configuradas"""
    print("🔍 DIAGNÓSTICO MASIVO DE CÁMARAS")
    print("=" * 60)
    
    camaras = cargar_camaras()
    
    if not camaras:
        print("❌ No se encontraron cámaras configuradas")
        print("\n💡 Verifica que exista uno de estos archivos:")
        print("   • config.json")
        print("   • camaras_config.json")
        return
    
    print(f"📊 Se analizarán {len(camaras)} cámaras")
    
    resultados_globales = {
        'total': len(camaras),
        'funcionales': 0,
        'con_problemas': 0,
        'no_funcionales': 0,
        'detalles': []
    }
    
    for i, cam in enumerate(camaras, 1):
        print(f"\n{'='*20} CÁMARA {i}/{len(camaras)} {'='*20}")
        
        try:
            resultado = diagnosticar_camara(cam)
            
            # Clasificar resultado
            success_count = sum([
                resultado.get('ping', False),
                resultado.get('puerto_rtsp', False),
                resultado.get('rtsp_stream', {}).get('success', False) if isinstance(resultado.get('rtsp_stream'), dict) else False
            ])
            
            if success_count >= 2:
                resultados_globales['funcionales'] += 1
                estado = 'FUNCIONAL'
            elif success_count == 1:
                resultados_globales['con_problemas'] += 1
                estado = 'CON_PROBLEMAS'
            else:
                resultados_globales['no_funcionales'] += 1
                estado = 'NO_FUNCIONAL'
            
            resultados_globales['detalles'].append({
                'ip': cam.get('ip', 'N/A'),
                'nombre': cam.get('nombre', 'Sin nombre'),
                'estado': estado,
                'resultado': resultado
            })
            
        except Exception as e:
            print(f"❌ Error diagnosticando cámara: {e}")
            resultados_globales['no_funcionales'] += 1
        
        if i < len(camaras):
            time.sleep(1)  # Pausa entre cámaras
    
    # Reporte final
    print("\n" + "="*60)
    print("📊 REPORTE FINAL DE DIAGNÓSTICO")
    print("="*60)
    
    total = resultados_globales['total']
    funcionales = resultados_globales['funcionales']
    problemas = resultados_globales['con_problemas']
    no_funcionales = resultados_globales['no_funcionales']
    
    print(f"📈 RESUMEN GENERAL:")
    print(f"   • Total de cámaras: {total}")
    print(f"   • ✅ Funcionales: {funcionales} ({funcionales/total*100:.1f}%)")
    print(f"   • ⚠️ Con problemas: {problemas} ({problemas/total*100:.1f}%)")
    print(f"   • ❌ No funcionales: {no_funcionales} ({no_funcionales/total*100:.1f}%)")
    
    print(f"\n📋 DETALLE POR CÁMARA:")
    for detalle in resultados_globales['detalles']:
        estado_emoji = {'FUNCIONAL': '✅', 'CON_PROBLEMAS': '⚠️', 'NO_FUNCIONAL': '❌'}
        emoji = estado_emoji.get(detalle['estado'], '❓')
        print(f"   {emoji} {detalle['nombre']} ({detalle['ip']}) - {detalle['estado']}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if no_funcionales > 0:
        print(f"   🔧 Revisar {no_funcionales} cámaras no funcionales")
    if problemas > 0:
        print(f"   ⚙️ Optimizar {problemas} cámaras con problemas")
    if funcionales == total:
        print(f"   🎉 ¡Todas las cámaras están funcionando correctamente!")

def mostrar_ayuda():
    """Mostrar ayuda del programa"""
    print("🔍 DIAGNÓSTICO DE CÁMARAS")
    print("=" * 40)
    print("Este programa diagnostica el estado de las cámaras configuradas.")
    print("\nUSO:")
    print("   python diagnostico_camaras_corregido.py")
    print("\nARCHIVOS DE CONFIGURACIÓN SOPORTADOS:")
    print("   • config.json")
    print("   • camaras_config.json")
    print("\nQUÉ SE VERIFICA:")
    print("   • Conectividad de red (ping)")
    print("   • Accesibilidad de puertos")
    print("   • Autenticación HTTP")
    print("   • Funcionalidad de stream RTSP")
    print("   • Formato de URLs")

if __name__ == "__main__":
    import sys
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
            mostrar_ayuda()
        else:
            diagnosticar_todas_camaras()
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Diagnóstico cancelado por usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()