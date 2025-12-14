"""
Event Base Classes - Clases base para el sistema de eventos.

Define la estructura base de todos los eventos del sistema.
"""
import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Event(ABC):
    """
    Clase base para todos los eventos del sistema.

    Todos los eventos deben heredar de esta clase y definir
    sus campos específicos como dataclass fields.

    Attributes:
        event_id: ID único del evento (generado automáticamente)
        timestamp: Momento en que ocurrió el evento
        user_id: ID del usuario relacionado (opcional)
        metadata: Datos adicionales del evento

    Examples:
        >>> @dataclass
        >>> class UserJoinedVIPEvent(Event):
        ...     plan_name: str
        ...     duration_days: int
    """

    # Campos automáticos (no deben ser sobrescritos)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Campos opcionales comunes
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Retorna el tipo de evento (nombre de la clase)."""
        return self.__class__.__name__

    def __str__(self) -> str:
        """Representación string del evento."""
        return f"{self.event_type}(user_id={self.user_id}, timestamp={self.timestamp})"
