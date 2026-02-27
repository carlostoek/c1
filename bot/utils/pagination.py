"""
Pagination Utilities - Sistema de paginación reutilizable.

Proporciona herramientas para:
- Paginar listas largas de elementos
- Generar keyboards de navegación
- Calcular offsets y límites
- Formatear headers de página
"""
import math
import re
from typing import List, TypeVar, Generic, Callable, Optional
from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup
from bot.utils.keyboards import create_inline_keyboard


T = TypeVar('T')  # Tipo genérico para elementos


@dataclass
class Page(Generic[T]):
    """
    Representa una página de elementos.

    Attributes:
        items: Lista de elementos en esta página
        current_page: Número de página actual (1-indexed)
        total_pages: Total de páginas disponibles
        total_items: Total de elementos en todas las páginas
        has_previous: Si hay página anterior
        has_next: Si hay página siguiente
        page_size: Número de elementos por página
    """

    items: List[T]
    current_page: int
    total_pages: int
    total_items: int
    has_previous: bool
    has_next: bool
    page_size: int

    @property
    def is_empty(self) -> bool:
        """Verifica si la página está vacía."""
        return len(self.items) == 0

    @property
    def start_index(self) -> int:
        """Índice del primer elemento de la página (1-indexed)."""
        if self.is_empty:
            return 0
        return (self.current_page - 1) * self.page_size + 1

    @property
    def end_index(self) -> int:
        """Índice del último elemento de la página (1-indexed)."""
        if self.is_empty:
            return 0
        return self.start_index + len(self.items) - 1


class Paginator(Generic[T]):
    """
    Paginador genérico para listas de elementos.

    Uso:
        # Crear paginador
        paginator = Paginator(items=my_list, page_size=10)

        # Obtener página específica
        page = paginator.get_page(page_number=2)

        # Verificar propiedades
        if page.has_next:
            next_page = paginator.get_page(page.current_page + 1)

    Attributes:
        items: Lista completa de elementos
        page_size: Número de elementos por página (default: 10)
    """

    def __init__(self, items: List[T], page_size: int = 10):
        """
        Inicializa el paginador.

        Args:
            items: Lista de elementos a paginar
            page_size: Número de elementos por página (default: 10)

        Raises:
            ValueError: Si page_size < 1
        """
        if page_size < 1:
            raise ValueError("page_size debe ser >= 1")

        self.items = items
        self.page_size = page_size
        self.total_items = len(items)
        self.total_pages = max(1, math.ceil(self.total_items / self.page_size))

    def get_page(self, page_number: int) -> Page[T]:
        """
        Obtiene una página específica.

        Args:
            page_number: Número de página (1-indexed)

        Returns:
            Page con los elementos de esa página

        Raises:
            ValueError: Si page_number < 1 o > total_pages
        """
        if page_number < 1:
            raise ValueError(f"page_number debe ser >= 1 (recibido: {page_number})")

        if page_number > self.total_pages:
            raise ValueError(
                f"page_number debe ser <= {self.total_pages} (recibido: {page_number})"
            )

        # Calcular offset y límite
        offset = (page_number - 1) * self.page_size
        limit = self.page_size

        # Extraer items de la página
        page_items = self.items[offset:offset + limit]

        # Determinar si hay páginas anterior/siguiente
        has_previous = page_number > 1
        has_next = page_number < self.total_pages

        return Page(
            items=page_items,
            current_page=page_number,
            total_pages=self.total_pages,
            total_items=self.total_items,
            has_previous=has_previous,
            has_next=has_next,
            page_size=self.page_size
        )

    def get_first_page(self) -> Page[T]:
        """Obtiene la primera página."""
        return self.get_page(1)

    def get_last_page(self) -> Page[T]:
        """Obtiene la última página."""
        return self.get_page(self.total_pages)


def create_pagination_keyboard(
    page: Page,
    callback_pattern: str,
    additional_buttons: Optional[List[List[dict]]] = None,
    back_callback: str = "admin:main"
) -> InlineKeyboardMarkup:
    """
    Crea un keyboard de paginación.

    Genera botones de navegación:
    [◀️ Anterior] [Página X/Y] [Siguiente ▶️]

    Si hay botones adicionales, se agregan arriba de la paginación.

    Args:
        page: Objeto Page con info de paginación
        callback_pattern: Pattern para callbacks de navegación.
            Debe contener {page} que será reemplazado por el número.
            Ejemplo: "vip:subscribers:page:{page}"
        additional_buttons: Lista de filas de botones adicionales (opcional)
        back_callback: Callback para botón "Volver" (default: "admin:main")

    Returns:
        InlineKeyboardMarkup con botones de paginación

    Ejemplos:
        >>> page = Page(items=[...], current_page=2, total_pages=5, ...)
        >>> keyboard = create_pagination_keyboard(
        ...     page=page,
        ...     callback_pattern="vip:subscribers:page:{page}"
        ... )
        # Genera:
        # [◀️ Anterior] [Página 2/5] [Siguiente ▶️]
        # [🔙 Volver]
    """
    buttons = []

    # Agregar botones adicionales si existen
    if additional_buttons:
        buttons.extend(additional_buttons)

    # Fila de navegación
    nav_row = []

    # Botón "Anterior" (solo si hay página anterior)
    if page.has_previous:
        prev_callback = callback_pattern.format(page=page.current_page - 1)
        nav_row.append({
            "text": "◀️ Anterior",
            "callback_data": prev_callback
        })

    # Botón de info de página (no clickeable, pero necesitamos callback)
    # Usamos callback especial que el handler puede ignorar
    nav_row.append({
        "text": f"Página {page.current_page}/{page.total_pages}",
        "callback_data": f"pagination:info:{page.current_page}"
    })

    # Botón "Siguiente" (solo si hay página siguiente)
    if page.has_next:
        next_callback = callback_pattern.format(page=page.current_page + 1)
        nav_row.append({
            "text": "Siguiente ▶️",
            "callback_data": next_callback
        })

    # Agregar fila de navegación solo si no está vacía
    if nav_row:
        buttons.append(nav_row)

    # Botón "Volver"
    buttons.append([{"text": "🔙 Volver", "callback_data": back_callback}])

    return create_inline_keyboard(buttons)


