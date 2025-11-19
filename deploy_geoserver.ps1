# Script PowerShell pour déployer GeoServer sur Railway
Write-Host "🚀 Déploiement GeoServer sur Railway..." -ForegroundColor Green

# Vérification de Railway CLI
if (-not (Get-Command "railway" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Railway CLI non trouvé. Installation..." -ForegroundColor Red
    Write-Host "📥 Installez Railway CLI depuis : https://railway.app/cli" -ForegroundColor Yellow
    Write-Host "🔧 Ou via npm : npm install -g @railway/cli" -ForegroundColor Yellow
    exit 1
}

# 1. Connexion à Railway
Write-Host "🔐 Connexion à Railway..." -ForegroundColor Blue
railway login

# 2. Création du projet
Write-Host "📦 Création du projet GeoServer..." -ForegroundColor Blue
railway new geoserver-agriweb

# 3. Configuration des variables d'environnement
Write-Host "⚙️ Configuration des variables d'environnement..." -ForegroundColor Blue
railway variables set GEOSERVER_ADMIN_PASSWORD=admin123
railway variables set GEOSERVER_ADMIN_USER=admin
railway variables set INITIAL_MEMORY=512M
railway variables set MAXIMUM_MEMORY=1024M
railway variables set ENVIRONMENT=production

# 4. Ajout de PostgreSQL
Write-Host "🐘 Ajout du service PostgreSQL..." -ForegroundColor Blue
railway add postgresql

# 5. Déploiement
Write-Host "🚀 Déploiement en cours..." -ForegroundColor Green
railway up --detach

Write-Host "✅ Déploiement lancé !" -ForegroundColor Green
Write-Host "🌐 Votre GeoServer sera disponible sur l'URL fournie par Railway" -ForegroundColor Cyan
Write-Host "📊 Consultez les logs avec : railway logs" -ForegroundColor Yellow
Write-Host "🔧 Dashboard : https://railway.app/dashboard" -ForegroundColor Yellow
