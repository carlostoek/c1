"""
Engine SQLAlchemy Async y factory de sesiones.
Configuración optimizada para SQLite en Termux.
"""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from config import Config
from bot.database.base import Base
from bot.database.models import BotConfig

# Importar modelos de gamificación para registrarlos en metadata
try:
    import bot.gamification.database.models  # noqa: F401
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ===== ENGINE GLOBAL =====
# Se inicializa una vez al llamar init_db()
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Retorna el engine de SQLAlchemy (debe estar inicializado).

    Raises:
        RuntimeError: Si el engine no ha sido inicializado con init_db()
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine no inicializado. "
            "Llama a init_db() primero."
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Retorna el factory de sesiones (debe estar inicializado).

    Raises:
        RuntimeError: Si el factory no ha sido inicializado con init_db()
    """
    if _session_factory is None:
        raise RuntimeError(
            "Session factory no inicializado. "
            "Llama a init_db() primero."
        )
    return _session_factory


class SessionContextManager:
    """Context manager para AsyncSession con manejo de errores."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
                logger.error(f"❌ Error en sesión de BD: {exc_val}")
        finally:
            await self.session.close()


def get_session() -> SessionContextManager:
    """
    Retorna un context manager para una sesión de base de datos.

    Uso:
        async with get_session() as session:
            # usar session
            # commit automático si no hay error
            # rollback automático si hay error

    Returns:
        SessionContextManager: Context manager de sesión
    """
    factory = get_session_factory()
    session = factory()
    return SessionContextManager(session)


async def init_db() -> None:
    """
    Inicializa el engine, configura SQLite y crea todas las tablas.

    Configuración para Termux:
    - WAL mode (Write-Ahead Logging) para mejor concurrencia
    - NORMAL synchronous (balance performance/seguridad)
    - Cache de 64MB
    - NullPool (SQLite no necesita connection pooling)

    También crea el registro inicial de BotConfig si no existe.
    """
    global _engine, _session_factory

    logger.info("🔧 Inicializando base de datos...")

    # Crear engine async con aiosqlite
    _engine = create_async_engine(
        Config.DATABASE_URL,
        echo=False,  # No loguear queries SQL (cambiar a True para debug)
        poolclass=NullPool,  # SQLite no necesita pool
        connect_args={
            "check_same_thread": False,  # Necesario para async
            "timeout": 30  # Timeout generoso para Termux
        }
    )

    # Configurar SQLite para mejor performance en Termux
    async with _engine.begin() as conn:
        # WAL mode: permite lecturas concurrentes mientras se escribe
        await conn.execute(text("PRAGMA journal_mode=WAL"))

        # NORMAL: fsync solo en checkpoints críticos (más rápido)
        await conn.execute(text("PRAGMA synchronous=NORMAL"))

        # Cache de 64MB (mejora performance de queries)
        await conn.execute(text("PRAGMA cache_size=-64000"))

        # Foreign keys habilitadas
        await conn.execute(text("PRAGMA foreign_keys=ON"))

        logger.info("✅ SQLite configurado (WAL mode, cache 64MB)")

    # Crear todas las tablas
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Tablas creadas/verificadas")

    # Crear session factory
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False  # No refrescar objetos después de commit
    )

    # Crear registro inicial de BotConfig (singleton)
    await _ensure_bot_config_exists()

    # Crear registro inicial de GamificationConfig (singleton)
    await _ensure_gamification_config_exists()

    # Crear niveles base si no existen
    await _ensure_base_levels_exist()

    logger.info("✅ Base de datos inicializada correctamente")


async def _ensure_bot_config_exists() -> None:
    """
    Crea el registro inicial de BotConfig si no existe.

    BotConfig es singleton: solo debe haber 1 registro (id=1).
    """
    async with get_session() as session:
        # Verificar si ya existe
        result = await session.get(BotConfig, 1)

        if result is None:
            # Crear registro inicial
            config = BotConfig(
                id=1,
                vip_channel_id=Config.VIP_CHANNEL_ID,
                free_channel_id=Config.FREE_CHANNEL_ID,
                wait_time_minutes=Config.DEFAULT_WAIT_TIME_MINUTES,
                vip_reactions=[],
                free_reactions=[],
                subscription_fees={"monthly": 10, "yearly": 100}
            )
            session.add(config)
            await session.commit()
            logger.info("✅ BotConfig inicial creado")
        else:
            logger.info("✅ BotConfig ya existe")


async def _ensure_gamification_config_exists() -> None:
    """
    Crea el registro inicial de GamificationConfig si no existe.

    GamificationConfig es singleton: solo debe haber 1 registro (id=1).
    """
    try:
        from bot.gamification.database.models import GamificationConfig
        from datetime import datetime, UTC

        async with get_session() as session:
            # Verificar si ya existe
            result = await session.get(GamificationConfig, 1)

            if result is None:
                # Crear registro inicial con valores por defecto
                config = GamificationConfig(
                    id=1,
                    besitos_per_reaction=1,
                    max_besitos_per_day=None,
                    streak_reset_hours=24,
                    notifications_enabled=True,
                    updated_at=datetime.now(UTC)
                )
                session.add(config)
                await session.commit()
                logger.info("✅ GamificationConfig inicial creado (notificaciones habilitadas)")
            else:
                logger.info("✅ GamificationConfig ya existe")
    except ImportError:
        logger.debug("Módulo de gamificación no disponible, saltando inicialización")


async def _ensure_base_levels_exist() -> None:
    """
    Crea niveles base del sistema de gamificación si no existen.

    Niveles por defecto:
    1. Novato (0 besitos)
    2. Entusiasta (100 besitos)
    3. Fanático (500 besitos)
    4. Leyenda (1000 besitos)
    """
    try:
        from bot.gamification.database.models import Level
        from datetime import datetime, UTC
        from sqlalchemy import select, func

        async with get_session() as session:
            # Contar niveles existentes
            stmt = select(func.count()).select_from(Level)
            result = await session.execute(stmt)
            level_count = result.scalar()

            if level_count == 0:
                # Crear niveles base
                base_levels = [
                    {
                        "name": "Novato",
                        "min_besitos": 0,
                        "order": 1,
                        "benefits": None,
                        "active": True,
                        "created_at": datetime.now(UTC)
                    },
                    {
                        "name": "Entusiasta",
                        "min_besitos": 100,
                        "order": 2,
                        "benefits": None,
                        "active": True,
                        "created_at": datetime.now(UTC)
                    },
                    {
                        "name": "Fanático",
                        "min_besitos": 500,
                        "order": 3,
                        "benefits": None,
                        "active": True,
                        "created_at": datetime.now(UTC)
                    },
                    {
                        "name": "Leyenda",
                        "min_besitos": 1000,
                        "order": 4,
                        "benefits": None,
                        "active": True,
                        "created_at": datetime.now(UTC)
                    }
                ]

                for level_data in base_levels:
                    level = Level(**level_data)
                    session.add(level)

                await session.commit()
                logger.info(f"✅ Creados {len(base_levels)} niveles base del sistema de gamificación")
            else:
                logger.info(f"✅ Ya existen {level_count} niveles en el sistema")
    except ImportError:
        logger.debug("Módulo de gamificación no disponible, saltando inicialización de niveles")


async def close_db() -> None:
    """
    Cierra el engine de base de datos (cleanup al apagar el bot).
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        logger.info("🔌 Base de datos cerrada")
        _engine = None
        _session_factory = None
