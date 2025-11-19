# Guide de Migration GeoServer vers Hébergement Indépendant

## 🎯 Objectif
Migrer votre GeoServer depuis `localhost:8080` vers un hébergement cloud indépendant pour permettre l'accès depuis n'importe où.

## 🔍 Options d'Hébergement

### 1. Railway (Recommandé) ⭐
- **Coût**: 5$/mois après 500h gratuites
- **Avantages**: Simple, rapide, PostgreSQL inclus
- **Inconvénients**: Pas de plan gratuit permanent

### 2. Render
- **Coût**: Gratuit (avec limitations)
- **Avantages**: Plan gratuit permanent
- **Inconvénients**: Plus lent, moins de ressources

### 3. VPS (Hetzner, DigitalOcean)
- **Coût**: 5-10$/mois
- **Avantages**: Contrôle total, performance
- **Inconvénients**: Configuration manuelle requise

## 🚀 Migration via Railway (Méthode Recommandée)

### Prérequis
```powershell
# Installation Railway CLI
npm install -g @railway/cli

# Vérification Docker
docker --version
```

### Étape 1: Déploiement Automatique
```powershell
# Exécution du script complet
.\deploy_complete.ps1
```

### Étape 2: Déploiement Manuel (Alternative)

#### 2.1 Connexion Railway
```powershell
railway login
```

#### 2.2 Création du projet
```powershell
railway project create geoserver-agriweb
```

#### 2.3 Déploiement GeoServer
```powershell
railway up --dockerfile Dockerfile.geoserver
```

#### 2.4 Configuration des variables
```powershell
railway variables set GEOSERVER_ADMIN_USER=admin
railway variables set GEOSERVER_ADMIN_PASSWORD=admin123
railway variables set JAVA_OPTS="-Xms512m -Xmx1024m"
```

### Étape 3: Migration des Données

#### 3.1 Export depuis le GeoServer local
```powershell
# Script automatique
python migrate_geoserver.py
```

#### 3.2 Export manuel (alternative)
1. Accédez à `http://localhost:8080/geoserver`
2. Connectez-vous (admin/admin)
3. Allez dans **Data > Workspaces**
4. Exportez chaque workspace en ZIP

#### 3.3 Import vers le GeoServer distant
1. Accédez à votre nouveau GeoServer Railway
2. Connectez-vous avec les mêmes identifiants
3. Importez les workspaces exportés

### Étape 4: Mise à Jour de l'Application

#### 4.1 Mise à jour automatique des URLs
```powershell
# Script qui met à jour tous les fichiers
python update_geoserver_urls.py
```

#### 4.2 Mise à jour manuelle (config.py)
```python
def get_geoserver_url():
    if os.getenv('ENVIRONMENT') == 'production':
        return "https://votre-app.up.railway.app/geoserver"
    return "http://localhost:8080/geoserver"
```

## 🛠️ Configuration Avancée

### Variables d'Environnement
```bash
# Production
GEOSERVER_URL=https://geoserver-agriweb.up.railway.app/geoserver
ENVIRONMENT=production
FLASK_ENV=production

# Développement  
GEOSERVER_URL=http://localhost:8080/geoserver
ENVIRONMENT=development
FLASK_ENV=development
```

### Fichier .env
```bash
# Créé automatiquement par update_geoserver_urls.py
GEOSERVER_URL=https://votre-geoserver.up.railway.app/geoserver
GEOSERVER_LOCAL_URL=http://localhost:8080/geoserver
ENVIRONMENT=production
```

## 🔧 Dépannage

### Problème: GeoServer ne démarre pas
```bash
# Vérification des logs Railway
railway logs

# Vérification locale
docker run -p 8080:8080 kartoza/geoserver:2.24.0
```

### Problème: Application ne trouve pas GeoServer
1. Vérifiez l'URL dans la configuration
2. Testez l'accès direct au GeoServer
3. Vérifiez les variables d'environnement

### Problème: Données manquantes
1. Relancez la migration avec `migrate_geoserver.py`
2. Vérifiez que le GeoServer local est accessible
3. Importez manuellement via l'interface web

## 📊 Coûts Estimés

| Service | Plan Gratuit | Plan Payant | Recommandation |
|---------|-------------|-------------|----------------|
| Railway | 500h/mois | 5$/mois | ⭐ Optimal |
| Render | Limité | 7$/mois | 💡 Budget |
| Hetzner VPS | - | 5€/mois | 🔧 Avancé |
| DigitalOcean | - | 5$/mois | 🔧 Avancé |

## ✅ Checklist de Migration

- [ ] Installation des outils (Railway CLI, Docker)
- [ ] Déploiement GeoServer sur Railway
- [ ] Configuration des variables d'environnement
- [ ] Migration des données (workspaces, couches)
- [ ] Mise à jour des URLs dans l'application
- [ ] Test de l'application avec le nouveau GeoServer
- [ ] Configuration du domaine personnalisé (optionnel)
- [ ] Sauvegarde de la configuration

## 🎉 Résultat Final

Après migration, vous aurez :
- **GeoServer accessible 24/7** depuis n'importe où
- **URL permanente** (ex: `https://geoserver-agriweb.up.railway.app/geoserver`)
- **Application indépendante** du poste local
- **Basculement automatique** entre environnements local/production

## 📞 Support

En cas de problème :
1. Consultez les logs Railway : `railway logs`
2. Vérifiez la documentation : [docs.railway.app](https://docs.railway.app)
3. Testez d'abord en local avec Docker
