# 🔧 DÉBOGAGE DÉPLOIEMENT RAILWAY - GUIDE MANUEL

## 🚨 Problème identifié et corrigé

### ❌ Erreur précédente :
```
The executable `/opt/geoserver_startup.sh` could not be found.
```

### ✅ Solution appliquée :
- Dockerfile corrigé pour supprimer le script personnalisé défaillant
- Utilisation du script de démarrage natif de kartoza/geoserver
- Nouveau déploiement lancé

## 🔍 VÉRIFICATIONS À EFFECTUER

### 1. Vérifier le statut Railway
```bash
railway status
```

### 2. Consulter les logs du nouveau déploiement
```bash
railway logs
```

### 3. Tester la connectivité
```bash
# Avec curl
curl -I https://geoserver-agriweb-production.up.railway.app/geoserver

# Avec PowerShell
Invoke-WebRequest -Uri "https://geoserver-agriweb-production.up.railway.app/geoserver" -Method GET

# Avec Python
python test_railway_simple.py
```

### 4. Ouvrir dans le navigateur
```
https://geoserver-agriweb-production.up.railway.app/geoserver
```

## 📊 Messages attendus

### ✅ Si le déploiement réussit :
- **Status 200** : GeoServer accessible
- **Interface de connexion** : Page de login GeoServer
- **admin / admin123** : Identifiants fonctionnels

### ⏳ Si encore en cours :
- **Status 404** : Service en cours de démarrage
- **"Train has not arrived"** : Déploiement en cours
- **Timeout** : Service encore en build

### ❌ Si échec persistant :
- **Status 500** : Erreur interne
- **Build failed** : Problème Dockerfile

## 🛠️ Actions de dépannage

### Si le problème persiste :

1. **Redéployer avec Dockerfile minimal**
   ```bash
   # Copier le Dockerfile minimal
   Copy-Item Dockerfile.minimal Dockerfile
   railway up
   ```

2. **Vérifier les variables d'environnement**
   ```bash
   railway variables
   ```

3. **Consulter le dashboard**
   ```bash
   railway open
   ```

## 📋 Dockerfile corrigé utilisé

```dockerfile
# Dockerfile minimal pour GeoServer Railway
FROM kartoza/geoserver:2.24.0

# Variables d'environnement Railway
ENV GEOSERVER_ADMIN_PASSWORD=admin123
ENV GEOSERVER_ADMIN_USER=admin

# Configuration mémoire optimisée pour Railway
ENV INITIAL_MEMORY=512M
ENV MAXIMUM_MEMORY=1024M

# Port standard GeoServer
EXPOSE 8080
```

## ⏰ Temps d'attente

- **Build Docker** : 1-2 minutes
- **Démarrage GeoServer** : 2-3 minutes
- **Total** : 3-5 minutes maximum

## 🎯 Prochaines étapes

Une fois GeoServer accessible :

1. **✅ Vérifier l'accès** : https://geoserver-agriweb-production.up.railway.app/geoserver
2. **🔐 Se connecter** : admin / admin123
3. **📦 Migrer les données** : `python migrate_geoserver_data.py`
4. **🚀 Passer en production** : `.\test_geoserver_final.ps1 -Production`

## 🌐 URLs importantes

- **GeoServer** : https://geoserver-agriweb-production.up.railway.app/geoserver
- **Dashboard** : https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475
- **Logs** : Voir le lien dans le build output

---

**Status** : 🔄 Nouveau déploiement en cours avec Dockerfile corrigé
