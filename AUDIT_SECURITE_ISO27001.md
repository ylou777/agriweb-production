# Audit de Sécurité ISO 27001 – HeliaPV / AgriWeb
**Date :** 6 mars 2026  
**Auditeur :** GitHub Copilot  
**Périmètre :** Codebase complète (repo `ylou777/agriweb-production`, branche `main`)  
**Statut global :** ⚠️ Non-conforme — 5 vulnérabilités critiques à traiter en priorité

---

## Résumé exécutif

| Niveau | Nombre | Statut |
|--------|--------|--------|
| 🔴 Critique | 5 | À traiter immédiatement |
| 🟠 Élevé | 6 | À traiter sous 7 jours |
| 🟡 Moyen | 5 | À planifier |
| ✅ Conforme | 8 | Maintenir |

---

## 🔴 CRITIQUES — Action immédiate

### [ ] C1 — Clés secrètes hardcodées dans le code source versionné
**Contrôle ISO 27001 :** A.8.24 (Utilisation de la cryptographie)  
**Fichiers concernés :**

| Fichier | Secret exposé | Ligne |
|---------|---------------|-------|
| `config.py` | `AIzaSyCzZGqZYWJe2O-hGDBAbUv68c3URzEkZmw` (Google Solar API) | L.3 |
| `stripe_config.py` | `sk_test_51QRwd8P3NsW4P31F...` (Stripe secret key) | L.13 |
| `auth_simple.py` | `app.secret_key = 'agriweb-auth-2025'` (Flask secret fixe) | L.38 |
| `agriweb_hebergement_gratuit.py` | `'agriweb-secret-key-2025-commercial'` (fallback Flask) | L.610 |
| `license_manager.py` | Clé Fernet `V9IOdZhPWH...` en clair | L.9 |

**Risque :** Un attaquant ayant accès au repo peut générer des frais Stripe, usurper l'identité de l'app, falsifier des licences.

**Remédiation :**
1. Révoquer immédiatement la clé Google Solar dans la console GCP
2. Révoquer la clé Stripe dans le dashboard Stripe → créer une nouvelle clé
3. Définir de vraies variables d'environnement sur Railway (Settings → Variables)
4. Retirer tous les fallbacks hardcodés — lever une erreur si la variable est absente :
```python
# Remplacer partout les fallbacks par :
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY non définie — configurer la variable d'environnement")
```

---

### [ ] C2 — Fichiers sensibles committés dans Git (historique inclus)
**Contrôle ISO 27001 :** A.8.10 (Suppression des informations)  
**Fichiers trackés par git :** `production_licenses.json`, `production_users.json`, `stripe_config.env`, `stripe_config.py`  
**Commits identifiés :** `de22e4b`, `ce35cb9`

**Risque :** Ces fichiers restent accessibles dans l'historique même après suppression.

**Remédiation :**
```bash
# 1. Installer git-filter-repo
pip install git-filter-repo

# 2. Purger les fichiers de l'historique
git filter-repo --invert-paths \
  --path stripe_config.py \
  --path stripe_config.env \
  --path production_users.json \
  --path production_licenses.json \
  --path users.json

# 3. Forcer le push
git push origin main --force

# 4. Ajouter au .gitignore (déjà absent — à ajouter)
echo "users.json" >> .gitignore
echo "production_*.json" >> .gitignore
echo "stripe_config.py" >> .gitignore
echo "stripe_config.env" >> .gitignore
```

---