def format_page_header(page: Page, title: str) -> str:
    """
    Formatea un header para una página paginada.

    Args:
        page: Objeto Page con info de paginación
        title: Título del listado

    Returns:
        String HTML formateado con header

    Ejemplos:
        >>> page = Page(items=[...], current_page=2, total_pages=5, total_items=47, ...)
        >>> header = format_page_header(page, "Suscriptores VIP")
        # Output:
        # 📋 <b>Suscriptores VIP</b>
        #
        # <b>Total:</b> 47 elementos
        # <b>Página:</b> 2/5 (mostrando 11-20)
    """
    if page.is_empty:
        return (
            f"📋 <b>{title}</b>\n\n"
            f"<i>No hay elementos para mostrar.</i>"
        )

    header = f"📋 <b>{title}</b>\n\n"
    header += f"<b>Total:</b> {page.total_items} elementos\n"
    header += f"<b>Página:</b> {page.current_page}/{page.total_pages}"

    # Agregar rango de elementos si hay items
    if not page.is_empty:
        header += f" (mostrando {page.start_index}-{page.end_index})"

    return header


def format_items_list(
    items: List[T],
    formatter: Callable[[T, int], str],
    separator: str = "\n"
) -> str:
    """
    Formatea una lista de elementos usando un formatter personalizado.

    Args:
        items: Lista de elementos a formatear
        formatter: Función que toma (item, index) y retorna string
            - item: Elemento a formatear
            - index: Índice en la página (1-indexed)
        separator: Separador entre elementos (default: newline)

    Returns:
        String con todos los elementos formateados

    Ejemplos:
        >>> def format_subscriber(sub, idx):
        ...     return f"{idx}. User {sub.user_id} - {sub.days_remaining} días"
        >>>
        >>> formatted = format_items_list(subscribers, format_subscriber)
        # Output:
        # 1. User 123456 - 15 días
        # 2. User 789012 - 8 días
        # ...
    """
    if not items:
        return ""

    formatted_items = []
    for idx, item in enumerate(items, start=1):
        formatted_item = formatter(item, idx)
        formatted_items.append(formatted_item)

    return separator.join(formatted_items)


# ===== HELPERS PARA CASOS COMUNES =====

def paginate_query_results(
    results: List[T],
    page_number: int,
    page_size: int = 10
) -> Page[T]:
    """
    Helper para paginar resultados de query.

    Uso típico:
        # Obtener todos los resultados de BD
        all_subscribers = await session.execute(query)
        results = all_subscribers.scalars().all()

        # Paginar
        page = paginate_query_results(results, page_number=2, page_size=10)

    Args:
        results: Lista completa de resultados
        page_number: Número de página deseada (1-indexed)
        page_size: Elementos por página (default: 10)

    Returns:
        Page con los elementos de esa página
    """
    paginator = Paginator(items=results, page_size=page_size)
    return paginator.get_page(page_number)


def extract_page_from_callback(callback_data: str, pattern: str) -> int:
    """
    Extrae el número de página de un callback data.

    Args:
        callback_data: String de callback (ej: "vip:subscribers:page:3")
        pattern: Pattern esperado con {page} como placeholder
            (ej: "vip:subscribers:page:{page}")

    Returns:
        Número de página extraído (1-indexed)

    Raises:
        ValueError: Si no se puede extraer el número de página

    Ejemplos:
        >>> extract_page_from_callback(
        ...     "vip:subscribers:page:3",
        ...     "vip:subscribers:page:{page}"
        ... )
        3
    """
    # Convertir pattern a regex
    # Escapar el pattern y luego reemplazar {page} con regex
    regex_pattern = re.escape(pattern)
    regex_pattern = regex_pattern.replace(r"\{page\}", r"(\d+)")

    match = re.match(regex_pattern, callback_data)

    if not match:
        raise ValueError(
            f"Callback data '{callback_data}' no coincide con pattern '{pattern}'"
        )

    page_str = match.group(1)

    try:
        page_number = int(page_str)
        if page_number < 1:
            raise ValueError(f"Número de página inválido: {page_number}")
        return page_number
    except ValueError as e:
        raise ValueError(f"No se pudo parsear número de página: {e}")
