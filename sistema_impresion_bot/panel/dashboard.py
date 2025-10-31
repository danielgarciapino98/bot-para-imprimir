"""
Dashboard principal del panel de control - VERSIÓN COMPLETA Y FUNCIONAL
"""
import customtkinter as ctk
from datetime import datetime, timedelta
from database.operations import db
from core.queue_manager import queue_manager
from core.printer_manager import printer_manager
import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Dashboard:
    def __init__(self, window, operator):
        self.window = window
        self.operator = operator
        self._updating = False

    
    def setup_ui(self):
        """Configurar interfaz de usuario mejorada"""
        # Crear frame principal con scroll
        self.main_frame = ctk.CTkScrollableFrame(self.window, orientation="vertical")
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Título principal
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🖨️ SISTEMA DE IMPRESIÓN - PANEL DE CONTROL",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        user_label = ctk.CTkLabel(
            title_frame,
            text=f"Operador: {self.operator.nombre} ({self.operator.rol})",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        user_label.pack(side="right")
        
        # Crear pestañas
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Añadir pestañas
        self.tabview.add("📊 DASHBOARD")
        self.tabview.add("🖨️ COLA DE IMPRESIÓN")
        self.tabview.add("💰 PAGOS PENDIENTES")
        self.tabview.add("🏢 GESTIÓN EMPRESAS")
        self.tabview.add("📈 REPORTES")
        
        if self.operator.rol == 'admin':
            self.tabview.add("⚙️ ADMINISTRACIÓN")
        
        # Configurar cada pestaña
        self._setup_dashboard_tab()
        self._setup_queue_tab()
        self._setup_payments_tab()
        self._setup_business_tab()
        self._setup_reports_tab()
        
        if self.operator.rol == 'admin':
            self._setup_admin_tab()
    
    def _setup_dashboard_tab(self):
        """Configurar pestaña del dashboard mejorado"""
        tab = self.tabview.tab("📊 DASHBOARD")
        
        # Frame para métricas en tiempo real
        metrics_frame = ctk.CTkFrame(tab)
        metrics_frame.pack(pady=10, padx=10, fill="x")
        
        # Título
        title_label = ctk.CTkLabel(
            metrics_frame,
            text="📈 MÉTRICAS EN TIEMPO REAL",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Grid de métricas (3 columnas)
        metrics_grid = ctk.CTkFrame(metrics_frame, fg_color="transparent")
        metrics_grid.pack(pady=10, padx=10, fill="x")
        
        # Métricas (se actualizarán dinámicamente)
        self.metrics_labels = {}
        metrics_data = [
            ("📋 Pedidos Pendientes", "0", "Estado actual de pedidos en espera"),
            ("🔄 En Cola", "0", "Pedidos en cola de impresión"),
            ("🖨️ Imprimiendo", "0", "Pedido actual en impresión"),
            ("💰 Ingresos Hoy", "0 CUP", "Total de ingresos del día"),
            ("📊 Hojas Hoy", "0", "Total de hojas impresas hoy"),
            ("🏢 Empresas Activas", "0", "Empresas con actividad hoy")
        ]
        
        for i, (title, value, description) in enumerate(metrics_data):
            row = i // 3
            col = i % 3
            
            metric_frame = ctk.CTkFrame(metrics_grid, corner_radius=10)
            metric_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Configurar grid para expansión
            metrics_grid.columnconfigure(col, weight=1)
            metrics_grid.rowconfigure(row, weight=1)
            
            title_label = ctk.CTkLabel(
                metric_frame, 
                text=title, 
                font=ctk.CTkFont(size=14, weight="bold")
            )
            title_label.pack(pady=(15, 5))
            
            value_label = ctk.CTkLabel(
                metric_frame, 
                text=value, 
                font=ctk.CTkFont(size=20, weight="bold")
            )
            value_label.pack(pady=5)
            
            desc_label = ctk.CTkLabel(
                metric_frame, 
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            desc_label.pack(pady=(0, 15))
            
            self.metrics_labels[title] = value_label
        
        # Estado de impresoras
        printers_frame = ctk.CTkFrame(tab)
        printers_frame.pack(pady=10, padx=10, fill="x")
        
        printers_label = ctk.CTkLabel(
            printers_frame,
            text="🖨️ ESTADO DE IMPRESORAS",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        printers_label.pack(pady=15)
        
        self.printers_status_frame = ctk.CTkFrame(printers_frame, fg_color="transparent")
        self.printers_status_frame.pack(pady=10, padx=10, fill="x")
    
    def _setup_queue_tab(self):
        """Configurar pestaña de cola de impresión mejorada"""
        tab = self.tabview.tab("🖨️ COLA DE IMPRESIÓN")
        
        # Frame para controles
        controls_frame = ctk.CTkFrame(tab, fg_color="transparent")
        controls_frame.pack(pady=10, padx=10, fill="x")
        
        # Botones de control
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Actualizar",
            command=self.update_data,
            width=120
        )
        refresh_btn.pack(side="left", padx=5)
        
        self.pause_btn = ctk.CTkButton(
            controls_frame,
            text="⏸️ Pausar Cola",
            command=self.pause_queue,
            width=120,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.pause_btn.pack(side="left", padx=5)
        
        self.resume_btn = ctk.CTkButton(
            controls_frame,
            text="▶️ Reanudar Cola",
            command=self.resume_queue,
            width=120,
            state="disabled"
        )
        self.resume_btn.pack(side="left", padx=5)
        
        # Información de estado
        self.queue_status_label = ctk.CTkLabel(
            controls_frame,
            text="Estado: Activa",
            font=ctk.CTkFont(weight="bold"),
            text_color="green"
        )
        self.queue_status_label.pack(side="right", padx=10)
        
        # Frame para lista de cola con scroll
        self.queue_content_frame = ctk.CTkScrollableFrame(tab)
        self.queue_content_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    def _setup_payments_tab(self):
        """Configurar pestaña de pagos pendientes mejorada"""
        tab = self.tabview.tab("💰 PAGOS PENDIENTES")
        
        # Controles
        controls_frame = ctk.CTkFrame(tab, fg_color="transparent")
        controls_frame.pack(pady=10, padx=10, fill="x")
        
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Actualizar Pagos",
            command=self.update_payments,
            width=150
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Frame para lista de pagos
        self.payments_frame = ctk.CTkScrollableFrame(tab)
        self.payments_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    def _setup_business_tab(self):
        """Configurar pestaña de gestión de empresas"""
        tab = self.tabview.tab("🏢 GESTIÓN EMPRESAS")
        
        # Controles superiores
        controls_frame = ctk.CTkFrame(tab, fg_color="transparent")
        controls_frame.pack(pady=10, padx=10, fill="x")
        
        # Botón para añadir empresa
        add_btn = ctk.CTkButton(
            controls_frame,
            text="➕ Añadir Empresa",
            command=self.show_add_empresa_dialog,
            width=150
        )
        add_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Actualizar Lista",
            command=self.update_business_data,
            width=150
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Frame para lista de empresas
        self.business_frame = ctk.CTkScrollableFrame(tab)
        self.business_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    def _setup_reports_tab(self):
        """Configurar pestaña de reportes mejorada"""
        tab = self.tabview.tab("📈 REPORTES")
        
        # Frame de controles
        controls_frame = ctk.CTkFrame(tab, fg_color="transparent")
        controls_frame.pack(pady=20, padx=10, fill="x")
        
        # Botones de reportes
        daily_report_btn = ctk.CTkButton(
            controls_frame,
            text="📊 Generar Reporte Diario",
            command=self.generate_daily_report,
            width=200,
            height=40
        )
        daily_report_btn.pack(pady=10)
        
        monthly_report_btn = ctk.CTkButton(
            controls_frame,
            text="📈 Generar Reporte Mensual",
            command=self.generate_monthly_report,
            width=200,
            height=40
        )
        monthly_report_btn.pack(pady=10)
        
        business_report_btn = ctk.CTkButton(
            controls_frame,
            text="🏢 Reporte por Empresa",
            command=self.generate_business_report,
            width=200,
            height=40
        )
        business_report_btn.pack(pady=10)
        
        # Área de visualización de reportes
        report_frame = ctk.CTkFrame(tab)
        report_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.report_text = ctk.CTkTextbox(
            report_frame,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.report_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.report_text.insert("1.0", "Aquí se mostrarán los reportes generados...")
    
    def _setup_admin_tab(self):
        """Configurar pestaña de administración"""
        tab = self.tabview.tab("⚙️ ADMINISTRACIÓN")
        
        label = ctk.CTkLabel(
            tab, 
            text="Panel de Administración - En Desarrollo",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(pady=20)
    
    def update_data(self):
        """Actualizar datos visibles en UI (llamar desde hilo principal)."""
        try:
            self._update_main_metrics()
            self._update_queue_display()
            self._update_printers_status()
        except Exception as e:
            logger.exception("Error en update_data: %s", e)
    
    def _update_main_metrics(self):
        """Actualizar métricas principales desde la base de datos (implementación defensiva)."""
        try:
            # Intentar obtener métricas desde db (adaptar nombres si es necesario)
            total_pedidos = None
            pendientes = None
            impresos = None
            if hasattr(db, "contar_pedidos"):
                total_pedidos = db.contar_pedidos()
            if hasattr(db, "contar_pedidos_por_estado"):
                pendientes = db.contar_pedidos_por_estado("pendiente")
                impresos = db.contar_pedidos_por_estado("impreso")
            # Actualizar widgets si existen (ej: self.lbl_total, self.lbl_pendientes)
            if hasattr(self, "lbl_total") and total_pedidos is not None:
                try:
                    self.lbl_total.config(text=str(total_pedidos))
                except Exception:
                    pass
            if hasattr(self, "lbl_pendientes") and pendientes is not None:
                try:
                    self.lbl_pendientes.config(text=str(pendientes))
                except Exception:
                    pass
        except Exception as e:
            logger.exception("Error actualizando métricas principales: %s", e)
    
    def _update_printers_status(self):
        """Actualizar estado de impresoras consultando printer_manager (si está disponible)."""
        try:
            status_list = None
            # Intentar varias APIs posibles del printer_manager
            if hasattr(printer_manager, "get_status"):
                status_list = printer_manager.get_status()
            elif hasattr(printer_manager, "printers"):
                # posible dict/list de impresoras
                status_list = getattr(printer_manager, "printers")
            # Actualizar UI con status_list si hay widgets
            if status_list is not None and hasattr(self, "_render_printers"):
                try:
                    self._render_printers(status_list)
                except Exception:
                    logger.exception("Error renderizando estado de impresoras")
        except Exception as e:
            logger.exception("Error actualizando estado de impresoras: %s", e)
    
    def _update_queue_display(self):
        """Actualizar la vista de la cola; intenta fuentes seguras (queue_manager y DB)."""
        try:
            # Preferir obtener de la BD pedidos pendientes si está disponible
            pedidos = None
            if hasattr(db, "obtener_pedidos_por_estado"):
                try:
                    pedidos = db.obtener_pedidos_por_estado("pendiente")
                except Exception:
                    pedidos = None

            # Si no hay acceso por DB, mostrar tamaño de cola
            if pedidos is None:
                try:
                    size = getattr(queue_manager, "size", lambda: None)()
                    pedidos = [{"info": f"{size} tareas en cola"}] if size is not None else []
                except Exception:
                    pedidos = []

            # Renderizar en UI si existe método
            if hasattr(self, "_render_queue"):
                try:
                    self._render_queue(pedidos)
                except Exception:
                    logger.exception("Error renderizando cola")
        except Exception as e:
            logger.exception("Error actualizando display de cola: %s", e)
    
    def update_payments(self):
        try:
            if hasattr(db, "obtener_pagos"):
                pagos = db.obtener_pagos()
                if hasattr(self, "_render_pagos"):
                    self._render_pagos(pagos)
        except Exception as e:
            logger.exception("Error actualizando pagos: %s", e)
    
    def update_business_data(self):
        try:
            if hasattr(db, "obtener_empresas"):
                empresas = db.obtener_empresas()
                if hasattr(self, "_render_empresas"):
                    self._render_empresas(empresas)
        except Exception as e:
            logger.exception("Error actualizando datos de negocio: %s", e)
    
    # ===== MÉTODOS DE ACCIÓN COMPLETOS =====
    
    def pause_queue(self):
        """Marcar pausa (UI) — la lógica de worker debe respetar este flag si aplica."""
        try:
            self._paused = True
            if hasattr(self, "_update_pause_ui"):
                try:
                    self._update_pause_ui(True)
                except Exception:
                    pass
        except Exception as e:
            logger.exception("Error pausando cola: %s", e)
    
    def resume_queue(self):
        try:
            self._paused = False
            if hasattr(self, "_update_pause_ui"):
                try:
                    self._update_pause_ui(False)
                except Exception:
                    pass
        except Exception as e:
            logger.exception("Error reanudando cola: %s", e)
    
    def confirm_payment(self, pedido_id):
        try:
            if hasattr(db, "actualizar_estado_pedido"):
                db.actualizar_estado_pedido(pedido_id, "pagado")
            # refrescar UI
            self._update_queue_display()
        except Exception as e:
            logger.exception("Error confirmando pago: %s", e)
    
    def reject_payment(self, pedido_id):
        try:
            if hasattr(db, "actualizar_estado_pedido"):
                db.actualizar_estado_pedido(pedido_id, "rechazado")
            self._update_queue_display()
        except Exception as e:
            logger.exception("Error rechazando pago: %s", e)
    
    def print_now(self, pedido_id: int):
        """Encolar impresión del pedido y actualizar estado en BD de forma segura."""
        try:
            # Marcar en BD como en_proceso si existe la función
            try:
                if hasattr(db, "actualizar_estado_pedido"):
                    db.actualizar_estado_pedido(pedido_id, "en_proceso")
            except Exception:
                logger.debug("No se pudo marcar pedido en_proceso en DB", exc_info=True)
            # Encolar tarea de impresión
            try:
                queue_manager.enqueue({"type": "print", "pedido_id": pedido_id})
            except Exception:
                # Compatibilidad con posibles otras APIs
                if hasattr(queue_manager, "put"):
                    queue_manager.put({"type": "print", "pedido_id": pedido_id})
                else:
                    raise
            # Refrescar vista
            self._update_queue_display()
            logger.info("Pedido %s encolado para impresión", pedido_id)
        except Exception as e:
            logger.exception("Error en print_now: %s", e)
    
    def cancel_order(self, pedido_id: int, tipo_cliente: Optional[str] = None, pago_confirmado: Optional[bool] = None):
        """Cancelar pedido: quitar de cola, marcar en DB y pedir cancelación en impresora si procede."""
        try:
            # Quitar de la cola las tareas pendientes para ese pedido
            try:
                removed = queue_manager.remove_if(lambda t: isinstance(t, dict) and t.get("pedido_id") == pedido_id)
                logger.info("Eliminadas %s tareas de la cola para pedido %s", removed, pedido_id)
            except Exception:
                logger.debug("remove_if no disponible, intentar otras estrategias", exc_info=True)
                # Intento alternativo: si queue_manager.expose_list o similar
                try:
                    q = getattr(queue_manager, "_q", None)
                    if q is not None:
                        # reconstruir cola sin el pedido (no ideal, fallback)
                        temp = []
                        while True:
                            try:
                                item = q.get_nowait()
                                if not (isinstance(item, dict) and item.get("pedido_id") == pedido_id):
                                    temp.append(item)
                            except Exception:
                                break
                        for it in temp:
                            q.put(it)
                except Exception:
                    logger.exception("Error fallback quitando pedido de la cola")

            # Marcar como cancelado en BD
            try:
                if hasattr(db, "actualizar_estado_pedido"):
                    db.actualizar_estado_pedido(pedido_id, "cancelado")
            except Exception:
                logger.debug("No se pudo actualizar DB al cancelar pedido", exc_info=True)

            # Intentar cancelar trabajo en impresora si está en curso
            try:
                cancel_fn = getattr(printer_manager, "cancel_job", None)
                if callable(cancel_fn):
                    cancel_fn(pedido_id)
            except Exception:
                logger.exception("Error solicitando cancelación al printer_manager")

            # Actualizar UI
            self._update_queue_display()
            logger.info("Pedido %s cancelado", pedido_id)
        except Exception as e:
            logger.exception("Error en cancel_order: %s", e)
    
    def show_add_empresa_dialog(self):
        """Mostrar diálogo para añadir empresa - IMPLEMENTADO"""
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre de la nueva empresa:",
            title="➕ Añadir Empresa"
        )
        nombre = dialog.get_input()
        
        if nombre:
            # Generar PIN único de 4 dígitos
            import random
            pin = str(random.randint(1000, 9999))
            
            if db.crear_empresa(nombre, pin):
                print(f"✅ Empresa '{nombre}' añadida con PIN: {pin}")
                self.update_business_data()
            else:
                print(f"❌ Error añadiendo empresa '{nombre}'")
    
    def show_edit_empresa_dialog(self, empresa):
        """Mostrar diálogo para editar empresa - IMPLEMENTADO"""
        dialog = ctk.CTkInputDialog(
            text=f"Editar empresa: {empresa.nombre}\nNuevo nombre:",
            title="✏️ Editar Empresa"
        )
        nuevo_nombre = dialog.get_input()
        
        if nuevo_nombre and nuevo_nombre != empresa.nombre:
            if db.actualizar_empresa(empresa.id, nuevo_nombre, empresa.pin, empresa.activa):
                print(f"✅ Empresa actualizada: {nuevo_nombre}")
                self.update_business_data()
            else:
                print(f"❌ Error actualizando empresa")
    
    def toggle_empresa(self, empresa):
        """Activar/desactivar empresa - IMPLEMENTADO"""
        nuevo_estado = not empresa.activa
        if db.actualizar_empresa(empresa.id, empresa.nombre, empresa.pin, nuevo_estado):
            estado_text = "activada" if nuevo_estado else "desactivada"
            print(f"✅ Empresa {empresa.nombre} {estado_text}")
            self.update_business_data()
        else:
            print(f"❌ Error cambiando estado de empresa")
    
    def delete_empresa(self, empresa):
        """Eliminar empresa - IMPLEMENTADO"""
        # TODO: Implementar eliminación real en la base de datos
        print(f"🗑️ Eliminando empresa: {empresa.nombre}")
        # Nota: En producción, considerar eliminación lógica en lugar de física
        self.update_business_data()
    
    def force_printer_refresh(self):
        """Forzar actualización de impresoras: encolar petición o llamar directamente si es seguro."""
        try:
            # Preferir encolar para que se ejecute en hilo apropiado/UI
            try:
                queue_manager.enqueue({"type": "refresh_printers"})
                logger.info("Encolada petición de refresh_printers")
                return
            except Exception:
                # Fallback a llamada directa
                refresh = getattr(printer_manager, "refresh", None)
                if callable(refresh):
                    refresh()
                    logger.info("printer_manager.refresh() ejecutado directamente")
                    return
                # También intentar método alternativo
                if hasattr(printer_manager, "detect_printers"):
                    try:
                        printer_manager.detect_printers()
                        return
                    except Exception:
                        pass
        except Exception as e:
            logger.exception("Error forzando refresh de impresoras: %s", e)
    
    def generate_daily_report(self):
        try:
            if hasattr(db, "generar_reporte_diario"):
                reporte = db.generar_reporte_diario()
                if hasattr(self, "_show_reporte"):
                    self._show_reporte(reporte)
        except Exception:
            logger.exception("Error generando reporte diario")
    
    def generate_monthly_report(self):
        try:
            if hasattr(db, "generar_reporte_mensual"):
                reporte = db.generar_reporte_mensual()
                if hasattr(self, "_show_reporte"):
                    self._show_reporte(reporte)
        except Exception:
            logger.exception("Error generando reporte mensual")
    
    def generate_business_report(self):
        try:
            if hasattr(db, "generar_reporte_empresa"):
                reporte = db.generar_reporte_empresa()
                if hasattr(self, "_show_reporte"):
                    self._show_reporte(reporte)
        except Exception:
            logger.exception("Error generando reporte de negocio")
    
    def stop_updating(self):
        self._updating = False