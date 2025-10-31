"""
Modelos de la base de datos para el sistema de impresión
"""

class Empresa:
    def __init__(self, id=None, nombre=None, pin=None, activa=True):
        self.id = id
        self.nombre = nombre
        self.pin = pin  # PIN de 4 dígitos
        self.activa = activa

class Cliente:
    def __init__(self, id=None, telegram_id=None, tipo=None, empresa_id=None, 
                 bloqueado_hasta=None, intentos_fallidos=0):
        self.id = id
        self.telegram_id = telegram_id
        self.tipo = tipo  # 'natural' o 'empresa'
        self.empresa_id = empresa_id
        self.bloqueado_hasta = bloqueado_hasta
        self.intentos_fallidos = intentos_fallidos

class Pedido:
    def __init__(self, id=None, cliente_id=None, archivo_path=None, tipo_archivo=None,
                 copias=1, color=False, precio_total=0, estado='pendiente',
                 metodo_pago=None, pago_confirmado=False, notas=None):
        self.id = id
        self.cliente_id = cliente_id
        self.archivo_path = archivo_path
        self.tipo_archivo = tipo_archivo
        self.copias = copias
        self.color = color  # True = color, False = blanco/negro
        self.precio_total = precio_total
        self.estado = estado  # 'pendiente', 'impreso', 'cancelado', 'error'
        self.metodo_pago = metodo_pago  # 'efectivo', 'transferencia'
        self.pago_confirmado = pago_confirmado
        self.notas = notas
        self.fecha_creacion = None

class Impresion:
    def __init__(self, id=None, pedido_id=None, hojas_color=0, hojas_bn=0, 
                 impresora_usada=None, estado='completada'):
        self.id = id
        self.pedido_id = pedido_id
        self.hojas_color = hojas_color
        self.hojas_bn = hojas_bn
        self.impresora_usada = impresora_usada
        self.estado = estado

class Operador:
    def __init__(self, id=None, usuario=None, password_hash=None, nombre=None, 
                 rol='operador', activo=True):
        self.id = id
        self.usuario = usuario
        self.password_hash = password_hash
        self.nombre = nombre
        self.rol = rol  # 'operador' o 'admin'
        self.activo = activo

class Consumible:
    def __init__(self, id=None, tipo=None, cantidad=0, unidad=None, fecha_registro=None):
        self.id = id
        self.tipo = tipo  # 'papel', 'tinta_color', 'tinta_negro'
        self.cantidad = cantidad
        self.unidad = unidad  # 'hojas', 'ml', 'paquetes'
        self.fecha_registro = fecha_registro