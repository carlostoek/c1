# Documentación de Servicios

Referencia de servicios y lógica de negocio reutilizable (a implementar en ONDA 1 Fase 1.4+).

## Introdución

Los servicios encapsulan la lógica de negocio del bot, separando la orquestación de handlers de la lógica de operaciones de BD.

**Beneficios:**
- Reutilización de lógica
- Fácil testing unitario
- Separación de responsabilidades
- Inyección de dependencias

## Estructura de Servicios

```
bot/services/
├── __init__.py             # Exports principales
├── base.py                 # Clase base (planeada)
├── subscription.py         # VIP/Free/Token logic
├── channel.py              # Gestión de canales Telegram
├── config.py               # Configuración del bot
└── container.py            # Dependency Injection container (ONDA 2+)
```

## Servicios Planeados

### 1. SubscriptionService (Fase 1.4)

Maneja lógica de suscripciones VIP, tokens y acceso Free.

```python
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from bot.database import InvitationToken, VIPSubscriber, FreeChannelRequest
from config import Config

class SubscriptionService:
    """
    Servicio de gestión de suscripciones VIP y Free.

    Responsabilidades:
    - Generación y validación de tokens
    - Creación y renovación de suscriptores VIP
    - Gestión de solicitudes Free
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: AsyncSession para operaciones de BD
        """
        self.session = session

    # ===== TOKENS =====

    async def generate_token(
        self,
        admin_id: int,
        duration_hours: int = 24
    ) -> str:
        """
        Genera nuevo token VIP único.

        Args:
            admin_id: User ID del admin que genera
            duration_hours: Horas de validez (default 24)

        Returns:
            Token de 16 caracteres alfanuméricos

        Raises:
            ValueError: Si admin_id es inválido
        """
        import secrets, string

        if not isinstance(admin_id, int) or admin_id < 1:
            raise ValueError("admin_id debe ser entero positivo")

        # Generar token único
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(16))

        # Crear en BD
        token_obj = InvitationToken(
            token=token,
            generated_by=admin_id,
            duration_hours=duration_hours
        )
        self.session.add(token_obj)
        await self.session.commit()

        return token

    async def validate_token(self, token: str) -> bool:
        """
        Valida que un token es válido (no usado, no expirado).

        Args:
            token: Token a validar

        Returns:
            True si es válido, False en otro caso
        """
        from sqlalchemy import select

        query = select(InvitationToken).where(
            InvitationToken.token == token
        )
        result = await self.session.execute(query)
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            return False

        return token_obj.is_valid()

    async def get_token(self, token: str) -> InvitationToken | None:
        """
        Obtiene un token por valor.

        Args:
            token: Valor del token

        Returns:
            Objeto InvitationToken o None si no existe
        """
        from sqlalchemy import select

        query = select(InvitationToken).where(
            InvitationToken.token == token
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_valid_tokens(self) -> list[InvitationToken]:
        """
        Lista todos los tokens válidos (no usados, no expirados).

        Returns:
            Lista de tokens válidos ordenados por fecha de creación
        """
        from sqlalchemy import select

        query = select(InvitationToken).where(
            InvitationToken.used == False
        ).order_by(InvitationToken.created_at.desc())
        result = await self.session.execute(query)
        tokens = result.scalars().all()

        return [t for t in tokens if not t.is_expired()]

    # ===== VIP SUBSCRIBERS =====

    async def redeem_token(
        self,
        user_id: int,
        token: str
    ) -> VIPSubscriber:
        """
        Canjea un token VIP para un usuario.

        Validaciones:
        - Token existe
        - Token no fue usado
        - Token no expiró
        - Usuario no es VIP activo

        Args:
            user_id: User ID del usuario
            token: Valor del token

        Returns:
            Objeto VIPSubscriber creado

        Raises:
            ValueError: Si token es inválido
            RuntimeError: Si usuario ya es VIP activo
        """
        # Obtener token
        token_obj = await self.get_token(token)

        if not token_obj or not token_obj.is_valid():
            raise ValueError("Token inválido o expirado")

        # Verificar que usuario no es VIP
        existing = await self.get_active_subscriber(user_id)
        if existing:
            raise RuntimeError("Usuario ya es VIP")

        # Crear suscriptor
        subscriber = VIPSubscriber(
            user_id=user_id,
            token_id=token_obj.id,
            expiry_date=datetime.utcnow() + timedelta(
                hours=token_obj.duration_hours
            ),
            status="active"
        )
        self.session.add(subscriber)

        # Marcar token como usado
        token_obj.used = True
        token_obj.used_by = user_id
        token_obj.used_at = datetime.utcnow()

        await self.session.commit()

        return subscriber

    async def get_active_subscriber(
        self,
        user_id: int
    ) -> VIPSubscriber | None:
        """
        Obtiene suscriptor VIP activo de usuario.

        Args:
            user_id: User ID

        Returns:
            VIPSubscriber si existe y activo, None en otro caso
        """
        from sqlalchemy import select, and_

        query = select(VIPSubscriber).where(
            and_(
                VIPSubscriber.user_id == user_id,
                VIPSubscriber.status == "active"
            )
        )
        result = await self.session.execute(query)
        subscriber = result.scalar_one_or_none()

        # Verificar que no expiró
        if subscriber and subscriber.is_expired():
            subscriber.status = "expired"
            await self.session.commit()
            return None

        return subscriber

    async def renew_subscription(
        self,
        user_id: int,
        duration_hours: int = 24
    ) -> VIPSubscriber:
        """
        Renueva la suscripción de un usuario VIP.

        Args:
            user_id: User ID
            duration_hours: Nuevas horas de validez

        Returns:
            VIPSubscriber actualizado

        Raises:
            ValueError: Si usuario no es VIP
        """
        subscriber = await self.get_active_subscriber(user_id)

        if not subscriber:
            raise ValueError("Usuario no es VIP")

        subscriber.expiry_date = datetime.utcnow() + timedelta(
            hours=duration_hours
        )
        await self.session.commit()

        return subscriber

    async def list_expiring_subscribers(
        self,
        days: int = 7
    ) -> list[VIPSubscriber]:
        """
        Lista suscriptores próximos a expirar.

        Args:
            days: Días dentro de los cuales expiran

        Returns:
            Lista de VIPSubscriber próximos a expirar
        """
        from sqlalchemy import select, and_

        soon = datetime.utcnow() + timedelta(days=days)

        query = select(VIPSubscriber).where(
            and_(
                VIPSubscriber.status == "active",
                VIPSubscriber.expiry_date <= soon,
                VIPSubscriber.expiry_date > datetime.utcnow()
            )
        ).order_by(VIPSubscriber.expiry_date)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def cleanup_expired_subscriptions(self) -> int:
        """
        Marca suscriptores expirados como 'expired'.

        Llamada por background task periódicamente.

        Returns:
            Cantidad de suscriptores marcados como expirados
        """
        from sqlalchemy import select, and_

        query = select(VIPSubscriber).where(
            and_(
                VIPSubscriber.status == "active",
                VIPSubscriber.expiry_date <= datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        expired = result.scalars().all()

        count = 0
        for subscriber in expired:
            subscriber.status = "expired"
            count += 1

        await self.session.commit()
        return count

    # ===== FREE REQUESTS =====

    async def create_free_request(self, user_id: int) -> FreeChannelRequest:
        """
        Crea solicitud de acceso Free para usuario.

        Validaciones:
        - Usuario no tiene solicitud pendiente

        Args:
            user_id: User ID

        Returns:
            FreeChannelRequest creado

        Raises:
            ValueError: Si usuario ya tiene solicitud pendiente
        """
        from sqlalchemy import select, and_

        # Verificar solicitud pendiente
        query = select(FreeChannelRequest).where(
            and_(
                FreeChannelRequest.user_id == user_id,
                FreeChannelRequest.processed == False
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Usuario ya tiene solicitud pendiente")

        # Crear solicitud
        request = FreeChannelRequest(user_id=user_id)
        self.session.add(request)
        await self.session.commit()

        return request

    async def get_pending_free_requests(
        self,
        ready_only: bool = False
    ) -> list[FreeChannelRequest]:
        """
        Lista solicitudes Free pendientes.

        Args:
            ready_only: Si True, solo las que cumplieron tiempo de espera

        Returns:
            Lista de FreeChannelRequest
        """
        from sqlalchemy import select

        query = select(FreeChannelRequest).where(
            FreeChannelRequest.processed == False
        ).order_by(FreeChannelRequest.request_date)

        result = await self.session.execute(query)
        requests = result.scalars().all()

        if ready_only:
            requests = [
                r for r in requests
                if r.is_ready(Config.DEFAULT_WAIT_TIME_MINUTES)
            ]

        return requests

    async def process_free_request(
        self,
        request_id: int
    ) -> FreeChannelRequest:
        """
        Marca solicitud Free como procesada.

        Llamada por background task después de procesar usuario.

        Args:
            request_id: ID de la solicitud

        Returns:
            FreeChannelRequest actualizado

        Raises:
            ValueError: Si request_id no existe
        """
        request = await self.session.get(FreeChannelRequest, request_id)

        if not request:
            raise ValueError(f"Request {request_id} no existe")

        request.processed = True
        request.processed_at = datetime.utcnow()
        await self.session.commit()

        return request

    async def get_wait_time_remaining(self, user_id: int) -> int:
        """
        Obtiene minutos restantes de espera para usuario Free.

        Args:
            user_id: User ID

        Returns:
            Minutos restantes (0 si ya está listo, -1 si no hay solicitud)
        """
        from sqlalchemy import select, and_

        query = select(FreeChannelRequest).where(
            and_(
                FreeChannelRequest.user_id == user_id,
                FreeChannelRequest.processed == False
            )
        )
        result = await self.session.execute(query)
        request = result.scalar_one_or_none()

        if not request:
            return -1

        wait_total = Config.DEFAULT_WAIT_TIME_MINUTES
        wait_elapsed = request.minutes_since_request()
        wait_remaining = max(0, wait_total - wait_elapsed)

        return wait_remaining
```

