"""
Stats Service - Cálculo de métricas y estadísticas.

Responsabilidades:
- Calcular estadísticas generales del sistema
- Métricas de suscriptores VIP (activos, expirados, próximos a expirar)
- Métricas de canal Free (solicitudes pendientes, procesadas)
- Métricas de tokens (generados, usados, expirados)
- Proyecciones de ingresos
- Cache de resultados para optimizar performance
"""
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

logger = logging.getLogger(__name__)


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
