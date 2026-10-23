# ══════════════════════════════════════════════════════════════════════════════
# Télémédecine Sécurisée — Makefile
# ══════════════════════════════════════════════════════════════════════════════
# Usage : make <target>
# ══════════════════════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
.PHONY: help install install-dev lint format test test-cov security-scan \
        docker-build docker-up docker-down docker-logs clean migrate seed \
        run-dev pre-commit-install

PYTHON := python
PIP := pip
DOCKER_COMPOSE := docker compose -f docker/docker-compose.yml
APP_NAME := telemedecine-securisee

# ── Aide ─────────────────────────────────────────────────────────────────────

help: ## Affiche cette aide
	@echo "══════════════════════════════════════════════════════════════"
	@echo "  $(APP_NAME) — Commandes disponibles"
	@echo "══════════════════════════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Installation ─────────────────────────────────────────────────────────────

install: ## Installe les dépendances de production
	@echo "📦 Installation des dépendances de production..."
	$(PIP) install -r requirements/base.txt
	$(PIP) install -e .
	@echo "✅ Installation terminée."

install-dev: ## Installe les dépendances de développement
	@echo "📦 Installation des dépendances de développement..."
	$(PIP) install -r requirements/dev.txt
	$(PIP) install -e ".[dev]"
	@echo "✅ Installation dev terminée."

# ── Qualité du code ──────────────────────────────────────────────────────────

lint: ## Vérifie le code (ruff + mypy)
	@echo "🔍 Vérification du code avec Ruff..."
	$(PYTHON) -m ruff check src/ tests/
	@echo "🔍 Vérification des types avec MyPy..."
	$(PYTHON) -m mypy src/
	@echo "✅ Lint terminé."

format: ## Formate le code avec Ruff
	@echo "🎨 Formatage du code..."
	$(PYTHON) -m ruff check --fix src/ tests/
	$(PYTHON) -m ruff format src/ tests/
	@echo "✅ Formatage terminé."

# ── Tests ────────────────────────────────────────────────────────────────────

test: ## Lance les tests unitaires
	@echo "🧪 Lancement des tests..."
	$(PYTHON) -m pytest tests/ -v
	@echo "✅ Tests terminés."

test-cov: ## Lance les tests avec couverture de code
	@echo "🧪 Lancement des tests avec couverture..."
	$(PYTHON) -m pytest tests/ -v --cov=src/app --cov-report=html --cov-report=term-missing
	@echo "📊 Rapport de couverture disponible dans htmlcov/"

# ── Sécurité ─────────────────────────────────────────────────────────────────

security-scan: ## Lance les analyses de sécurité (bandit + safety)
	@echo "🔒 Analyse de sécurité avec Bandit..."
	$(PYTHON) -m bandit -r src/ -c pyproject.toml
	@echo "🔒 Vérification des vulnérabilités connues avec Safety..."
	$(PYTHON) -m safety check --file requirements/base.txt
	@echo "✅ Scan de sécurité terminé."

# ── Docker ───────────────────────────────────────────────────────────────────

docker-build: ## Construit les images Docker
	@echo "🐳 Construction des images Docker..."
	$(DOCKER_COMPOSE) build
	@echo "✅ Build Docker terminé."

docker-up: ## Démarre tous les services Docker
	@echo "🐳 Démarrage des services..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services démarrés."
	@echo "   App      : http://localhost:8000"
	@echo "   Grafana  : http://localhost:3000"
	@echo "   Prometheus: http://localhost:9090"

docker-down: ## Arrête tous les services Docker
	@echo "🐳 Arrêt des services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Services arrêtés."

docker-logs: ## Affiche les logs des services Docker
	@echo "📋 Logs des services Docker..."
	$(DOCKER_COMPOSE) logs -f

# ── Base de données ──────────────────────────────────────────────────────────

migrate: ## Lance les migrations Alembic
	@echo "🗃️  Exécution des migrations..."
	$(PYTHON) -m alembic upgrade head
	@echo "✅ Migrations appliquées."

seed: ## Peuple la base de données avec des données de test
	@echo "🌱 Peuplement de la base de données..."
	$(PYTHON) -m app.scripts.seed
	@echo "✅ Données de test insérées."

# ── Développement ────────────────────────────────────────────────────────────

run-dev: ## Lance le serveur de développement
	@echo "🚀 Démarrage du serveur de développement..."
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pre-commit-install: ## Installe les hooks pre-commit
	@echo "🪝 Installation des hooks pre-commit..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Hooks pre-commit installés."

# ── Nettoyage ────────────────────────────────────────────────────────────────

clean: ## Nettoie les fichiers générés
	@echo "🧹 Nettoyage..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf dist/ build/
	@echo "✅ Nettoyage terminé."