### 2. ChannelService (Fase 1.4)

Gestión de operaciones con canales de Telegram.

```python
from aiogram import Bot
from config import Config
import logging

logger = logging.getLogger(__name__)

class ChannelService:
    """
    Servicio de gestión de canales de Telegram.

    Responsabilidades:
    - Invitar usuarios a canales
    - Remover usuarios
    - Obtener información del canal
    """

    def __init__(self, bot: Bot):
        """
        Inicializa servicio.

        Args:
            bot: Instancia Bot de Aiogram
        """
        self.bot = bot

    async def invite_to_vip_channel(self, user_id: int) -> bool:
        """
        Invita usuario al canal VIP.

        Args:
            user_id: User ID a invitar

        Returns:
            True si se invitó exitosamente, False en error
        """
        if not Config.VIP_CHANNEL_ID:
            logger.error("Canal VIP no configurado")
            return False

        try:
            await self.bot.add_chat_member(
                chat_id=Config.VIP_CHANNEL_ID,
                user_id=user_id,
                can_post_messages=False,
                can_edit_messages=False,
            )
            logger.info(f"Usuario {user_id} invitado a canal VIP")
            return True

        except Exception as e:
            logger.error(f"Error invitando a VIP: {e}")
            return False

    async def invite_to_free_channel(self, user_id: int) -> bool:
        """
        Invita usuario al canal Free.

        Args:
            user_id: User ID a invitar

        Returns:
            True si se invitó exitosamente, False en error
        """
        if not Config.FREE_CHANNEL_ID:
            logger.error("Canal Free no configurado")
            return False

        try:
            await self.bot.add_chat_member(
                chat_id=Config.FREE_CHANNEL_ID,
                user_id=user_id,
                can_post_messages=False,
                can_edit_messages=False,
            )
            logger.info(f"Usuario {user_id} invitado a canal Free")
            return True

        except Exception as e:
            logger.error(f"Error invitando a Free: {e}")
            return False

    async def remove_from_channel(
        self,
        channel_id: str,
        user_id: int
    ) -> bool:
        """
        Remueve usuario de canal.

        Args:
            channel_id: ID del canal
            user_id: User ID a remover

        Returns:
            True si se removió, False en error
        """
        try:
            await self.bot.ban_chat_member(
                chat_id=channel_id,
                user_id=user_id
            )
            logger.info(f"Usuario {user_id} removido del canal {channel_id}")
            return True

        except Exception as e:
            logger.warning(f"No se pudo remover usuario: {e}")
            return False

    async def get_channel_info(self, channel_id: str) -> dict | None:
        """
        Obtiene información del canal.

        Args:
            channel_id: ID del canal

        Returns:
            Dict con info del canal o None si no existe
        """
        try:
            chat = await self.bot.get_chat(channel_id)
            return {
                "id": chat.id,
                "title": chat.title,
                "type": chat.type,
                "member_count": await self.bot.get_chat_member_count(channel_id),
            }
        except Exception as e:
            logger.error(f"Error obteniendo info del canal: {e}")
            return None
```

