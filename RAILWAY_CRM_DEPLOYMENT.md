# 🚀 GUIDE COMPLET : Déployer AgriWeb avec CRM sur Railway

## 📊 État Actuel

✅ **Ce que vous avez** :
- Version Railway existante SANS CRM (dossier `AgriWeb-Railway-Deploy/`)
- Version locale complète AVEC CRM (dossier `AgW3b/`)
- Templates CRM : `crm_web.html`, `crm_calendrier.html` dans `AgW3b/templates/`
- Base SQLite locale : `KPI/kpi_sunstice.db` avec 64 prospects

📋 **Ce que nous allons faire** :
1. Copier les fichiers CRM vers le dossier Railway
2. Mettre à jour le code principal avec les routes CRM
3. Configurer PostgreSQL pour Railway
4. Migrer vos données existantes
5. Déployer sur Railway

---

## 📁 ÉTAPE 1 : Préparation des Fichiers

### 1.1 Copier les Templates CRM

```powershell
# Copier les templates CRM
Copy-Item "AgW3b\templates\crm_web.html" "AgriWeb-Railway-Deploy\templates\"
Copy-Item "AgW3b\templates\crm_calendrier.html" "AgriWeb-Railway-Deploy\templates\"
Copy-Item "AgW3b\templates\crm_projets.html" "AgriWeb-Railway-Deploy\templates\"
```

### 1.2 Vérifier les fichiers nécessaires

Fichiers déjà créés ✅ :
- `database_adapter.py` - Adaptateur SQLite/PostgreSQL
- `migrate_data.py` - Script de migration
- `requirements.txt` - Dépendances mises à jour
- `DEPLOYMENT_GUIDE.md` - Guide détaillé
- `README.md` - Documentation
- `.env.example` - Exemple de configuration

---

## 🔧 ÉTAPE 2 : Extraire les Routes CRM du Fichier Principal

Vous devez copier les routes CRM de `agriweb_hebergement_gratuit.py` vers `agriweb_railway_deploy.py`.

### Routes CRM à copier :

```python
# ROUTES CRM - À ajouter dans agriweb_railway_deploy.py

# 1. Route dashboard CRM principal
@app.route("/crm")
def crm_dashboard():
    # ... (copier tout le contenu de cette fonction)

# 2. Route calendrier
@app.route("/crm/calendrier")
def crm_calendrier():
    # ... (copier tout le contenu)

# 3. Route projets
@app.route("/crm/projets")  
def crm_projets():
    # ... (copier tout le contenu)

# 4. API Routes
@app.route("/api/crm/prospects")
def get_prospects():
    # ... (copier tout le contenu)

@app.route("/api/crm/prospects/<int:prospect_id>", methods=["PUT"])
def update_prospect(prospect_id):
    # ... (copier tout le contenu)

@app.route("/api/crm/prospects/<int:prospect_id>", methods=["DELETE"])
def delete_prospect(prospect_id):
    # ... (copier tout le contenu)

@app.route("/api/crm/appointments")
def get_all_appointments():
    # ... (copier tout le contenu)

@app.route("/api/crm/projets")
def get_projets():
    # ... (copier tout le contenu)

# ... toutes les autres routes /api/crm/*
```

### Comment identifier ces routes :

```powershell
# Chercher toutes les routes CRM dans votre fichier local
cd AgW3b
Select-String -Path "agriweb_hebergement_gratuit.py" -Pattern '@app.route.*crm' -Context 0,20
```

---

## 🗄️ ÉTAPE 3 : Adapter le Code pour PostgreSQL

### 3.1 Remplacer les connexions SQLite directes

**AVANT** (dans votre code local) :
```python
conn = sqlite3.connect(CRM_DB_PATH)
cursor = conn.cursor()
# ... requêtes ...
conn.commit()
conn.close()
```

**APRÈS** (pour Railway) :
```python
from database_adapter import get_db_connection, execute_query

# Pour SELECT
results = execute_query(
    "SELECT * FROM agriweb_prospects WHERE statut = %s", 
    ('nouveau',), 
    fetch_all=True
)

# Pour INSERT/UPDATE/DELETE
execute_query(
    "UPDATE agriweb_prospects SET statut = %s WHERE id = %s",
    ('contacte', prospect_id)
)
```

