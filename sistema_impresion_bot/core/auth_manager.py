"""
Gestión de autenticación y autorización
"""
import hashlib
import time
from database.operations import db

class AuthManager:
    def __init__(self):
        self.failed_attempts = {}
        self.lockout_time = 300  # 5 minutos en segundos
    
    def authenticate_operator(self, username, password):
        """Autenticar operador"""
        # Limpiar intentos fallidos antiguos
        self._clean_old_attempts()
        
        # Verificar si está bloqueado
        if self._is_locked_out(username):
            return None, "Cuenta bloqueada temporalmente por demasiados intentos fallidos"
        
        # Verificar credenciales
        operator = db.verificar_operador(username, password)
        
        if operator:
            # Resetear intentos fallidos en éxito
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            return operator, "Autenticación exitosa"
        else:
            # Registrar intento fallido
            self._register_failed_attempt(username)
            attempts = self.failed_attempts[username]['count']
            remaining = 3 - attempts
            
            if remaining <= 0:
                return None, "Cuenta bloqueada. Intenta nuevamente en 5 minutos"
            else:
                return None, f"Credenciales incorrectas. Te quedan {remaining} intentos"
    
    def _register_failed_attempt(self, username):
        """Registrar intento fallido"""
        now = time.time()
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {'count': 0, 'first_attempt': now}
        
        self.failed_attempts[username]['count'] += 1
        self.failed_attempts[username]['last_attempt'] = now
    
    def _is_locked_out(self, username):
        """Verificar si el usuario está bloqueado"""
        if username not in self.failed_attempts:
            return False
        
        attempts_info = self.failed_attempts[username]
        
        # Si ha pasado el tiempo de bloqueo, resetear
        if time.time() - attempts_info.get('first_attempt', 0) > self.lockout_time:
            del self.failed_attempts[username]
            return False
        
        # Bloquear después de 3 intentos fallidos
        return attempts_info['count'] >= 3
    
    def _clean_old_attempts(self):
        """Limpiar intentos fallidos antiguos"""
        now = time.time()
        usernames_to_remove = []
        
        for username, attempts_info in self.failed_attempts.items():
            if now - attempts_info.get('first_attempt', 0) > self.lockout_time:
                usernames_to_remove.append(username)
        
        for username in usernames_to_remove:
            del self.failed_attempts[username]
    
    def has_permission(self, operator, permission):
        """Verificar si un operador tiene un permiso específico"""
        if operator.rol == 'admin':
            return True
        
        # Definir permisos por rol
        permissions = {
            'operador': [
                'view_dashboard', 'view_queue', 'confirm_payments',
                'manage_prints', 'add_notes', 'view_reports'
            ],
            'admin': [
                'view_dashboard', 'view_queue', 'confirm_payments',
                'manage_prints', 'add_notes', 'view_reports',
                'manage_operators', 'system_config', 'database_management'
            ]
        }
        
        return permission in permissions.get(operator.rol, [])

# Instancia global
auth_manager = AuthManager()