"""
Management Handlers - Gestión avanzada de suscriptores y solicitudes.

Handlers para:
- Listar suscriptores VIP con paginación
- Filtrar suscriptores por estado
- Ver detalles de suscriptor individual
- Expulsión manual de suscriptores
- Visualización de cola Free
"""
import logging
from datetime import datetime, timedelta

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.database.models import VIPSubscriber, FreeChannelRequest
from bot.services.container import ServiceContainer
from bot.utils.pagination import (
    paginate_query_results,
    create_pagination_keyboard,
    format_page_header,
    format_items_list,
)
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


# ===== LISTADO DE SUSCRIPTORES VIP =====

@admin_router.callback_query(F.data == "vip:list_subscribers")
async def callback_list_vip_subscribers(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra listado paginado de suscriptores VIP.

    Por defecto muestra solo activos en la página 1.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"👥 Usuario {callback.from_user.id} listando suscriptores VIP")

    await callback.answer("📋 Cargando suscriptores...", show_alert=False)

    # Mostrar página 1, filtro "active"
    await _show_vip_subscribers_page(
        callback=callback,
        session=session,
        page_number=1,
        filter_status="active"
    )


@admin_router.callback_query(F.data.startswith("vip:subscribers:page:"))
async def callback_vip_subscribers_page(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Navega a una página específica de suscriptores VIP.

    Callback data format: "vip:subscribers:page:N:FILTER"

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    # Parsear callback data
    parts = callback.data.split(":")

    try:
        page_number = int(parts[3])
        filter_status = parts[4] if len(parts) > 4 else "active"
    except (IndexError, ValueError) as e:
        logger.error(f"❌ Error parseando callback: {callback.data} - {e}")
        await callback.answer("❌ Error de navegación", show_alert=True)
        return

    logger.debug(
        f"👥 Usuario {callback.from_user.id} navegando a página {page_number}, "
        f"filtro={filter_status}"
    )

    await _show_vip_subscribers_page(
        callback=callback,
        session=session,
        page_number=page_number,
        filter_status=filter_status
    )


@admin_router.callback_query(F.data.startswith("vip:filter:"))
async def callback_vip_filter(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Cambia filtro de visualización de suscriptores.

    Filtros disponibles:
    - active: Solo activos
    - expired: Solo expirados
    - expiring_soon: Próximos a expirar (7 días)
    - all: Todos

    Callback data format: "vip:filter:FILTER"

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    filter_status = callback.data.split(":")[2]

    logger.info(
        f"🔍 Usuario {callback.from_user.id} aplicando filtro: {filter_status}"
    )

    await callback.answer(f"🔍 Filtrando: {_get_filter_name(filter_status)}")

    # Mostrar página 1 con nuevo filtro
    await _show_vip_subscribers_page(
        callback=callback,
        session=session,
        page_number=1,
        filter_status=filter_status
    )


async def _show_vip_subscribers_page(
    callback: CallbackQuery,
    session: AsyncSession,
    page_number: int,
    filter_status: str = "active"
):
    """
    Muestra una página de suscriptores VIP con filtro aplicado.

    Args:
        callback: Callback query
        session: Sesión de BD
        page_number: Número de página a mostrar
        filter_status: Filtro a aplicar (active, expired, expiring_soon, all)
    """
    # Construir query según filtro
    query = select(VIPSubscriber).order_by(VIPSubscriber.expiry_date.desc())

    if filter_status == "active":
        query = query.where(VIPSubscriber.status == "active")
    elif filter_status == "expired":
        query = query.where(VIPSubscriber.status == "expired")
    elif filter_status == "expiring_soon":
        # Próximos 7 días
        cutoff_date = datetime.utcnow() + timedelta(days=7)
        query = query.where(
            and_(
                VIPSubscriber.status == "active",
                VIPSubscriber.expiry_date <= cutoff_date,
                VIPSubscriber.expiry_date > datetime.utcnow()
            )
        )
    # "all" no aplica filtro adicional

    # Ejecutar query
    result = await session.execute(query)
    subscribers = result.scalars().all()

    # Paginar resultados
    page = paginate_query_results(
        results=list(subscribers),
        page_number=page_number,
        page_size=10
    )

    # Formatear mensaje
    filter_name = _get_filter_name(filter_status)
    header = format_page_header(page, f"Suscriptores VIP - {filter_name}")

    if page.is_empty:
        text = f"{header}\n\n<i>No hay suscriptores en esta categoría.</i>"
    else:
        items_text = format_items_list(page.items, _format_vip_subscriber)
        text = f"{header}\n\n{items_text}"

    # Crear keyboard con filtros y paginación
    additional_buttons = [
        # Fila de filtros
        [
            {"text": "✅ Activos" if filter_status == "active" else "Activos",
             "callback_data": "vip:filter:active"},
            {"text": "❌ Expirados" if filter_status == "expired" else "Expirados",
             "callback_data": "vip:filter:expired"},
        ],
        [
            {"text": "⏱️ Por Expirar" if filter_status == "expiring_soon" else "Por Expirar",
             "callback_data": "vip:filter:expiring_soon"},
            {"text": "📋 Todos" if filter_status == "all" else "Todos",
             "callback_data": "vip:filter:all"},
        ]
    ]

    keyboard = create_pagination_keyboard(
        page=page,
        callback_pattern=f"vip:subscribers:page:{{page}}:{filter_status}",
        additional_buttons=additional_buttons,
        back_callback="admin:vip"
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje: {e}")


def _get_filter_name(filter_status: str) -> str:
    """Retorna nombre legible del filtro."""
    names = {
        "active": "Activos",
        "expired": "Expirados",
        "expiring_soon": "Por Expirar (7 días)",
        "all": "Todos"
    }
    return names.get(filter_status, "Todos")


def _format_vip_subscriber(subscriber: VIPSubscriber, index: int) -> str:
    """
    Formatea un suscriptor VIP para listado.

    Args:
        subscriber: Objeto VIPSubscriber
        index: Índice en la lista (1-indexed)

    Returns:
        String HTML formateado
    """
    # Calcular días restantes
    if subscriber.status == "active":
        days_remaining = (subscriber.expiry_date - datetime.utcnow()).days

        # Emoji según días restantes
        if days_remaining > 30:
            emoji = "🟢"
        elif days_remaining > 7:
            emoji = "🟡"
        else:
            emoji = "🔴"

        days_text = f"{days_remaining} días"
    else:
        emoji = "⚪"
        days_text = "Expirado"

    # Formatear fecha de expiración
    expiry_str = subscriber.expiry_date.strftime("%Y-%m-%d")

    return (
        f"{emoji} <b>{index}.</b> "
        f"User <code>{subscriber.user_id}</code>\n"
        f"   └─ Expira: {expiry_str} ({days_text})"
    )


# ===== DETALLES DE SUSCRIPTOR =====

@admin_router.callback_query(F.data.startswith("vip:details:"))
async def callback_vip_subscriber_details(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra detalles completos de un suscriptor VIP.

    Callback data format: "vip:details:USER_ID"

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    try:
        user_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError) as e:
        logger.error(f"❌ Error parseando user_id: {callback.data} - {e}")
        await callback.answer("❌ Error al cargar detalles", show_alert=True)
        return

    logger.info(f"👤 Usuario {callback.from_user.id} viendo detalles de {user_id}")

    container = ServiceContainer(session, callback.bot)

    # Obtener suscriptor
    subscriber = await container.subscription.get_vip_subscriber(user_id)

    if not subscriber:
        await callback.answer("❌ Suscriptor no encontrado", show_alert=True)
        return

    # Formatear detalles
    text = _format_subscriber_details(subscriber)

    # Keyboard con acciones
    buttons = []

    if subscriber.status == "active":
        buttons.append([
            {"text": "🗑️ Expulsar del Canal",
             "callback_data": f"vip:kick:{user_id}"}
        ])

    buttons.append([
        {"text": "🔙 Volver al Listado",
         "callback_data": "vip:list_subscribers"}
    ])

    keyboard = create_inline_keyboard(buttons)

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


def _format_subscriber_details(subscriber: VIPSubscriber) -> str:
    """
    Formatea detalles completos de un suscriptor.

    Args:
        subscriber: Objeto VIPSubscriber

    Returns:
        String HTML formateado
    """
    # Status emoji
    status_emoji = "🟢" if subscriber.status == "active" else "⚪"
    status_text = "Activo" if subscriber.status == "active" else "Expirado"

    # Calcular días
    if subscriber.status == "active":
        days_remaining = (subscriber.expiry_date - datetime.utcnow()).days
        days_text = f"{days_remaining} días restantes"
    else:
        days_ago = (datetime.utcnow() - subscriber.expiry_date).days
        days_text = f"Expiró hace {days_ago} días"

    # Formatear fechas
    join_date = subscriber.join_date.strftime("%Y-%m-%d %H:%M")
    expiry_date = subscriber.expiry_date.strftime("%Y-%m-%d %H:%M")

    text = f"""
👤 <b>Detalles de Suscriptor VIP</b>

<b>User ID:</b> <code>{subscriber.user_id}</code>
<b>Estado:</b> {status_emoji} {status_text}

<b>Fecha de Ingreso:</b> {join_date}
<b>Fecha de Expiración:</b> {expiry_date}
<b>Tiempo:</b> {days_text}

<b>Token Usado:</b> ID {subscriber.token_id}
    """.strip()

    return text


# ===== EXPULSIÓN MANUAL =====

@admin_router.callback_query(F.data.startswith("vip:kick:"))
async def callback_vip_kick_subscriber(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Expulsa manualmente a un suscriptor VIP del canal.

    Callback data format: "vip:kick:USER_ID"

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    try:
        user_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError) as e:
        logger.error(f"❌ Error parseando user_id: {callback.data} - {e}")
        await callback.answer("❌ Error al expulsar", show_alert=True)
        return

    logger.warning(
        f"🗑️ Admin {callback.from_user.id} expulsando manualmente a {user_id}"
    )

    await callback.answer("🗑️ Expulsando...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener suscriptor
        subscriber = await container.subscription.get_vip_subscriber(user_id)

        if not subscriber:
            await callback.answer("❌ Suscriptor no encontrado", show_alert=True)
            return

        if subscriber.status != "active":
            await callback.answer(
                "⚠️ Este suscriptor ya no está activo",
                show_alert=True
            )
            return

        # Marcar como expirado en BD
        subscriber.status = "expired"
        await session.commit()

        # Intentar expulsar del canal (mejor esfuerzo)
        vip_channel = await container.channel.get_vip_channel_id()
        expulsion_success = False

        if vip_channel:
            try:
                # Intentar usar ban_chat_member
                await callback.bot.ban_chat_member(vip_channel, user_id)
                expulsion_success = True
            except Exception as e:
                logger.warning(f"⚠️ No se pudo expulsar a {user_id} del canal: {e}")
                expulsion_success = False

        await callback.message.edit_text(
            f"✅ <b>Suscriptor Marcado Expirado</b>\n\n"
            f"User <code>{user_id}</code> ha sido marcado como expirado.\n\n"
            f"{'✅ También fue expulsado del canal VIP.' if expulsion_success else '⚠️ No se pudo expulsar del canal (revisar permisos del bot).'}\n\n"
            f"Esta acción es permanente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver al Listado",
                  "callback_data": "vip:list_subscribers"}]
            ]),
            parse_mode="HTML"
        )

        logger.info(f"✅ Suscriptor {user_id} marcado expirado manualmente")

    except Exception as e:
        logger.error(f"❌ Error expulsando suscriptor {user_id}: {e}", exc_info=True)

        await callback.message.edit_text(
            "❌ <b>Error al Expulsar</b>\n\n"
            "Ocurrió un error inesperado. Intenta nuevamente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver al Listado",
                  "callback_data": "vip:list_subscribers"}]
            ]),
            parse_mode="HTML"
        )