### 3. ConfigService (Fase 1.4)

Gestión de configuración del bot en BD.

```python
from bot.database import BotConfig
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

class ConfigService:
    """
    Servicio de configuración del bot.

    Maneja lectura/escritura de BotConfig (singleton).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_config(self) -> BotConfig:
        """
        Obtiene configuración global del bot.

        Returns:
            BotConfig singleton
        """
        config = await self.session.get(BotConfig, 1)

        if not config:
            # Crear si no existe (no debería pasar)
            config = BotConfig(id=1)
            self.session.add(config)
            await self.session.commit()

        return config

    async def set_vip_channel(self, channel_id: str) -> None:
        """
        Configura ID del canal VIP.

        Args:
            channel_id: Nuevo ID del canal
        """
        config = await self.get_config()
        config.vip_channel_id = channel_id
        await self.session.commit()

    async def set_free_channel(self, channel_id: str) -> None:
        """
        Configura ID del canal Free.

        Args:
            channel_id: Nuevo ID del canal
        """
        config = await self.get_config()
        config.free_channel_id = channel_id
        await self.session.commit()

    async def set_wait_time(self, minutes: int) -> None:
        """
        Configura tiempo de espera Free.

        Args:
            minutes: Minutos (1-10080)

        Raises:
            ValueError: Si minutos está fuera de rango
        """
        if not 1 <= minutes <= 10080:
            raise ValueError("Minutos debe estar entre 1 y 10080")

        config = await self.get_config()
        config.wait_time_minutes = minutes
        await self.session.commit()

    async def set_reactions(
        self,
        vip_reactions: list[str] = None,
        free_reactions: list[str] = None
    ) -> None:
        """
        Configura reacciones de los canales.

        Args:
            vip_reactions: Array de emojis para VIP
            free_reactions: Array de emojis para Free
        """
        config = await self.get_config()

        if vip_reactions is not None:
            config.vip_reactions = vip_reactions

        if free_reactions is not None:
            config.free_reactions = free_reactions

        await self.session.commit()

    async def set_subscription_fees(
        self,
        monthly: float = None,
        yearly: float = None
    ) -> None:
        """
        Configura tarifas de suscripción.

        Args:
            monthly: Precio mensual
            yearly: Precio anual
        """
        config = await self.get_config()

        if monthly is not None or yearly is not None:
            config.subscription_fees = {
                "monthly": monthly or config.subscription_fees.get("monthly"),
                "yearly": yearly or config.subscription_fees.get("yearly"),
            }

        await self.session.commit()
```

