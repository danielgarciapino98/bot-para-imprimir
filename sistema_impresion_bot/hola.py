try:
    import win32ui
    import win32print
    import win32con
    print("✅ ¡Excelente! Todos los módulos se importaron correctamente.")
    print(f"Versión de pywin32 instalada: {win32api.__version__ if 'win32api' in dir() else 'No disponible'}")
except ImportError as e:
    print(f"Error: {e}. Aún hay un problema con la instalación.")