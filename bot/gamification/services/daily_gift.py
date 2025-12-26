"""Servicio de gestión de regalo diario.

Responsabilidades:
- Verificar elegibilidad para reclamar
- Calcular y mantener rachas de días consecutivos
- Otorgar besitos por regalo diario
- Integrar con BesitoService para transacciones
"""

from typing import Optional, Tuple
from datetime import datetime, UTC, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import pytz

from bot.gamification.database.models import (
    DailyGiftClaim,
    GamificationConfig
)
from bot.gamification.database.enums import TransactionType

logger = logging.getLogger(__name__)

# Zona horaria de Ciudad de México
MEXICO_TZ = pytz.timezone('America/Mexico_City')


class DailyGiftService:
    """Servicio de gestión de regalo diario."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def can_claim_daily_gift(self, user_id: int) -> bool:
        """Verifica si el usuario puede reclamar el regalo diario.

        Compara solo la fecha (sin hora) en zona horaria de Ciudad de México.

        Args:
            user_id: ID del usuario

        Returns:
            True si puede reclamar (diferentes fechas), False si ya reclamó hoy
        """
        claim = await self._get_or_create_claim_record(user_id)

        # Si nunca ha reclamado, puede reclamar
        if not claim.last_claim_date:
            return True

        # Obtener fecha actual en zona horaria de Ciudad de México
        now_mx = datetime.now(MEXICO_TZ)
        today_date = now_mx.date()

        # Convertir last_claim_date a zona horaria de Ciudad de México
        last_claim_mx = claim.last_claim_date.replace(tzinfo=UTC).astimezone(MEXICO_TZ)
        last_claim_date = last_claim_mx.date()

        # Comparar solo las fechas (sin hora)
        can_claim = today_date != last_claim_date

        logger.debug(
            f"User {user_id}: today={today_date}, last_claim={last_claim_date}, "
            f"can_claim={can_claim}"
        )

        return can_claim

    async def calculate_streak(
        self,
        user_id: int,
        last_claim_date: Optional[datetime]
    ) -> int:
        """Calcula la racha de días consecutivos.

        Lógica:
        - Si last_claim_date es None: racha = 1 (primer día)
        - Si diferencia es 1 día: incrementa racha
        - Si diferencia es 0 días: mantiene racha (ya reclamó hoy, no debería pasar)
        - Si diferencia > 1 día: reinicia racha a 1

        Args:
            user_id: ID del usuario
            last_claim_date: Última fecha de reclamación

        Returns:
            Nueva racha calculada
        """
        claim = await self._get_or_create_claim_record(user_id)

        # Si nunca ha reclamado, es el primer día
        if not last_claim_date:
            return 1

        # Obtener fecha actual en zona horaria de Ciudad de México
        now_mx = datetime.now(MEXICO_TZ)
        today_date = now_mx.date()

        # Convertir last_claim_date a zona horaria de Ciudad de México
        last_claim_mx = last_claim_date.replace(tzinfo=UTC).astimezone(MEXICO_TZ)
        last_claim_date_only = last_claim_mx.date()

        # Calcular diferencia en días
        days_diff = (today_date - last_claim_date_only).days

        if days_diff == 0:
            # Mismo día, mantener racha (no debería pasar)
            new_streak = claim.current_streak
        elif days_diff == 1:
            # Día consecutivo, incrementar racha
            new_streak = claim.current_streak + 1
        else:
            # Se perdió la racha, reiniciar a 1
            new_streak = 1

        logger.debug(
            f"User {user_id}: days_diff={days_diff}, "
            f"old_streak={claim.current_streak}, new_streak={new_streak}"
        )

        return new_streak

    async def claim_daily_gift(self, user_id: int) -> Tuple[bool, str, dict]:
        """Reclama el regalo diario y otorga besitos.

        Flujo completo:
        1. Verifica si el sistema está habilitado
        2. Verifica si el usuario puede reclamar
        3. Obtiene configuración de besitos
        4. Calcula y actualiza racha
        5. Otorga besitos vía BesitoService
        6. Actualiza registro de reclamación
        7. Retorna resultado con detalles

        Args:
            user_id: ID del usuario

        Returns:
            Tuple (success, message, details)
            - success: True si se reclamó exitosamente
            - message: Mensaje descriptivo
            - details: Dict con {besitos_earned, current_streak, total_claims}
        """
        # 1. Verificar si el sistema está habilitado
        config = await self._get_config()
        if not config.daily_gift_enabled:
            return False, "❌ El sistema de regalo diario está desactivado", {}

        # 2. Verificar si el usuario puede reclamar
        can_claim = await self.can_claim_daily_gift(user_id)
        if not can_claim:
            # Calcular cuándo puede reclamar nuevamente
            next_claim = await self._get_next_claim_time()
            return (
                False,
                f"⏰ Ya reclamaste tu regalo hoy.\n"
                f"Próximo regalo disponible: {next_claim}",
                {}
            )

        # 3. Obtener configuración de besitos
        besitos_amount = config.daily_gift_besitos

        # 4. Obtener registro y calcular racha
        claim = await self._get_or_create_claim_record(user_id)
        new_streak = await self.calculate_streak(user_id, claim.last_claim_date)

        # 5. Otorgar besitos vía BesitoService
        from bot.gamification.services.besito import BesitoService
        besito_service = BesitoService(self.session)

        try:
            granted = await besito_service.grant_besitos(
                user_id=user_id,
                amount=besitos_amount,
                transaction_type=TransactionType.DAILY_GIFT,
                description=f"Regalo diario (día {new_streak})",
                reference_id=user_id
            )
        except Exception as e:
            logger.error(
                f"Error granting besitos to user {user_id}: {e}",
                exc_info=True
            )
            return False, f"❌ Error al otorgar besitos: {str(e)}", {}

        # 6. Actualizar registro de reclamación
        now_mx = datetime.now(MEXICO_TZ)
        now_utc = now_mx.astimezone(UTC)

        claim.last_claim_date = now_utc
        claim.current_streak = new_streak
        claim.total_claims += 1

        # Actualizar récord de racha si es necesario
        if new_streak > claim.longest_streak:
            claim.longest_streak = new_streak

        await self.session.commit()
        await self.session.refresh(claim)

        logger.info(
            f"User {user_id} claimed daily gift: "
            f"+{granted} besitos, streak={new_streak}, total_claims={claim.total_claims}"
        )

        # 7. Retornar resultado exitoso
        details = {
            'besitos_earned': granted,
            'current_streak': new_streak,
            'longest_streak': claim.longest_streak,
            'total_claims': claim.total_claims
        }

        streak_emoji = "🔥" if new_streak > 1 else "🎁"
        message = (
            f"🎉 ¡Regalo diario reclamado!\n\n"
            f"💋 +{granted} besitos\n"
            f"{streak_emoji} Racha: {new_streak} día{'s' if new_streak != 1 else ''}"
        )

        if new_streak == claim.longest_streak and new_streak > 1:
            message += f"\n🏆 ¡Nuevo récord personal!"

        return True, message, details

    async def get_daily_gift_status(self, user_id: int) -> dict:
        """Obtiene el estado del regalo diario para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con:
            {
                'can_claim': bool,
                'current_streak': int,
                'longest_streak': int,
                'total_claims': int,
                'next_claim_time': str (si can_claim=False),
                'besitos_amount': int
            }
        """
        config = await self._get_config()
        claim = await self._get_or_create_claim_record(user_id)
        can_claim = await self.can_claim_daily_gift(user_id)

        status = {
            'can_claim': can_claim and config.daily_gift_enabled,
            'current_streak': claim.current_streak,
            'longest_streak': claim.longest_streak,
            'total_claims': claim.total_claims,
            'besitos_amount': config.daily_gift_besitos,
            'system_enabled': config.daily_gift_enabled
        }

        if not can_claim:
            status['next_claim_time'] = await self._get_next_claim_time()

        return status

    async def reset_user_streak(self, user_id: int) -> bool:
        """Reinicia la racha de un usuario (uso administrativo).

        Args:
            user_id: ID del usuario

        Returns:
            True si se reinició exitosamente
        """
        claim = await self._get_or_create_claim_record(user_id)
        claim.current_streak = 0
        await self.session.commit()

        logger.info(f"Admin reset streak for user {user_id}")
        return True

    # ========================================
    # MÉTODOS PRIVADOS
    # ========================================

    async def _get_or_create_claim_record(self, user_id: int) -> DailyGiftClaim:
        """Obtiene o crea el registro de reclamación del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            DailyGiftClaim del usuario
        """
        stmt = select(DailyGiftClaim).where(DailyGiftClaim.user_id == user_id)
        result = await self.session.execute(stmt)
        claim = result.scalar_one_or_none()

        if not claim:
            claim = DailyGiftClaim(user_id=user_id)
            self.session.add(claim)
            await self.session.commit()
            await self.session.refresh(claim)
            logger.info(f"Created DailyGiftClaim for user {user_id}")

        return claim

    async def _get_config(self) -> GamificationConfig:
        """Obtiene la configuración global de gamificación.

        Returns:
            GamificationConfig singleton (id=1)
        """
        config = await self.session.get(GamificationConfig, 1)

        if not config:
            # Crear configuración por defecto si no existe
            config = GamificationConfig(
                id=1,
                daily_gift_enabled=True,
                daily_gift_besitos=10
            )
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)
            logger.info("Created default GamificationConfig")

        return config

    async def _get_next_claim_time(self) -> str:
        """Calcula cuándo estará disponible el próximo regalo.

        Returns:
            String con el tiempo relativo (ej: "en 5 horas")
        """
        now_mx = datetime.now(MEXICO_TZ)
        # Próximo regalo es a las 00:00 del día siguiente
        tomorrow_date = now_mx.date() + timedelta(days=1)
        next_midnight = MEXICO_TZ.localize(datetime.combine(tomorrow_date, datetime.min.time()))

        time_diff = next_midnight - now_mx
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"en {hours} hora{'s' if hours != 1 else ''} y {minutes} minuto{'s' if minutes != 1 else ''}"
        else:
            return f"en {minutes} minuto{'s' if minutes != 1 else ''}"
