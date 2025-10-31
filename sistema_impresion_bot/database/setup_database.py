"""
Configuración inicial de la base de datos
"""
import sqlite3
import os
from datetime import datetime

def crear_tablas():
    """Crear todas las tablas necesarias en la base de datos"""
    
    # Asegurar que la carpeta storage existe
    os.makedirs('storage', exist_ok=True)
    
    conn = sqlite3.connect('storage/sistema_impresion.db')
    cursor = conn.cursor()
    
    # Tabla de empresas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            pin TEXT NOT NULL UNIQUE,
            activa BOOLEAN DEFAULT TRUE,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            tipo TEXT NOT NULL CHECK(tipo IN ('natural', 'empresa')),
            empresa_id INTEGER,
            bloqueado_hasta DATETIME,
            intentos_fallidos INTEGER DEFAULT 0,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        )
    ''')
    
    # Tabla de pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            archivo_path TEXT NOT NULL,
            tipo_archivo TEXT NOT NULL,
            copias INTEGER NOT NULL DEFAULT 1,
            color BOOLEAN NOT NULL DEFAULT FALSE,
            precio_total REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'impreso', 'cancelado', 'error')),
            metodo_pago TEXT CHECK(metodo_pago IN ('efectivo', 'transferencia')),
            pago_confirmado BOOLEAN DEFAULT FALSE,
            notas TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')
    
    # Tabla de impresiones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS impresiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            hojas_color INTEGER DEFAULT 0,
            hojas_bn INTEGER DEFAULT 0,
            impresora_usada TEXT,
            estado TEXT NOT NULL DEFAULT 'completada' CHECK(estado IN ('completada', 'error', 'pausada')),
            fecha_impresion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
        )
    ''')
    
    # Tabla de operadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'operador' CHECK(rol IN ('operador', 'admin')),
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de consumibles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consumibles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('papel', 'tinta_color', 'tinta_negro')),
            cantidad REAL NOT NULL,
            unidad TEXT NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar administrador por defecto
    cursor.execute('''
        INSERT OR IGNORE INTO operadores 
        (usuario, password_hash, nombre, rol) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin123', 'Administrador Principal', 'admin'))
    
    conn.commit()
    conn.close()
    print("✅ Base de datos creada exitosamente!")

if __name__ == '__main__':
    crear_tablas()