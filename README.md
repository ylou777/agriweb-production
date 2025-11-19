# AgriWeb CRM - Déploiement Railway 🚀

Application complète AgriWeb avec système CRM intégré, déployée sur Railway avec PostgreSQL.

## 🎯 Fonctionnalités

### Module Cartographique
- ✅ Recherche par adresse, commune, département
- ✅ Analyse parcelles RPG, parkings, friches, toitures
- ✅ Calcul distances postes BT/HTA
- ✅ API GeoServer pour couches cartographiques
- ✅ Export cartes et rapports PDF

### Module CRM (Nouveau)
- ✅ Gestion prospects avec 64+ champs
- ✅ Calendrier des rendez-vous (FullCalendar.js)
- ✅ Suivi projets avec étapes et documents
- ✅ Intégration Pages Blanches et Société.com
- ✅ Recherche SIRET entreprises
- ✅ Informations dirigeant (nom, email, tél, SIRET)
- ✅ Statistiques et tableaux de bord

### Module Paiement
- ✅ Intégration Stripe (abonnements)
- ✅ Système d'essai gratuit
- ✅ Gestion utilisateurs et sessions

## 📦 Architecture Technique

```
AgriWeb-Railway-Deploy/
├── agriweb_railway_deploy.py   # Application Flask principale
├── start_railway.py             # Point d'entrée Railway
├── database_adapter.py          # Adaptateur SQLite/PostgreSQL
├── migrate_data.py              # Migration données
├── requirements.txt             # Dépendances Python
├── nixpacks.toml               # Configuration build Railway
├── Procfile                    # Commande démarrage
├── .env.example                # Variables d'environnement
├── DEPLOYMENT_GUIDE.md         # Guide détaillé
├── templates/                  # Templates HTML
│   ├── crm_web.html           # Interface CRM
│   ├── crm_calendrier.html    # Calendrier
│   └── ...
├── static/                     # Assets statiques
└── modules/                    # Modules métier
```

## 🚀 Déploiement Rapide

### 1. Prérequis
- Compte Railway (gratuit) : https://railway.app
- Clés Stripe : https://dashboard.stripe.com/apikeys
- Repository GitHub

### 2. Configuration Railway

**Créer le projet :**
```bash
# Via Railway CLI
railway init
railway add postgresql

# Ou via interface web
# 1. New Project → Deploy from GitHub
# 2. Add Service → PostgreSQL
```

**Variables d'environnement :**
```bash
# Dans Railway Dashboard → Variables
DATABASE_URL=postgresql://...  # Auto-généré par Railway
FLASK_SECRET_KEY=votre-clé-secrète-aléatoire
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
PORT=5000
FLASK_ENV=production
```

### 3. Déployer

```bash
git add .
git commit -m "Deploy AgriWeb CRM to Railway"
git push origin main
```

Railway déploiera automatiquement !

### 4. Initialiser la BDD

Après le premier déploiement, dans le Shell Railway :
```bash
python database_adapter.py
```

## 📊 Migration Données Existantes

Si vous avez déjà des prospects en local (SQLite) :

```bash
# Depuis Railway Shell
python migrate_data.py
```

Ou en local avec Railway CLI :
```bash
railway run python migrate_data.py /path/to/kpi_sunstice.db
```

## 🔧 Configuration

### Clés Stripe

⚠️ **Production uniquement** - Utilisez les clés LIVE :

1. Dashboard Stripe → Développeurs → Clés API
2. Copier "Clé secrète" (`sk_live_...`)
3. Copier "Clé publiable" (`pk_live_...`)
4. Ajouter dans Railway Variables

### Secret Key Flask

Générer une clé sécurisée :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### GeoServer (Optionnel)

Si vous utilisez GeoServer :
```bash
GEOSERVER_URL=https://your-geoserver.com/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=your_password
```

## 🧪 Tests

**Health Check :**
```bash
curl https://votre-app.railway.app/health
```

**Endpoints CRM :**
- `/crm` - Dashboard CRM
- `/crm/calendrier` - Calendrier rendez-vous
- `/crm/projets` - Gestion projets
- `/api/crm/prospects` - API prospects (JSON)

**Endpoints Carto :**
- `/` - Page d'accueil
- `/demo` - Démo interactive
- `/search_by_commune` - Recherche commune
- `/rapport_departement` - Rapport département

## 📖 Documentation

- [Guide de Déploiement Complet](./DEPLOYMENT_GUIDE.md)
- [Variables d'Environnement](./.env.example)
- [Migration de Données](./migrate_data.py)

## 🐛 Dépannage

**Application ne démarre pas :**
```bash
# Vérifier les logs Railway
railway logs

# Vérifier les variables
railway variables
```

**Erreur Database :**
```bash
# Vérifier la connexion PostgreSQL
railway run python -c "from database_adapter import get_db_connection; print('✅ DB OK')"
```

**Erreur Stripe :**
- Vérifier que les clés commencent par `sk_live_` et `pk_live_`
- S'assurer qu'elles sont bien définies dans Railway Variables

## 📈 Performance

- **Cold Start** : ~5-10s (Railway Hobby plan)
- **Response Time** : <200ms moyenne
- **Database** : PostgreSQL avec connexion pooling
- **Static Files** : Servies via Flask (considérer CDN pour prod)

## 🔒 Sécurité

- ✅ HTTPS automatique (Railway)
- ✅ Clés API en variables d'environnement
- ✅ Mots de passe hashés (bcrypt)
- ✅ JWT pour authentification
- ✅ CORS configuré
- ✅ Rate limiting activé

## 💰 Coûts Railway

- **Hobby Plan** : $5/mois (500h)
- **PostgreSQL** : Inclus (1GB)
- **Bandwidth** : 100GB/mois inclus

## 🆘 Support

- Railway Docs : https://docs.railway.app
- Stripe Docs : https://stripe.com/docs
- Issues : Créer une issue GitHub

## 📝 Changelog

### v2.0.0 - CRM Complet (Nov 2025)
- ✨ Système CRM web complet
- ✨ Calendrier rendez-vous FullCalendar
- ✨ Gestion dirigeants + SIRET
- ✨ Support PostgreSQL
- ✨ Migration SQLite → PostgreSQL
- 🔧 Adaptateur base de données dynamique

### v1.0.0 - Version Initiale
- ✅ Module cartographique AgriWeb
- ✅ Recherche parcelles et toitures
- ✅ Intégration Stripe
- ✅ Système authentification

---

Made with ❤️ for AgriWeb
