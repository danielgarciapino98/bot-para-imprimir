"""
Sistema de Impresión Automatizado - Punto de Entrada Principal
"""
import os
import sys
import asyncio
import logging
import threading
import inspect
from functools import partial

def inicializar_sistema():
    """Inicializar todo el sistema"""
    print("🖨️ Iniciando Sistema de Impresión Automatizado...")
    
    # Asegurar que estamos en el directorio correcto
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Importar después de cambiar directorio
    from utils.helpers import crear_carpetas_necesarias, backup_database
    from database.setup_database import crear_tablas
    
    # Crear carpetas necesarias
    crear_carpetas_necesarias()
    
    # Crear base de datos
    print("📦 Inicializando base de datos...")
    crear_tablas()
    
    # Crear backup inicial
    print("💾 Creando backup inicial...")
    backup_database()
    
    print("✅ Sistema inicializado correctamente!")

def ejecutar_bot():
    """Ejecutar el bot de Telegram con event loop correcto en este hilo"""
    try:
        # Crear y asignar un event loop para este hilo ANTES de usar librerías que lo requieran
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Importar e instanciar el bot con el loop ya asignado al hilo
        from bots.telegram_bot import TelegramBot
        bot = TelegramBot()

        run = getattr(bot, "run", None)
        if callable(run):
            run()
            return

        start = getattr(bot, "start", None)
        if start is None:
            logging.warning("TelegramBot no define run() ni start(), no se inició el bot")
            return

        if asyncio.iscoroutinefunction(start):
            sig = inspect.signature(start)
            if len(sig.parameters) == 0:
                loop.run_until_complete(start())
                try:
                    loop.run_forever()
                except KeyboardInterrupt:
                    pass
            else:
                logging.warning("TelegramBot.start requiere parámetros (handler); no se llamará directamente")
        else:
            sig = inspect.signature(start)
            if len(sig.parameters) == 0:
                start()
            else:
                logging.warning("TelegramBot.start requiere parámetros (handler); no se llamará directamente")

    except Exception as e:
        logging.exception("Error en el bot")
        print(f"❌ Error en el bot: {e}")

def ejecutar_sistema_completo():
    """Ejecutar el sistema completo (Bot + Panel)"""
    try:
        bot_thread = threading.Thread(target=ejecutar_bot, daemon=True, name="Thread-1 (ejecutar_bot)")
        bot_thread.start()
        print("🤖 Bot de Telegram iniciado en segundo plano...")

        from panel.main_window import MainWindow
        print("🎛️ Iniciando Panel de Control...")
        panel = MainWindow()
        panel.run()

    except Exception as e:
        logging.exception("Error iniciando sistema")
        print(f"❌ Error iniciando sistema: {e}")
        sys.exit(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    inicializar_sistema()
    ejecutar_sistema_completo()