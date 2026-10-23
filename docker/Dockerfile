# ══════════════════════════════════════════════════════════════════════════════
# Télémédecine Sécurisée — Dockerfile (Production Multi-stage)
# ══════════════════════════════════════════════════════════════════════════════
# Build : docker build -f docker/Dockerfile -t telemedecine-securisee .
# Run   : docker run -p 8000:8000 --env-file .env telemedecine-securisee
# ══════════════════════════════════════════════════════════════════════════════

# ── Stage 1 : Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Métadonnées OCI
LABEL org.opencontainers.image.title="telemedecine-securisee"
LABEL org.opencontainers.image.description="Plateforme de télémédecine sécurisée avec détection IA"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="henri983"
LABEL org.opencontainers.image.authors="henri983"
LABEL org.opencontainers.image.source="https://github.com/henri983/telemedecine-securisee"
LABEL org.opencontainers.image.licenses="MIT"

# Variables d'environnement pour le build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Installer les dépendances système nécessaires à la compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements/base.txt requirements/base.txt
COPY requirements/prod.txt requirements/prod.txt
RUN pip install --prefix=/install --no-warn-script-location \
    -r requirements/prod.txt

# ── Stage 2 : Production ────────────────────────────────────────────────────
FROM python:3.12-slim AS production

# Métadonnées OCI
LABEL org.opencontainers.image.title="telemedecine-securisee"
LABEL org.opencontainers.image.description="Plateforme de télémédecine sécurisée avec détection IA"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="henri983"
LABEL org.opencontainers.image.authors="henri983"
LABEL org.opencontainers.image.source="https://github.com/henri983/telemedecine-securisee"
LABEL org.opencontainers.image.licenses="MIT"

# Variables d'environnement runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    ENVIRONMENT=production \
    PORT=8000

# Installer les dépendances runtime minimales
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Créer un utilisateur non-root pour la sécurité
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/false --create-home appuser

# Copier les dépendances Python depuis le builder
COPY --from=builder /install /usr/local

# Créer la structure de répertoires
WORKDIR /app
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Copier le code source
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser alembic/ /app/alembic/
COPY --chown=appuser:appuser alembic.ini /app/alembic.ini
COPY --chown=appuser:appuser pyproject.toml /app/pyproject.toml

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port de l'application
EXPOSE ${PORT}

# Healthcheck — vérifie que l'application répond
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Point d'entrée avec tini pour une gestion propre des signaux
ENTRYPOINT ["tini", "--"]

# Commande de démarrage avec Gunicorn + Uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
