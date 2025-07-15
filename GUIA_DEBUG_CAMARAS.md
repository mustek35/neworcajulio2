# 🔍 GUÍA DE USO - DEBUG DE CÁMARAS

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
