"""
Funciones auxiliares y utilidades
"""
import os
import shutil
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def crear_carpetas_necesarias():
    """Crear todas las carpetas necesarias para el sistema"""
    carpetas = [
        'storage/temp_files',
        'storage/backups',
        'storage/sounds',
        'storage/logs',
        'assets/icons',
        'assets/images'
    ]
    
    for carpeta in carpetas:
        os.makedirs(carpeta, exist_ok=True)
    
    print("✅ Carpetas del sistema creadas/verificadas")

def limpiar_archivos_temporales():
    """Limpiar archivos temporales antiguos"""
    try:
        temp_dir = 'storage/temp_files'
        if not os.path.exists(temp_dir):
            return
        
        ahora = datetime.now()
        for archivo in os.listdir(temp_dir):
            archivo_path = os.path.join(temp_dir, archivo)
            if os.path.isfile(archivo_path):
                # Eliminar archivos con más de 1 hora
                tiempo_creacion = datetime.fromtimestamp(os.path.getctime(archivo_path))
                if ahora - tiempo_creacion > timedelta(hours=1):
                    os.remove(archivo_path)
                    logger.info(f"Archivo temporal eliminado: {archivo}")
                    
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {e}")

def calcular_precio(copias, es_color):
    """Calcular precio total basado en copias y tipo de impresión"""
    precio_unitario = 13 if es_color else 10
    return copias * precio_unitario

def formatear_tiempo(segundos):
    """Formatear segundos a formato legible"""
    if segundos < 60:
        return f"{segundos} segundos"
    elif segundos < 3600:
        minutos = segundos // 60
        return f"{minutos} minutos"
    else:
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        return f"{horas}h {minutos}m"

def validar_archivo(nombre_archivo, tamaño_bytes):
    """Validar archivo antes de procesar"""
    # Extensiones permitidas
    extensiones_permitidas = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.xlsx', '.xls'}
    
    # Verificar extensión
    _, extension = os.path.splitext(nombre_archivo)
    if extension.lower() not in extensiones_permitidas:
        return False, f"Tipo de archivo no permitido: {extension}"
    
    # Verificar tamaño (2MB máximo)
    if tamaño_bytes > 2 * 1024 * 1024:
        return False, "El archivo excede el límite de 2MB"
    
    return True, "Archivo válido"

def generar_codigo_pedido():
    """Generar código único para pedido"""
    from datetime import datetime
    return f"PED{datetime.now().strftime('%Y%m%d%H%M%S')}"

def backup_database():
    """Crear backup de la base de datos"""
    try:
        from datetime import datetime
        import shutil
        
        db_original = 'storage/sistema_impresion.db'
        if not os.path.exists(db_original):
            return False
        
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_backup = f'storage/backups/sistema_impresion_backup_{fecha}.db'
        
        shutil.copy2(db_original, db_backup)
        
        # Mantener solo los últimos 7 backups
        backups = sorted([f for f in os.listdir('storage/backups') if f.startswith('sistema_impresion_backup')])
        if len(backups) > 7:
            for old_backup in backups[:-7]:
                os.remove(os.path.join('storage/backups', old_backup))
        
        logger.info(f"Backup creado: {db_backup}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        return False