#!/usr/bin/env python3
"""
Archivo de ejecución simple - ELIMINA ERRORES
"""

print("🚀 INICIANDO SISTEMA DE IMPRESIÓN...")

try:
    # Verificar dependencias
    import sys
    import os
    
    # Añadir directorio actual al path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("✅ Python version:", sys.version)
    
    # Intentar importar componentes
    try:
        from bots.telegram_bot import TelegramBot
        print("✅ Módulo de Telegram cargado")
    except Exception as e:
        print("❌ Error en módulo Telegram:", e)
    
    try:
        from panel.main_window import main as panel_main
        print("✅ Módulo de Panel cargado") 
    except Exception as e:
        print("❌ Error en módulo Panel:", e)
    
    # Menú simple
    while True:
        print("\n" + "="*50)
        print("🎯 SISTEMA DE IMPRESIÓN - EL PRECIO DEL MAÑANA")
        print("="*50)
        print("1. 🤖 Ejecutar Bot de Telegram")
        print("2. 🖥️ Ejecutar Panel de Control") 
        print("3. 🚪 Salir")
        
        opcion = input("\nSelecciona una opción (1-3): ").strip()
        
        if opcion == "1":
            print("\n🚀 Iniciando Bot de Telegram...")
            try:
                bot = TelegramBot()
                bot.run()
            except Exception as e:
                print(f"❌ Error: {e}")
                print("💡 Asegúrate de tener configurado TELEGRAM_BOT_TOKEN en .env")
                
        elif opcion == "2":
            print("\n🖥️ Iniciando Panel de Control...")
            try:
                panel_main()
            except Exception as e:
                print(f"❌ Error: {e}")
                
        elif opcion == "3":
            print("👋 ¡Hasta pronto!")
            break
        else:
            print("❌ Opción no válida")

except Exception as e:
    print(f"💥 ERROR CRÍTICO: {e}")
    input("Presiona Enter para salir...")