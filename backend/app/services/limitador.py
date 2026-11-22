"""Limitador de ventana deslizante en memoria (por proceso). Protege la cuota de geocodificación."""

import threading
import time
from collections import defaultdict, deque


class LimitadorVentana:
    def __init__(self, maximo: int, ventana_segundos: float) -> None:
        self.maximo = maximo
        self.ventana = ventana_segundos
        self._eventos: dict[str, deque[float]] = defaultdict(deque)
        self._candado = threading.Lock()

    def intentar(self, clave: str) -> int | None:
        """Registra un uso. Devuelve None si se permite o los segundos de espera si se excede."""
        ahora = time.monotonic()
        with self._candado:
            cola = self._eventos[clave]
            while cola and ahora - cola[0] >= self.ventana:
                cola.popleft()
            if len(cola) >= self.maximo:
                return max(1, int(self.ventana - (ahora - cola[0])) + 1)
            cola.append(ahora)
            return None
