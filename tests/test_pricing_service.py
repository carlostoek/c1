"""
Tests del Pricing Service - Sistema de tarifas/planes de suscripción.

Valida:
- Creación de planes
- Listado de planes
- Obtención de planes por ID
- Actualización de planes
- Eliminación de planes
- Relación con tokens
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import get_session_factory, get_engine
from bot.database.models import SubscriptionPlan
from bot.services.pricing import PricingService


@pytest.mark.asyncio
async def test_create_plan():
    """Test: Crear un nuevo plan."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Crear plan
        plan = await service.create_plan(
            name="Plan Mensual",
            duration_days=30,
            price=9.99,
            created_by=123456
        )

        # Validaciones
        assert plan.id is not None
        assert plan.name == "Plan Mensual"
        assert plan.duration_days == 30
        assert plan.price == 9.99
        assert plan.currency == "$"
        assert plan.active is True


@pytest.mark.asyncio
async def test_get_all_plans():
    """Test: Obtener todos los planes."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Crear múltiples planes
        plans_data = [
            ("Plan Mensual", 30, 9.99),
            ("Plan Trimestral", 90, 24.99),
            ("Plan Anual", 365, 79.99),
        ]

        for name, days, price in plans_data:
            await service.create_plan(name, days, price, 123456)

        # Obtener todos
        plans = await service.get_all_plans(active_only=True)

        # Validaciones
        assert len(plans) >= 3  # Al menos los 3 que creamos


@pytest.mark.asyncio
async def test_get_plan_by_id():
    """Test: Obtener plan por ID."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Crear plan
        plan = await service.create_plan("Plan Test", 30, 9.99, 123456)

        # Obtener por ID
        retrieved = await service.get_plan_by_id(plan.id)

        # Validaciones
        assert retrieved is not None
        assert retrieved.id == plan.id
        assert retrieved.name == "Plan Test"


@pytest.mark.asyncio
async def test_update_plan():
    """Test: Actualizar un plan."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Crear plan
        plan = await service.create_plan("Plan Original", 30, 9.99, 123456)
        original_id = plan.id

        # Actualizar
        updated = await service.update_plan(
            original_id,
            name="Plan Actualizado",
            price=14.99
        )

        # Validaciones
        assert updated is not None
        assert updated.id == original_id
        assert updated.name == "Plan Actualizado"
        assert updated.price == 14.99


@pytest.mark.asyncio
async def test_toggle_plan_status():
    """Test: Activar/desactivar plan."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Crear plan (activo por defecto)
        plan = await service.create_plan("Plan Test", 30, 9.99, 123456)
        assert plan.active is True

        # Desactivar
        toggled = await service.toggle_plan_status(plan.id)
        assert toggled.active is False

        # Activar de nuevo
        toggled = await service.toggle_plan_status(plan.id)
        assert toggled.active is True


@pytest.mark.asyncio
async def test_delete_plan():
    """Test: Eliminar plan sin tokens."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Crear plan
        plan = await service.create_plan("Plan Temporal", 30, 9.99, 123456)
        plan_id = plan.id

        # Eliminar
        result = await service.delete_plan(plan_id)
        assert result is True

        # Verificar que está eliminado
        retrieved = await service.get_plan_by_id(plan_id)
        assert retrieved is None


@pytest.mark.asyncio
async def test_validation_errors():
    """Test: Validación de errores de entrada."""
    async with get_session_factory()() as session:
        service = PricingService(session)

        # Test: Nombre vacío
        with pytest.raises(ValueError, match="nombre"):
            await service.create_plan("", 30, 9.99, 123456)

        # Test: Duración inválida
        with pytest.raises(ValueError, match="duración"):
            await service.create_plan("Plan Test", 0, 9.99, 123456)

        # Test: Precio negativo
        with pytest.raises(ValueError, match="precio"):
            await service.create_plan("Plan Test", 30, -1, 123456)
