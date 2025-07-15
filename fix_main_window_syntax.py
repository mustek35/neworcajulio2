# ========================================================================================
# ARCHIVO: fix_main_window_syntax.py
# Reparador para error de sintaxis en main_window.py
# ========================================================================================

import os
import shutil
from datetime import datetime

def fix_main_window_syntax():
    """
    Repara el error de sintaxis en main_window.py
    """
    print("🔧 Reparando error de sintaxis en main_window.py...")
    
    archivo_main = "ui/main_window.py"
    
    if not os.path.exists(archivo_main):
        print(f"❌ No se encontró {archivo_main}")
        return False
    
    # Crear backup antes de reparar
    backup_file = f"{archivo_main}.backup_syntax_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(archivo_main, backup_file)
    print(f"💾 Backup creado: {backup_file}")
    
    try:
        # Leer contenido actual
        with open(archivo_main, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📄 Total de líneas: {len(lines)}")
        
        # Buscar y reparar líneas con strings sin terminar
        fixed_lines = []
        errors_found = 0
        
        for i, line in enumerate(lines, 1):
            original_line = line
            
            # Detectar strings sin terminar comunes
            if ('self.result_text.append("🔍 Iniciando diagnóstico...' in line and 
                not line.rstrip().endswith('"') and not line.rstrip().endswith('")') and
                not line.rstrip().endswith('")')):
                
                # Reparar esta línea específica
                if line.rstrip().endswith('...'):
                    line = line.rstrip() + '")\n'
                else:
                    line = line.rstrip() + '")\n'
                
                print(f"🔧 Línea {i}: String sin terminar reparado")
                errors_found += 1
            
            # Detectar otros patterns de strings sin terminar
            elif ('"' in line and 
                  line.count('"') % 2 != 0 and 
                  not line.strip().endswith('\\') and
                  not '"""' in line and
                  not "'''" in line):
                
                # Si la línea termina con texto pero sin comillas de cierre
                if (line.rstrip().endswith('...') or 
                    line.rstrip().endswith('diagnóstico') or
                    line.rstrip().endswith('detallados')):
                    
                    line = line.rstrip() + '")\n'
                    print(f"🔧 Línea {i}: String pattern reparado")
                    errors_found += 1
            
            fixed_lines.append(line)
        
        # Escribir archivo reparado
        with open(archivo_main, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"✅ Reparación completada: {errors_found} errores corregidos")
        
        # Verificar sintaxis
        try:
            with open(archivo_main, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, archivo_main, 'exec')
            print("✅ Verificación de sintaxis: OK")
            return True
            
        except SyntaxError as e:
            print(f"❌ Aún hay errores de sintaxis: {e}")
            print(f"   Línea {e.lineno}: {e.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error durante la reparación: {e}")
        return False

def manual_fix_instructions():
    """
    Instrucciones para reparación manual si el automático falla
    """
    print("\n" + "="*60)
    print("🛠️ REPARACIÓN MANUAL ALTERNATIVA")
    print("="*60)
    
    print("\n1. 📝 Abre ui/main_window.py en tu editor de código")
    print("2. 🔍 Ve a la línea 1913 (o cerca)")
    print("3. 🔧 Busca líneas como:")
    print('   self.result_text.append("🔍 Iniciando diagnóstico...')
    print("4. ✅ Agrégale la comilla de cierre:")
    print('   self.result_text.append("🔍 Iniciando diagnóstico...")')
    
    print("\n🔍 PATRONES A BUSCAR Y CORREGIR:")
    print('   • Líneas que terminan con: append("texto...')
    print('   • Líneas que terminan con: f"texto...')
    print('   • Cualquier string que no tenga comilla de cierre')
    
    print("\n💡 CONSEJO:")
    print("   • Usa Ctrl+F para buscar: append(\"")
    print("   • Verifica que cada string tenga comillas balanceadas")
    print("   • Guarda y prueba ejecutar la app nuevamente")

def restore_from_backup():
    """
    Restaurar desde backup más reciente
    """
    print("\n🔄 OPCIÓN: RESTAURAR DESDE BACKUP")
    print("-" * 40)
    
    # Buscar backups
    backups = []
    for file in os.listdir("."):
        if file.startswith("main_window.py.backup"):
            backups.append(file)
    
    if not backups:
        print("❌ No se encontraron backups automáticos")
        return False
    
    # Ordenar por fecha (más reciente primero)
    backups.sort(reverse=True)
    
    print("📁 Backups encontrados:")
    for i, backup in enumerate(backups[:5], 1):  # Mostrar solo los 5 más recientes
        print(f"   {i}. {backup}")
    
    print(f"\n¿Restaurar desde {backups[0]}? (s/N): ", end="")
    response = input().strip().lower()
    
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            shutil.copy2(backups[0], "ui/main_window.py")
            print(f"✅ Restaurado desde {backups[0]}")
            return True
        except Exception as e:
            print(f"❌ Error restaurando: {e}")
            return False
    
    return False

def main():
    """
    Función principal del reparador
    """
    print("🚨 REPARADOR DE ERROR DE SINTAXIS")
    print("=" * 50)
    print("Error detectado: SyntaxError en ui/main_window.py línea 1913")
    print("Causa probable: String literal sin terminar durante aplicación de parches")
    
    print("\n🔧 OPCIONES DE REPARACIÓN:")
    print("1. 🤖 Reparación automática")
    print("2. 🔄 Restaurar desde backup")
    print("3. 🛠️ Instrucciones manuales")
    print("4. ❌ Salir")
    
    while True:
        try:
            opcion = input("\nSelecciona opción (1-4): ").strip()
            
            if opcion == "1":
                print("\n🤖 Iniciando reparación automática...")
                if fix_main_window_syntax():
                    print("\n🎉 ¡Reparación exitosa!")
                    print("💡 Prueba ejecutar tu aplicación: python app.py")
                else:
                    print("\n⚠️ La reparación automática no fue completamente exitosa")
                    manual_fix_instructions()
                break
                
            elif opcion == "2":
                print("\n🔄 Restaurando desde backup...")
                if restore_from_backup():
                    print("\n✅ Restauración completada")
                    print("💡 Ahora puedes aplicar los parches de debug manualmente")
                else:
                    print("\n❌ No se pudo restaurar desde backup")
                break
                
            elif opcion == "3":
                manual_fix_instructions()
                break
                
            elif opcion == "4":
                print("\n👋 Saliendo...")
                break
                
            else:
                print("❌ Opción inválida. Usa 1, 2, 3 o 4")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Cancelado por usuario")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break

if __name__ == "__main__":
    main()