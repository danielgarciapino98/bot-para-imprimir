"""
Login modal simple y fiable.
Devuelve un dict {'username': ...} si login ok, o None si se cierra/cancela.
"""
import logging
import tkinter as tk
try:
    import customtkinter as ctk
except Exception:
    ctk = None

logger = logging.getLogger(__name__)

class LoginWindow:
    def __init__(self, parent=None):
        self.parent = parent
        self.is_root = parent is None
        self.result = None

        # Crear ventana: Toplevel si hay parent, si no root
        if self.parent:
            if ctk and hasattr(ctk, "CTkToplevel"):
                self.win = ctk.CTkToplevel(self.parent)
            else:
                self.win = tk.Toplevel(self.parent)
        else:
            if ctk and hasattr(ctk, "CTk"):
                self.win = ctk.CTk()
            else:
                self.win = tk.Tk()

        self.win.title("Login")
        try:
            self.win.resizable(False, False)
        except Exception:
            pass

        self._build_ui()

        # when modal, ensure proper close handling
        try:
            self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass

    def _build_ui(self):
        Frame = ctk.CTkFrame if ctk else tk.Frame
        Entry = ctk.CTkEntry if ctk else tk.Entry
        Button = ctk.CTkButton if ctk else tk.Button
        Label = ctk.CTkLabel if ctk else tk.Label

        frame = Frame(self.win)
        frame.pack(padx=20, pady=16, fill="x")

        Label(frame, text="Usuario:").pack(anchor="w")
        self.entry_user = Entry(frame)
        self.entry_user.pack(fill="x", pady=(0,8))

        Label(frame, text="PIN/Clave (opcional):").pack(anchor="w")
        self.entry_pass = Entry(frame, show="*")
        self.entry_pass.pack(fill="x", pady=(0,12))

        btn_frame = Frame(frame)
        btn_frame.pack(fill="x")
        submit = Button(btn_frame, text="Ingresar", command=self._on_submit)
        submit.pack(side="left", expand=True, fill="x", padx=(0,6))
        cancel = Button(btn_frame, text="Cancelar", command=self._on_close)
        cancel.pack(side="left", expand=True, fill="x")

        # focus
        try:
            self.entry_user.focus_set()
        except Exception:
            pass

    def _on_submit(self):
        username = ""
        try:
            username = (self.entry_user.get() or "").strip()
        except Exception:
            username = ""

        # validación simple: usuario no vacío -> success
        if username:
            # puedes integrar aquí DB real: from database.operations import db ...
            self.result = {"username": username}
            self._close_and_return()
        else:
            # feedback sencillo: marcar campo
            try:
                self.entry_user.delete(0, "end")
                self.entry_user.insert(0, "")
                self.entry_user.focus_set()
            except Exception:
                pass

    def _on_close(self):
        self.result = None
        self._close_and_return()

    def _close_and_return(self):
        try:
            # si es Toplevel soltamos grab (si hubo)
            try:
                self.win.grab_release()
            except Exception:
                pass
            self.win.destroy()
        except Exception:
            pass

    def show(self):
        """Mostrar modal: si hay parent hace grab_set/wait_window; si no, mainloop."""
        if self.is_root:
            try:
                self.win.deiconify()
                self.win.mainloop()
            except Exception:
                logger.exception("Error en mainloop de login", exc_info=True)
            return self.result
        else:
            try:
                self.win.transient(self.parent)
            except Exception:
                pass
            try:
                self.win.grab_set()
            except Exception:
                pass
            try:
                self.win.deiconify()
                self.win.wait_window()
            except Exception:
                logger.exception("Error mostrando login modal", exc_info=True)
            return self.result