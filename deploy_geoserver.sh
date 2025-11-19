#!/bin/bash
# Script de déploiement GeoServer sur Railway

echo "🚀 Déploiement GeoServer sur Railway..."

# 1. Initialisation du projet Railway
echo "📦 Création du projet Railway..."
railway login
railway new geoserver-agriweb --template docker

# 2. Configuration des variables d'environnement
echo "⚙️ Configuration des variables..."
railway variables set GEOSERVER_ADMIN_PASSWORD=admin123
railway variables set GEOSERVER_ADMIN_USER=admin
railway variables set INITIAL_MEMORY=512M
railway variables set MAXIMUM_MEMORY=1024M
railway variables set ENVIRONMENT=production

# 3. Ajout du service PostgreSQL
echo "🐘 Ajout de PostgreSQL..."
railway add postgresql

# 4. Déploiement
echo "🚀 Déploiement en cours..."
railway up

echo "✅ Déploiement terminé !"
echo "🌐 Votre GeoServer sera disponible sur l'URL fournie par Railway"
echo "📊 Consultez les logs : railway logs"
