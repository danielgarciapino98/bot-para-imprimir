"""
Operaciones de base de datos para el sistema de impresión
"""
import sqlite3
import os
from datetime import datetime, timedelta
from .models import Empresa, Cliente, Pedido, Impresion, Operador, Consumible

class DatabaseManager:
    def __init__(self, db_path='storage/sistema_impresion.db'):
        self.db_path = db_path
        os.makedirs('storage', exist_ok=True)
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    # --- OPERACIONES EMPRESAS ---
    def crear_empresa(self, nombre, pin):
        """Crear una nueva empresa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO empresas (nombre, pin) VALUES (?, ?)',
                (nombre, pin)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verificar_pin_empresa(self, pin):
        """Verificar si un PIN de empresa es válido"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, nombre FROM empresas WHERE pin = ? AND activa = TRUE',
            (pin,)
        )
        resultado = cursor.fetchone()
        conn.close()
        return Empresa(resultado[0], resultado[1], pin) if resultado else None
    
    def obtener_empresas(self):
        """Obtener todas las empresas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, pin, activa FROM empresas ORDER BY nombre')
        empresas = []
        for row in cursor.fetchall():
            empresas.append(Empresa(*row))
        conn.close()
        return empresas
    
    # --- OPERACIONES CLIENTES ---
    def obtener_o_crear_cliente(self, telegram_id, tipo='natural', empresa_id=None):
        """Obtener cliente existente o crear uno nuevo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Buscar cliente existente
        cursor.execute(
            'SELECT id, telegram_id, tipo, empresa_id, bloqueado_hasta, intentos_fallidos FROM clientes WHERE telegram_id = ?',
            (telegram_id,)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            cliente = Cliente(*resultado)
        else:
            # Crear nuevo cliente
            cursor.execute(
                'INSERT INTO clientes (telegram_id, tipo, empresa_id) VALUES (?, ?, ?)',
                (telegram_id, tipo, empresa_id)
            )
            cliente = Cliente(cursor.lastrowid, telegram_id, tipo, empresa_id)
            conn.commit()
        
        conn.close()
        return cliente
    
    def actualizar_intento_fallido(self, telegram_id):
        """Actualizar intentos fallidos y bloquear si es necesario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT intentos_fallidos FROM clientes WHERE telegram_id = ?',
            (telegram_id,)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            intentos = resultado[0] + 1
            if intentos >= 3:
                # Bloquear por 5 minutos
                bloqueado_hasta = datetime.now() + timedelta(minutes=5)
                cursor.execute(
                    'UPDATE clientes SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE telegram_id = ?',
                    (intentos, bloqueado_hasta, telegram_id)
                )
            else:
                cursor.execute(
                    'UPDATE clientes SET intentos_fallidos = ? WHERE telegram_id = ?',
                    (intentos, telegram_id)
                )
            conn.commit()
        conn.close()
    
    def resetear_intentos(self, telegram_id):
        """Resetear intentos fallidos después de éxito"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE clientes SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE telegram_id = ?',
            (telegram_id,)
        )
        conn.commit()
        conn.close()
    
    # --- OPERACIONES PEDIDOS ---
    def crear_pedido(self, pedido):
        """Crear un nuevo pedido"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pedidos 
            (cliente_id, archivo_path, tipo_archivo, copias, color, precio_total, estado, metodo_pago, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pedido.cliente_id, pedido.archivo_path, pedido.tipo_archivo, 
              pedido.copias, pedido.color, pedido.precio_total, 
              pedido.estado, pedido.metodo_pago, pedido.notas))
        
        pedido_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pedido_id
    
    def obtener_pedidos_pendientes(self):
        """Obtener pedidos pendientes de impresión"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.cliente_id, p.archivo_path, p.tipo_archivo, p.copias, 
                   p.color, p.precio_total, p.estado, p.metodo_pago, p.pago_confirmado,
                   p.notas, p.fecha_creacion, c.telegram_id, c.tipo
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.estado = 'pendiente'
            ORDER BY p.fecha_creacion
        ''')
        pedidos = []
        for row in cursor.fetchall():
            pedido = Pedido(*row[:11])
            pedido.fecha_creacion = row[11]
            pedidos.append((pedido, row[12], row[13]))  # pedido, telegram_id, tipo_cliente
        conn.close()
        return pedidos
    
    # --- OPERACIONES OPERADORES ---
    def verificar_operador(self, usuario, password):
        """Verificar credenciales de operador"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, usuario, password_hash, nombre, rol FROM operadores WHERE usuario = ? AND activo = TRUE',
            (usuario,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[2] == password:  # En producción usar hashing!
            return Operador(*resultado)
        return None
    
    # --- MÉTODOS PARA EMPRESAS ---
    def obtener_empresas(self):
        """Obtener todas las empresas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, pin, activa FROM empresas ORDER BY nombre')
        empresas = []
        for row in cursor.fetchall():
            empresas.append(Empresa(*row))
        conn.close()
        return empresas

    def crear_empresa(self, nombre, pin):
        """Crear una nueva empresa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO empresas (nombre, pin) VALUES (?, ?)',
                (nombre, pin)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def actualizar_empresa(self, empresa_id, nombre, pin, activa):
        """Actualizar información de una empresa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE empresas SET nombre = ?, pin = ?, activa = ? WHERE id = ?',
                (nombre, pin, activa, empresa_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error actualizando empresa: {e}")
            return False
        finally:
            conn.close()

    # --- MÉTODOS PARA PEDIDOS ---  
    def confirmar_pago_pedido(self, pedido_id):
        """Confirmar pago de un pedido"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE pedidos SET pago_confirmado = TRUE WHERE id = ?',
                (pedido_id,)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error confirmando pago: {e}")
            return False
        finally:
            conn.close()

    def obtener_pedidos_por_empresa(self, empresa_id):
        """
        Devuelve la lista de pedidos asociados a una empresa.
        Ajusta nombres de tabla/columnas según tu esquema.
        """
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT id, empresa_id, cliente, estado, total, fecha_creacion "
                "FROM pedidos WHERE empresa_id = ? ORDER BY fecha_creacion DESC",
                (empresa_id,)
            )
            rows = cur.fetchall()
            # Mapear a dicts (opcional)
            pedidos = [
                {
                    "id": r[0],
                    "empresa_id": r[1],
                    "cliente": r[2],
                    "estado": r[3],
                    "total": r[4],
                    "fecha_creacion": r[5],
                }
                for r in rows
            ]
            return pedidos
        except Exception as e:
            # Loguear si tienes logger; aquí devolvemos lista vacía en fallo
            print(f"Error obtener_pedidos_por_empresa: {e}")
            return []
# Instancia global de DatabaseManager
db = DatabaseManager()