## Inyección de Dependencias

En ONDA 2+, usar container para DI:

```python
from dependency_injector import containers, providers

class ServiceContainer(containers.DeclarativeContainer):
    """Container de servicios"""

    db_session = providers.Singleton(
        get_session
    )

    subscription_service = providers.Factory(
        SubscriptionService,
        session=db_session
    )

    channel_service = providers.Factory(
        ChannelService,
        bot=providers.Singleton(Bot)
    )

    config_service = providers.Factory(
        ConfigService,
        session=db_session
    )

# Uso en handler
@router.message.command("test")
async def test_handler(message: Message):
    service = ServiceContainer.subscription_service()
    tokens = await service.list_valid_tokens()
```

## Testing de Servicios

Ejemplos de tests (ONDA 2+):

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_generate_token(session_mock):
    """Test generación de token"""
    service = SubscriptionService(session_mock)

    token = await service.generate_token(admin_id=123, duration_hours=24)

    assert len(token) == 16
    assert all(c.isalnum() for c in token)

@pytest.mark.asyncio
async def test_redeem_token_valid(session_mock):
    """Test canje de token válido"""
    service = SubscriptionService(session_mock)

    # Mock token válido
    token_mock = MagicMock()
    token_mock.is_valid.return_value = True
    token_mock.id = 1
    token_mock.duration_hours = 24

    service.get_token = AsyncMock(return_value=token_mock)
    service.get_active_subscriber = AsyncMock(return_value=None)

    subscriber = await service.redeem_token(user_id=456, token="ABC123XYZ")

    assert subscriber.user_id == 456
    assert subscriber.status == "active"

@pytest.mark.asyncio
async def test_redeem_token_invalid(session_mock):
    """Test canje de token inválido"""
    service = SubscriptionService(session_mock)

    service.get_token = AsyncMock(return_value=None)

    with pytest.raises(ValueError):
        await service.redeem_token(user_id=456, token="INVALID")
```

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
**Estado:** Documentación de servicios planeados (implementación en Fase 1.4)
