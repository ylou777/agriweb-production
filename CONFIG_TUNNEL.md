# 🎯 CONFIGURATION AGRIWEB - TUNNEL GEOSERVER

## 📋 Variable d'environnement à ajouter

Ajoutez cette variable dans votre plateforme d'hébergement :

```
GEOSERVER_TUNNEL_URL=https://3de153b73a2d.ngrok-free.app/geoserver
```

## 🌐 URLs disponibles

- **Interface GeoServer :** https://3de153b73a2d.ngrok-free.app/geoserver
- **Interface Web :** https://3de153b73a2d.ngrok-free.app/geoserver/web/
- **API REST :** https://3de153b73a2d.ngrok-free.app/geoserver/rest/
- **WMS :** https://3de153b73a2d.ngrok-free.app/geoserver/wms
- **WFS :** https://3de153b73a2d.ngrok-free.app/geoserver/wfs

## ⚙️ Configuration automatique

L'AgriWeb va automatiquement :
1. ✅ Détecter `GEOSERVER_TUNNEL_URL` 
2. ✅ Utiliser cette URL comme priorité
3. ✅ Se connecter à votre GeoServer local

## 🔄 Étapes de déploiement

1. **Ajoutez** la variable `GEOSERVER_TUNNEL_URL`
2. **Redéployez** votre AgriWeb
3. **Testez** → AgriWeb utilise votre GeoServer local !

## 📊 Statut du tunnel

- ✅ **Tunnel actif :** https://3de153b73a2d.ngrok-free.app
- ✅ **GeoServer local :** localhost:8080 (accessible)
- ✅ **Configuration :** Prêt pour déploiement

## ⚠️ Important
- Gardez le terminal avec ngrok ouvert
- URL ngrok change à chaque redémarrage (plan gratuit)
- Pour URL fixe : ngrok plan payant ($5/mois)

---
**🚀 PRÊT POUR LE DÉPLOIEMENT !**
