"""
Subscription Service - Gestión de suscripciones VIP/Free.

Responsabilidades:
- Generación de tokens de invitación
- Validación y canje de tokens
- Gestión de suscriptores VIP (crear, extender, expirar)
- Gestión de solicitudes Free (crear, procesar)
- Limpieza automática de datos antiguos
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatInviteLink
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import Config
from bot.database.models import (
    InvitationToken,
    VIPSubscriber,
    FreeChannelRequest,
    BotConfig
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service para gestionar suscripciones VIP y Free.

    VIP Flow:
    1. Admin genera token → generate_vip_token()
    2. Usuario canjea token → redeem_vip_token()
    3. Usuario recibe invite link → create_invite_link()
    4. Suscripción expira automáticamente → expire_vip_subscribers() (background)

    Free Flow:
    1. Usuario solicita acceso → create_free_request()
    2. Espera N minutos
    3. Sistema procesa cola → approve_ready_free_requests() (background)
    4. Usuario es aprobado y notificado
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el service.

        Args:
            session: Sesión de base de datos
            bot: Instancia del bot de Telegram
        """
        self.session = session
        self.bot = bot
        logger.debug("✅ SubscriptionService inicializado")

    # ===== TOKENS VIP =====

    async def generate_vip_token(
        self,
        generated_by: int,
        duration_hours: int = 24,
        plan_id: Optional[int] = None
    ) -> InvitationToken:
        """
        Genera un token de invitación único para canal VIP.

        El token:
        - Tiene 16 caracteres alfanuméricos
        - Es único (verifica duplicados)
        - Expira después de duration_hours
        - Puede usarse solo 1 vez
        - Opcionalmente vinculado a un plan de suscripción

        Args:
            generated_by: User ID del admin que genera el token
            duration_hours: Duración del token en horas (default: 24h)
            plan_id: ID del plan de suscripción (opcional)

        Returns:
            InvitationToken: Token generado

        Raises:
            ValueError: Si duration_hours es inválido
            RuntimeError: Si no se puede generar token único después de 10 intentos
        """
        if duration_hours < 1:
            raise ValueError("duration_hours debe ser al menos 1")

        # Generar token único
        max_attempts = 10
        token_str = None

        for attempt in range(max_attempts):
            # secrets.token_urlsafe(12) genera ~16 chars después de strip
            token_str = secrets.token_urlsafe(12)[:16]

            # Verificar que no exista
            result = await self.session.execute(
                select(InvitationToken).where(
                    InvitationToken.token == token_str
                )
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                # Token único encontrado
                break

            logger.warning(f"⚠️ Token duplicado generado (intento {attempt + 1})")
        else:
            # No se encontró token único después de max_attempts
            raise RuntimeError(
                "No se pudo generar token único después de 10 intentos"
            )

        # Crear token
        token = InvitationToken(
            token=token_str,
            generated_by=generated_by,
            created_at=datetime.utcnow(),
            duration_hours=duration_hours,
            used=False,
            plan_id=plan_id  # Vincular con plan (opcional)
        )

        self.session.add(token)
        # No commit - dejar que el handler maneje la transacción

        logger.info(
            f"✅ Token VIP generado: {token.token} "
            f"(válido por {duration_hours}h, plan_id: {plan_id}, generado por {generated_by})"
        )

        return token

    async def validate_token(
        self,
        token_str: str
    ) -> Tuple[bool, str, Optional[InvitationToken]]:
        """
        Valida un token de invitación.

        Un token es válido si:
        - Existe en la base de datos
        - No ha sido usado (used=False)
        - No ha expirado (created_at + duration_hours > now)

        Args:
            token_str: String del token (16 caracteres)

        Returns:
            Tuple[bool, str, Optional[InvitationToken]]:
                - bool: True si válido, False si inválido
                - str: Mensaje de error/éxito
                - Optional[InvitationToken]: Token si existe, None si no
        """
        # Buscar token con eager load de relación plan (evita lazy loading en contexto async)
        result = await self.session.execute(
            select(InvitationToken).where(
                InvitationToken.token == token_str
            ).options(selectinload(InvitationToken.plan))
        )
        token = result.scalar_one_or_none()

        if token is None:
            return False, "❌ Token no encontrado", None

        if token.used:
            return False, "❌ Este token ya fue usado", token

        if token.is_expired():
            return False, "❌ Token expirado", token

        return True, "✅ Token válido", token

    async def redeem_vip_token(
        self,
        token_str: str,
        user_id: int
    ) -> Tuple[bool, str, Optional[VIPSubscriber]]:
        """
        Canjea un token VIP y crea/extiende suscripción.

        Si el usuario ya es VIP:
        - Extiende su suscripción (no crea nueva)

        Si el usuario es nuevo:
        - Crea nueva suscripción VIP

        Args:
            token_str: String del token
            user_id: ID del usuario que canjea

        Returns:
            Tuple[bool, str, Optional[VIPSubscriber]]:
                - bool: True si éxito, False si error
                - str: Mensaje descriptivo
                - Optional[VIPSubscriber]: Suscriptor creado/actualizado
        """
        # Validar token
        is_valid, message, token = await self.validate_token(token_str)

        if not is_valid:
            return False, message, None

        # Marcar token como usado
        token.used = True
        token.used_by = user_id
        token.used_at = datetime.utcnow()

        # Verificar si usuario ya es VIP
        result = await self.session.execute(
            select(VIPSubscriber).where(
                VIPSubscriber.user_id == user_id
            )
        )
        existing_subscriber = result.scalar_one_or_none()

        if existing_subscriber:
            # Usuario ya es VIP: extender suscripción
            # Agregar token.duration_hours a la fecha de expiración actual
            extension = timedelta(hours=token.duration_hours)

            # Si ya expiró, partir desde ahora
            if existing_subscriber.is_expired():
                existing_subscriber.expiry_date = datetime.utcnow() + extension
            else:
                # Si aún está activo, extender desde la fecha actual de expiración
                existing_subscriber.expiry_date += extension

            existing_subscriber.status = "active"

            # No commit - dejar que el handler maneje la transacción

            logger.info(
                f"✅ Suscripción VIP extendida: user {user_id} "
                f"(nueva expiración: {existing_subscriber.expiry_date})"
            )

            return True, "✅ Suscripción VIP extendida exitosamente", existing_subscriber

        # Usuario nuevo: crear suscripción
        expiry_date = datetime.utcnow() + timedelta(hours=token.duration_hours)

        subscriber = VIPSubscriber(
            user_id=user_id,
            join_date=datetime.utcnow(),
            expiry_date=expiry_date,
            status="active",
            token_id=token.id
        )

        self.session.add(subscriber)
        # No commit - dejar que el handler maneje la transacción

        logger.info(
            f"✅ Nuevo suscriptor VIP: user {user_id} "
            f"(expira: {expiry_date})"
        )

        return True, "✅ Suscripción VIP activada exitosamente", subscriber

    # ===== GESTIÓN VIP =====

    async def get_vip_subscriber(self, user_id: int) -> Optional[VIPSubscriber]:
        """
        Obtiene el suscriptor VIP por user_id.

        Args:
            user_id: ID del usuario

        Returns:
            VIPSubscriber si existe, None si no
        """
        result = await self.session.execute(
            select(VIPSubscriber).where(
                VIPSubscriber.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def is_vip_active(self, user_id: int) -> bool:
        """
        Verifica si un usuario tiene suscripción VIP activa.

        Args:
            user_id: ID del usuario

        Returns:
            True si VIP activo, False si no
        """
        subscriber = await self.get_vip_subscriber(user_id)

        if subscriber is None:
            return False

        if subscriber.status != "active":
            return False

        if subscriber.is_expired():
            return False

        return True

    async def activate_vip_subscription(
        self,
        user_id: int,
        token_id: int,
        duration_hours: int
    ) -> VIPSubscriber:
        """
        Activa una suscripción VIP para un usuario (método privado de deep link).

        NUEVO: Usado por el flujo de deep link para activar automáticamente
        la suscripción sin pasar por el flujo de canje manual.

        Args:
            user_id: ID del usuario que activa
            token_id: ID del token a usar
            duration_hours: Duración de la suscripción en horas

        Returns:
            VIPSubscriber: Suscriptor creado o actualizado

        Raises:
            ValueError: Si el usuario ya es VIP o token inválido
        """
        # Verificar si usuario ya es VIP
        result = await self.session.execute(
            select(VIPSubscriber).where(
                VIPSubscriber.user_id == user_id
            )
        )
        existing_subscriber = result.scalar_one_or_none()

        if existing_subscriber:
            # Usuario ya es VIP: extender suscripción
            extension = timedelta(hours=duration_hours)

            # Si ya expiró, partir desde ahora
            if existing_subscriber.is_expired():
                existing_subscriber.expiry_date = datetime.utcnow() + extension
            else:
                # Si aún está activo, extender desde la fecha actual de expiración
                existing_subscriber.expiry_date += extension

            existing_subscriber.status = "active"

            # No commit - dejar que el handler maneje la transacción
            logger.info(
                f"✅ Suscripción VIP extendida vía deep link: user {user_id} "
                f"(nueva expiración: {existing_subscriber.expiry_date})"
            )

            return existing_subscriber

        # Usuario nuevo: crear suscripción
        expiry_date = datetime.utcnow() + timedelta(hours=duration_hours)

        subscriber = VIPSubscriber(
            user_id=user_id,
            join_date=datetime.utcnow(),
            expiry_date=expiry_date,
            status="active",
            token_id=token_id
        )

        self.session.add(subscriber)
        # No commit - dejar que el handler maneje la transacción

        logger.info(
            f"✅ Nuevo suscriptor VIP vía deep link: user {user_id} "
            f"(expira: {expiry_date})"
        )

        return subscriber

    async def grant_vip_days(
        self,
        user_id: int,
        days: int,
        extend_existing: bool = True,
        source: str = "reward"
    ) -> Tuple[bool, str, Optional[VIPSubscriber]]:
        """
        Otorga días VIP a un usuario (usado por recompensas de gamificación).

        Si el usuario ya es VIP y extend_existing=True:
        - Extiende su suscripción agregando los días

        Si el usuario no es VIP o extend_existing=False:
        - Crea nueva suscripción desde ahora

        Args:
            user_id: ID del usuario
            days: Cantidad de días a otorgar
            extend_existing: Si extender suscripción existente (default: True)
            source: Fuente de la recompensa (para logging)

        Returns:
            Tuple[bool, str, Optional[VIPSubscriber]]:
                - bool: True si éxito
                - str: Mensaje descriptivo
                - Optional[VIPSubscriber]: Suscriptor creado/actualizado
        """
        if days < 1:
            return False, "days debe ser al menos 1", None

        # Calcular duración en horas
        duration_hours = days * 24

        # Verificar si usuario ya es VIP
        result = await self.session.execute(
            select(VIPSubscriber).where(
                VIPSubscriber.user_id == user_id
            )
        )
        existing_subscriber = result.scalar_one_or_none()

        if existing_subscriber and extend_existing:
            # Extender suscripción existente
            extension = timedelta(hours=duration_hours)

            if existing_subscriber.is_expired():
                # Si expiró, partir desde ahora
                existing_subscriber.expiry_date = datetime.utcnow() + extension
            else:
                # Si aún activo, extender desde fecha actual
                existing_subscriber.expiry_date += extension

            existing_subscriber.status = "active"

            logger.info(
                f"✅ VIP extendido por {days} días ({source}): user {user_id} "
                f"(nueva expiración: {existing_subscriber.expiry_date})"
            )

            return True, f"Suscripción VIP extendida por {days} días", existing_subscriber

        # Crear nueva suscripción
        expiry_date = datetime.utcnow() + timedelta(hours=duration_hours)

        subscriber = VIPSubscriber(
            user_id=user_id,
            join_date=datetime.utcnow(),
            expiry_date=expiry_date,
            status="active",
            token_id=None  # Sin token asociado (viene de reward)
        )

        self.session.add(subscriber)

        logger.info(
            f"✅ Nuevo VIP por {days} días ({source}): user {user_id} "
            f"(expira: {expiry_date})"
        )

        return True, f"Suscripción VIP activada por {days} días", subscriber

    async def expire_vip_subscribers(self) -> int:
        """
        Marca como expirados los suscriptores VIP cuya fecha pasó.

        Esta función se ejecuta periódicamente en background.

        Returns:
            Cantidad de suscriptores expirados
        """
        # Buscar suscriptores activos con fecha de expiración pasada
        result = await self.session.execute(
            select(VIPSubscriber).where(
                VIPSubscriber.status == "active",
                VIPSubscriber.expiry_date < datetime.utcnow()
            )
        )
        expired_subscribers = result.scalars().all()

        count = 0
        for subscriber in expired_subscribers:
            subscriber.status = "expired"
            count += 1
            logger.info(f"⏱️ VIP expirado: user {subscriber.user_id}")

        if count > 0:
            await self.session.commit()
            logger.info(f"✅ {count} suscriptor(es) VIP marcados como expirados")

        return count

    async def kick_expired_vip_from_channel(self, channel_id: str) -> int:
        """
        Expulsa suscriptores expirados del canal VIP.

        Esta función se ejecuta después de expire_vip_subscribers()
        en el background task.

        Args:
            channel_id: ID del canal VIP (ej: "-1001234567890")

        Returns:
            Cantidad de usuarios expulsados
        """
        # Buscar suscriptores expirados
        result = await self.session.execute(
            select(VIPSubscriber).where(
                VIPSubscriber.status == "expired"
            )
        )
        expired_subscribers = result.scalars().all()

        kicked_count = 0
        for subscriber in expired_subscribers:
            try:
                # Intentar expulsar del canal
                await self.bot.ban_chat_member(
                    chat_id=channel_id,
                    user_id=subscriber.user_id
                )

                # Desbanear inmediatamente (solo expulsar, no banear permanente)
                await self.bot.unban_chat_member(
                    chat_id=channel_id,
                    user_id=subscriber.user_id
                )

                kicked_count += 1
                logger.info(f"👢 Usuario expulsado de VIP: {subscriber.user_id}")

            except Exception as e:
                logger.warning(
                    f"⚠️ No se pudo expulsar a user {subscriber.user_id}: {e}"
                )

        if kicked_count > 0:
            logger.info(f"✅ {kicked_count} usuario(s) expulsados del canal VIP")

        return kicked_count

    async def get_all_vip_subscribers(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[VIPSubscriber]:
        """
        Obtiene lista de suscriptores VIP con paginación.

        Args:
            status: Filtrar por status ("active", "expired", None=todos)
            limit: Máximo de resultados (default: 100)
            offset: Offset para paginación (default: 0)

        Returns:
            Lista de suscriptores
        """
        query = select(VIPSubscriber).order_by(
            VIPSubscriber.expiry_date.desc()
        )

        if status:
            query = query.where(VIPSubscriber.status == status)

        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ===== CANAL FREE =====

    async def create_free_request(self, user_id: int) -> FreeChannelRequest:
        """
        Crea una solicitud de acceso al canal Free.

        Si el usuario ya tiene una solicitud pendiente, la retorna.

        Args:
            user_id: ID del usuario

        Returns:
            FreeChannelRequest: Solicitud creada o existente
        """
        # Verificar si ya tiene solicitud pendiente
        result = await self.session.execute(
            select(FreeChannelRequest).where(
                FreeChannelRequest.user_id == user_id,
                FreeChannelRequest.processed == False
            ).order_by(FreeChannelRequest.request_date.desc())
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(
                f"ℹ️ Usuario {user_id} ya tiene solicitud Free pendiente "
                f"(hace {existing.minutes_since_request()} min)"
            )
            return existing

        # Crear nueva solicitud
        request = FreeChannelRequest(
            user_id=user_id,
            request_date=datetime.utcnow(),
            processed=False
        )

        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)

        logger.info(f"✅ Solicitud Free creada: user {user_id}")

        return request

    async def get_free_request(self, user_id: int) -> Optional[FreeChannelRequest]:
        """
        Obtiene la solicitud Free pendiente de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            FreeChannelRequest si existe pendiente, None si no
        """
        result = await self.session.execute(
            select(FreeChannelRequest).where(
                FreeChannelRequest.user_id == user_id,
                FreeChannelRequest.processed == False
            ).order_by(FreeChannelRequest.request_date.desc())
        )
        return result.scalar_one_or_none()

    async def create_free_request_from_join_request(
        self,
        user_id: int,
        from_chat_id: str
    ) -> tuple[bool, str, Optional[FreeChannelRequest]]:
        """
        Crea solicitud Free desde ChatJoinRequest.

        Valida que la solicitud viene del canal correcto (seguridad)
        y verifica que no haya solicitudes duplicadas.

        Args:
            user_id: ID del usuario que solicita
            from_chat_id: ID del chat desde donde solicita

        Returns:
            tuple: (success, message, request)
                - success: True si creó nueva solicitud
                - message: Descripción del resultado
                - request: FreeChannelRequest (nueva o existente)
        """
        from bot.database.models import BotConfig

        # Verificar canal configurado
        config = await self.session.get(BotConfig, 1)

        if not config or not config.free_channel_id:
            return False, "Canal Free no configurado", None

        # Validar canal correcto (SEGURIDAD)
        if config.free_channel_id != from_chat_id:
            logger.warning(
                f"⚠️ Intento de solicitud desde canal no autorizado: "
                f"{from_chat_id} (esperado: {config.free_channel_id})"
            )
            return False, "Solicitud desde canal no autorizado", None

        # Verificar duplicados
        existing = await self.get_free_request(user_id)

        if existing and not existing.processed:
            minutes_since = existing.minutes_since_request()
            logger.info(
                f"ℹ️ Usuario {user_id} ya tiene solicitud Free pendiente "
                f"({minutes_since} min transcurridos)"
            )
            return False, f"Ya tienes solicitud pendiente ({minutes_since} minutos)", existing

        # Crear nueva solicitud
        request = await self.create_free_request(user_id)

        return True, "Solicitud creada exitosamente", request

    async def get_ready_free_requests_to_process(self, wait_time_minutes: int) -> List[FreeChannelRequest]:
        """
        Obtiene la cola de solicitudes Free que cumplieron el tiempo de espera.
        Usa SELECT ... FOR UPDATE para bloquear las filas y evitar race conditions.
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=wait_time_minutes)

        stmt = (
            select(FreeChannelRequest)
            .where(
                FreeChannelRequest.processed == False,
                FreeChannelRequest.request_date <= cutoff_time
            )
            .order_by(FreeChannelRequest.request_date.asc())
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        ready_requests = result.scalars().all()

        if ready_requests:
            logger.info(f"ℹ️ {len(ready_requests)} solicitud(es) Free listas para procesar.")

        return list(ready_requests)

    async def approve_ready_free_requests(
        self,
        wait_time_minutes: int,
        free_channel_id: str
    ) -> tuple[int, int]:
        """
        Aprueba solicitudes Free que cumplieron el tiempo de espera, notifica
        al usuario y limpia el estado de la solicitud.
        Args:
            wait_time_minutes: Tiempo de espera en minutos
            free_channel_id: ID del canal Free
        Returns:
            tuple: (success_count, error_count)
        """
        ready_requests = await self.get_ready_free_requests_to_process(wait_time_minutes)

        if not ready_requests:
            return 0, 0

        success_count = 0
        error_count = 0

        for request in ready_requests:
            try:
                # 1. Aprobar la solicitud directamente
                await self.bot.approve_chat_join_request(
                    chat_id=free_channel_id,
                    user_id=request.user_id
                )

                # 2. Enviar onboarding welcome (reemplaza notificación simple)
                try:
                    # Import local para evitar circular import
                    from bot.handlers.user.narrative.onboarding import send_onboarding_welcome

                    await send_onboarding_welcome(
                        bot=self.bot,
                        user_id=request.user_id,
                        session=self.session
                    )
                    logger.info(f"✅ Onboarding welcome enviado a user {request.user_id}")
                except Exception as notify_err:
                    logger.warning(
                        f"⚠️ No se pudo enviar onboarding a user {request.user_id}: {notify_err}"
                    )

                # 3. Eliminar la solicitud para limpiar el estado
                await self.session.delete(request)

                success_count += 1
                logger.info(f"✅ Solicitud Free aprobada para user {request.user_id}")

            except TelegramBadRequest as e:
                # Error común si el usuario ya no está esperando (canceló, ya entró, etc.)
                if "HIDE_REQUESTER_MISSING" in e.message or "USER_ALREADY_PARTICIPANT" in e.message:
                    logger.warning(
                        f"⚠️ Solicitud para user {request.user_id} ya no era válida (probablemente ya está en el canal o canceló). "
                        f"Se limpiará de la cola. Error: {e}"
                    )
                    # Igualmente se elimina para limpiar la cola
                    await self.session.delete(request)
                    error_count += 1 # Contar como error manejado
                else:
                    error_count += 1
                    logger.error(
                        f"❌ Error de Telegram no manejado aprobando solicitud user {request.user_id}: {e}",
                        exc_info=True
                    )
            except Exception as e:
                error_count += 1
                logger.error(
                    f"❌ Error inesperado aprobando solicitud user {request.user_id}: {e}",
                    exc_info=True
                )
                # No se elimina la solicitud en caso de error desconocido para poder reintentar

        # Hacer commit de todos los cambios (eliminaciones y actualizaciones)
        if success_count > 0 or error_count > 0:
            await self.session.commit()

        return success_count, error_count


    async def send_free_request_notification(
        self,
        user_id: int,
        user_name: str,
        channel_name: str,
        wait_time_minutes: int,
        custom_message: Optional[str] = None
    ) -> bool:
        """
        Envía notificación automática cuando usuario solicita acceso Free.

        Reemplaza variables en el mensaje:
        - {user_name} → Nombre del usuario
        - {channel_name} → Nombre del canal
        - {wait_time} → Tiempo de espera en minutos

        Args:
            user_id: ID del usuario
            user_name: Nombre del usuario
            channel_name: Nombre del canal
            wait_time_minutes: Tiempo de espera
            custom_message: Mensaje personalizado (opcional)

        Returns:
            bool: True si envío exitoso, False si error
        """
        try:
            # Obtener template
            if not custom_message:
                from bot.database.models import BotConfig
                config = await self.session.get(BotConfig, 1)
                template = config.free_welcome_message if config and config.free_welcome_message else (
                    "Hola {user_name}, tu solicitud de acceso a {channel_name} ha sido registrada. "
                    "Debes esperar {wait_time} minutos antes de ser aprobado."
                )
            else:
                template = custom_message

            # Reemplazar variables
            message = template.format(
                user_name=user_name,
                channel_name=channel_name,
                wait_time=wait_time_minutes
            )

            # Enviar mensaje (sin parse_mode para prevenir inyección HTML)
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=None
            )

            logger.info(f"✅ Notificación Free enviada a user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"❌ Error enviando notificación a user {user_id}: {e}",
                exc_info=True
            )
            return False

    async def cleanup_old_free_requests(self, days_old: int = 30) -> int:
        """
        Elimina solicitudes Free antiguas (ya procesadas).

        Args:
            days_old: Eliminar solicitudes procesadas hace más de N días

        Returns:
            Cantidad de solicitudes eliminadas
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await self.session.execute(
            delete(FreeChannelRequest).where(
                FreeChannelRequest.processed == True,
                FreeChannelRequest.processed_at < cutoff_date
            )
        )

        deleted_count = result.rowcount
        await self.session.commit()

        if deleted_count > 0:
            logger.info(f"🗑️ {deleted_count} solicitud(es) Free antiguas eliminadas")

        return deleted_count

    # ===== INVITE LINKS =====

    async def create_invite_link(
        self,
        channel_id: str,
        user_id: int,
        expire_hours: int = 1
    ) -> ChatInviteLink:
        """
        Crea un invite link único para un usuario.

        El link:
        - Es de un solo uso (member_limit=1)
        - Expira después de expire_hours
        - Es específico para el usuario (se puede trackear)

        Args:
            channel_id: ID del canal (ej: "-1001234567890")
            user_id: ID del usuario
            expire_hours: Horas hasta que expira el link

        Returns:
            ChatInviteLink: Link de invitación creado

        Raises:
            TelegramAPIError: Si el bot no tiene permisos en el canal
        """
        expire_date = datetime.utcnow() + timedelta(hours=expire_hours)

        invite_link = await self.bot.create_chat_invite_link(
            chat_id=channel_id,
            name=f"User {user_id}",
            expire_date=expire_date,
            member_limit=1  # Solo 1 persona puede usar este link
        )

        logger.info(
            f"🔗 Invite link creado para user {user_id}: "
            f"{invite_link.invite_link[:30]}..."
        )

        return invite_link
