"""
Script para ejecutar solo el panel de control
"""
from panel.main_window import MainWindow

if __name__ == '__main__':
    print("🎛️ Iniciando Panel de Control...")
    app = MainWindow()
    app.run()