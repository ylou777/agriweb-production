# 🌾 AgriWeb 2.0 - Production

**Solution d'analyse agricole géographique professionnelle**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

## 🚀 Déploiement sur Railway

### Déploiement automatique
1. Allez sur [Railway.app](https://railway.app)
2. Créez un nouveau projet
3. Connectez ce repository GitHub: `https://github.com/ylou777/agriweb-production`
4. Railway détectera automatiquement la configuration

### Variables d'environnement requises
Dans Railway, configurez ces variables :

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=false
ENVIRONMENT=production

# GeoServer (optionnel)
GEOSERVER_URL=https://your-geoserver-url
```

## 🛠️ Architecture

- **Framework** : Flask (Python)
- **Hébergement** : Railway (gratuit)
- **Authentification** : Session-based sécurisé
- **Interface** : Responsive HTML/CSS/JS
- **Cartographie** : Intégration GeoServer

## � Fonctionnalités

### ✅ Disponible maintenant
- 🔐 Système d'authentification complet
- 📊 Dashboard utilisateur
- 🆓 Essai gratuit (50 recherches)
- 🌐 Interface responsive moderne
- 🔒 Sécurité par variables d'environnement
- **Utilisation d'API IGN, cadastre, urbanisme (GPU), Sirene**

---

## ▶️ Lancer l'application

```bash
python agriweb_source.py
