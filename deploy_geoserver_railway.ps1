# Script PowerShell pour déployer GeoServer sur Railway

Write-Host "🚂 DÉPLOIEMENT GEOSERVER SUR RAILWAY" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Vérifier si Railway CLI est installé
try {
    railway --version | Out-Null
    Write-Host "✅ Railway CLI détecté" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI non installé" -ForegroundColor Red
    Write-Host "Installez-le: npm install -g @railway/cli" -ForegroundColor Yellow
    exit 1
}

# 1. Créer dossier et fichiers
Write-Host "1️⃣ Création du projet GeoServer..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "geoserver-production"
Set-Location "geoserver-production"

# 2. Créer Dockerfile
Write-Host "2️⃣ Configuration Dockerfile..." -ForegroundColor Blue
$dockerfileContent = @"
# Dockerfile pour GeoServer sur Railway
FROM kartoza/geoserver:2.24.1

# Variables d'environnement par défaut
ENV GEOSERVER_ADMIN_USER=admin
ENV GEOSERVER_ADMIN_PASSWORD=geoserver_admin_2024
ENV GEOSERVER_USERS=railway_user:railway_password_2024

# Configuration additionnelle
ENV GEOSERVER_CSRF_DISABLED=true
ENV INITIAL_MEMORY=512M
ENV MAXIMUM_MEMORY=1G

# Port d'écoute
EXPOSE 8080

# Healthcheck pour Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/geoserver/web/ || exit 1
"@

$dockerfileContent | Out-File -FilePath "Dockerfile" -Encoding UTF8

# 3. Initialiser Railway
Write-Host "3️⃣ Initialisation Railway..." -ForegroundColor Blue
railway login

# 4. Créer projet
Write-Host "4️⃣ Création du projet Railway..." -ForegroundColor Blue
railway new

# 5. Variables d'environnement
Write-Host "5️⃣ Configuration des variables..." -ForegroundColor Blue
railway variables set GEOSERVER_ADMIN_USER=admin
railway variables set GEOSERVER_ADMIN_PASSWORD=VotreMotDePasseAdmin2024
railway variables set GEOSERVER_USERS=railway_user:VotreMotDePasseUser2024

# 6. Déploiement
Write-Host "6️⃣ Déploiement en cours..." -ForegroundColor Blue
railway up

# 7. Afficher le statut
Write-Host "7️⃣ Récupération de l'URL..." -ForegroundColor Blue
railway status

Write-Host ""
Write-Host "✅ GeoServer déployé sur Railway !" -ForegroundColor Green
Write-Host "📝 Notez l'URL affichée par 'railway status'" -ForegroundColor Yellow
Write-Host "🔧 Configurez ensuite votre app AgriWeb avec cette URL:" -ForegroundColor Yellow
Write-Host ""
Write-Host "railway variables set GEOSERVER_URL=https://VOTRE-URL.up.railway.app/geoserver" -ForegroundColor Cyan
Write-Host "railway variables set GEOSERVER_USERNAME=railway_user" -ForegroundColor Cyan
Write-Host "railway variables set GEOSERVER_PASSWORD=VotreMotDePasseUser2024" -ForegroundColor Cyan
