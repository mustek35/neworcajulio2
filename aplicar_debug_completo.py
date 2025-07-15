#!/usr/bin/env python3
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
        print("\nAsegúrate de ejecutar este script desde el directorio raíz del proyecto.")
        return False
    
    success_count = 0
    
    # 1. Aplicar debug mejorado para cámaras
    print("\n🔧 1. Aplicando debug mejorado para cámaras...")
    try:
        from debug_camera_enhanced import aplicar_debug_camara
        aplicar_debug_camara()
        success_count += 1
        print("   ✅ Debug de cámaras aplicado")
    except Exception as e:
        print(f"   ❌ Error aplicando debug de cámaras: {e}")
    
    # 2. Aplicar parche a MainWindow
    print("\n🔧 2. Aplicando parche a MainWindow...")
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
    print("\n🔧 3. Verificando archivos de debug...")
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
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE APLICACIÓN:")
    print(f"   ✅ Parches aplicados: {success_count}/2")
    
    if success_count == 2:
        print("\n🎉 DEBUG APLICADO EXITOSAMENTE")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Reinicia la aplicación principal")
        print("   2. Ve al menú '🔍 Debug' para nuevas opciones")
        print("   3. Usa 'Probar Todas las Cámaras' para test rápido")
        print("   4. Usa 'Monitor RTSP en Vivo' para monitoreo continuo")
        print("   5. Revisa la consola para mensajes de debug detallados")
        print("\n🔍 DIAGNÓSTICO MANUAL:")
        print("   • Ejecuta: python diagnostico_camaras.py")
        print("   • Ejecuta: python rtsp_monitor.py")
        print("\n📝 LOGS MEJORADOS:")
        print("   • Información de conexión RTSP detallada")
        print("   • Estado de frames en tiempo real")
        print("   • Diagnóstico automático de errores")
        
    else:
        print("\n⚠️ APLICACIÓN PARCIAL")
        print("Algunos parches no se pudieron aplicar completamente.")
        print("Revisa los errores anteriores y ejecuta manualmente si es necesario.")
    
    return success_count == 2

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
