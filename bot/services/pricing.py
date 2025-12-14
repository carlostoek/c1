"""
Pricing Service - Gestión de planes de suscripción.

Proporciona operaciones CRUD para planes/tarifas:
- Crear planes
- Listar planes activos
- Obtener plan por ID
- Actualizar planes
- Activar/desactivar planes
"""
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import SubscriptionPlan, InvitationToken

logger = logging.getLogger(__name__)


class PricingService:
    """
    Servicio para gestionar planes de suscripción.

    Attributes:
        session: Sesión de base de datos
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de pricing.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    async def create_plan(
        self,
        name: str,
        duration_days: int,
        price: float,
        created_by: int,
        currency: str = "$"
    ) -> SubscriptionPlan:
        """
        Crea un nuevo plan de suscripción.

        Args:
            name: Nombre del plan (ej: "Plan Mensual")
            duration_days: Duración en días
            price: Precio del plan
            created_by: User ID del admin que crea el plan
            currency: Símbolo de moneda (default: "$")

        Returns:
            SubscriptionPlan creado

        Raises:
            ValueError: Si los parámetros son inválidos

        Examples:
            >>> plan = await service.create_plan(
            ...     name="Plan Mensual",
            ...     duration_days=30,
            ...     price=9.99,
            ...     created_by=123456
            ... )
        """
        # Validaciones
        if not name or len(name.strip()) == 0:
            raise ValueError("El nombre del plan no puede estar vacío")

        if duration_days <= 0:
            raise ValueError("La duración debe ser mayor a 0 días")

        if price < 0:
            raise ValueError("El precio no puede ser negativo")

        # Crear plan
        plan = SubscriptionPlan(
            name=name.strip(),
            duration_days=duration_days,
            price=price,
            currency=currency,
            active=True,
            created_at=datetime.utcnow(),
            created_by=created_by
        )

        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)

        logger.info(
            f"✅ Plan creado: {plan.name} ({plan.duration_days} días, "
            f"{plan.currency}{plan.price}) por admin {created_by}"
        )

        return plan

    async def get_all_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        """
        Obtiene todos los planes.

        Args:
            active_only: Si True, solo retorna planes activos (default: True)

        Returns:
            Lista de SubscriptionPlan ordenados por duración
        """
        query = select(SubscriptionPlan).order_by(SubscriptionPlan.duration_days.asc())

        if active_only:
            query = query.where(SubscriptionPlan.active == True)

        result = await self.session.execute(query)
        plans = result.scalars().all()

        logger.debug(f"📋 Obtenidos {len(plans)} planes (active_only={active_only})")

        return list(plans)

    async def get_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """
        Obtiene un plan por su ID.

        Args:
            plan_id: ID del plan

        Returns:
            SubscriptionPlan o None si no existe
        """
        result = await self.session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            logger.debug(f"📦 Plan encontrado: {plan.name} (ID: {plan_id})")
        else:
            logger.warning(f"⚠️ Plan no encontrado: ID {plan_id}")

        return plan

    async def update_plan(
        self,
        plan_id: int,
        name: Optional[str] = None,
        duration_days: Optional[int] = None,
        price: Optional[float] = None,
        currency: Optional[str] = None
    ) -> Optional[SubscriptionPlan]:
        """
        Actualiza un plan existente.

        Args:
            plan_id: ID del plan a actualizar
            name: Nuevo nombre (opcional)
            duration_days: Nueva duración (opcional)
            price: Nuevo precio (opcional)
            currency: Nuevo símbolo de moneda (opcional)

        Returns:
            SubscriptionPlan actualizado o None si no existe

        Raises:
            ValueError: Si los parámetros son inválidos
        """
        plan = await self.get_plan_by_id(plan_id)

        if not plan:
            return None

        # Validar y actualizar campos
        if name is not None:
            if len(name.strip()) == 0:
                raise ValueError("El nombre no puede estar vacío")
            plan.name = name.strip()

        if duration_days is not None:
            if duration_days <= 0:
                raise ValueError("La duración debe ser mayor a 0 días")
            plan.duration_days = duration_days

        if price is not None:
            if price < 0:
                raise ValueError("El precio no puede ser negativo")
            plan.price = price

        if currency is not None:
            plan.currency = currency

        await self.session.commit()
        await self.session.refresh(plan)

        logger.info(f"✅ Plan actualizado: {plan.name} (ID: {plan_id})")

        return plan

    async def toggle_plan_status(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """
        Activa o desactiva un plan.

        Args:
            plan_id: ID del plan

        Returns:
            SubscriptionPlan actualizado o None si no existe
        """
        plan = await self.get_plan_by_id(plan_id)

        if not plan:
            return None

        plan.active = not plan.active

        await self.session.commit()
        await self.session.refresh(plan)

        status = "activado" if plan.active else "desactivado"
        logger.info(f"✅ Plan {status}: {plan.name} (ID: {plan_id})")

        return plan

    async def delete_plan(self, plan_id: int) -> bool:
        """
        Elimina un plan (solo si no tiene tokens asociados).

        Args:
            plan_id: ID del plan a eliminar

        Returns:
            True si se eliminó, False si no existe o tiene tokens
        """
        plan = await self.get_plan_by_id(plan_id)

        if not plan:
            return False

        # Verificar si tiene tokens usando query directa
        result = await self.session.execute(
            select(func.count(InvitationToken.id)).where(
                InvitationToken.plan_id == plan_id
            )
        )
        token_count = result.scalar() or 0

        if token_count > 0:
            logger.warning(
                f"⚠️ No se puede eliminar plan {plan.name}: "
                f"tiene {token_count} tokens asociados"
            )
            return False

        await self.session.delete(plan)
        await self.session.commit()

        logger.info(f"✅ Plan eliminado: {plan.name} (ID: {plan_id})")

        return True