### 3.2 Différences SQLite vs PostgreSQL

| Fonctionnalité | SQLite | PostgreSQL |
|---|---|---|
| Placeholder | `?` | `%s` |
| AUTOINCREMENT | `AUTOINCREMENT` | `SERIAL` |
| datetime | `TIMESTAMP` | `TIMESTAMP` |
| ILIKE | Non supporté | `ILIKE` (insensible à la casse) |

---

## 🐘 ÉTAPE 4 : Configuration PostgreSQL Railway

### 4.1 Créer la base de données

1. **Aller sur Railway.app**
2. **Ouvrir votre projet AgriWeb**
3. **Cliquer "+ New"** → **Database** → **PostgreSQL**
4. Railway créera automatiquement `DATABASE_URL`

### 4.2 Variables d'environnement Railway

Dans l'onglet **Variables** de votre projet Railway, ajouter :

```bash
# Database (auto-généré par Railway PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:port/dbname  # ✅ Automatique

# Flask
FLASK_SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire-64-caractères-minimum

# Stripe (Production)
STRIPE_SECRET_KEY=sk_live_VOTRE_CLE_SECRETE_STRIPE
STRIPE_PUBLISHABLE_KEY=pk_live_VOTRE_CLE_PUBLIQUE_STRIPE

# GeoServer (optionnel)
GEOSERVER_URL=https://agriweb-prod.ngrok-free.app/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=votre_password

# Application
PORT=5000
FLASK_ENV=production
```

### 4.3 Générer une clé Flask sécurisée

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copier le résultat dans `FLASK_SECRET_KEY`.

---

## 🚢 ÉTAPE 5 : Déploiement sur Railway

### 5.1 Préparer le dépôt Git

```powershell
cd AgriWeb-Railway-Deploy

# Vérifier les fichiers modifiés
git status

# Ajouter tous les nouveaux fichiers CRM
git add .

# Commit avec message descriptif
git commit -m "feat: Add CRM module with PostgreSQL support

- Add CRM dashboard, calendar, and projects views
- Add database adapter for SQLite/PostgreSQL compatibility
- Add migration script for existing data
- Update requirements with Stripe, bcrypt, email-validator
- Add deployment documentation"

# Pousser vers GitHub (Railway détectera automatiquement)
git push origin main
```

### 5.2 Railway détecte et déploie automatiquement

Railway va :
1. ✅ Détecter le push sur `main`
2. ✅ Lire `nixpacks.toml`
3. ✅ Installer les dépendances (`requirements.txt`)
4. ✅ Exécuter `start_railway.py`
5. ✅ Initialiser PostgreSQL via `database_adapter.py`

### 5.3 Surveiller le déploiement

Dans Railway :
- **Onglet "Logs"** : Voir les logs en temps réel
- Chercher :
  ```
  🐘 [DATABASE] Mode PostgreSQL détecté
  📊 [DATABASE] Tables CRM initialisées avec succès!
  🚀 Démarrage AgriWeb sur 127.0.0.1:5000
  ```

---

## 📊 ÉTAPE 6 : Migrer les Données Existantes

### 6.1 Préparer la base SQLite locale

```powershell
# Vérifier le nombre de prospects
cd KPI
sqlite3 kpi_sunstice.db "SELECT COUNT(*) FROM agriweb_prospects;"
# Résultat attendu: 64

# Exporter pour backup
sqlite3 kpi_sunstice.db ".dump agriweb_prospects" > backup_prospects.sql
```

### 6.2 Option A : Migration via Railway Shell

```bash
# Dans Railway : Onglet "Shell"
python migrate_data.py

# Résultat attendu :
# 🔄 MIGRATION SQLite → PostgreSQL
# ==================================================
# 📊 Migration depuis SQLite : ../KPI/kpi_sunstice.db
# 📈 64 prospects à migrer
#    Migré : 10/64
#    Migré : 20/64
#    ...
# ✅ Migration terminée !
#    ✓ Migrés : 64
#    ✗ Erreurs : 0
```

### 6.3 Option B : Migration via Railway CLI

```powershell
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login

# Lier au projet
railway link

# Migrer
railway run python migrate_data.py
```

---

## ✅ ÉTAPE 7 : Vérification Post-Déploiement

### 7.1 Tester les endpoints

