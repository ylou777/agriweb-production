# 🚀 GUIDE RAPIDE - CONNEXION GEOSERVER LOCAL

## ✅ Situation actuelle
- [x] ngrok installé et configuré avec authtoken
- [x] Scripts de tunnel créés
- [ ] GeoServer local démarré
- [ ] Tunnel ngrok actif

## 🎯 OPTION 1: Script PowerShell Simple (Recommandé)

```powershell
# 1. Assurez-vous que GeoServer est démarré sur port 8080
# 2. Exécutez le script PowerShell:
.\start_tunnel_simple.ps1

# Pour arrêter le tunnel:
.\start_tunnel_simple.ps1 -Stop
```

## 🎯 OPTION 2: Script Python Complet

```bash
# Lancer le script Python et choisir option 1:
python tunnel_geoserver_complete.py
# Puis entrer: 1
```

## 🎯 OPTION 3: Commandes manuelles

```powershell
# 1. Vérifier GeoServer local
Invoke-WebRequest -Uri "http://localhost:8080/geoserver/web/" -TimeoutSec 5

# 2. Démarrer ngrok (dans un terminal séparé)
cd C:\ngrok\
.\ngrok.exe http 8080

# 3. Récupérer l'URL publique (exemple: https://abc123.ngrok-free.app)
# 4. Configurer AgriWeb avec:
$env:GEOSERVER_TUNNEL_URL = "https://VOTRE-URL.ngrok-free.app/geoserver"
```

## 📋 Étapes suivantes après tunnel actif

1. **Copier l'URL tunnel** (ex: https://abc123.ngrok-free.app/geoserver)

2. **Configurer votre plateforme d'hébergement** :
   - Railway: Ajouter variable `GEOSERVER_TUNNEL_URL`
   - Render: Ajouter variable `GEOSERVER_TUNNEL_URL`
   - Heroku: `heroku config:set GEOSERVER_TUNNEL_URL=https://...`

3. **Redéployer AgriWeb** - Il utilisera automatiquement votre GeoServer local !

## 🔧 Dépannage rapide

**GeoServer local non accessible ?**
```powershell
# Vérifier les processus Java (GeoServer)
Get-Process -Name java -ErrorAction SilentlyContinue
```

**ngrok ne démarre pas ?**
```powershell
# Vérifier la version
C:\ngrok\ngrok.exe version

# Vérifier l'authtoken
C:\ngrok\ngrok.exe config check
```

**Tunnel déconnecté ?**
- Normal avec compte gratuit ngrok
- Relancez simplement le script
- L'URL changera (comportement normal)

## ⭐ RECOMMANDATION

Utilisez le **script PowerShell simple** pour commencer :
```powershell
.\start_tunnel_simple.ps1
```

Il automatise tout le processus ! 🎉
