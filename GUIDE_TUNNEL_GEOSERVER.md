# 🚀 GUIDE EXPRESS - CONNEXION GEOSERVER LOCAL À AGRIWEB

## 🎯 Objectif
Connecter votre GeoServer local (localhost:8080) à votre AgriWeb hébergé en ligne

## ✅ Prérequis (FAIT !)
- [x] ngrok installé 
- [x] Authtoken configuré: 31UrhBFN9GpDYlr8yORTQkwedNI_29vvhqzAb5naKvH8hRV9d
- [x] GeoServer local fonctionnel sur port 8080

## 🚀 ÉTAPES RAPIDES

### 1. Vérifier GeoServer local
```powershell
# Test rapide
Invoke-WebRequest -Uri "http://localhost:8080/geoserver/web/" -TimeoutSec 5
```

### 2. Démarrer le tunnel ngrok
```powershell
# Ouvrir un nouveau terminal PowerShell et exécuter:
ngrok http 8080
```

### 3. Récupérer l'URL publique
Une fois ngrok démarré, vous verrez quelque chose comme:
```
Forwarding    https://abc123-456-789.ngrok-free.app -> http://localhost:8080
```

### 4. Configurer AgriWeb avec l'URL tunnel
```powershell
# Définir la variable d'environnement (remplacez par votre URL ngrok)
$env:GEOSERVER_TUNNEL_URL = "https://abc123-456-789.ngrok-free.app/geoserver"

# Vérifier la configuration
echo $env:GEOSERVER_TUNNEL_URL
```

### 5. Tester la connexion
```powershell
# Test depuis l'extérieur
Invoke-WebRequest -Uri "$env:GEOSERVER_TUNNEL_URL/web/" -TimeoutSec 10
```

## 🌐 Configuration pour hébergement en ligne

### Railway/Render/Heroku
Ajoutez cette variable d'environnement dans votre plateforme:
```
GEOSERVER_TUNNEL_URL=https://VOTRE-URL-NGROK.ngrok-free.app/geoserver
```

### Redéploiement
Une fois la variable ajoutée, redéployez AgriWeb. Il utilisera automatiquement votre GeoServer local !

## ⚡ Avantages de cette solution
- ✅ GeoServer stable (votre machine locale)
- ✅ Toutes vos données déjà configurées
- ✅ Performances optimales
- ✅ Contrôle total sur la configuration
- ✅ Pas de limitations Railway

## 🔧 Dépannage
- Si ngrok se déconnecte, relancez juste `ngrok http 8080`
- L'URL ngrok peut changer à chaque redémarrage (normal pour compte gratuit)
- Pour une URL fixe, upgrade vers ngrok Pro

## 📊 Test complet
Votre AgriWeb affichera:
```
🌐 Utilisation GeoServer via tunnel: https://votre-url.ngrok-free.app/geoserver
```

C'est tout ! Votre AgriWeb en ligne utilisera maintenant votre GeoServer local stable. 🎉