### [ ] C3 — Mot de passe admin haché en SHA-256 sans sel
**Contrôle ISO 27001 :** A.5.17 (Informations d'authentification)  
**Fichier :** `users.json`

```json
"admin@agriweb.fr": {
  "password": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
}
```
Ce hash est SHA-256 de `admin123` — crack instantané par rainbow table.  
Le compte `ylaurent.perso@gmail.com` utilise PBKDF2+sel (format `hash:sel`) — correct.

**Risque :** Compromission immédiate du compte admin si la base est exfiltrée.

**Remédiation :**
- Supprimer `users.json` du repo (fichier legacy)
- Recréer le compte admin via `auth_system_improved.py` qui utilise PBKDF2 (100 000 itérations)
- Forcer le changement de mot de passe à la prochaine connexion

---

### [ ] C4 — Route de debug exposée publiquement sans authentification
**Contrôle ISO 27001 :** A.8.8 (Gestion des vulnérabilités techniques)  
**Fichier :** `agriweb_hebergement_gratuit.py` ligne 5284

```python
@app.route("/debug/auth", methods=["GET"])
def debug_auth():
    return jsonify({
        "endpoints": {"register": "/register (POST)", "login": "/login (POST)", ...},
        "database": "SQLite operational",
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    })
```
Accessible sur `https://app.heliapv.fr/debug/auth` sans login.

**Remédiation :**
```python
@app.route("/debug/auth", methods=["GET"])
@require_auth
def debug_auth():
    if not request.current_user.get('is_admin'):
        abort(403)
    return jsonify({...})
```
Ou mieux : supprimer complètement cette route en production.

---

### [ ] C5 — CORS wildcard sur toutes les API
**Contrôle ISO 27001 :** A.8.20 (Sécurité des réseaux)  
**Fichier :** `agriweb_hebergement_gratuit.py` lignes 706-708 et 12097-12100

```python
response.headers.add('Access-Control-Allow-Origin', '*')
response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
```
Couplé à l'absence partielle de CSRF, expose aux attaques cross-site.

**Remédiation :**
```python
ALLOWED_ORIGINS = [
    'https://app.heliapv.fr',
    'https://heliapv.fr',
    'http://localhost:5000',  # dev seulement
]

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
```

---

## 🟠 ÉLEVÉS — Traiter sous 7 jours

### [ ] H1 — Absence de rate limiting sur les routes d'authentification
**Contrôle ISO 27001 :** A.8.5 (Authentification sécurisée)  
**État :** Mentionné dans la doc / PowerPoint mais **non implémenté** dans le code.

**Remédiation :**
```bash
pip install flask-limiter
```
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day"])

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute; 20 per hour")
def login(): ...

@app.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute; 20 per hour")
def auth_login(): ...
```

---

### [ ] H2 — GEOSERVER_CSRF_DISABLED=true dans Dockerfile
**Contrôle ISO 27001 :** A.8.20 (Sécurité des réseaux)  
**Fichier :** `Dockerfile` ligne 8

```dockerfile
ENV GEOSERVER_CSRF_DISABLED=true
```

**Remédiation :**
```dockerfile
# Supprimer la ligne CSRF_DISABLED et utiliser la whitelist à la place :
ENV GEOSERVER_CSRF_WHITELIST=app.heliapv.fr,heliapv.fr
```

---

### [ ] H3 — Durée de vie des sessions non définie
**Contrôle ISO 27001 :** A.8.5 (Authentification sécurisée)  
**État :** Aucun `PERMANENT_SESSION_LIFETIME` configuré → sessions immortelles.

**Remédiation :**
```python
# Dans agriweb_hebergement_gratuit.py, après la définition de app :
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

@app.before_request
def make_session_permanent():
    session.permanent = True
```

---

### [ ] H4 — Informations système divulguées dans les logs de démarrage
**Contrôle ISO 27001 :** A.8.15 (Journalisation)  
**Fichier :** `geoserver_proxy.py` ligne 43

```python
logger.info(f"[GeoServer] Utilisateur: {GEOSERVER_USER}")
```

**Remédiation :**
```python
logger.info(f"[GeoServer] Utilisateur: {'*' * len(GEOSERVER_USER)}")
```

---

### [ ] H5 — Email personnel hardcodé comme fallback
**Contrôle ISO 27001 :** A.5.17 (Informations d'authentification)  
**Fichiers :** `auth_system_improved.py` L.24, `production_config.py` L.14

```python
'email': os.getenv('SMTP_EMAIL', 'ylaurent.perso@gmail.com'),
```

**Remédiation :** Supprimer le fallback. Si `SMTP_EMAIL` absent → désactiver l'envoi d'email et logger un warning. Ne jamais exposer une adresse personnelle dans le code public.

---

### [ ] H6 — Nombreuses routes API sans authentification
**Contrôle ISO 27001 :** A.8.3 (Restriction des accès)  
**État :** Sur ~50 routes `/api/` analysées, seulement **2 utilisent `@require_auth`**.

Routes exposées sans auth consommant des APIs payantes :
- `/api/lidar/copc-roof` (COPC streaming IGN)
- `/api/solar/building-insights` (Google Solar — coût par requête)
- `/api/solar/dsm-roof` (Google Solar)
- `/api/solar/flux-heatmap` (Google Solar)
- `/api/ai/roof-type`

**Remédiation :** Ajouter `@require_auth` sur toutes les routes qui consomment des APIs payantes ou accèdent aux données CRM.

---

## 🟡 MOYENS — Planifier

### [ ] M1 — Journalisation de sécurité insuffisante
**Contrôle ISO 27001 :** A.8.15 (Journalisation)

```python
# Actuel : uniquement les erreurs
logging.basicConfig(filename='error.log', level=logging.ERROR)
```

Manquent : échecs de connexion, accès refusés, export de données, modifications CRM.

**Remédiation :** Créer un logger de sécurité dédié :
```python
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('security.log')
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
security_logger.addHandler(handler)

# Utilisation
security_logger.warning(f"LOGIN_FAILED | ip={request.remote_addr} | email={email}")
security_logger.info(f"LOGIN_SUCCESS | user={user_id} | ip={request.remote_addr}")
```

---

### [ ] M2 — Constructeurs SQL avec interpolation de chaînes (migrations)
**Contrôle ISO 27001 :** A.8.28 (Codage sécurisé)  
**Fichier :** `database_adapter.py` L.128, `auth_database.py` L.85-86

Les noms de tables/colonnes sont construits avec des f-strings. Bien que issus d'une liste interne, ce pattern est risqué si la source évolue.

**Remédiation :** Valider les noms de tables/colonnes contre une liste blanche (`allowlist`) avant interpolation :
```python
ALLOWED_TABLES = {'agriweb_prospects', 'project_fiches', 'users'}
ALLOWED_COLUMNS = {'user_id', 'siret', 'notes', ...}

def safe_column(name):
    if name not in ALLOWED_COLUMNS:
        raise ValueError(f"Nom de colonne non autorisé : {name}")
    return name
```

---

### [ ] M3 — auth_simple.py : connexion sans mot de passe
**Contrôle ISO 27001 :** A.5.17 (Informations d'authentification)

`auth_simple.py` permet une connexion par email seul, sans mot de passe. Ce module doit être désactivé ou supprimé en production.

---

### [ ] M4 — Pas de politique de backup documentée
**Contrôle ISO 27001 :** A.8.13 (Sauvegarde des informations)

La base SQLite locale `agriweb_users.db` n'a pas de backup automatisé. La base PostgreSQL Railway dépend du plan Railway.

**Remédiation :** Créer un script de backup quotidien + documenter la procédure de restauration.

---

### [ ] M5 — Headers de sécurité HTTP manquants
**Contrôle ISO 27001 :** A.8.20 (Sécurité des réseaux)

Absents : `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.

**Remédiation :**
```bash
pip install flask-talisman
```
```python
from flask_talisman import Talisman
Talisman(app,
    force_https=True,
    strict_transport_security=True,
    frame_options='DENY',
    content_security_policy={
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
        'img-src': ["'self'", "data:", "*.tile.openstreetmap.org", "*.ign.fr"],
    }
)
```

---

## ✅ Points conformes — À maintenir

| # | Contrôle | Détail |
|---|----------|--------|
| 1 | PBKDF2 100 000 iter | `auth_system_improved.py` — hachage robuste avec sel |
| 2 | HTTPS forcé | `force_https()` + ProxyFix Railway configuré correctement |
| 3 | SESSION_COOKIE_HTTPONLY | `True` configuré ligne 628 |
| 4 | SESSION_COOKIE_SECURE | Conditionnel selon variable `COOKIE_SECURE` |
| 5 | Tokens email `secrets.token_hex(32)` | Entropie suffisante (256 bits) |
| 6 | Variables d'env Railway | Stripe & DB URL lus depuis `os.getenv()` |
| 7 | PostgreSQL en production | Séparation SQLite dev / PostgreSQL Railway correcte |
| 8 | Validation email par regex | RFC-compliant dans `auth_system_improved.py` |

---

## Plan de remédiation priorisé

| Priorité | # | Action | Effort estimé |
|----------|---|--------|---------------|
| 🔴 Immédiat | C1 | Révoquer et supprimer les clés hardcodées | 1h |
| 🔴 Immédiat | C2 | `git filter-repo` pour purger l'historique Git | 2h |
| 🔴 Immédiat | C3 | Migrer compte admin vers PBKDF2 | 30min |
| 🔴 J+1 | C4 | Protéger `/debug/auth` ou la supprimer | 15min |
| 🔴 J+1 | C5 | Restreindre CORS aux origines autorisées | 30min |
| 🟠 J+3 | H1 | Flask-Limiter sur `/login` (5 req/min) | 1h |
| 🟠 J+3 | H2 | Désactiver `GEOSERVER_CSRF_DISABLED` | 15min |
| 🟠 J+3 | H3 | `PERMANENT_SESSION_LIFETIME = 8h` | 15min |
| 🟠 J+7 | H4 | Masquer credentials dans les logs | 15min |
| 🟠 J+7 | H5 | Supprimer email perso des fallbacks | 15min |
| 🟠 J+7 | H6 | `@require_auth` sur les routes API payantes | 2h |
| 🟡 J+14 | M1 | Logger sécurité dédié (login fail/success) | 2h |
| 🟡 J+14 | M5 | Flask-Talisman (CSP + sécurity headers) | 1h |
| 🟡 J+30 | M2 | Allowlist pour interpolations SQL | 1h |
| 🟡 J+30 | M3 | Désactiver `auth_simple.py` en production | 30min |
| 🟡 J+30 | M4 | Script de backup PostgreSQL automatisé | 2h |

---

## Checklist de suivi (cocher au fur et à mesure)

```
CRITIQUES
[ ] C1 - Clés hardcodées révoquées + supprimées du code
[ ] C2 - Historique Git purgé (git filter-repo)
[ ] C3 - Compte admin@agriweb.fr migré vers PBKDF2
[ ] C4 - Route /debug/auth protégée ou supprimée
[ ] C5 - CORS restreint aux origines connues

ÉLEVÉS
[ ] H1 - Flask-Limiter installé et configuré sur /login
[ ] H2 - GEOSERVER_CSRF_DISABLED retiré du Dockerfile
[ ] H3 - PERMANENT_SESSION_LIFETIME = 8h configuré
[ ] H4 - Credentials masqués dans les logs de démarrage
[ ] H5 - Email personnel supprimé des fallbacks
[ ] H6 - @require_auth ajouté sur routes API payantes

MOYENS
[ ] M1 - Security logger dédié créé
[ ] M2 - Allowlist SQL pour interpolations dynamiques
[ ] M3 - auth_simple.py désactivé en production
[ ] M4 - Script backup PostgreSQL automatisé
[ ] M5 - Flask-Talisman (headers HTTP sécurité)
```

---

*Rapport généré le 6 mars 2026. À réviser après chaque point traité.*
