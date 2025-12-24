"""Tests para LevelService."""

import pytest
from bot.gamification.services.level import LevelService
from bot.gamification.database.models import Level, UserGamification


# ========================================
# TESTS: CRUD NIVELES
# ========================================


@pytest.mark.asyncio
async def test_create_level_success(db_session):
    """Crear nivel exitosamente."""
    service = LevelService(db_session)

    level = await service.create_level(
        name="Novato",
        min_besitos=0,
        order=1,
        benefits={"multiplier": 1.0}
    )

    assert level.id is not None
    assert level.name == "Novato"
    assert level.min_besitos == 0
    assert level.order == 1
    assert level.active is True


@pytest.mark.asyncio
async def test_create_level_duplicate_name(db_session):
    """No permitir nombres duplicados."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)

    with pytest.raises(ValueError, match="already exists"):
        await service.create_level("Novato", 100, 2)


@pytest.mark.asyncio
async def test_create_level_duplicate_min_besitos(db_session):
    """No permitir min_besitos duplicados."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)

    with pytest.raises(ValueError, match="min_besitos"):
        await service.create_level("Regular", 0, 2)


@pytest.mark.asyncio
async def test_create_level_invalid_order(db_session):
    """Rechazar order <= 0."""
    service = LevelService(db_session)

    with pytest.raises(ValueError, match="order must be > 0"):
        await service.create_level("Novato", 0, 0)


@pytest.mark.asyncio
async def test_create_level_negative_besitos(db_session):
    """Rechazar min_besitos < 0."""
    service = LevelService(db_session)

    with pytest.raises(ValueError, match="min_besitos must be >= 0"):
        await service.create_level("Novato", -10, 1)


@pytest.mark.asyncio
async def test_update_level_success(db_session):
    """Actualizar nivel exitosamente."""
    service = LevelService(db_session)

    level = await service.create_level("Novato", 0, 1)

    updated = await service.update_level(
        level.id,
        name="Principiante",
        benefits={"multiplier": 1.1}
    )

    assert updated.name == "Principiante"
    assert updated.min_besitos == 0  # No cambió
    assert '"multiplier": 1.1' in updated.benefits


@pytest.mark.asyncio
async def test_update_level_duplicate_name(db_session):
    """No permitir update a nombre duplicado."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    await service.create_level("Regular", 500, 2)

    with pytest.raises(ValueError, match="already exists"):
        await service.update_level(level1.id, name="Regular")


@pytest.mark.asyncio
async def test_delete_level(db_session):
    """Soft-delete de nivel."""
    service = LevelService(db_session)

    level = await service.create_level("Novato", 0, 1)
    assert level.active is True

    result = await service.delete_level(level.id)
    assert result is True

    # Verificar soft-delete
    deleted = await service.get_level_by_id(level.id)
    assert deleted.active is False


@pytest.mark.asyncio
async def test_get_all_levels_active_only(db_session):
    """Obtener solo niveles activos."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)
    await service.delete_level(level2.id)

    levels = await service.get_all_levels(active_only=True)
    assert len(levels) == 1
    assert levels[0].name == "Novato"


@pytest.mark.asyncio
async def test_get_all_levels_include_inactive(db_session):
    """Obtener todos los niveles (incluyendo inactivos)."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)
    await service.delete_level(level2.id)

    levels = await service.get_all_levels(active_only=False)
    assert len(levels) == 2


@pytest.mark.asyncio
async def test_get_level_by_id(db_session):
    """Obtener nivel por ID."""
    service = LevelService(db_session)

    level = await service.create_level("Novato", 0, 1)

    found = await service.get_level_by_id(level.id)
    assert found is not None
    assert found.name == "Novato"


# ========================================
# TESTS: CÁLCULO DE NIVELES
# ========================================


@pytest.mark.asyncio
async def test_calculate_level_for_besitos(db_session):
    """Calcular nivel correcto según besitos."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    await service.create_level("Regular", 500, 2)
    await service.create_level("Fanático", 2000, 3)

    # Con 0 besitos → Novato
    level = await service.calculate_level_for_besitos(0)
    assert level.name == "Novato"

    # Con 750 besitos → Regular
    level = await service.calculate_level_for_besitos(750)
    assert level.name == "Regular"

    # Con 3000 besitos → Fanático
    level = await service.calculate_level_for_besitos(3000)
    assert level.name == "Fanático"


@pytest.mark.asyncio
async def test_calculate_level_for_besitos_edge_case(db_session):
    """Calcular nivel en caso límite (justo el min_besitos)."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    await service.create_level("Regular", 500, 2)

    # Con exactamente 500 besitos → Regular
    level = await service.calculate_level_for_besitos(500)
    assert level.name == "Regular"


@pytest.mark.asyncio
async def test_get_next_level_exists(db_session):
    """Obtener siguiente nivel cuando existe."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    next_level = await service.get_next_level(level1.id)
    assert next_level is not None
    assert next_level.name == "Regular"


@pytest.mark.asyncio
async def test_get_next_level_max_level(db_session):
    """Obtener None cuando ya está en nivel máximo."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    next_level = await service.get_next_level(level2.id)
    assert next_level is None


@pytest.mark.asyncio
async def test_get_besitos_to_next_level(db_session):
    """Calcular besitos faltantes para siguiente nivel."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    await service.create_level("Regular", 500, 2)

    # Crear usuario con 200 besitos en nivel Novato
    user = UserGamification(user_id=12345, total_besitos=200, current_level_id=level1.id)
    db_session.add(user)
    await db_session.commit()

    besitos_needed = await service.get_besitos_to_next_level(12345)
    assert besitos_needed == 300  # 500 - 200


