# 🏗️ Architecture Technique — Télémédecine Sécurisée

> Document de référence décrivant l'architecture technique de la plateforme de télémédecine sécurisée.  
> **Version** : 1.0.0 | **Dernière mise à jour** : 2026-10-23 | **Auteur** : henri983

---

## 📑 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Diagramme d'architecture](#diagramme-darchitecture)
- [Description des composants](#description-des-composants)
- [Flux de données](#flux-de-données)
- [Flux d'authentification](#flux-dauthentification)
- [Flux de détection IA](#flux-de-détection-ia)
- [Décisions d'architecture (ADR)](#décisions-darchitecture-adr)
- [Choix technologiques](#choix-technologiques)

---

## Vue d'ensemble

L'architecture de la plateforme suit les principes suivants :

- **Défense en profondeur** : chaque couche applique ses propres contrôles de sécurité
- **Séparation des responsabilités** : découpage clair en couches (API, Services, Données)
- **Chiffrement omniprésent** : données chiffrées au repos et en transit
- **Observabilité** : monitoring, logging structuré et audit trail intégrés
- **Scalabilité horizontale** : statelessness des services, sessions externalisées dans Redis

---

## Diagramme d'architecture

### Architecture globale

```mermaid
graph TB
    subgraph Internet["🌐 Internet"]
        CLIENT_WEB["🖥️ Navigateur Web<br/>React SPA"]
        CLIENT_MOBILE["📱 Application Mobile<br/>React Native"]
    end

    subgraph DMZ["🛡️ Zone Démilitarisée"]
        LB["Load Balancer<br/>Nginx"]
        WAF["Web Application Firewall<br/>ModSecurity"]
        TLS["Terminaison TLS 1.3"]
    end

    subgraph Application["⚙️ Zone Application"]
        direction TB
        
        subgraph APILayer["Couche API - FastAPI"]
            ROUTER["Router / Middleware"]
            AUTH_MW["Middleware Auth JWT"]
            RATE_MW["Middleware Rate Limiting"]
            SEC_HEADERS["Middleware Security Headers"]
            CORS_MW["Middleware CORS"]
        end

        subgraph Services["Couche Services"]
            AUTH_SVC["🔑 Auth Service"]
            PATIENT_SVC["👤 Patient Service"]
            CONSULT_SVC["🩺 Consultation Service"]
            MEDICAL_SVC["📋 Medical Record Service"]
            RGPD_SVC["📜 RGPD Service"]
            AUDIT_SVC["📝 Audit Service"]
        end

        subgraph CoreSecurity["Noyau Sécurité"]
            CRYPTO["🔐 AES-256-GCM Engine"]
            RBAC["🛡️ RBAC Engine"]
            ARGON["🔒 Argon2id Hasher"]
        end

        subgraph AIEngine["🤖 Moteur IA"]
            FEATURE_ENG["Feature Engineering"]
            ISOLATION_FOREST["IsolationForest"]
            ALERT_ENGINE["Alert Engine"]
        end
    end

    subgraph Data["💾 Zone Données"]
        PG[("PostgreSQL 16<br/>Données chiffrées AES-256")]
        REDIS[("Redis 7<br/>Sessions / Cache / Rate Limit")]
    end

    subgraph Observability["📊 Zone Observabilité"]
        PROMETHEUS["Prometheus"]
        GRAFANA["Grafana"]
        ALERTMANAGER["AlertManager"]
        STRUCTURED_LOGS["Logs JSON structurés<br/>(sans PII)"]
    end

    CLIENT_WEB -->|HTTPS| LB
    CLIENT_MOBILE -->|HTTPS| LB
    LB --> WAF --> TLS --> ROUTER

    ROUTER --> AUTH_MW --> RATE_MW --> SEC_HEADERS --> CORS_MW

    CORS_MW --> AUTH_SVC
    CORS_MW --> PATIENT_SVC
    CORS_MW --> CONSULT_SVC
    CORS_MW --> MEDICAL_SVC
    CORS_MW --> RGPD_SVC

    AUTH_SVC --> CRYPTO
    AUTH_SVC --> ARGON
    AUTH_SVC --> RBAC
    PATIENT_SVC --> CRYPTO
    CONSULT_SVC --> CRYPTO
    MEDICAL_SVC --> CRYPTO
    RGPD_SVC --> CRYPTO

    Services --> AUDIT_SVC

    CRYPTO --> PG
    AUTH_SVC --> REDIS
    RATE_MW --> REDIS

    CORS_MW --> FEATURE_ENG --> ISOLATION_FOREST --> ALERT_ENGINE
    ALERT_ENGINE --> AUDIT_SVC

    Services --> PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERTMANAGER
    AUDIT_SVC --> STRUCTURED_LOGS
```

### Architecture en couches

```mermaid
graph TD
    subgraph Presentation["📱 Couche Présentation"]
        API_ENDPOINTS["Endpoints REST API<br/>FastAPI Routers"]
        SCHEMAS["Schémas Pydantic v2<br/>Validation entrée/sortie"]
    end

    subgraph Business["⚙️ Couche Métier"]
        SERVICES_LAYER["Services<br/>Logique applicative"]
        DOMAIN["Domaine<br/>Règles métier"]
    end

    subgraph Security_Layer["🔐 Couche Sécurité"]
        AUTH_LAYER["Authentification<br/>JWT + Refresh"]
        AUTHZ_LAYER["Autorisation<br/>RBAC"]
        ENCRYPTION_LAYER["Chiffrement<br/>AES-256-GCM"]
        AUDIT_LAYER["Audit<br/>Trail complet"]
    end

    subgraph Persistence["💾 Couche Persistance"]
        ORM["SQLAlchemy 2.0<br/>Modèles"]
        MIGRATIONS["Alembic<br/>Migrations"]
        DB_SESSION["Session Manager<br/>Connection Pool"]
    end

    Presentation --> Business
    Business --> Security_Layer
    Security_Layer --> Persistence
```

---

## Description des composants

### 1. Couche Réseau / DMZ

| Composant | Rôle | Technologie |
|-----------|------|-------------|
| **Load Balancer** | Distribution du trafic, terminaison SSL | Nginx |
| **WAF** | Protection contre les attaques web (injection, XSS) | ModSecurity / règles OWASP CRS |
| **TLS** | Chiffrement des communications | TLS 1.3, certificats Let's Encrypt |

### 2. Couche API

| Composant | Rôle | Détails |
|-----------|------|---------|
| **Router** | Routage des requêtes vers les endpoints | FastAPI APIRouter, versioning `/api/v1/` |
| **Middleware Auth** | Validation des JWT, extraction de l'identité | Vérification signature, expiration, claims |
| **Middleware Rate Limiting** | Protection anti brute-force | 5 req/15 min (auth), 100 req/min (API), via Redis |
| **Middleware Security Headers** | Injection des en-têtes de sécurité | HSTS, CSP, X-Frame-Options, etc. |
| **Middleware CORS** | Contrôle des origines autorisées | Whitelist stricte des domaines |

### 3. Couche Services

| Service | Responsabilité | Endpoints principaux |
|---------|---------------|---------------------|
| **Auth Service** | Authentification, tokens, sessions | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| **Patient Service** | Gestion des patients | `GET/POST/PUT /patients/` |
| **Consultation Service** | Gestion des consultations | `GET/POST/PUT /consultations/` |
| **Medical Record Service** | Dossiers médicaux chiffrés | `GET/POST /medical-records/` |
| **RGPD Service** | Exercice des droits RGPD | `GET /rgpd/access`, `DELETE /rgpd/erase` |
| **Audit Service** | Journalisation des actions | Interne, pas d'endpoint public |

### 4. Noyau Sécurité

| Composant | Algorithme / Standard | Configuration |
|-----------|----------------------|---------------|
| **Chiffrement** | AES-256-GCM | Clés dérivées via HKDF, nonces aléatoires 96 bits |
| **Hachage** | Argon2id | memory_cost=65536, time_cost=3, parallelism=4 |
| **JWT** | HMAC-SHA256 | Access: 15 min, Refresh: 7 jours, rotation |
| **RBAC** | Rôles hiérarchiques | Admin > Praticien > Patient |

### 5. Moteur IA

| Composant | Rôle | Détails |
|-----------|------|---------|
| **Feature Engineering** | Extraction de caractéristiques des requêtes | 8 features comportementales en temps réel |
| **IsolationForest** | Détection d'anomalies | Seuil configurable, contamination=0.1 |
| **Alert Engine** | Déclenchement des alertes | 3 niveaux : critique, avertissement, information |

### 6. Couche Données

| Composant | Technologie | Usage |
|-----------|------------|-------|
| **Base principale** | PostgreSQL 16 | Données persistantes, chiffrées au niveau applicatif |
| **Cache / Sessions** | Redis 7 | Sessions JWT, rate limiting, cache applicatif |

### 7. Observabilité

| Composant | Technologie | Métriques |
|-----------|------------|-----------|
| **Métriques** | Prometheus | Latence, débit, erreurs, saturation (RED + USE) |
| **Dashboards** | Grafana | Visualisation temps réel, alertes visuelles |
| **Alerting** | AlertManager | Notifications critiques (email, Slack) |
| **Logs** | structlog (JSON) | Logs structurés sans données personnelles |

---

## Flux de données

### Flux principal : Accès à un dossier médical

```mermaid
sequenceDiagram
    autonumber
    participant P as 👤 Patient/Praticien
    participant GW as 🛡️ API Gateway
    participant MW as ⚙️ Middleware
    participant API as 📡 FastAPI
    participant RBAC as 🔑 RBAC
    participant SVC as 📋 Medical Service
    participant CRYPTO as 🔐 AES-256-GCM
    participant DB as 💾 PostgreSQL
    participant AI as 🤖 IA Engine
    participant AUDIT as 📝 Audit

    P->>GW: GET /api/v1/medical-records/{id}
    GW->>MW: Requête HTTPS (TLS 1.3)
    
    MW->>MW: Vérification Rate Limit (Redis)
    MW->>MW: Validation JWT (signature + expiration)
    MW->>MW: Injection Security Headers
    
    MW->>API: Requête authentifiée
    API->>RBAC: Vérification des permissions
    
    alt Permission accordée
        RBAC-->>API: ✅ Autorisé
        API->>SVC: Récupérer dossier médical
        SVC->>DB: SELECT données chiffrées
        DB-->>SVC: Données chiffrées (AES-256-GCM)
        SVC->>CRYPTO: Déchiffrement
        CRYPTO-->>SVC: Données en clair
        SVC-->>API: Dossier médical
        API-->>P: 200 OK + données
    else Permission refusée
        RBAC-->>API: ❌ Non autorisé
        API-->>P: 403 Forbidden
    end

    API->>AI: Analyse comportementale (async)
    AI->>AI: Extraction features + IsolationForest
    API->>AUDIT: Log de l'accès (sans PII)
```

### Flux de chiffrement des données

```mermaid
sequenceDiagram
    autonumber
    participant SVC as 📋 Service
    participant CRYPTO as 🔐 Crypto Engine
    participant KMS as 🗝️ Key Manager
    participant DB as 💾 PostgreSQL

    Note over SVC,DB: Écriture (chiffrement)
    SVC->>CRYPTO: Données sensibles en clair
    CRYPTO->>KMS: Demande clé de chiffrement
    KMS-->>CRYPTO: Clé AES-256 (via HKDF)
    CRYPTO->>CRYPTO: Génération nonce 96 bits (aléatoire)
    CRYPTO->>CRYPTO: Chiffrement AES-256-GCM
    CRYPTO-->>SVC: {nonce || ciphertext || tag}
    SVC->>DB: INSERT données chiffrées

    Note over SVC,DB: Lecture (déchiffrement)
    SVC->>DB: SELECT données chiffrées
    DB-->>SVC: {nonce || ciphertext || tag}
    SVC->>CRYPTO: Données chiffrées
    CRYPTO->>KMS: Demande clé de déchiffrement
    KMS-->>CRYPTO: Clé AES-256 (via HKDF)
    CRYPTO->>CRYPTO: Déchiffrement AES-256-GCM + vérification tag
    CRYPTO-->>SVC: Données en clair ✅
```

---

## Flux d'authentification

```mermaid
sequenceDiagram
    autonumber
    participant U as 👤 Utilisateur
    participant API as 📡 FastAPI
    participant AUTH as 🔑 Auth Service
    participant ARGON as 🔒 Argon2id
    participant REDIS as 📦 Redis
    participant DB as 💾 PostgreSQL
    participant AUDIT as 📝 Audit

    Note over U,AUDIT: Connexion (Login)
    U->>API: POST /api/v1/auth/login {email, password}
    API->>AUTH: Authentifier l'utilisateur
    AUTH->>DB: SELECT user WHERE email = ?
    DB-->>AUTH: Utilisateur + hash Argon2id
    AUTH->>ARGON: Vérifier password vs hash
    
    alt Mot de passe valide
        ARGON-->>AUTH: ✅ Valide
        AUTH->>AUTH: Générer Access Token JWT (15 min)
        AUTH->>AUTH: Générer Refresh Token (7 jours)
        AUTH->>REDIS: Stocker session {user_id, refresh_token, IP, UA}
        AUTH-->>API: {access_token, refresh_token, expires_in}
        API-->>U: 200 OK + tokens
        AUTH->>AUDIT: Log connexion réussie
    else Mot de passe invalide
        ARGON-->>AUTH: ❌ Invalide
        AUTH->>REDIS: Incrémenter compteur échecs (IP)
        AUTH-->>API: Identifiants invalides
        API-->>U: 401 Unauthorized
        AUTH->>AUDIT: Log tentative échouée
    end

    Note over U,AUDIT: Rafraîchissement du token
    U->>API: POST /api/v1/auth/refresh {refresh_token}
    API->>AUTH: Vérifier refresh token
    AUTH->>REDIS: Valider refresh_token
    
    alt Refresh token valide
        REDIS-->>AUTH: ✅ Session active
        AUTH->>AUTH: Rotation : nouveau access + refresh token
        AUTH->>REDIS: Invalider ancien refresh, stocker nouveau
        AUTH-->>API: {new_access_token, new_refresh_token}
        API-->>U: 200 OK + nouveaux tokens
    else Refresh token invalide
        REDIS-->>AUTH: ❌ Session invalide / expirée
        AUTH-->>API: Session expirée
        API-->>U: 401 Unauthorized
    end

    Note over U,AUDIT: Déconnexion (Logout)
    U->>API: POST /api/v1/auth/logout
    API->>AUTH: Invalider la session
    AUTH->>REDIS: Supprimer session + blacklist access token
    AUTH-->>API: ✅ Déconnecté
    API-->>U: 200 OK
    AUTH->>AUDIT: Log déconnexion
```

---

## Flux de détection IA

```mermaid
sequenceDiagram
    autonumber
    participant REQ as 📨 Requête entrante
    participant MW as ⚙️ AI Middleware
    participant FE as 🔧 Feature Engine
    participant IF as 🧠 IsolationForest
    participant AE as 🚨 Alert Engine
    participant ADMIN as 👨‍💼 Admin
    participant AUDIT as 📝 Audit Log
    participant REDIS as 📦 Redis

    REQ->>MW: Requête HTTP (métadonnées)
    MW->>FE: Extraire les features

    FE->>REDIS: Récupérer historique utilisateur
    REDIS-->>FE: Historique récent (fenêtre glissante)

    FE->>FE: Calculer features
    Note right of FE: - request_frequency<br/>- hour_of_day<br/>- endpoint_diversity<br/>- data_volume<br/>- error_rate<br/>- geo_anomaly<br/>- session_duration<br/>- access_pattern

    FE->>IF: Vecteur de features [8 dimensions]
    IF->>IF: Calcul du score d'anomalie

    alt Score < -0.5 (CRITIQUE)
        IF-->>AE: 🔴 Score anomalie critique
        AE->>AUDIT: Log alerte critique
        AE->>ADMIN: 🚨 Notification immédiate
        AE-->>MW: Action : BLOQUER la requête
        MW-->>REQ: 429 Too Many Requests
    else Score entre -0.5 et -0.3 (AVERTISSEMENT)
        IF-->>AE: 🟡 Score anomalie modéré
        AE->>AUDIT: Log avertissement
        AE-->>MW: Action : OBSERVER (requête autorisée)
        MW-->>REQ: Requête traitée normalement
    else Score >= -0.3 (NORMAL)
        IF-->>FE: 🟢 Comportement normal
        FE-->>MW: Aucune action
        MW-->>REQ: Requête traitée normalement
    end

    MW->>REDIS: Mettre à jour l'historique utilisateur
```

---

## Décisions d'architecture (ADR)

### ADR-001 : Choix de FastAPI comme framework

- **Statut** : ✅ Accepté
- **Date** : 2026-10-01
- **Contexte** : Besoin d'un framework Python performant, avec support natif d'OpenAPI, validation automatique et architecture asynchrone.
- **Décision** : Utiliser FastAPI avec Uvicorn comme serveur ASGI.
- **Justification** :
  - Performance supérieure à Flask/Django REST grâce à l'async natif
  - Génération automatique de la documentation OpenAPI/Swagger
  - Validation intégrée via Pydantic v2 (performances C)
  - Injection de dépendances native (simplifie les tests)
  - Typage statique intégral avec support MyPy
- **Alternatives considérées** : Django REST Framework (trop lourd), Flask (pas de validation native), Starlette (trop bas niveau)
- **Conséquences** : Nécessite Python 3.12+, courbe d'apprentissage async pour les contributeurs

### ADR-002 : Chiffrement AES-256-GCM au niveau applicatif

- **Statut** : ✅ Accepté
- **Date** : 2026-10-03
- **Contexte** : Les données médicales sont des données sensibles au sens du RGPD (Article 9). Le chiffrement doit garantir la confidentialité même en cas de compromission de la base de données.
- **Décision** : Chiffrer toutes les données médicales sensibles au niveau applicatif avec AES-256-GCM avant stockage en base.
- **Justification** :
  - Chiffrement authentifié (GCM) : intégrité + confidentialité
  - Indépendant du SGBD : portable, pas de dépendance à une feature spécifique PostgreSQL
  - Contrôle total des clés côté application
  - Nonce unique par opération : pas de réutilisation de vecteur d'initialisation
- **Alternatives considérées** : TDE PostgreSQL (ne protège pas contre un accès SQL), pgcrypto (dépendance SGBD), chiffrement disque (ne protège pas en cas d'accès logique)
- **Conséquences** : Léger surcoût CPU pour chiffrement/déchiffrement, impossibilité de faire des requêtes SQL sur les champs chiffrés (recherche par index impossible sur ces champs)

### ADR-003 : IsolationForest pour la détection d'anomalies

- **Statut** : ✅ Accepté
- **Date** : 2026-10-07
- **Contexte** : Besoin de détecter des comportements suspects (exfiltration de données, compromission de compte) en temps réel, sans base de données d'attaques labellisées.
- **Décision** : Utiliser l'algorithme IsolationForest de scikit-learn pour la détection d'anomalies non supervisée.
- **Justification** :
  - Fonctionne sans données labellisées (apprentissage non supervisé)
  - Complexité linéaire O(n) : adapté au temps réel
  - Robuste sur les distributions déséquilibrées (peu d'anomalies vs beaucoup de normal)
  - Interprétabilité via le score d'anomalie [-1, 1]
  - Léger en mémoire et en CPU
- **Alternatives considérées** : Autoencoders (trop complexe, nécessite GPU), One-Class SVM (ne scale pas), règles statiques (trop de faux positifs/négatifs)
- **Conséquences** : Nécessite une phase de calibration initiale, seuils à ajuster en production

### ADR-004 : Sessions externalisées dans Redis

- **Statut** : ✅ Accepté
- **Date** : 2026-10-05
- **Contexte** : L'application doit être stateless pour permettre le scaling horizontal. Les sessions JWT et le rate limiting nécessitent un stockage partagé rapide.
- **Décision** : Utiliser Redis comme store de sessions, refresh tokens et compteurs de rate limiting.
- **Justification** :
  - Latence sub-milliseconde pour les lookups
  - TTL natif pour l'expiration automatique des sessions
  - Opérations atomiques (INCR) pour le rate limiting
  - Permet le scaling horizontal de l'API sans sticky sessions
- **Alternatives considérées** : Sessions en base PostgreSQL (trop lent), sessions en mémoire (pas distribué), Memcached (pas de persistance)
- **Conséquences** : Dépendance opérationnelle à Redis, nécessite monitoring Redis

### ADR-005 : Logs structurés JSON sans PII

- **Statut** : ✅ Accepté
- **Date** : 2026-10-08
- **Contexte** : Les logs doivent être exploitables pour le debugging et le monitoring, mais ne doivent contenir aucune donnée personnelle identifiable (PII) conformément au RGPD.
- **Décision** : Utiliser structlog pour produire des logs JSON structurés, avec pseudonymisation automatique des identifiants.
- **Justification** :
  - Format JSON compatible avec les outils d'observabilité (ELK, Loki)
  - Pseudonymisation automatique (user_id hashé, pas de nom/email)
  - Contexte enrichi (request_id, trace_id) pour le tracing distribué
  - Conformité RGPD : aucune PII dans les logs
- **Alternatives considérées** : Logging standard Python (pas structuré), loguru (pas de pseudonymisation intégrée)
- **Conséquences** : Nécessite des processeurs de log custom pour la pseudonymisation

---

## Choix technologiques

### Matrice de décision

| Critère | Poids | FastAPI | Django REST | Flask |
|---------|-------|---------|-------------|-------|
| Performance async | 25% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Validation automatique | 20% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Documentation auto (OpenAPI) | 15% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Typage statique | 15% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Écosystème sécurité | 15% | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Simplicité / DX | 10% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Score pondéré** | **100%** | **4.75** | **3.55** | **2.55** |

### Justification des choix de sécurité

| Composant | Choix | Justification sécurité |
|-----------|-------|----------------------|
| **Chiffrement** | AES-256-GCM | Standard NIST, chiffrement authentifié, résistant aux attaques par canal auxiliaire |
| **Hachage** | Argon2id | Vainqueur du Password Hashing Competition 2015, résistant GPU et ASIC |
| **Tokens** | JWT + HMAC-SHA256 | Standard RFC 7519, rotation des refresh tokens, blacklisting |
| **Rate Limiting** | Token Bucket (Redis) | Protection anti brute-force, configuration par endpoint |
| **CORS** | Whitelist stricte | Prévention CSRF, origines autorisées uniquement |
| **Headers** | OWASP Secure Headers | Conformité OWASP, protection navigateur |

---

> 📖 Retour au [README principal](../README.md) | 📜 [Conformité RGPD](RGPD.md) | 🔐 [Politique de sécurité](SECURITY.md)
