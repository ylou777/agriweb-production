#!/bin/bash
# Script de déploiement GeoServer sur Railway

echo "🚂 DÉPLOIEMENT GEOSERVER SUR RAILWAY"
echo "====================================="

# 1. Créer nouveau projet Railway
echo "1️⃣ Création du projet GeoServer..."
railway new geoserver-production
cd geoserver-production

# 2. Copier le Dockerfile
echo "2️⃣ Configuration Dockerfile..."
cp ../Dockerfile.geoserver-railway ./Dockerfile

# 3. Variables d'environnement Railway
echo "3️⃣ Configuration des variables..."
railway variables set GEOSERVER_ADMIN_USER=admin
railway variables set GEOSERVER_ADMIN_PASSWORD=VotreMotDePasseAdmin2024
railway variables set GEOSERVER_USERS=railway_user:VotreMotDePasseUser2024

# 4. Déploiement
echo "4️⃣ Déploiement en cours..."
railway up

# 5. Récupérer l'URL
echo "5️⃣ Récupération de l'URL..."
railway status

echo ""
echo "✅ GeoServer déployé sur Railway !"
echo "📝 Notez l'URL affichée par 'railway status'"
echo "🔧 Configurez ensuite votre app AgriWeb avec cette URL"