```powershell
# Health check
curl https://votre-app.railway.app/health

# CRM Dashboard
curl https://votre-app.railway.app/crm

# API Prospects (devrait retourner JSON avec 64 prospects)
curl https://votre-app.railway.app/api/crm/prospects

# Calendrier
curl https://votre-app.railway.app/crm/calendrier
```

### 7.2 Vérifier dans le navigateur

1. **Page d'accueil** : `https://votre-app.railway.app/`
2. **CRM** : `https://votre-app.railway.app/crm`
   - ✅ Doit afficher 64 prospects
   - ✅ Boutons "Éditer" fonctionnels
   - ✅ Champs dirigeant (nom, SIRET, email, tél)
   - ✅ Lien Société.com visible si SIRET renseigné

3. **Calendrier** : `https://votre-app.railway.app/crm/calendrier`
   - ✅ FullCalendar affiché
   - ✅ Événements chargés
   - ✅ Bouton "Y aller" (Google Maps)

### 7.3 Vérifier les logs Railway

```
✅ [DATABASE] Tables CRM initialisées
✅ Base de données d'authentification initialisée
✅ Système d'authentification commercial initialisé
✅ Stripe configuré
🚀 Démarrage AgriWeb sur 127.0.0.1:5000
```

---

## 🐛 Dépannage

### Problème : "Module not found: database_adapter"

**Cause** : Fichier `database_adapter.py` manquant

**Solution** :
```powershell
# Vérifier que le fichier existe
ls AgriWeb-Railway-Deploy\database_adapter.py

# Si manquant, le recréer
# (utilisez le contenu fourni précédemment)
```

### Problème : "No DATABASE_URL found"

**Cause** : PostgreSQL non ajouté à Railway

**Solution** :
1. Railway Dashboard → Votre projet
2. "+ New" → Database → PostgreSQL
3. Attendre création (1-2 minutes)
4. Redéployer

### Problème : "Table does not exist"

**Cause** : `database_adapter.init_database()` pas exécuté

**Solution** :
```bash
# Dans Railway Shell
python database_adapter.py
```

### Problème : "UnicodeEncodeError"

**Cause** : Emojis dans print() (Windows)

**Solution** : Remplacer tous les print() avec emojis par du texte simple
```python
# AVANT
print("✅ Stripe configuré")

# APRÈS  
print("[OK] Stripe configuré")
```

---

## 📈 Prochaines Étapes

### Optimisations recommandées

1. **Backup automatique PostgreSQL** :
   ```bash
   railway run pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```

2. **Nom de domaine personnalisé** :
   - Railway Settings → Domains
   - Ajouter votre domaine (ex: `crm.agriweb.fr`)

3. **Monitoring** :
   - Ajouter Sentry pour le tracking d'erreurs
   - Configurer des alertes Railway

4. **CI/CD avancé** :
   - Tests automatiques avant déploiement
   - Environnements staging/production séparés

---

## 📚 Ressources

- [Documentation Railway](https://docs.railway.app)
- [PostgreSQL vs SQLite](https://www.sqlite.org/whentouse.html)
- [Flask avec PostgreSQL](https://flask.palletsprojects.com/en/2.3.x/)
- [Stripe Documentation](https://stripe.com/docs)

---

## ✨ Résumé - Checklist Complète

- [ ] Templates CRM copiés vers `AgriWeb-Railway-Deploy/templates/`
- [ ] Routes CRM ajoutées dans `agriweb_railway_deploy.py`
- [ ] Code adapté pour PostgreSQL (remplacer `sqlite3.connect()`)
- [ ] PostgreSQL ajouté sur Railway
- [ ] Variables d'environnement configurées (STRIPE, FLASK_SECRET_KEY)
- [ ] Code poussé sur GitHub (`git push`)
- [ ] Déploiement Railway réussi (logs OK)
- [ ] Tables CRM créées (`database_adapter.py`)
- [ ] Données migrées (64 prospects → PostgreSQL)
- [ ] Tests endpoints (/crm, /api/crm/prospects, /crm/calendrier)
- [ ] Vérification navigateur (dashboard, édition, calendrier)

---

🎉 **Votre AgriWeb avec CRM sera déployé sur Railway avec PostgreSQL !**

Pour toute question, consultez `DEPLOYMENT_GUIDE.md` ou les logs Railway.
