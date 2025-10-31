"""
Gestión de impresoras físicas - VERSIÓN MEJORADA CON DETECCIÓN REAL
"""
import os
import logging
import subprocess
import win32print  # Para Windows
from utils.config_loader import CONFIG

logger = logging.getLogger(__name__)

class PrinterManager:
    def __init__(self):
        self.printers = {
            'negro': CONFIG['printers']['negro'],
            'color': CONFIG['printers']['color']
        }
        self.available_printers = self._get_available_printers()
    
    def _get_available_printers(self):
        """Obtener lista de impresoras disponibles en el sistema - MEJORADO"""
        try:
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            available = {}
            
            for printer_info in printers:
                printer_name = printer_info[2]
                logger.info(f"Impresora detectada: {printer_name}")
                
                # Verificar si coincide con nuestras impresoras configuradas
                for printer_type, config_name in self.printers.items():
                    if config_name.lower() in printer_name.lower():
                        # Verificar estado real de la impresora
                        if self._check_printer_ready(printer_name):
                            available[printer_type] = printer_name
                            logger.info(f"✅ Impresora {printer_type} configurada: {printer_name}")
                        else:
                            logger.warning(f"⚠️ Impresora {printer_type} encontrada pero no disponible: {printer_name}")
            
            # Si no encontramos impresoras, mostrar advertencia
            if not available:
                logger.warning("❌ No se encontraron impresoras configuradas disponibles")
                # Configurar impresoras por defecto como no disponibles
                for printer_type in self.printers.keys():
                    available[printer_type] = None
            
            return available
            
        except Exception as e:
            logger.error(f"❌ Error detectando impresoras: {e}")
            # Retornar todas como no disponibles
            return {printer_type: None for printer_type in self.printers.keys()}
    
    def _check_printer_ready(self, printer_name):
        """Verificar si una impresora está realmente disponible"""
        try:
            handle = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(handle, 2)
            win32print.ClosePrinter(handle)
            
            # Verificar estado de la impresora
            status = printer_info['Status']
            
            # Estados que indican problemas
            error_states = {
                win32print.PRINTER_STATUS_OFFLINE,
                win32print.PRINTER_STATUS_ERROR,
                win32print.PRINTER_STATUS_NO_TONER,
                win32print.PRINTER_STATUS_PAPER_OUT,
                win32print.PRINTER_STATUS_PAPER_JAM,
                win32print.PRINTER_STATUS_OUTPUT_BIN_FULL
            }
            
            if status in error_states:
                logger.warning(f"Impresora {printer_name} en estado de error: {status}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error verificando impresora {printer_name}: {e}")
            return False
    
    def check_printer_status(self, printer_type):
        """Verificar estado de una impresora - MEJORADO"""
        try:
            printer_name = self.available_printers.get(printer_type)
            
            if not printer_name:
                return {
                    'disponible': False, 
                    'error': f'Impresora {printer_type} no encontrada o no disponible',
                    'nombre': self.printers[printer_type],
                    'estado': 'NO ENCONTRADA'
                }
            
            # Verificar estado real
            handle = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(handle, 2)
            
            # Mapear estados a texto legible
            status_codes = {
                0: "LISTA",
                1: "PAUSADA", 
                2: "ERROR",
                4: "PENDIENTE ELIMINACIÓN",
                8: "SIN PAPEL",
                16: "PAPEL ATASCADO",
                32: "IMPRIMIENDO",
                64: "PROCESANDO",
                128: "INICIALIZANDO",
                256: "ESPERANDO",
                512: "CALENTANDO",
                1024: "TONER BAJO",
                2048: "SIN TONER",
                4096: "PÁGINA IMPRIMIÉNDOSE",
                8192: "BANDEA DE SALIDA LLENA",
                16384: "MANUAL",
                32768: "PROBLEMA",
                65536: "OFFLINE"
            }
            
            status_text = status_codes.get(printer_info['Status'], "DESCONOCIDO")
            
            status = {
                'disponible': printer_info['Status'] == 0,  # Solo disponible si estado es 0
                'nombre': printer_name,
                'estado': status_text,
                'estado_codigo': printer_info['Status'],
                'trabajos_pendientes': printer_info['cJobs'],
                'detalles': f"{printer_name} - {status_text}"
            }
            
            win32print.ClosePrinter(handle)
            return status
            
        except Exception as e:
            logger.error(f"Error verificando estado de impresora {printer_type}: {e}")
            return {
                'disponible': False, 
                'error': str(e),
                'nombre': self.printers.get(printer_type, 'N/A'),
                'estado': 'ERROR'
            }
    
    def print_file(self, file_path, printer_type, copies=1):
        """Imprimir archivo en la impresora especificada - MEJORADO"""
        try:
            printer_name = self.available_printers.get(printer_type)
            if not printer_name:
                return False, f"Impresora {printer_type} no disponible"
            
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            # Verificar que la impresora esté lista
            status = self.check_printer_status(printer_type)
            if not status['disponible']:
                return False, f"Impresora no disponible: {status['estado']}"
            
            # Preparar trabajo de impresión
            handle = win32print.OpenPrinter(printer_name)
            
            try:
                # Leer archivo como binario
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                
                # Crear trabajo de impresión
                job_info = {
                    "Document": "Impresión Bot", 
                    "DataType": "RAW",
                    "pDatatype": "RAW",
                }
                
                job = win32print.StartDocPrinter(handle, 1, job_info)
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, file_data)
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
                
                logger.info(f"✅ Archivo {file_path} enviado a impresora {printer_name} ({copies} copias)")
                return True, "Impresión enviada correctamente"
                
            except Exception as e:
                return False, f"Error en impresión: {str(e)}"
            finally:
                win32print.ClosePrinter(handle)
                
        except Exception as e:
            logger.error(f"Error general en impresión: {e}")
            return False, f"Error general: {str(e)}"
    
    def get_all_printers_status(self):
        """Obtener estado de todas las impresoras - MEJORADO"""
        status = {}
        for printer_type in ['negro', 'color']:
            status[printer_type] = self.check_printer_status(printer_type)
        return status

# Instancia global
printer_manager = PrinterManager()