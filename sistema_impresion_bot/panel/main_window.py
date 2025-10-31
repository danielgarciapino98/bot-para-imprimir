"""
MainWindow simple: crea un único root, muestra login modal, luego dashboard básico.
No usa lambdas en after; es seguro con el bot en thread aparte.
"""
import logging
import tkinter as tk
try:
    import customtkinter as ctk
except Exception:
    ctk = None

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self):
        # único root
        if ctk and hasattr(ctk, "CTk"):
            self.root = ctk.CTk()
            self.Frame = ctk.CTkFrame
            self.Label = ctk.CTkLabel
            self.Button = ctk.CTkButton
            self.Listbox = None  # customtkinter no tiene listbox; usaremos tk.Listbox si hace falta
        else:
            self.root = tk.Tk()
            self.Frame = tk.Frame
            self.Label = tk.Label
            self.Button = tk.Button
        self.root.title("Panel de Control - Sistema de Impresión")
        try:
            self.root.geometry("700x420")
        except Exception:
            pass

        self.operator = None
        self.dashboard_frame = None

    def _show_login(self):
        from panel.login_window import LoginWindow
        login = LoginWindow(parent=self.root)
        operador = login.show()  # modal
        return operador

    def _build_dashboard(self):
        # limpiar contenido si existe
        for w in self.root.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        header = self.Frame(self.root)
        header.pack(fill="x", padx=12, pady=8)
        title = self.Label(header, text=f"Operador: {self.operator.get('username') if self.operator else 'Invitado'}", anchor="w")
        try:
            title.pack(side="left")
        except Exception:
            title.pack(anchor="w")

        btn_logout = self.Button(header, text="Cerrar sesión", command=self._on_logout)
        try:
            btn_logout.pack(side="right")
        except Exception:
            btn_logout.pack(anchor="e")

        body = self.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12, pady=(4,12))

        # Panel simple: lista de impresoras (si existen) y botones de acción
        printers_label = self.Label(body, text="Impresoras detectadas:")
        printers_label.pack(anchor="nw")

        # intentar obtener impresoras desde core.printer_manager si existe
        printers = []
        try:
            from core.printer_manager import printer_manager
            printers = getattr(printer_manager, "list_printers", lambda: [])() or []
        except Exception:
            # fallback: intentar obtener atributo printers si existe
            try:
                from core import printer_manager
                printers = getattr(printer_manager, "detected", []) or []
            except Exception:
                printers = []

        # usar tk.Listbox para compatibilidad
        lb = tk.Listbox(body, height=8)
        lb.pack(fill="x", pady=(6,12))
        if printers:
            for p in printers:
                try:
                    lb.insert("end", str(p))
                except Exception:
                    pass
        else:
            lb.insert("end", "No hay impresoras detectadas")

        controls = self.Frame(body)
        controls.pack(fill="x")
        btn_refresh = self.Button(controls, text="Refrescar impresoras", command=self._refresh_printers)
        try:
            btn_refresh.pack(side="left")
        except Exception:
            btn_refresh.pack(anchor="w")
        btn_exit = self.Button(controls, text="Salir", command=self.close)
        try:
            btn_exit.pack(side="right")
        except Exception:
            btn_exit.pack(anchor="e")

    def _on_logout(self):
        self.operator = None
        # mostrar login de nuevo
        operador = self._show_login()
        if operador:
            self.operator = operador
        # reconstruir dashboard con nuevo operador (o invitado)
        self._build_dashboard()

    def _refresh_printers(self):
        # simple: reconstruir dashboard (intenta leer impresoras otra vez)
        self._build_dashboard()

    def run(self):
        # mostrar login modal
        operador = self._show_login()
        if operador:
            self.operator = operador
        else:
            # si se cerró el login, salir
            try:
                self.root.destroy()
            except Exception:
                pass
            return

        # construir dashboard y entrar en mainloop
        self._build_dashboard()
        try:
            self.root.mainloop()
        except Exception:
            logger.exception("mainloop finalizó con excepción", exc_info=True)

    def close(self):
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass