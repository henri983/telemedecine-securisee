"""
Fixtures pytest pour la plateforme de télémédecine sécurisée.

Ce fichier fournit toutes les fixtures partagées entre les tests:
- Application FastAPI de test
- Client HTTP async
- Session de base de données en mémoire
- Services de sécurité configurés pour les tests
- Utilisateurs et patients de test
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import Settings
from src.security.crypto import EncryptionService
from src.security.jwt_handler import JWTHandler
from src.security.rbac import Permission, ROLE_PERMISSIONS
from src.ai.anomaly_detector import AnomalyDetector
from src.models.user import User, UserRole
from src.models.patient import Patient


# ---------------------------------------------------------------------------
# Configuration de test
# ---------------------------------------------------------------------------

TEST_SECRET_KEY = "test-secret-key-for-jwt-do-not-use-in-production-1234567890"
TEST_ENCRYPTION_KEY = "0" * 64  # 32 bytes en hex pour AES-256
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Crée une boucle d'événements pour toute la session de tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Paramètres de configuration pour les tests."""
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        SECRET_KEY=TEST_SECRET_KEY,
        ENCRYPTION_KEY=TEST_ENCRYPTION_KEY,
        ENVIRONMENT="test",
        DEBUG=True,
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        ALGORITHM="HS256",
    )


# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine():
    """Moteur SQLAlchemy async en mémoire pour les tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    # Import du Base pour créer les tables
    from src.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Session de base de données transactionnelle pour chaque test."""
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# Services de sécurité
# ---------------------------------------------------------------------------

@pytest.fixture
def encryption_service() -> EncryptionService:
    """Service de chiffrement avec clé de test."""
    return EncryptionService(key_hex=TEST_ENCRYPTION_KEY)


@pytest.fixture
def jwt_handler() -> JWTHandler:
    """Gestionnaire JWT avec secret de test."""
    return JWTHandler(
        secret_key=TEST_SECRET_KEY,
        algorithm="HS256",
        access_token_expire_minutes=30,
    )


@pytest.fixture
def anomaly_detector() -> AnomalyDetector:
    """Détecteur d'anomalies configuré pour les tests."""
    return AnomalyDetector()


# ---------------------------------------------------------------------------
# Utilisateurs de test
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_admin_user() -> User:
    """Utilisateur admin de test."""
    return User(
        id=uuid.uuid4(),
        email="admin@telemedecine-test.fr",
        hashed_password="$2b$12$hashed_password_placeholder_admin",
        full_name="Admin Test",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_praticien_user() -> User:
    """Utilisateur praticien de test."""
    return User(
        id=uuid.uuid4(),
        email="dr.dupont@telemedecine-test.fr",
        hashed_password="$2b$12$hashed_password_placeholder_praticien",
        full_name="Dr. Jean Dupont",
        role=UserRole.PRATICIEN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_patient_user() -> User:
    """Utilisateur patient de test."""
    return User(
        id=uuid.uuid4(),
        email="patient@telemedecine-test.fr",
        hashed_password="$2b$12$hashed_password_placeholder_patient",
        full_name="Marie Martin",
        role=UserRole.PATIENT,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_user(sample_admin_user) -> User:
    """Alias par défaut: utilisateur admin."""
    return sample_admin_user


@pytest.fixture
def sample_patient(sample_patient_user, encryption_service) -> Patient:
    """Patient de test avec données chiffrées."""
    return Patient(
        id=uuid.uuid4(),
        user_id=sample_patient_user.id,
        first_name_encrypted=encryption_service.encrypt("Marie"),
        last_name_encrypted=encryption_service.encrypt("Martin"),
        date_of_birth_encrypted=encryption_service.encrypt("1985-03-15"),
        social_security_encrypted=encryption_service.encrypt("185031234567890"),
        phone_encrypted=encryption_service.encrypt("+33612345678"),
        address_encrypted=encryption_service.encrypt("12 Rue de la Paix, 75001 Paris"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Headers d'authentification
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_auth_headers(jwt_handler, sample_admin_user) -> dict[str, str]:
    """Headers HTTP avec token JWT admin valide."""
    token = jwt_handler.create_access_token(
        subject=str(sample_admin_user.id),
        extra_claims={
            "email": sample_admin_user.email,
            "role": sample_admin_user.role.value,
        },
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def praticien_auth_headers(jwt_handler, sample_praticien_user) -> dict[str, str]:
    """Headers HTTP avec token JWT praticien valide."""
    token = jwt_handler.create_access_token(
        subject=str(sample_praticien_user.id),
        extra_claims={
            "email": sample_praticien_user.email,
            "role": sample_praticien_user.role.value,
        },
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient_auth_headers(jwt_handler, sample_patient_user) -> dict[str, str]:
    """Headers HTTP avec token JWT patient valide."""
    token = jwt_handler.create_access_token(
        subject=str(sample_patient_user.id),
        extra_claims={
            "email": sample_patient_user.email,
            "role": sample_patient_user.role.value,
        },
    )
    return {"Authorization": f"Bearer {token}"}


def auth_headers_for_role(jwt_handler: JWTHandler, role: str) -> dict[str, str]:
    """Génère des headers d'authentification pour un rôle donné."""
    user_id = str(uuid.uuid4())
    token = jwt_handler.create_access_token(
        subject=user_id,
        extra_claims={
            "email": f"{role}@telemedecine-test.fr",
            "role": role,
        },
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Application FastAPI et client HTTP
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def app(db_session, test_settings):
    """Application FastAPI configurée pour les tests."""
    from src.main import create_app

    test_app = create_app(settings=test_settings)

    # Override de la dépendance de session DB
    from src.dependencies import get_db_session

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db_session] = override_get_db

    yield test_app

    test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour tester l'API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Content-Type": "application/json"},
    ) as ac:
        yield ac
