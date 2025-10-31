"""
Gestión de colas de impresión
"""
import threading
import queue
import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class QueueManager:
    """
    Manager simple de cola de tareas seguro para hilos.
    Métodos expuestos para compatibilidad con el código existente:
     - enqueue(task)
     - get_nowait() -> task or None
     - pop_task() -> task or None (sin bloqueo)
     - remove_if(predicate) -> elimina tareas que cumplan predicate
     - start_worker(processor) -> inicia worker que llama processor(task)
    """
    def __init__(self):
        self._q = queue.Queue()
        self._lock = threading.Lock()
        self._worker = None
        self._worker_stop = threading.Event()

    def enqueue(self, task: Any) -> None:
        """Añadir tarea a la cola"""
        self._q.put(task)
        logger.debug("Tarea encolada: %s", task)

    def get_nowait(self):
        """Intentar obtener tarea sin bloquear, devolver None si vacía"""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def pop_task(self):
        """Alias no bloqueante para obtener una tarea"""
        return self.get_nowait()

    def remove_if(self, predicate: Callable[[Any], bool]) -> int:
        """
        Eliminar tareas que cumplan predicate.
        Devuelve el número de tareas eliminadas.
        Nota: operación no muy eficiente pero segura.
        """
        removed = 0
        temp = []
        # vaciar cola
        while True:
            try:
                t = self._q.get_nowait()
                if predicate(t):
                    removed += 1
                else:
                    temp.append(t)
            except queue.Empty:
                break
        # devolver tareas no eliminadas
        for t in temp:
            self._q.put(t)
        if removed:
            logger.info("QueueManager: eliminadas %d tareas", removed)
        return removed

    def size(self) -> int:
        return self._q.qsize()

    def start_worker(self, processor: Callable[[Any], None], poll_interval: float = 0.2, name: str = "queue_worker"):
        """
        Inicia un hilo daemon que tomará tareas y llamará processor(task).
        Si ya existe un worker corriendo, no hace nada.
        """
        if self._worker and self._worker.is_alive():
            return

        def _loop():
            logger.info("QueueManager: worker iniciado")
            while not self._worker_stop.is_set():
                try:
                    task = self._q.get(timeout=poll_interval)
                except queue.Empty:
                    continue
                try:
                    processor(task)
                except Exception:
                    logger.exception("Error procesando tarea: %s", task)
                finally:
                    try:
                        self._q.task_done()
                    except Exception:
                        pass
            logger.info("QueueManager: worker detenido")

        self._worker_stop.clear()
        self._worker = threading.Thread(target=_loop, daemon=True, name=name)
        self._worker.start()

    def stop_worker(self, wait: bool = False):
        """Pide detener el worker; si wait True hace join()."""
        self._worker_stop.set()
        if wait and self._worker:
            self._worker.join(timeout=2)

# Instancia global usada por el resto del proyecto
queue_manager = QueueManager()