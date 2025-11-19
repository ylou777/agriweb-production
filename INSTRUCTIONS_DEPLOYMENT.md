# 🚀 CONFIGURATION FINALE AGRIWEB + TUNNEL

## ✅ TUNNEL ACTIF
URL GeoServer: https://3de153b73a2d.ngrok-free.app/geoserver

## 🔧 CONFIGURATION PLATEFORME

### Variable d'environnement à ajouter :
```
GEOSERVER_TUNNEL_URL=https://3de153b73a2d.ngrok-free.app/geoserver
```

### ⚙️ Instructions par plateforme :

#### 🚂 Railway
1. Allez sur railway.app
2. Sélectionnez votre projet AgriWeb
3. Onglet "Variables"
4. Ajoutez : `GEOSERVER_TUNNEL_URL` = `https://3de153b73a2d.ngrok-free.app/geoserver`
5. Redéployez

#### 🎨 Render
1. Allez sur render.com
2. Sélectionnez votre service AgriWeb
3. Onglet "Environment"
4. Ajoutez : `GEOSERVER_TUNNEL_URL` = `https://3de153b73a2d.ngrok-free.app/geoserver`
5. Redéployez

#### 💜 Heroku
1. Allez sur heroku.com
2. Sélectionnez votre app AgriWeb
3. Onglet "Settings" → "Config Vars"
4. Ajoutez : `GEOSERVER_TUNNEL_URL` = `https://3de153b73a2d.ngrok-free.app/geoserver`
5. L'app redémarre automatiquement

## 🔍 VÉRIFICATION

Une fois redéployé, votre AgriWeb utilisera automatiquement votre GeoServer local via le tunnel !

Le fichier `agriweb_hebergement_gratuit.py` contient déjà la logique :
```python
# Priorité: TUNNEL > PRODUCTION > LOCAL
if Config.GEOSERVER_TUNNEL:
    return Config.GEOSERVER_TUNNEL  # ← Utilisé en priorité !
```

## ⚠️ IMPORTANT
- Gardez le terminal ngrok ouvert
- URL tunnel change à chaque redémarrage ngrok (gratuit)
- Pour URL fixe : ngrok plan payant

## 🎉 AVANTAGES OBTENUS
✅ GeoServer stable (votre machine)
✅ Toutes vos données disponibles
✅ Pas de limitations Railway
✅ Contrôle total
✅ Performances optimales

---
**🚀 PRÊT POUR LE DÉPLOIEMENT !**