# ===== VISUALIZACIÓN COLA FREE =====

@admin_router.callback_query(F.data == "free:view_queue")
async def callback_view_free_queue(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra cola de solicitudes Free paginada.

    Por defecto muestra solo pendientes en la página 1.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"📋 Usuario {callback.from_user.id} viendo cola Free")

    await callback.answer("📋 Cargando cola...", show_alert=False)

    # Mostrar página 1, filtro "pending"
    await _show_free_queue_page(
        callback=callback,
        session=session,
        page_number=1,
        filter_status="pending"
    )


@admin_router.callback_query(F.data.startswith("free:queue:page:"))
async def callback_free_queue_page(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Navega a una página específica de la cola Free.

    Callback data format: "free:queue:page:N" o "free:queue:page:N:FILTER"

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    # Parsear callback data
    parts = callback.data.split(":")

    try:
        page_number = int(parts[3])
        filter_status = parts[4] if len(parts) > 4 else "pending"
    except (IndexError, ValueError) as e:
        logger.error(f"❌ Error parseando callback: {callback.data} - {e}")
        await callback.answer("❌ Error de navegación", show_alert=True)
        return

    logger.debug(
        f"📋 Usuario {callback.from_user.id} navegando a página {page_number}, "
        f"filtro={filter_status}"
    )

    await _show_free_queue_page(
        callback=callback,
        session=session,
        page_number=page_number,
        filter_status=filter_status
    )


@admin_router.callback_query(F.data.startswith("free:filter:"))
async def callback_free_filter(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Cambia filtro de visualización de cola Free.

    Filtros disponibles:
    - pending: Solo pendientes
    - ready: Listas para procesar (tiempo cumplido)
    - processed: Ya procesadas
    - all: Todas

    Callback data format: "free:filter:FILTER"

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    filter_status = callback.data.split(":")[2]

    logger.info(
        f"🔍 Usuario {callback.from_user.id} aplicando filtro Free: {filter_status}"
    )

    await callback.answer(f"🔍 Filtrando: {_get_free_filter_name(filter_status)}")

    # Mostrar página 1 con nuevo filtro
    await _show_free_queue_page(
        callback=callback,
        session=session,
        page_number=1,
        filter_status=filter_status
    )


async def _show_free_queue_page(
    callback: CallbackQuery,
    session: AsyncSession,
    page_number: int,
    filter_status: str = "pending"
):
    """
    Muestra una página de la cola Free con filtro aplicado.

    Args:
        callback: Callback query
        session: Sesión de BD
        page_number: Número de página a mostrar
        filter_status: Filtro a aplicar (pending, ready, processed, all)
    """
    from bot.database.models import BotConfig

    # Obtener tiempo de espera configurado
    config_result = await session.execute(
        select(BotConfig.wait_time_minutes).where(BotConfig.id == 1)
    )
    wait_time_minutes = config_result.scalar() or 5

    # Construir query según filtro
    query = select(FreeChannelRequest).order_by(
        FreeChannelRequest.request_date.asc()  # Más antiguas primero
    )

    if filter_status == "pending":
        query = query.where(FreeChannelRequest.processed == False)
    elif filter_status == "ready":
        # Listas para procesar (tiempo cumplido y no procesadas)
        cutoff_time = datetime.utcnow() - timedelta(minutes=wait_time_minutes)
        query = query.where(
            and_(
                FreeChannelRequest.processed == False,
                FreeChannelRequest.request_date <= cutoff_time
            )
        )
    elif filter_status == "processed":
        query = query.where(FreeChannelRequest.processed == True)
    # "all" no aplica filtro adicional

    # Ejecutar query
    result = await session.execute(query)
    requests = result.scalars().all()

    # Paginar resultados
    page = paginate_query_results(
        results=list(requests),
        page_number=page_number,
        page_size=10
    )

    # Formatear mensaje
    filter_name = _get_free_filter_name(filter_status)
    header = format_page_header(page, f"Cola Free - {filter_name}")

    if page.is_empty:
        text = f"{header}\n\n<i>No hay solicitudes en esta categoría.</i>"
    else:
        # Formatter específico que incluye wait_time
        def formatter(req, idx):
            return _format_free_request(req, idx, wait_time_minutes)

        items_text = format_items_list(page.items, formatter)
        text = f"{header}\n\n{items_text}"

    # Agregar info de configuración
    text += f"\n\n⏱️ <i>Tiempo de espera configurado: {wait_time_minutes} min</i>"

    # Crear keyboard con filtros y paginación
    additional_buttons = [
        # Fila de filtros
        [
            {"text": "⏳ Pendientes" if filter_status == "pending" else "Pendientes",
             "callback_data": "free:filter:pending"},
            {"text": "✅ Listas" if filter_status == "ready" else "Listas",
             "callback_data": "free:filter:ready"},
        ],
        [
            {"text": "🔄 Procesadas" if filter_status == "processed" else "Procesadas",
             "callback_data": "free:filter:processed"},
            {"text": "📋 Todas" if filter_status == "all" else "Todas",
             "callback_data": "free:filter:all"},
        ]
    ]

    keyboard = create_pagination_keyboard(
        page=page,
        callback_pattern=f"free:queue:page:{{page}}:{filter_status}",
        additional_buttons=additional_buttons,
        back_callback="admin:free"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


def _get_free_filter_name(filter_status: str) -> str:
    """Retorna nombre legible del filtro Free."""
    names = {
        "pending": "Pendientes",
        "ready": "Listas para Procesar",
        "processed": "Procesadas",
        "all": "Todas"
    }
    return names.get(filter_status, "Todas")


def _format_free_request(
    request: FreeChannelRequest,
    index: int,
    wait_time_minutes: int
) -> str:
    """
    Formatea una solicitud Free para listado.

    Args:
        request: Objeto FreeChannelRequest
        index: Índice en la lista (1-indexed)
        wait_time_minutes: Tiempo de espera configurado

    Returns:
        String HTML formateado
    """
    # Calcular tiempo transcurrido
    elapsed_minutes = (datetime.utcnow() - request.request_date).total_seconds() / 60

    if request.processed:
        # Solicitud ya procesada
        emoji = "✅"
        processed_date = request.processed_at.strftime("%Y-%m-%d %H:%M")
        status_text = f"Procesada: {processed_date}"
    else:
        # Solicitud pendiente
        remaining_minutes = wait_time_minutes - elapsed_minutes

        if remaining_minutes <= 0:
            # Lista para procesar
            emoji = "🟢"
            status_text = f"Lista (hace {abs(int(remaining_minutes))} min)"
        elif remaining_minutes < 2:
            # Muy próxima
            emoji = "🟡"
            status_text = f"Falta {int(remaining_minutes)} min"
        else:
            # Aún esperando
            emoji = "⏳"
            status_text = f"Falta {int(remaining_minutes)} min"

    # Formatear fecha de solicitud
    request_date = request.request_date.strftime("%Y-%m-%d %H:%M")

    return (
        f"{emoji} <b>{index}.</b> "
        f"User <code>{request.user_id}</code>\n"
        f"   ├─ Solicitó: {request_date}\n"
        f"   └─ {status_text}"
    )
