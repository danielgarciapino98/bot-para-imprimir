import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('storage/logs/system.log', encoding='utf-8')
    ]
)

def main():
    print("🖨️ SISTEMA DE IMPRESIÓN - EL PRECIO DEL MAÑANA")
    print("=" * 50)
    
    # Verificar Python version
    if sys.version_info < (3, 8):
        print("❌ Se requiere Python 3.8 o superior")
        return
    
    # Verificar dependencias
    try:
        import telegram
        import PyQt5
        print("✅ Dependencias verificadas")
    except ImportError as e:
        print(f"❌ Faltan dependencias: {e}")
        print("Instala con: pip install python-telegram-bot PyQt5 pillow pywin32")
        return
    
    # Crear carpetas necesarias
    folders = ['storage/temp_files', 'storage/backups', 'storage/logs', 'storage/sounds']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    print("📁 Estructura de carpetas verificada")
    
    # Mostrar menú
    while True:
        print("\n🎯 MENÚ PRINCIPAL:")
        print("1. 🤖 Ejecutar solo Bot de Telegram")
        print("2. 🖥️ Ejecutar solo Panel de Control")
        print("3. 🔄 Ejecutar Ambos (Recomendado)")
        print("4. ⚙️ Verificar Configuración")
        print("5. 🚪 Salir")
        
        opcion = input("\nSelecciona una opción (1-5): ").strip()
        
        if opcion == "1":
            ejecutar_bot()
        elif opcion == "2":
            ejecutar_panel()
        elif opcion == "3":
            ejecutar_ambos()
        elif opcion == "4":
            verificar_configuracion()
        elif opcion == "5":
            print("👋 ¡Hasta pronto!")
            break
        else:
            print("❌ Opción no válida")

def ejecutar_bot():
    """Ejecutar solo el bot de Telegram"""
    try:
        print("\n🚀 Iniciando Bot de Telegram...")
        
        # Importar después de verificar dependencias
        from bots.telegram_bot import TelegramBot
        
        bot = TelegramBot()
        print("✅ Bot iniciado correctamente")
        print("🤖 El bot está funcionando. Presiona Ctrl+C para detenerlo.")
        
        bot.run()
        
    except Exception as e:
        print(f"❌ Error iniciando el bot: {e}")
        logging.error(f"Error en bot: {e}")

def ejecutar_panel():
    """Ejecutar solo el panel de control"""
    try:
        print("\n🖥️ Iniciando Panel de Control...")
        
        from PyQt5.QtWidgets import QApplication
        from panel.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("El Precio Del Mañana")
        
        window = MainWindow()
        window.show()
        
        print("✅ Panel iniciado correctamente")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Error iniciando el panel: {e}")
        logging.error(f"Error en panel: {e}")

def ejecutar_ambos():
    """Ejecutar ambos sistemas"""
    try:
        print("\n🔄 Iniciando ambos sistemas...")
        
        # Ejecutar en procesos separados
        import subprocess
        import threading
        
        def run_bot():
            try:
                subprocess.run([sys.executable, __file__, "bot"], check=True)
            except subprocess.CalledProcessError:
                pass
        
        def run_panel():
            try:
                subprocess.run([sys.executable, __file__, "panel"], check=True)
            except subprocess.CalledProcessError:
                pass
        
        # Ejecutar en hilos separados
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        panel_thread = threading.Thread(target=run_panel, daemon=True)
        
        bot_thread.start()
        panel_thread.start()
        
        print("✅ Ambos sistemas iniciados")
        print("📱 Bot: http://t.me/... (configura tu bot token)")
        print("🖥️ Panel: Interfaz gráfica iniciada")
        
        # Mantener el programa corriendo
        bot_thread.join()
        panel_thread.join()
        
    except Exception as e:
        print(f"❌ Error iniciando sistemas: {e}")

def verificar_configuracion():
    """Verificar la configuración del sistema"""
    print("\n⚙️ VERIFICANDO CONFIGURACIÓN...")
    
    # Verificar archivos esenciales
    archivos_esenciales = ['.env', 'config.yaml', 'database/models.py']
    for archivo in archivos_esenciales:
        if os.path.exists(archivo):
            print(f"✅ {archivo}")
        else:
            print(f"❌ {archivo} - NO ENCONTRADO")
    
    # Verificar carpetas
    carpetas_esenciales = ['storage', 'bots', 'core', 'database', 'panel', 'utils']
    for carpeta in carpetas_esenciales:
        if os.path.exists(carpeta):
            print(f"✅ {carpeta}/")
        else:
            print(f"❌ {carpeta}/ - NO ENCONTRADA")
    
    # Verificar variables de entorno
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if token:
            print("✅ TELEGRAM_BOT_TOKEN - CONFIGURADO")
        else:
            print("❌ TELEGRAM_BOT_TOKEN - NO CONFIGURADO")
            
    except ImportError:
        print("❌ python-dotenv no instalado")

if __name__ == "__main__":
    # Si se pasa argumento, ejecutar modo específico
    if len(sys.argv) > 1:
        modo = sys.argv[1]
        if modo == "bot":
            ejecutar_bot()
        elif modo == "panel":
            ejecutar_panel()
        else:
            main()
    else:
        main()