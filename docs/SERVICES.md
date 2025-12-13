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
├── stats.py                # Estadísticas y métricas (T18)
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

### 4. StatsService (T18 - Implementado)

Servicio de cálculo de métricas y estadísticas del sistema.

```python
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    VIPSubscriber,
    InvitationToken,
    FreeChannelRequest,
    BotConfig
)


@dataclass
class OverallStats:
    """Estadísticas generales del sistema."""

    # VIP Stats
    total_vip_active: int
    total_vip_expired: int
    total_vip_expiring_soon: int  # Próximos 7 días

    # Free Stats
    total_free_pending: int
    total_free_processed: int

    # Token Stats
    total_tokens_generated: int
    total_tokens_used: int
    total_tokens_expired: int
    total_tokens_available: int

    # Activity Stats
    new_vip_today: int
    new_vip_this_week: int
    new_vip_this_month: int

    # Revenue Stats (proyectado)
    projected_monthly_revenue: float
    projected_yearly_revenue: float

    # Timestamp
    calculated_at: datetime

    def to_dict(self) -> Dict:
        """Convierte a dict para serialización."""
        data = asdict(self)
        data['calculated_at'] = self.calculated_at.isoformat()
        return data


@dataclass
class VIPStats:
    """Estadísticas detalladas de VIP."""

    total_active: int
    total_expired: int
    total_all_time: int

    # Por tiempo de suscripción
    expiring_today: int
    expiring_this_week: int
    expiring_this_month: int

    # Actividad temporal
    new_today: int
    new_this_week: int
    new_this_month: int

    # Top subscribers (por días restantes)
    top_subscribers: List[Dict]  # [{user_id, days_remaining, expiry_date}]

    calculated_at: datetime

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['calculated_at'] = self.calculated_at.isoformat()
        return data


@dataclass
class FreeStats:
    """Estadísticas detalladas de Free."""

    total_pending: int
    total_processed: int
    total_all_time: int

    # Por estado de procesamiento
    ready_to_process: int  # Cumplieron tiempo de espera
    still_waiting: int     # Aún no cumplen tiempo

    # Tiempo promedio de espera
    avg_wait_time_minutes: float

    # Actividad temporal
    new_requests_today: int
    new_requests_this_week: int
    new_requests_this_month: int

    # Solicitudes próximas (por tiempo restante)
    next_to_process: List[Dict]  # [{user_id, minutes_remaining, request_date}]

    calculated_at: datetime

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['calculated_at'] = self.calculated_at.isoformat()
        return data


@dataclass
class TokenStats:
    """Estadísticas detalladas de tokens."""

    total_generated: int
    total_used: int
    total_expired: int
    total_available: int  # No usados y no expirados

    # Por período
    generated_today: int
    generated_this_week: int
    generated_this_month: int

    used_today: int
    used_this_week: int
    used_this_month: int

    # Tasa de conversión
    conversion_rate: float  # % de tokens usados vs generados

    calculated_at: datetime

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['calculated_at'] = self.calculated_at.isoformat()
        return data


class StatsService:
    """
    Service para calcular métricas y estadísticas del sistema.

    Features:
    - Cache interno con TTL de 5 minutos
    - Queries optimizadas con índices
    - Dataclasses para resultados estructurados
    """

    # TTL del cache en segundos (5 minutos)
    CACHE_TTL = 300

    def __init__(self, session: AsyncSession):
        """
        Inicializa el service.

        Args:
            session: Sesión de base de datos
        """
        self.session = session
        self._cache: Dict[str, Tuple[any, datetime]] = {}

        logger.debug("✅ StatsService inicializado")

    # ===== CACHE MANAGEMENT =====

    def _is_cache_fresh(self, key: str) -> bool:
        """
        Verifica si el cache de una key es fresco.

        Args:
            key: Key del cache

        Returns:
            True si el cache es válido, False si expiró o no existe
        """
        if key not in self._cache:
            return False

        _, cached_at = self._cache[key]
        age = (datetime.utcnow() - cached_at).total_seconds()

        return age < self.CACHE_TTL

    def _get_from_cache(self, key: str) -> Optional[any]:
        """
        Obtiene valor del cache si es fresco.

        Args:
            key: Key del cache

        Returns:
            Valor cacheado o None si no existe/expiró
        """
        if not self._is_cache_fresh(key):
            return None

        value, _ = self._cache[key]
        logger.debug(f"📦 Cache hit: {key}")
        return value

    def _set_cache(self, key: str, value: any) -> None:
        """
        Guarda valor en cache con timestamp actual.

        Args:
            key: Key del cache
            value: Valor a cachear
        """
        self._cache[key] = (value, datetime.utcnow())
        logger.debug(f"💾 Cache set: {key}")

    def clear_cache(self) -> None:
        """Limpia todo el cache (útil para testing o forzar recálculo)."""
        self._cache.clear()
        logger.info("🗑️ Cache limpiado")

    # ===== OVERALL STATS =====

    async def get_overall_stats(self, force_refresh: bool = False) -> OverallStats:
        """
        Obtiene estadísticas generales del sistema.

        Args:
            force_refresh: Si True, ignora cache y recalcula

        Returns:
            OverallStats con todas las métricas
        """
        cache_key = "overall_stats"

        # Intentar obtener de cache
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        logger.info("📊 Calculando estadísticas generales...")

        # VIP Stats
        vip_active = await self._count_vip_by_status("active")
        vip_expired = await self._count_vip_by_status("expired")
        vip_expiring_soon = await self._count_vip_expiring_in_days(7)

        # Free Stats
        free_pending = await self._count_free_by_status(processed=False)
        free_processed = await self._count_free_by_status(processed=True)

        # Token Stats
        total_tokens = await self._count_all_tokens()
        tokens_used = await self._count_tokens_by_status(used=True)
        tokens_expired = await self._count_expired_tokens()
        tokens_available = total_tokens - tokens_used - tokens_expired

        # Activity Stats
        new_vip_today = await self._count_new_vip_in_period(days=1)
        new_vip_week = await self._count_new_vip_in_period(days=7)
        new_vip_month = await self._count_new_vip_in_period(days=30)

        # Revenue Stats
        monthly_revenue, yearly_revenue = await self._calculate_projected_revenue()

        stats = OverallStats(
            total_vip_active=vip_active,
            total_vip_expired=vip_expired,
            total_vip_expiring_soon=vip_expiring_soon,
            total_free_pending=free_pending,
            total_free_processed=free_processed,
            total_tokens_generated=total_tokens,
            total_tokens_used=tokens_used,
            total_tokens_expired=tokens_expired,
            total_tokens_available=tokens_available,
            new_vip_today=new_vip_today,
            new_vip_this_week=new_vip_week,
            new_vip_this_month=new_vip_month,
            projected_monthly_revenue=monthly_revenue,
            projected_yearly_revenue=yearly_revenue,
            calculated_at=datetime.utcnow()
        )

        # Guardar en cache
        self._set_cache(cache_key, stats)

        logger.info(f"✅ Stats calculadas: {vip_active} VIP activos, {free_pending} Free pendientes")

        return stats

    # ===== VIP STATS =====

    async def get_vip_stats(self, force_refresh: bool = False) -> VIPStats:
        """
        Obtiene estadísticas detalladas de VIP.

        Args:
            force_refresh: Si True, ignora cache

        Returns:
            VIPStats con métricas detalladas
        """
        cache_key = "vip_stats"

        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        logger.info("📊 Calculando estadísticas VIP...")

        # Conteos básicos
        active = await self._count_vip_by_status("active")
        expired = await self._count_vip_by_status("expired")
        all_time = await self._count_all_vip()

        # Por tiempo de expiración
        expiring_today = await self._count_vip_expiring_in_days(1)
        expiring_week = await self._count_vip_expiring_in_days(7)
        expiring_month = await self._count_vip_expiring_in_days(30)

        # Actividad temporal
        new_today = await self._count_new_vip_in_period(days=1)
        new_week = await self._count_new_vip_in_period(days=7)
        new_month = await self._count_new_vip_in_period(days=30)

        # Top subscribers
        top_subs = await self._get_top_vip_subscribers(limit=10)

        stats = VIPStats(
            total_active=active,
            total_expired=expired,
            total_all_time=all_time,
            expiring_today=expiring_today,
            expiring_this_week=expiring_week,
            expiring_this_month=expiring_month,
            new_today=new_today,
            new_this_week=new_week,
            new_this_month=new_month,
            top_subscribers=top_subs,
            calculated_at=datetime.utcnow()
        )

        self._set_cache(cache_key, stats)

        return stats

    # ===== FREE STATS =====

    async def get_free_stats(self, force_refresh: bool = False) -> FreeStats:
        """
        Obtiene estadísticas detalladas de Free.

        Args:
            force_refresh: Si True, ignora cache

        Returns:
            FreeStats con métricas detalladas
        """
        cache_key = "free_stats"

        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        logger.info("📊 Calculando estadísticas Free...")

        # Conteos básicos
        pending = await self._count_free_by_status(processed=False)
        processed = await self._count_free_by_status(processed=True)
        all_time = await self._count_all_free_requests()

        # Por estado de procesamiento
        wait_time = await self._get_configured_wait_time()
        ready = await self._count_free_ready_to_process(wait_time)
        still_waiting = pending - ready

        # Tiempo promedio
        avg_wait = await self._calculate_avg_wait_time()

        # Actividad temporal
        new_today = await self._count_new_free_in_period(days=1)
        new_week = await self._count_new_free_in_period(days=7)
        new_month = await self._count_new_free_in_period(days=30)

        # Próximas a procesar
        next_to_process = await self._get_next_free_to_process(limit=10, wait_time_minutes=wait_time)

        stats = FreeStats(
            total_pending=pending,
            total_processed=processed,
            total_all_time=all_time,
            ready_to_process=ready,
            still_waiting=still_waiting,
            avg_wait_time_minutes=avg_wait,
            new_requests_today=new_today,
            new_requests_this_week=new_week,
            new_requests_this_month=new_month,
            next_to_process=next_to_process,
            calculated_at=datetime.utcnow()
        )

        self._set_cache(cache_key, stats)

        return stats

    # ===== TOKEN STATS =====

    async def get_token_stats(self, force_refresh: bool = False) -> TokenStats:
        """
        Obtiene estadísticas detalladas de tokens.

        Args:
            force_refresh: Si True, ignora cache

        Returns:
            TokenStats con métricas detalladas
        """
        cache_key = "token_stats"

        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        logger.info("📊 Calculando estadísticas de tokens...")

        # Conteos básicos
        total_generated = await self._count_all_tokens()
        total_used = await self._count_tokens_by_status(used=True)
        total_expired = await self._count_expired_tokens()
        total_available = total_generated - total_used - total_expired

        # Por período (generados)
        gen_today = await self._count_tokens_generated_in_period(days=1)
        gen_week = await self._count_tokens_generated_in_period(days=7)
        gen_month = await self._count_tokens_generated_in_period(days=30)

        # Por período (usados)
        used_today = await self._count_tokens_used_in_period(days=1)
        used_week = await self._count_tokens_used_in_period(days=7)
        used_month = await self._count_tokens_used_in_period(days=30)

        # Tasa de conversión
        conversion_rate = (total_used / total_generated * 100) if total_generated > 0 else 0.0

        stats = TokenStats(
            total_generated=total_generated,
            total_used=total_used,
            total_expired=total_expired,
            total_available=total_available,
            generated_today=gen_today,
            generated_this_week=gen_week,
            generated_this_month=gen_month,
            used_today=used_today,
            used_this_week=used_week,
            used_this_month=used_month,
            conversion_rate=round(conversion_rate, 2),
            calculated_at=datetime.utcnow()
        )

        self._set_cache(cache_key, stats)

        return stats

    # ===== HELPER QUERIES - VIP =====

    async def _count_vip_by_status(self, status: str) -> int:
        """Cuenta VIP por status."""
        result = await self.session.execute(
            select(func.count(VIPSubscriber.id))
            .where(VIPSubscriber.status == status)
        )
        return result.scalar() or 0

    async def _count_all_vip(self) -> int:
        """Cuenta todos los VIP (histórico)."""
        result = await self.session.execute(
            select(func.count(VIPSubscriber.id))
        )
        return result.scalar() or 0

    async def _count_vip_expiring_in_days(self, days: int) -> int:
        """Cuenta VIP que expiran en X días."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)

        result = await self.session.execute(
            select(func.count(VIPSubscriber.id))
            .where(
                and_(
                    VIPSubscriber.status == "active",
                    VIPSubscriber.expiry_date <= cutoff_date,
                    VIPSubscriber.expiry_date > datetime.utcnow()
                )
            )
        )
        return result.scalar() or 0

    async def _count_new_vip_in_period(self, days: int) -> int:
        """Cuenta VIP nuevos en los últimos X días."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(func.count(VIPSubscriber.id))
            .where(VIPSubscriber.join_date >= cutoff_date)
        )
        return result.scalar() or 0

    async def _get_top_vip_subscribers(self, limit: int = 10) -> List[Dict]:
        """Obtiene top VIP por días restantes (ordenados)."""
        result = await self.session.execute(
            select(
                VIPSubscriber.user_id,
                VIPSubscriber.expiry_date,
                VIPSubscriber.join_date
            )
            .where(VIPSubscriber.status == "active")
            .order_by(VIPSubscriber.expiry_date.desc())
            .limit(limit)
        )

        subscribers = []
        for row in result:
            days_remaining = (row.expiry_date - datetime.utcnow()).days
            subscribers.append({
                "user_id": row.user_id,
                "days_remaining": max(0, days_remaining),
                "expiry_date": row.expiry_date.isoformat()
            })

        return subscribers

    # ===== HELPER QUERIES - FREE =====

    async def _count_free_by_status(self, processed: bool) -> int:
        """Cuenta solicitudes Free por estado de procesamiento."""
        result = await self.session.execute(
            select(func.count(FreeChannelRequest.id))
            .where(FreeChannelRequest.processed == processed)
        )
        return result.scalar() or 0

    async def _count_all_free_requests(self) -> int:
        """Cuenta todas las solicitudes Free (histórico)."""
        result = await self.session.execute(
            select(func.count(FreeChannelRequest.id))
        )
        return result.scalar() or 0

    async def _count_free_ready_to_process(self, wait_time_minutes: int) -> int:
        """Cuenta solicitudes Free listas para procesar."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=wait_time_minutes)

        result = await self.session.execute(
            select(func.count(FreeChannelRequest.id))
            .where(
                and_(
                    FreeChannelRequest.processed == False,
                    FreeChannelRequest.request_date <= cutoff_time
                )
            )
        )
        return result.scalar() or 0

    async def _count_new_free_in_period(self, days: int) -> int:
        """Cuenta solicitudes Free nuevas en los últimos X días."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(func.count(FreeChannelRequest.id))
            .where(FreeChannelRequest.request_date >= cutoff_date)
        )
        return result.scalar() or 0

    async def _calculate_avg_wait_time(self) -> float:
        """Calcula tiempo promedio de espera en minutos."""
        result = await self.session.execute(
            select(
                FreeChannelRequest.request_date,
                FreeChannelRequest.processed_at
            )
            .where(
                and_(
                    FreeChannelRequest.processed == True,
                    FreeChannelRequest.processed_at.isnot(None)
                )
            )
            .limit(100)  # Últimas 100 para promedio representativo
        )

        wait_times = []
        for row in result:
            if row.processed_at and row.request_date:
                diff = (row.processed_at - row.request_date).total_seconds() / 60
                wait_times.append(diff)

        if not wait_times:
            return 0.0

        return round(sum(wait_times) / len(wait_times), 2)

    async def _get_next_free_to_process(
        self,
        limit: int,
        wait_time_minutes: int
    ) -> List[Dict]:
        """Obtiene próximas solicitudes Free a procesar."""
        result = await self.session.execute(
            select(
                FreeChannelRequest.user_id,
                FreeChannelRequest.request_date
            )
            .where(FreeChannelRequest.processed == False)
            .order_by(FreeChannelRequest.request_date.asc())
            .limit(limit)
        )

        requests = []
        for row in result:
            elapsed_minutes = (datetime.utcnow() - row.request_date).total_seconds() / 60
            remaining_minutes = max(0, wait_time_minutes - elapsed_minutes)

            requests.append({
                "user_id": row.user_id,
                "minutes_remaining": round(remaining_minutes, 1),
                "request_date": row.request_date.isoformat()
            })

        return requests

    async def _get_configured_wait_time(self) -> int:
        """Obtiene tiempo de espera configurado."""
        result = await self.session.execute(
            select(BotConfig.wait_time_minutes).where(BotConfig.id == 1)
        )
        config = result.scalar()
        return config if config else 5

    # ===== HELPER QUERIES - TOKENS =====

    async def _count_all_tokens(self) -> int:
        """Cuenta todos los tokens generados."""
        result = await self.session.execute(
            select(func.count(InvitationToken.id))
        )
        return result.scalar() or 0

    async def _count_tokens_by_status(self, used: bool) -> int:
        """Cuenta tokens por estado de uso."""
        result = await self.session.execute(
            select(func.count(InvitationToken.id))
            .where(InvitationToken.used == used)
        )
        return result.scalar() or 0

    async def _count_expired_tokens(self) -> int:
        """Cuenta tokens expirados (no usados pero expirados)."""
        result = await self.session.execute(
            select(func.count(InvitationToken.id))
            .where(
                and_(
                    InvitationToken.used == False,
                    InvitationToken.created_at + timedelta(hours=24) < datetime.utcnow()
                )
            )
        )
        return result.scalar() or 0

    async def _count_tokens_generated_in_period(self, days: int) -> int:
        """Cuenta tokens generados en los últimos X días."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(func.count(InvitationToken.id))
            .where(InvitationToken.created_at >= cutoff_date)
        )
        return result.scalar() or 0

    async def _count_tokens_used_in_period(self, days: int) -> int:
        """Cuenta tokens usados en los últimos X días."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(func.count(InvitationToken.id))
            .where(
                and_(
                    InvitationToken.used == True,
                    InvitationToken.used_at >= cutoff_date
                )
            )
        )
        return result.scalar() or 0

    # ===== HELPER QUERIES - REVENUE =====

    async def _calculate_projected_revenue(self) -> Tuple[float, float]:
        """
        Calcula ingreso proyectado mensual y anual.

        Basado en:
        - Número de VIP activos
        - Tarifa mensual configurada en BotConfig

        Returns:
            Tuple[monthly_revenue, yearly_revenue]
        """
        # Obtener tarifa mensual
        result = await self.session.execute(
            select(BotConfig.subscription_fees).where(BotConfig.id == 1)
        )
        fees = result.scalar()

        if not fees or "monthly" not in fees:
            return 0.0, 0.0

        monthly_fee = fees.get("monthly", 0)

        # Contar VIP activos
        active_vip = await self._count_vip_by_status("active")

        # Proyección simple
        monthly_revenue = active_vip * monthly_fee
        yearly_revenue = monthly_revenue * 12

        return round(monthly_revenue, 2), round(yearly_revenue, 2)
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

    stats_service = providers.Factory(
        StatsService,
        session=db_session
    )

# Uso en handler
@router.message.command("test")
async def test_handler(message: Message):
    service = ServiceContainer.subscription_service()
    tokens = await service.list_valid_tokens()

    # Uso del StatsService
    stats_service = ServiceContainer.stats_service()
    overall_stats = await stats_service.get_overall_stats()
```

