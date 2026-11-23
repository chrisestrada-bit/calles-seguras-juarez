"""Limitador de ventana deslizante en memoria (por proceso).

Protege la cuota de geocodificación y frena el abuso de registro e inicio de sesión. Al vivir en memoria,
con varias réplicas cada una lleva su propia cuenta (documentado en docs/auditoria-final/).
"""

import threading
import time
from collections import defaultdict, deque


class LimitadorVentana:
    def __init__(self, maximo: int, ventana_segundos: float) -> None:
        self.maximo = maximo
        self.ventana = ventana_segundos
        self._eventos: dict[str, deque[float]] = defaultdict(deque)
        self._candado = threading.Lock()

    def _purgar(self, cola: deque[float], ahora: float) -> None:
        while cola and ahora - cola[0] >= self.ventana:
            cola.popleft()

    def _espera(self, cola: deque[float], ahora: float) -> int | None:
        if len(cola) >= self.maximo:
            return max(1, int(self.ventana - (ahora - cola[0])) + 1)
        return None

    def intentar(self, clave: str) -> int | None:
        """Registra un uso. Devuelve None si se permite o los segundos de espera si se excede."""
        ahora = time.monotonic()
        with self._candado:
            cola = self._eventos[clave]
            self._purgar(cola, ahora)
            espera = self._espera(cola, ahora)
            if espera is None:
                cola.append(ahora)
            return espera

    def consultar(self, clave: str) -> int | None:
        """Como `intentar`, pero sin registrar el uso (p. ej. comprobar un bloqueo antes de validar)."""
        ahora = time.monotonic()
        with self._candado:
            if clave not in self._eventos:
                return None
            cola = self._eventos[clave]
            self._purgar(cola, ahora)
            return self._espera(cola, ahora)

    def registrar(self, clave: str) -> None:
        ahora = time.monotonic()
        with self._candado:
            cola = self._eventos[clave]
            self._purgar(cola, ahora)
            cola.append(ahora)

    def olvidar(self, clave: str) -> None:
        with self._candado:
            self._eventos.pop(clave, None)

    def limpiar(self) -> None:
        with self._candado:
            self._eventos.clear()
