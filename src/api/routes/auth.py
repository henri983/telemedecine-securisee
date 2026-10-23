"""
Routes d'authentification et gestion des sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session, get_jwt_handler
from src.models.user import User, UserRole
from src.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from src.security.jwt_handler import JWTHandler
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscription d'un utilisateur",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Enregistre un nouvel utilisateur après validation de robustesse du mot de passe."""
    auth_service = AuthService(db_session=db)

    # Vérification robustesse du mot de passe
    if not auth_service.validate_password_strength(payload.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial.",
        )

    # Vérification doublon
    stmt = select(User).where(User.email == payload.email.lower().strip())
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cette adresse email.",
        )

    user = await auth_service.register(
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    if payload.full_name:
        user.full_name = payload.full_name
        await db.flush()

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Connexion sécurisée",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db_session),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> TokenResponse:
    """Authentifie un utilisateur et délivre un jeton JWT avec signature numérique."""
    auth_service = AuthService(db_session=db)

    stmt = select(User).where(User.email == payload.email.lower().strip())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
        )

    if not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
        )

    token = jwt_handler.create_access_token(
        subject=str(user.id),
        role=user.role,
        extra_claims={"email": user.email, "role": user.role.value},
    )
    refresh_token = jwt_handler.create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        refresh_token=refresh_token,
    )
