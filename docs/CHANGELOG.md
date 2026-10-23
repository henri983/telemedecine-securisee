# 📋 Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Versionnage Sémantique](https://semver.org/lang/fr/).

---

## [1.0.0] - 2026-10-23

### Ajouté

#### 🏥 API REST Sécurisée
- API REST complète pour la télémédecine avec FastAPI
- Endpoints patients (`/api/v1/patients/`)
- Endpoints consultations (`/api/v1/consultations/`)
- Endpoints dossiers médicaux (`/api/v1/medical-records/`)
- Documentation interactive Swagger UI et ReDoc
- Versioning API (`/api/v1/`)

#### 🔐 Sécurité
- Chiffrement **AES-256-GCM** de toutes les données médicales sensibles
- Hachage des mots de passe avec **Argon2id** (RFC 9106)
- Système d'authentification **JWT** avec access tokens (15 min) et refresh tokens (7 jours)
- **Rotation des refresh tokens** à chaque utilisation
- Contrôle d'accès basé sur les rôles (**RBAC**) : Admin, Praticien, Patient
- **Rate limiting** anti brute-force (5 tentatives / 15 min par IP)
- **Headers de sécurité HTTP** : HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **CORS** avec whitelist stricte des origines autorisées
- **Audit trail** complet de toutes les actions sensibles (sans PII dans les logs)

#### 🤖 Intelligence Artificielle
- Module de détection de comportements suspects via **IsolationForest**
- Extraction de **8 features comportementales** en temps réel
- Système d'alertes à **3 niveaux** (critique, avertissement, information)
- Analyse asynchrone des requêtes pour impact performance minimal

#### 📜 Conformité RGPD
- Endpoint **droit d'accès** (Article 15) — `GET /api/v1/rgpd/access`
- Endpoint **droit de rectification** (Article 16) — `PUT /api/v1/rgpd/rectify`
- Endpoint **droit à l'effacement** (Article 17) — `DELETE /api/v1/rgpd/erase`
- Endpoint **droit à la portabilité** (Article 20) — `GET /api/v1/rgpd/export`
- Endpoint **droit d'opposition** (Article 21) — `POST /api/v1/rgpd/object`
- **Consentement explicite** traçable et révocable
- **Pseudonymisation** des identifiants dans les logs et métriques
- **Minimisation des données** collectées

#### 🔄 CI/CD
- Pipeline **GitHub Actions** complet (lint, tests, sécurité, build, deploy)
- Analyse statique de sécurité (**Bandit** — SAST)
- Vérification des dépendances vulnérables (**Safety** — SCA)
- Scan des images Docker (**Trivy**)
- Vérification du typage (**MyPy**)
- Formatage automatique (**Black** + **isort**)
- Linting (**Ruff**)

#### 📊 Monitoring
- Stack de monitoring **Prometheus** + **Grafana**
- Métriques de performance (latence, débit, erreurs)
- Métriques de sécurité (connexions échouées, anomalies IA)
- Dashboards Grafana préconfigurés
- **Logs structurés JSON** via structlog (sans données personnelles)

#### 🧪 Tests
- Tests unitaires (pytest) — couverture ≥ 90%
- Tests d'intégration (pytest + httpx) — couverture ≥ 80%
- Tests de sécurité (headers, rate limiting)
- Fixtures partagées et factory patterns

#### 📚 Documentation
- Documentation d'**architecture** technique détaillée avec diagrammes Mermaid
- Document de **conformité RGPD** complet
- **Analyse d'impact** (DPIA) conforme Article 35
- **Politique de sécurité** avec procédure de divulgation responsable
- **README** professionnel avec guide de démarrage rapide

#### 🐳 Infrastructure
- **Dockerfile** de production multi-stage optimisé
- **docker-compose.yml** pour l'orchestration des services
- Configuration **Prometheus** et **Grafana**
- **Makefile** avec toutes les commandes de gestion du projet
- Migrations **Alembic** pour le schéma de base de données

---

## [Unreleased]

### Planifié pour v1.1.0
- 🔐 Authentification multi-facteurs (MFA/TOTP) pour les praticiens
- 🗄️ Réplication PostgreSQL synchrone
- 📱 Notifications push pour les alertes de sécurité
- 🔍 Recherche full-text sur les dossiers médicaux (côté serveur, post-déchiffrement)
- 📈 Amélioration du modèle IA (features supplémentaires, calibration)

---

[1.0.0]: https://github.com/henri983/telemedecine-securisee/releases/tag/v1.0.0
[Unreleased]: https://github.com/henri983/telemedecine-securisee/compare/v1.0.0...HEAD
