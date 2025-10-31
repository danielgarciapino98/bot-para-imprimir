import yaml
import os
from dotenv import load_dotenv

load_dotenv()

def crear_config_automatica():
    """Crear configuración automáticamente si no existe"""
    config_default = {
        'telegram': {
            'bot_token': os.getenv('BOT_TOKEN', 'TU_BOT_TOKEN_AQUI'),
            'admin_ids': [int(os.getenv('ADMIN_ID', 123456789))]
        },
        'printers': {
            'negro': 'negro',
            'color': 'nueva_cable', 
            'max_file_size': 2
        },
        'prices': {
            'black_white': 10,
            'color': 13
        },
        'business_hours': {
            'start': '08:00',
            'end': '16:00',
            'timezone': 'America/Havana'
        },
        'notifications': {
            'reminder_hours': 2,
            'sound_enabled': True,
            'default_sound': 'storage/sounds/notification.mp3'
        },
        'database': {
            'path': 'storage/sistema_impresion.db',
            'backup_interval': 24
        }
    }
    
    with open('config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config_default, f, default_flow_style=False, allow_unicode=True)
    
    print("✅ config.yaml creado automáticamente con valores por defecto")
    return config_default

def load_config():
    """Cargar configuración - crea automáticamente si no existe"""
    try:
        if not os.path.exists('config.yaml'):
            print("📁 Creando config.yaml automáticamente...")
            return crear_config_automatica()
        
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        print("✅ Configuración cargada correctamente")
        return config
        
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        print("🔄 Creando configuración por defecto...")
        return crear_config_automatica()

# Cargar configuración global
CONFIG = load_config()