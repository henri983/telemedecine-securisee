"""
Module de base de données asynchrone.

Fournit le moteur SQLAlchemy async, la fabrique de sessions
et la dépendance FastAPI pour l'injection de session.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def _create_engine() -> AsyncEngine:
    """
    Crée le moteur SQLAlchemy asynchrone.

    Configure le pool de connexions selon l'environnement.
    """
    settings = get_settings()
    engine_kwargs: dict = {
        "echo": not settings.is_production,
        "future": True,
    }

    # SQLite n'utilise pas de pool de connexions classique
    if "sqlite" not in settings.DATABASE_URL:
        engine_kwargs.update({
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        })

    return create_async_engine(settings.DATABASE_URL, **engine_kwargs)


engine: AsyncEngine = _create_engine()

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dépendance FastAPI fournissant une session de base de données.

    Gère automatiquement le commit/rollback et la fermeture de la session.

    Yields:
        AsyncSession: Session de base de données active.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialise la base de données en créant toutes les tables.

    À appeler au démarrage de l'application.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Ferme le moteur de base de données.

    À appeler à l'arrêt de l'application.
    """
    await engine.dispose()
