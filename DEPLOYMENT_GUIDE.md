# 🚀 Guide de Déploiement AgriWeb CRM sur Railway

## 📋 Prérequis

1. **Compte Railway** : https://railway.app
2. **Clés Stripe** (mode production)
3. **Repository GitHub** connecté à Railway

## 🔧 Étapes de Déploiement

### 1. Créer le Projet Railway

1. Aller sur Railway.app
2. Cliquer sur "New Project"
3. Choisir "Deploy from GitHub repo"
4. Sélectionner votre repository `agriweb-production`

### 2. Ajouter PostgreSQL

1. Dans votre projet Railway, cliquer sur "+ New"
2. Choisir "Database" → "PostgreSQL"
3. Railway créera automatiquement la variable `DATABASE_URL`

### 3. Configurer les Variables d'Environnement

Dans Railway, aller dans l'onglet "Variables" et ajouter :

```bash
# Flask Configuration
FLASK_SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire

# Stripe (Production Keys)
STRIPE_SECRET_KEY=sk_live_VOTRE_CLE_SECRETE
STRIPE_PUBLISHABLE_KEY=pk_live_VOTRE_CLE_PUBLIQUE

# GeoServer (optionnel)
GEOSERVER_URL=https://votre-geoserver-url/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=votre_password

# Application
PORT=5000
FLASK_ENV=production
```

### 4. Configuration des Fichiers

Railway utilise automatiquement :
- `nixpacks.toml` pour la configuration build
- `Procfile` pour la commande de démarrage
- `requirements.txt` pour les dépendances Python

### 5. Déploiement

1. Pousser vos changements sur GitHub :
```bash
git add .
git commit -m "Add CRM features for Railway deployment"
git push origin main
```

2. Railway détectera automatiquement les changements et déploiera

### 6. Initialiser la Base de Données

Après le premier déploiement :

1. Ouvrir le terminal Railway (onglet "Shell")
2. Exécuter :
```bash
python database_adapter.py
```

Cela créera toutes les tables CRM dans PostgreSQL.

## 🧪 Vérification Post-Déploiement

### Tester l'Application

1. **Page d'accueil** : `https://votre-app.railway.app/`
2. **CRM Dashboard** : `https://votre-app.railway.app/crm`
3. **Calendrier** : `https://votre-app.railway.app/crm/calendrier`
4. **Health Check** : `https://votre-app.railway.app/health`

### Vérifier les Logs

Dans Railway, aller dans l'onglet "Logs" pour voir :
- ✅ Connexion PostgreSQL réussie
- ✅ Tables CRM initialisées
- ✅ Stripe configuré
- ✅ Application démarrée sur port 5000

## 🔐 Sécurité

### Clés Stripe en Production

⚠️ **Important** : Utilisez uniquement les clés Stripe **LIVE** (commençant par `sk_live_` et `pk_live_`)

Pour obtenir vos clés :
1. Aller sur https://dashboard.stripe.com
2. Développeurs → Clés API
3. Copier "Clé secrète" et "Clé publiable" (mode Production)

### Secret Key Flask

Générer une clé secrète forte :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 📊 Migration des Données Existantes

Si vous avez déjà des prospects dans votre base SQLite locale :

### Option 1 : Export/Import SQL

1. **Exporter depuis SQLite** :
```bash
sqlite3 KPI/kpi_sunstice.db .dump > backup.sql
```

2. **Convertir et importer** (nécessite adaptation du format SQLite → PostgreSQL)

### Option 2 : Script Python de Migration

Créer un script qui lit SQLite et écrit dans PostgreSQL :
```python
# migration_script.py
from database_adapter import get_db_connection
import sqlite3

# Lire depuis SQLite local
local_db = sqlite3.connect('KPI/kpi_sunstice.db')
prospects = local_db.execute('SELECT * FROM agriweb_prospects').fetchall()

# Écrire vers PostgreSQL Railway
with get_db_connection() as conn:
    cursor = conn.cursor()
    for prospect in prospects:
        # Insérer chaque prospect
        cursor.execute("INSERT INTO agriweb_prospects (...) VALUES (...)", prospect)
    conn.commit()
```

## 🐛 Dépannage

### L'application ne démarre pas

- Vérifier les logs Railway
- S'assurer que `DATABASE_URL` est bien définie
- Vérifier que toutes les dépendances sont dans `requirements.txt`

### Erreur de connexion PostgreSQL

- Vérifier que la base PostgreSQL est bien créée dans Railway
- Vérifier que `DATABASE_URL` commence par `postgresql://`

### Erreur Stripe

- Vérifier que `STRIPE_SECRET_KEY` est définie
- S'assurer d'utiliser les clés LIVE en production

## 📈 Prochaines Étapes

1. **Configurer un nom de domaine personnalisé** dans Railway
2. **Activer les backups automatiques** de PostgreSQL
3. **Configurer les notifications par email**
4. **Ajouter un système de logs centralisé**

## 💡 Commandes Utiles

### Redéployer
```bash
git push origin main
```

### Voir les logs en temps réel
Dans Railway : Onglet "Logs" → Mode "Live"

### Accéder au shell
Dans Railway : Onglet "Shell" → Ouvrir terminal

### Backup PostgreSQL
```bash
# Dans le terminal Railway
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

## 🆘 Support

- Documentation Railway : https://docs.railway.app
- Documentation Stripe : https://stripe.com/docs
- Issues GitHub : Créer une issue dans votre repository