@pytest.mark.asyncio
async def test_get_besitos_to_next_level_max_level(db_session):
    """Retornar None cuando está en nivel máximo."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    # Usuario en nivel máximo
    user = UserGamification(user_id=12345, total_besitos=1000, current_level_id=level2.id)
    db_session.add(user)
    await db_session.commit()

    besitos_needed = await service.get_besitos_to_next_level(12345)
    assert besitos_needed is None


# ========================================
# TESTS: LEVEL-UPS
# ========================================


@pytest.mark.asyncio
async def test_check_and_apply_level_up_success(db_session):
    """Aplicar level-up cuando corresponde."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    # Usuario con 600 besitos pero en nivel Novato
    user = UserGamification(user_id=12345, total_besitos=600, current_level_id=level1.id)
    db_session.add(user)
    await db_session.commit()

    changed, old_level, new_level = await service.check_and_apply_level_up(12345)

    assert changed is True
    assert old_level.name == "Novato"
    assert new_level.name == "Regular"

    # Verificar cambio en BD
    await db_session.refresh(user)
    assert user.current_level_id == level2.id


@pytest.mark.asyncio
async def test_check_and_apply_level_up_no_change(db_session):
    """No aplicar level-up cuando ya está en nivel correcto."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    await service.create_level("Regular", 500, 2)

    # Usuario con 300 besitos en nivel Novato (correcto)
    user = UserGamification(user_id=12345, total_besitos=300, current_level_id=level1.id)
    db_session.add(user)
    await db_session.commit()

    changed, old_level, new_level = await service.check_and_apply_level_up(12345)

    assert changed is False
    assert old_level is None
    assert new_level is None


@pytest.mark.asyncio
async def test_set_user_level_admin_override(db_session):
    """Forzar nivel específico (admin override)."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    # Usuario con 100 besitos
    user = UserGamification(user_id=12345, total_besitos=100, current_level_id=level1.id)
    db_session.add(user)
    await db_session.commit()

    # Admin fuerza nivel Regular
    result = await service.set_user_level(12345, level2.id)
    assert result is True

    await db_session.refresh(user)
    assert user.current_level_id == level2.id


# ========================================
# TESTS: PROGRESIÓN
# ========================================


@pytest.mark.asyncio
async def test_get_user_level_progress(db_session):
    """Obtener progresión completa de usuario."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    # Usuario con 300 besitos en Novato
    user = UserGamification(user_id=12345, total_besitos=300, current_level_id=level1.id)
    db_session.add(user)
    await db_session.commit()

    progress = await service.get_user_level_progress(12345)

    assert progress['current_level'].name == "Novato"
    assert progress['next_level'].name == "Regular"
    assert progress['current_besitos'] == 300
    assert progress['besitos_to_next'] == 200  # 500 - 300
    assert progress['progress_percentage'] == 60.0  # (300-0)/(500-0) * 100


@pytest.mark.asyncio
async def test_get_user_level_progress_max_level(db_session):
    """Progresión cuando está en nivel máximo."""
    service = LevelService(db_session)

    await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    # Usuario en nivel máximo
    user = UserGamification(user_id=12345, total_besitos=1000, current_level_id=level2.id)
    db_session.add(user)
    await db_session.commit()

    progress = await service.get_user_level_progress(12345)

    assert progress['current_level'].name == "Regular"
    assert progress['next_level'] is None
    assert progress['besitos_to_next'] is None


# ========================================
# TESTS: ESTADÍSTICAS
# ========================================


@pytest.mark.asyncio
async def test_get_level_distribution(db_session):
    """Obtener distribución de usuarios por nivel."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)
    level2 = await service.create_level("Regular", 500, 2)

    # 3 usuarios en Novato
    for i in range(3):
        user = UserGamification(user_id=1000 + i, total_besitos=100, current_level_id=level1.id)
        db_session.add(user)

    # 2 usuarios en Regular
    for i in range(2):
        user = UserGamification(user_id=2000 + i, total_besitos=600, current_level_id=level2.id)
        db_session.add(user)

    await db_session.commit()

    distribution = await service.get_level_distribution()

    assert distribution["Novato"] == 3
    assert distribution["Regular"] == 2


@pytest.mark.asyncio
async def test_get_users_in_level(db_session):
    """Obtener lista de usuarios en nivel específico."""
    service = LevelService(db_session)

    level1 = await service.create_level("Novato", 0, 1)

    # 3 usuarios en Novato con diferentes besitos
    user1 = UserGamification(user_id=1001, total_besitos=300, current_level_id=level1.id)
    user2 = UserGamification(user_id=1002, total_besitos=100, current_level_id=level1.id)
    user3 = UserGamification(user_id=1003, total_besitos=200, current_level_id=level1.id)

    db_session.add_all([user1, user2, user3])
    await db_session.commit()

    users = await service.get_users_in_level(level1.id, limit=10)

    assert len(users) == 3
    # Verificar orden descendente por besitos
    assert users[0].total_besitos == 300
    assert users[1].total_besitos == 200
    assert users[2].total_besitos == 100