## Lazy Loading en ServiceContainer

El ServiceContainer implementa lazy loading para optimizar el consumo de memoria en Termux:

```python
class ServiceContainer:
    """
    Contenedor de servicios con lazy loading.

    Los servicios se instancian solo cuando se acceden por primera vez.
    Esto reduce el consumo de memoria inicial en Termux.

    Patrón: Dependency Injection + Lazy Initialization

    Uso:
        container = ServiceContainer(session, bot)

        # Primera vez: carga el service
        token = await container.subscription.generate_token(...)

        # Segunda vez: reutiliza instancia
        result = await container.subscription.validate_token(...)
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el container con dependencias base.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        assert session is not None, "session no puede ser None"
        assert bot is not None, "bot no puede ser None"

        self._session = session
        self._bot = bot

        # Services (cargados lazy)
        self._subscription_service = None
        self._channel_service = None
        self._config_service = None
        self._stats_service = None

        logger.debug("🏭 ServiceContainer inicializado (modo lazy)")

    # ===== SUBSCRIPTION SERVICE =====

    @property
    def subscription(self):
        """
        Service de gestión de suscripciones VIP/Free.

        Se carga lazy (solo en primer acceso).

        Returns:
            SubscriptionService: Instancia del service
        """
        if self._subscription_service is None:
            from bot.services.subscription import SubscriptionService
            logger.debug("🔄 Lazy loading: SubscriptionService")
            self._subscription_service = SubscriptionService(self._session, self._bot)

        return self._subscription_service

    # ===== CHANNEL SERVICE =====

    @property
    def channel(self):
        """
        Service de gestión de canales Telegram.

        Se carga lazy (solo en primer acceso).

        Returns:
            ChannelService: Instancia del service
        """
        if self._channel_service is None:
            from bot.services.channel import ChannelService
            logger.debug("🔄 Lazy loading: ChannelService")
            self._channel_service = ChannelService(self._session, self._bot)

        return self._channel_service

    # ===== CONFIG SERVICE =====

    @property
    def config(self):
        """
        Service de configuración del bot.

        Se carga lazy (solo en primer acceso).

        Returns:
            ConfigService: Instancia del service
        """
        if self._config_service is None:
            from bot.services.config import ConfigService
            logger.debug("🔄 Lazy loading: ConfigService")
            self._config_service = ConfigService(self._session)

        return self._config_service

    # ===== STATS SERVICE =====

    @property
    def stats(self):
        """
        Service de estadísticas.

        Se carga lazy (solo en primer acceso).

        Returns:
            StatsService: Instancia del service
        """
        if self._stats_service is None:
            from bot.services.stats import StatsService
            logger.debug("🔄 Lazy loading: StatsService")
            self._stats_service = StatsService(self._session)

        return self._stats_service

    # ===== UTILIDADES =====

    def get_loaded_services(self) -> list[str]:
        """
        Retorna lista de servicios ya cargados en memoria.

        Útil para debugging y monitoring de uso de memoria.

        Returns:
            Lista de nombres de services cargados
        """
        loaded = []

        if self._subscription_service is not None:
            loaded.append("subscription")
        if self._channel_service is not None:
            loaded.append("channel")
        if self._config_service is not None:
            loaded.append("config")
        if self._stats_service is not None:
            loaded.append("stats")

        return loaded

    async def preload_critical_services(self):
        """
        Precarga servicios críticos de forma explícita.

        Se puede llamar en background después del startup
        para "calentar" los services más usados.

        Críticos: subscription, config (usados frecuentemente)
        No críticos: channel, stats (usados ocasionalmente)
        """
        logger.info("🔥 Precargando services críticos...")

        # Trigger lazy load accediendo a las properties
        _ = self.subscription
        _ = self.config

        logger.info(f"✅ Services precargados: {self.get_loaded_services()}")
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

@pytest.mark.asyncio
async def test_stats_service_overall(session_mock):
    """Test cálculo de estadísticas generales"""
    service = StatsService(session_mock)

    # Mock de resultados de queries
    service._count_vip_by_status = AsyncMock(return_value=5)
    service._count_vip_expiring_in_days = AsyncMock(return_value=2)
    service._count_free_by_status = AsyncMock(return_value=10)
    service._count_all_tokens = AsyncMock(return_value=20)
    service._count_tokens_by_status = AsyncMock(return_value=8)
    service._count_expired_tokens = AsyncMock(return_value=2)
    service._calculate_projected_revenue = AsyncMock(return_value=(500.0, 6000.0))

    stats = await service.get_overall_stats()

    assert isinstance(stats, OverallStats)
    assert stats.total_vip_active == 5
    assert stats.total_vip_expiring_soon == 2
    assert stats.total_free_pending == 10
    assert stats.total_tokens_generated == 20
    assert stats.projected_monthly_revenue == 500.0

@pytest.mark.asyncio
async def test_stats_service_cache(session_mock):
    """Test funcionamiento del cache"""
    service = StatsService(session_mock)

    # Mock de resultados
    service._count_vip_by_status = AsyncMock(return_value=3)

    # Primera llamada
    stats1 = await service.get_overall_stats()
    timestamp1 = stats1.calculated_at

    # Segunda llamada (debe usar cache)
    stats2 = await service.get_overall_stats()
    timestamp2 = stats2.calculated_at

    assert timestamp1 == timestamp2  # Mismo timestamp = cache usado

    # Forzar recálculo
    stats3 = await service.get_overall_stats(force_refresh=True)
    timestamp3 = stats3.calculated_at

    assert timestamp3 > timestamp1  # Nuevo timestamp = recálculo forzado
```

## Dashboard Integration (T27)

El servicio de estadísticas se integra con el dashboard de estado del sistema (T27) para proporcionar métricas clave en tiempo real:

- `get_overall_stats()` - Utilizado por el dashboard para mostrar estadísticas generales del sistema
- `get_config_status()` - Utilizado por el dashboard para mostrar estado de configuración
- `get_scheduler_status()` - Utilizado por el dashboard para mostrar estado de tareas en segundo plano

El dashboard completo proporciona:
- Visualización del estado de los canales VIP y Free
- Estadísticas clave como VIPs activos, solicitudes Free pendientes y tokens disponibles
- Health checks del sistema con identificación de problemas y advertencias
- Acciones rápidas para acceso directo a funciones administrativas
- Información actualizada sobre tareas en segundo plano

---

**Última actualización:** 2025-12-13
**Versión:** 1.1.0
**Estado:** Documentación actualizada con StatsService (T18) y Dashboard Integration (T27) - Implementado
