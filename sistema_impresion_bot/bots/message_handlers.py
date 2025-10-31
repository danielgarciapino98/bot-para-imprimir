"""
Manejadores específicos para mensajes y archivos del bot
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.operations import db
from database.models import Pedido

logger = logging.getLogger(__name__)

class MessageHandlers:
    def __init__(self):
        self.temp_dir = "storage/temp_files"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar documentos subidos"""
        user_id = update.message.from_user.id
        document = update.message.document
        
        # Verificar si estamos en proceso de subir archivo
        if not context.user_data.get('esperando_archivo'):
            await update.message.reply_text("❌ Por favor, selecciona primero el tipo de archivo desde el menú.")
            return
        
        # Verificar tamaño del archivo (2MB máximo)
        if document.file_size > 2 * 1024 * 1024:
            await update.message.reply_text("❌ El archivo es demasiado grande. Límite: 2MB")
            return
        
        try:
            # Descargar archivo
            file = await document.get_file()
            file_extension = document.file_name.split('.')[-1].lower()
            file_path = os.path.join(self.temp_dir, f"{user_id}_{document.file_id}.{file_extension}")
            
            await file.download_to_drive(file_path)
            
            # Guardar información del archivo
            context.user_data['archivo_path'] = file_path
            context.user_data['tipo_archivo'] = context.user_data.get('tipo_archivo_seleccionado', 'documento')
            context.user_data['nombre_archivo'] = document.file_name
            context.user_data['esperando_archivo'] = False
            
            # Solicitar cantidad de copias
            await self.solicitar_copias(update, context)
            
        except Exception as e:
            logger.error(f"Error procesando documento: {e}")
            await update.message.reply_text("❌ Error al procesar el archivo. Por favor, intenta nuevamente.")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar fotos subidas"""
        user_id = update.message.from_user.id
        photo = update.message.photo[-1]  # La foto de mayor calidad
        
        # Verificar si estamos en proceso de subir archivo
        if not context.user_data.get('esperando_archivo'):
            await update.message.reply_text("❌ Por favor, selecciona primero el tipo de archivo desde el menú.")
            return
        
        # Verificar tamaño del archivo (2MB máximo)
        if photo.file_size > 2 * 1024 * 1024:
            await update.message.reply_text("❌ La imagen es demasiado grande. Límite: 2MB")
            return
        
        try:
            # Descargar archivo
            file = await photo.get_file()
            file_path = os.path.join(self.temp_dir, f"{user_id}_{photo.file_id}.jpg")
            
            await file.download_to_drive(file_path)
            
            # Guardar información del archivo
            context.user_data['archivo_path'] = file_path
            context.user_data['tipo_archivo'] = 'imagen'
            context.user_data['nombre_archivo'] = f"imagen_{user_id}.jpg"
            context.user_data['esperando_archivo'] = False
            
            # Solicitar cantidad de copias
            await self.solicitar_copias(update, context)
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            await update.message.reply_text("❌ Error al procesar la imagen. Por favor, intenta nuevamente.")
    
    async def solicitar_copias(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Solicitar cantidad de copias - Versión segura sin Markdown"""
        keyboard = [
            [InlineKeyboardButton("1", callback_data="copias_1"),
            InlineKeyboardButton("2", callback_data="copias_2"),
            InlineKeyboardButton("5", callback_data="copias_5")],
            [InlineKeyboardButton("10", callback_data="copias_10"),
            InlineKeyboardButton("Otra cantidad", callback_data="copias_otra")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        nombre_archivo = context.user_data.get('nombre_archivo', 'archivo')
        
        await update.message.reply_text(
            f"📄 Archivo recibido: {nombre_archivo}\n\n"
            "Selecciona la cantidad de copias:",
            reply_markup=reply_markup
        )
    
    async def handle_copias_selection(self, query, context: ContextTypes.DEFAULT_TYPE, copias: int):
        """Manejar selección de cantidad de copias - CORREGIDO"""
        try:
            context.user_data['copias'] = copias
            
            # Mostrar advertencia si son más de 50 copias
            if copias > 50:
                await query.edit_message_text(
                    f"⚠️ Advertencia: Has solicitado {copias} copias.\n\n"
                    "¿Estás seguro de continuar?",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Sí, continuar", callback_data="confirmar_copias"),
                        InlineKeyboardButton("❌ No, cambiar", callback_data="cancelar_copias")
                    ]])
                )
            else:
                await self.solicitar_color(query, context)
        except Exception as e:
            logger.error(f"Error en handle_copias_selection: {e}")
            await query.edit_message_text("❌ Error al procesar las copias. Por favor, intenta nuevamente.")
    
    async def solicitar_color(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Solicitar selección de color o blanco/negro - CORREGIDO"""
        try:
            copias = context.user_data.get('copias', 1)
            nombre_archivo = context.user_data.get('nombre_archivo', 'archivo')
            
            keyboard = [
                [InlineKeyboardButton("⚫ Blanco y Negro", callback_data="color_bn")],
                [InlineKeyboardButton("🎨 Color", callback_data="color_color")],
                [InlineKeyboardButton("🔙 Cambiar copias", callback_data="cambiar_copias")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📄 Archivo: {nombre_archivo}\n"
                f"📋 Copias: {copias}\n\n"
                "Selecciona el tipo de impresión:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en solicitar_color: {e}")
            await query.edit_message_text("❌ Error al cargar opciones. Por favor, intenta nuevamente.")
    
    async def handle_color_selection(self, query, context: ContextTypes.DEFAULT_TYPE, es_color: bool):
        """Manejar selección de color - CORREGIDO"""
        try:
            context.user_data['color'] = es_color
            
            # Calcular precio
            copias = context.user_data.get('copias', 1)
            precio_unitario = 13 if es_color else 10
            precio_total = copias * precio_unitario
            
            context.user_data['precio_total'] = precio_total
            
            tipo_cliente = context.user_data.get('tipo_cliente', 'natural')
            
            if tipo_cliente == 'empresa':
                await self.confirmar_pedido_empresa(query, context, precio_total)
            else:
                await self.solicitar_metodo_pago(query, context, precio_total)
        except Exception as e:
            logger.error(f"Error en handle_color_selection: {e}")
            await query.edit_message_text("❌ Error al seleccionar color. Por favor, intenta nuevamente.")
    
    async def solicitar_metodo_pago(self, query, context: ContextTypes.DEFAULT_TYPE, precio_total: float):
        """Solicitar método de pago para clientes naturales - CORREGIDO"""
        try:
            copias = context.user_data.get('copias', 1)
            color_text = "Color" if context.user_data.get('color') else "Blanco y Negro"
            
            keyboard = [
                [InlineKeyboardButton("💵 Efectivo al recoger", callback_data="pago_efectivo")],
                [InlineKeyboardButton("🏦 Transferencia", callback_data="pago_transferencia")],
                [InlineKeyboardButton("🔙 Cambiar tipo", callback_data="cambiar_color")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📄 Resumen del Pedido\n\n"
                f"• Archivo: {context.user_data.get('nombre_archivo', 'N/A')}\n"
                f"• Copias: {copias}\n"
                f"• Tipo: {color_text}\n"
                f"• Precio total: {precio_total} CUP\n\n"
                "Selecciona el método de pago:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en solicitar_metodo_pago: {e}")
            await query.edit_message_text("❌ Error al cargar métodos de pago. Por favor, intenta nuevamente.")
    
    async def confirmar_pedido_empresa(self, query, context: ContextTypes.DEFAULT_TYPE, precio_total: float):
        """Confirmar pedido para empresas - CORREGIDO"""
        try:
            copias = context.user_data.get('copias', 1)
            color_text = "Color" if context.user_data.get('color') else "Blanco y Negro"
            empresa_nombre = context.user_data.get('empresa_nombre', 'Empresa')
            
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar Impresión", callback_data="confirmar_pedido")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_pedido")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🏢 Pedido Empresarial - {empresa_nombre}\n\n"
                f"• Archivo: {context.user_data.get('nombre_archivo', 'N/A')}\n"
                f"• Copias: {copias}\n"
                f"• Tipo: {color_text}\n"
                f"• Precio total: {precio_total} CUP\n\n"
                "Las impresiones se realizarán inmediatamente después de la confirmación.",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en confirmar_pedido_empresa: {e}")
            await query.edit_message_text("❌ Error al confirmar pedido. Por favor, intenta nuevamente.")
    
    async def confirmar_pedido_natural(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Confirmar pedido para clientes naturales - CORREGIDO"""
        try:
            copias = context.user_data.get('copias', 1)
            color_text = "Color" if context.user_data.get('color') else "Blanco y Negro"
            precio_total = context.user_data.get('precio_total', 0)
            metodo_pago = context.user_data.get('metodo_pago', 'efectivo')
            
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_pedido")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_pedido")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            metodo_text = "Efectivo al recoger" if metodo_pago == 'efectivo' else "Transferencia"
            
            await query.edit_message_text(
                f"📄 Resumen Final del Pedido\n\n"
                f"• Archivo: {context.user_data.get('nombre_archivo', 'N/A')}\n"
                f"• Copias: {copias}\n"
                f"• Tipo: {color_text}\n"
                f"• Método de pago: {metodo_text}\n"
                f"• Precio total: {precio_total} CUP\n\n"
                "¿Confirmas el pedido?",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en confirmar_pedido_natural: {e}")
            await query.edit_message_text("❌ Error al confirmar pedido. Por favor, intenta nuevamente.")
    
    async def solicitar_transferencia(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Solicitar información de transferencia - CORREGIDO"""
        try:
            precio_total = context.user_data.get('precio_total', 0)
            
            keyboard = [
                [InlineKeyboardButton("✅ Ya realicé la transferencia", callback_data="confirmar_pedido")],
                [InlineKeyboardButton("🔙 Cambiar método", callback_data="cambiar_metodo")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🏦 Información para Transferencia\n\n"
                f"• Monto a transferir: {precio_total} CUP\n"
                f"• Banco: Banco Metropolitano\n"
                f"• Cuenta: 1234-5678-9012-3456\n"
                f"• Titular: Impresiones Rápidas S.A.\n\n"
                "Una vez realizada la transferencia, confirma aquí:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en solicitar_transferencia: {e}")
            await query.edit_message_text("❌ Error al cargar información de transferencia. Por favor, intenta nuevamente.")
    
    async def crear_pedido_db(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, metodo_pago: str = None):
        """Crear pedido en la base de datos"""
        try:
            # Obtener cliente
            tipo_cliente = context.user_data.get('tipo_cliente', 'natural')
            empresa_id = context.user_data.get('empresa_id')
            
            cliente = db.obtener_o_crear_cliente(user_id, tipo_cliente, empresa_id)
            
            # Crear objeto pedido
            pedido = Pedido(
                cliente_id=cliente.id,
                archivo_path=context.user_data.get('archivo_path'),
                tipo_archivo=context.user_data.get('tipo_archivo'),
                copias=context.user_data.get('copias', 1),
                color=context.user_data.get('color', False),
                precio_total=context.user_data.get('precio_total', 0),
                estado='pendiente',
                metodo_pago=metodo_pago,
                pago_confirmado=(tipo_cliente == 'empresa')  # Empresas confirmadas automáticamente
            )
            
            # Guardar en BD
            pedido_id = db.crear_pedido(pedido)
            return pedido_id
            
        except Exception as e:
            logger.error(f"Error creando pedido: {e}")
            return None

# Instancia global
message_handlers = MessageHandlers()