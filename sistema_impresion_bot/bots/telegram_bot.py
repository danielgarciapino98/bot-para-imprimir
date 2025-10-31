"""
Bot principal de Telegram para el sistema de impresión
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder,
)
from utils.config_loader import CONFIG
from database.operations import db
from core.queue_manager import queue_manager  # Importar queue_manager desde core

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        # Inicialización mínima del bot sin tocar UI ni crear hilos aquí
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar menú principal (handler /start y fallback para mensajes)"""
        try:
            keyboard = [
                [InlineKeyboardButton("👤 Cliente Natural", callback_data="cliente_natural")],
                [InlineKeyboardButton("🏢 Cliente Empresa", callback_data="cliente_empresa")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "🖨️ Menú Principal\n\nSelecciona tu tipo de cliente:"

            # Si viene como mensaje
            if update and getattr(update, "message", None):
                await update.message.reply_text(text, reply_markup=reply_markup)
            # Si viene como callback_query
            elif update and getattr(update, "callback_query", None):
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                # Fallback seguro
                logger.debug("start() llamado sin update.message ni update.callback_query")
        except Exception as e:
            logger.error("Error en start: %s", e)
            try:
                if update and getattr(update, "message", None):
                    await update.message.reply_text("❌ Error mostrando el menú. Intenta de nuevo.")
            except Exception:
                pass

    async def handle_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar clicks en botones"""
        try:
            query = update.callback_query
            await query.answer()

            data = query.data
            logger.info("Botón presionado: %s", data)

            if data == "cliente_natural":
                await self.menu_archivos_natural(query, context)
            elif data == "cliente_empresa":
                await self.solicitar_pin_empresa(query, context)
            elif data == "menu_principal":
                await self.menu_principal(query, context)
            elif data.startswith("tipo_"):
                await self.seleccionar_tipo_archivo(query, context, data)
            elif data.startswith("copias_"):
                await self.manejar_seleccion_copias(query, context, data)
            elif data in ["color_bn", "color_color"]:
                await self.manejar_seleccion_color(query, context, data)
            elif data in ["pago_efectivo", "pago_transferencia"]:
                await self.manejar_metodo_pago(query, context, data)
            elif data == "confirmar_pedido":
                await self.confirmar_pedido_final(query, context)
            elif data in ["confirmar_copias", "cancelar_copias"]:
                await self.manejar_confirmacion_copias(query, context, data)
            elif data in ["cambiar_copias", "cambiar_color", "cambiar_metodo"]:
                await self.manejar_cambios(query, context, data)
            else:
                logger.warning("Callback no manejado: %s", data)
                await query.edit_message_text("❌ Comando no reconocido. Por favor, usa el menú.")
        except Exception as e:
            logger.error("Error en handle_button_click: %s", e)
            try:
                if update and getattr(update, "callback_query", None) and update.callback_query.message:
                    await update.callback_query.message.reply_text(
                        "❌ Error al procesar la solicitud. Por favor, intenta nuevamente."
                    )
            except Exception:
                pass

    async def seleccionar_tipo_archivo(self, query, context, tipo_archivo):
        """Manejar selección de tipo de archivo"""
        try:
            context.user_data["tipo_archivo_seleccionado"] = tipo_archivo.replace("tipo_", "")
            context.user_data["esperando_archivo"] = True

            tipos = {
                "word": "Documento Word",
                "pdf": "Documento PDF",
                "imagen": "Imagen (PNG/JPG)",
                "excel": "Excel",
            }

            tipo_nombre = tipos.get(context.user_data["tipo_archivo_seleccionado"], "archivo")

            await query.edit_message_text(f"📄 Has seleccionado: {tipo_nombre}\n\nPor favor, envía el archivo ahora:")
        except Exception as e:
            logger.error("Error en seleccionar_tipo_archivo: %s", e)
            await query.edit_message_text("❌ Error al procesar la selección. Por favor, intenta nuevamente.")

    async def manejar_seleccion_copias(self, query, context, data_copias):
        """Manejar selección de cantidad de copias"""
        try:
            from bots.message_handlers import message_handlers

            if data_copias == "copias_otra":
                await query.edit_message_text("🔢 Por favor, escribe la cantidad de copias que necesitas:")
                context.user_data["esperando_copias"] = True
            else:
                copias = int(data_copias.replace("copias_", ""))
                await message_handlers.handle_copias_selection(query, context, copias)
        except Exception as e:
            logger.error("Error en manejar_seleccion_copias: %s", e)
            await query.edit_message_text("❌ Error al procesar las copias. Por favor, intenta nuevamente.")

    async def manejar_confirmacion_copias(self, query, context, data_confirmacion):
        """Manejar confirmación de copias grandes"""
        try:
            from bots.message_handlers import message_handlers

            if data_confirmacion == "confirmar_copias":
                await message_handlers.solicitar_color(query, context)
            else:
                await message_handlers.solicitar_copias(query, context)
        except Exception as e:
            logger.error("Error en manejar_confirmacion_copias: %s", e)
            await query.edit_message_text("❌ Error al confirmar. Por favor, intenta nuevamente.")

    async def manejar_seleccion_color(self, query, context, data_color):
        """Manejar selección de color"""
        try:
            from bots.message_handlers import message_handlers

            es_color = data_color == "color_color"
            await message_handlers.handle_color_selection(query, context, es_color)
        except Exception as e:
            logger.error("Error en manejar_seleccion_color: %s", e)
            await query.edit_message_text("❌ Error al seleccionar color. Por favor, intenta nuevamente.")

    async def manejar_metodo_pago(self, query, context, metodo_pago):
        """Manejar selección de método de pago"""
        try:
            from bots.message_handlers import message_handlers

            metodo = metodo_pago.replace("pago_", "")
            context.user_data["metodo_pago"] = metodo

            if metodo == "efectivo":
                await message_handlers.confirmar_pedido_natural(query, context)
            else:
                await message_handlers.solicitar_transferencia(query, context)
        except Exception as e:
            logger.error("Error en manejar_metodo_pago: %s", e)
            await query.edit_message_text("❌ Error al seleccionar método de pago. Por favor, intenta nuevamente.")

    async def manejar_cambios(self, query, context, data_cambio):
        """Manejar botones de cambio/retroceso"""
        try:
            from bots.message_handlers import message_handlers

            if data_cambio == "cambiar_copias":
                await message_handlers.solicitar_copias(query, context)
            elif data_cambio == "cambiar_color":
                await message_handlers.solicitar_color(query, context)
            elif data_cambio == "cambiar_metodo":
                precio_total = context.user_data.get("precio_total", 0)
                await message_handlers.solicitar_metodo_pago(query, context, precio_total)
        except Exception as e:
            logger.error("Error en manejar_cambios: %s", e)
            await query.edit_message_text("❌ Error al procesar el cambio. Por favor, intenta nuevamente.")

    async def confirmar_pedido_final(self, query, context):
        """Confirmar pedido final"""
        try:
            from bots.message_handlers import message_handlers

            user_id = query.from_user.id
            pedido_id = await message_handlers.crear_pedido_db(
                context, user_id, context.user_data.get("metodo_pago")
            )

            if pedido_id:
                tipo_cliente = context.user_data.get("tipo_cliente", "natural")
                if tipo_cliente == "empresa":
                    await query.edit_message_text(
                        "✅ Pedido confirmado para empresa\n\n"
                        "Tu pedido ha sido añadido a la cola de impresión y se procesará inmediatamente.\n\n"
                        "📞 Te notificaremos cuando esté listo para recoger."
                    )
                else:
                    if context.user_data.get("metodo_pago") == "efectivo":
                        await query.edit_message_text(
                            "✅ Pedido confirmado\n\n"
                            "Tu pedido ha sido añadido a la cola de impresión.\n"
                            "💰 Método de pago: Efectivo al recoger\n\n"
                            "📞 Te notificaremos cuando esté listo."
                        )
                    else:
                        await query.edit_message_text(
                            "✅ Pedido confirmado\n\n"
                            "Tu pedido ha sido añadido a la cola de impresión.\n"
                            "🏦 Método de pago: Transferencia\n"
                            "📧 Por favor, realiza la transferencia y espera la confirmación.\n\n"
                            "💳 Número de cuenta: 1234-5678-9012-3456"
                        )
            else:
                await query.edit_message_text(
                    "❌ Error al procesar el pedido\n\nPor favor, intenta nuevamente o contacta con soporte."
                )
        except Exception as e:
            logger.error("Error en confirmar_pedido_final: %s", e)
            await query.edit_message_text("❌ Error al confirmar el pedido. Por favor, intenta nuevamente.")

    async def solicitar_pin_empresa(self, query, context):
        """Solicitar PIN de empresa"""
        try:
            text = "🏢 Acceso Empresarial\n\nPor favor, ingresa tu PIN de 4 dígitos:"
            context.user_data["esperando_pin"] = True
            context.user_data["tipo_cliente"] = "empresa"
            await query.edit_message_text(text)
        except Exception as e:
            logger.error("Error en solicitar_pin_empresa: %s", e)
            await query.edit_message_text("❌ Error al procesar. Por favor, intenta nuevamente.")

    async def menu_archivos_natural(self, query, context):
        """Menú de tipos de archivo para clientes naturales"""
        try:
            keyboard = [
                [InlineKeyboardButton("📄 Documento Word", callback_data="tipo_word")],
                [InlineKeyboardButton("📊 Documento PDF", callback_data="tipo_pdf")],
                [InlineKeyboardButton("🖼️ Imagen (PNG/JPG)", callback_data="tipo_imagen")],
                [InlineKeyboardButton("📊 Excel", callback_data="tipo_excel")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="menu_principal")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "👤 Cliente Natural\n\nSelecciona el tipo de archivo que deseas imprimir:"
            context.user_data["tipo_cliente"] = "natural"
            context.user_data["esperando_archivo"] = False
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error("Error en menu_archivos_natural: %s", e)
            await query.edit_message_text("❌ Error al cargar el menú. Por favor, intenta nuevamente.")

    async def menu_principal(self, query, context):
        """Volver al menú principal"""
        try:
            keyboard = [
                [InlineKeyboardButton("👤 Cliente Natural", callback_data="cliente_natural")],
                [InlineKeyboardButton("🏢 Cliente Empresa", callback_data="cliente_empresa")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "🖨️ Menú Principal\n\nSelecciona tu tipo de cliente:"
            context.user_data.clear()
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error("Error en menu_principal: %s", e)
            await query.edit_message_text("❌ Error al cargar el menú. Por favor, intenta nuevamente.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto"""
        try:
            if not update or not getattr(update, "message", None):
                return
            user_message = update.message.text
            user_id = update.message.from_user.id

            # Verificar si estamos esperando PIN de empresa
            if context.user_data.get("esperando_pin"):
                await self.verificar_pin_empresa(update, context, user_message, user_id)
                return

            # Verificar si estamos esperando cantidad de copias personalizada
            if context.user_data.get("esperando_copias"):
                try:
                    copias = int(user_message)
                    if copias > 0:
                        from bots.message_handlers import message_handlers
                        context.user_data["esperando_copias"] = False
                        await message_handlers.handle_copias_selection(update, context, copias)
                    else:
                        await update.message.reply_text("❌ Por favor, ingresa un número válido mayor a 0")
                except ValueError:
                    await update.message.reply_text("❌ Por favor, ingresa un número válido")
                return

            # Si no es un caso especial, mostrar menú principal
            await self.start(update, context)
        except Exception as e:
            logger.error("Error en handle_message: %s", e)
            try:
                await update.message.reply_text("❌ Error al procesar el mensaje. Por favor, intenta nuevamente.")
            except Exception:
                pass

    async def verificar_pin_empresa(self, update: Update, context: ContextTypes.DEFAULT_TYPE, pin: str, user_id: int):
        """Verificar PIN de empresa"""
        try:
            cliente = db.obtener_o_crear_cliente(user_id, "empresa")
            if getattr(cliente, "bloqueado_hasta", None):
                await update.message.reply_text(
                    "❌ Demasiados intentos fallidos. Tu cuenta está bloqueada temporalmente. Por favor, intenta nuevamente en 5 minutos."
                )
                return

            empresa = db.verificar_pin_empresa(pin)
            if empresa:
                db.resetear_intentos(user_id)
                context.user_data["empresa_id"] = getattr(empresa, "id", None)
                context.user_data["empresa_nombre"] = getattr(empresa, "nombre", None)
                context.user_data["esperando_pin"] = False
                await self.menu_archivos_empresa(update, context, context.user_data["empresa_nombre"])
            else:
                db.actualizar_intento_fallido(user_id)
                cliente = db.obtener_o_crear_cliente(user_id, "empresa")
                if getattr(cliente, "intentos_fallidos", 0) >= 3:
                    await update.message.reply_text("❌ Demasiados intentos fallidos. Tu cuenta ha sido bloqueada por 5 minutos.")
                else:
                    intentos_restantes = 3 - getattr(cliente, "intentos_fallidos", 0)
                    await update.message.reply_text(f"❌ PIN incorrecto. Te quedan {intentos_restantes} intentos.")
        except Exception as e:
            logger.error("Error en verificar_pin_empresa: %s", e)
            try:
                await update.message.reply_text("❌ Error al verificar el PIN. Por favor, intenta nuevamente.")
            except Exception:
                pass

    async def menu_archivos_empresa(self, update: Update, context: ContextTypes.DEFAULT_TYPE, empresa_nombre: str):
        """Menú de tipos de archivo para empresas"""
        try:
            keyboard = [
                [InlineKeyboardButton("📄 Documento Word", callback_data="tipo_word")],
                [InlineKeyboardButton("📊 Documento PDF", callback_data="tipo_pdf")],
                [InlineKeyboardButton("🖼️ Imagen (PNG/JPG)", callback_data="tipo_imagen")],
                [InlineKeyboardButton("📊 Excel", callback_data="tipo_excel")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="menu_principal")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"🏢 {empresa_nombre}\n\nSelecciona el tipo de archivo que deseas imprimir:"
            context.user_data["esperando_archivo"] = False
            await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error("Error en menu_archivos_empresa: %s", e)
            try:
                await update.message.reply_text("❌ Error al cargar el menú. Por favor, intenta nuevamente.")
            except Exception:
                pass

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar documentos subidos"""
        try:
            from bots.message_handlers import message_handlers
            await message_handlers.handle_document(update, context)
        except Exception as e:
            logger.error("Error en handle_document: %s", e)
            try:
                await update.message.reply_text("❌ Error al procesar el documento. Por favor, intenta nuevamente.")
            except Exception:
                pass

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar fotos subidas"""
        try:
            from bots.message_handlers import message_handlers
            await message_handlers.handle_photo(update, context)
        except Exception as e:
            logger.error("Error en handle_photo: %s", e)
            try:
                await update.message.reply_text("❌ Error al procesar la imagen. Por favor, intenta nuevamente.")
            except Exception:
                pass

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Manejar errores globales"""
        try:
            err = getattr(context, "error", None)
            logger.error("Error no manejado: %s", err)
            try:
                if isinstance(update, Update):
                    if getattr(update, "callback_query", None) and update.callback_query.message:
                        await update.callback_query.message.reply_text("❌ Ocurrió un error inesperado. Por favor, intenta nuevamente.")
                    elif getattr(update, "message", None):
                        await update.message.reply_text("❌ Ocurrió un error inesperado. Por favor, intenta nuevamente.")
            except Exception as e:
                logger.error("No se pudo notificar al usuario del error: %s", e)
        except Exception as e:
            logger.error("Error en el manejador de errores: %s", e)

    def run(self):
        """Arrancar el bot de forma segura; carga token desde CONFIG, entorno o .env"""
        token = None
        # 1) Intentar desde CONFIG
        try:
            token = CONFIG.get("telegram_token") if isinstance(CONFIG, dict) else getattr(CONFIG, "get", lambda k: None)("telegram_token")
        except Exception:
            token = None

        # 2) Intentar desde variables de entorno ya cargadas
        if not token:
            token = os.getenv("TELEGRAM_TOKEN") or os.getenv("telegram_token") or os.getenv("BOT_TOKEN")

        # 3) Intentar cargar .env automáticamente usando python-dotenv si está disponible
        if not token:
            try:
                from dotenv import load_dotenv, find_dotenv  # type: ignore
                dotenv_path = find_dotenv(usecwd=True)
                if dotenv_path:
                    load_dotenv(dotenv_path, override=False)
                    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("telegram_token") or os.getenv("BOT_TOKEN")
            except Exception:
                # python-dotenv no disponible o fallo; seguiremos con fallback manual
                pass

        # 4) Fallback manual: buscar .env en la raíz del proyecto (dos niveles arriba por seguridad)
        if not token:
            try:
                # rutas a comprobar: cwd, carpeta del proyecto (../ desde bots), dos niveles arriba
                candidates = [
                    os.path.join(os.getcwd(), ".env"),
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
                ]
                for p in candidates:
                    if p and os.path.exists(p):
                        with open(p, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith("#") or "=" not in line:
                                    continue
                                k, v = line.split("=", 1)
                                k = k.strip()
                                v = v.strip().strip('\'"')
                                if k and v:
                                    os.environ.setdefault(k, v)
                        token = os.getenv("TELEGRAM_TOKEN") or os.getenv("telegram_token") or os.getenv("BOT_TOKEN")
                        if token:
                            break
            except Exception:
                logger.exception("Falló lectura manual de .env")

        if not token:
            logger.warning(
                "Telegram token ausente: el bot no se iniciará. Verifica:\n"
                " - d:\\sistema_impresion_bot\\.env contiene TELEGRAM_TOKEN=tu_token\n"
                " - o utils/config_loader CONFIG tiene 'telegram_token'\n"
                " - o la variable de entorno TELEGRAM_TOKEN/BOT_TOKEN está definida"
            )
            return

        # Iniciar la aplicación del bot
        logger.info("Telegram token cargado correctamente. Iniciando bot...")
        try:
            self.application = ApplicationBuilder().token(token).build()

            # Registrar handlers
            try:
                self.application.add_handler(CommandHandler("start", self.start))
                self.application.add_handler(CallbackQueryHandler(self.handle_button_click))
                self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
                self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
                self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
                self.application.add_error_handler(self.error_handler)
            except Exception:
                logger.exception("Error registrando handlers")

            # Ejecutar polling
            self.application.run_polling()
        except Exception as e:
            logger.exception("Error iniciando TelegramBot: %s", e)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()