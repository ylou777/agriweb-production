# Script PowerShell de déploiement complet AgriWeb + GeoServer
# Automatise le déploiement des deux applications

Write-Host "🚀 Déploiement complet AgriWeb + GeoServer" -ForegroundColor Green

# Vérification des prérequis
Write-Host "`n1. Vérification des prérequis..." -ForegroundColor Yellow

if (-not (Get-Command "railway" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Railway CLI non installé" -ForegroundColor Red
    Write-Host "💡 Installation: npm install -g @railway/cli" -ForegroundColor Cyan
    exit 1
}

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker non installé" -ForegroundColor Red
    Write-Host "💡 Installez Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Prérequis OK" -ForegroundColor Green

# Connexion Railway
Write-Host "`n2. Connexion Railway..." -ForegroundColor Yellow
railway login

# Déploiement GeoServer
Write-Host "`n3. Déploiement GeoServer..." -ForegroundColor Yellow

$projectName = Read-Host "Nom du projet Railway (défaut: geoserver-agriweb)"
if ([string]::IsNullOrEmpty($projectName)) {
    $projectName = "geoserver-agriweb"
}

# Création du projet GeoServer
Write-Host "Création du projet $projectName..." -ForegroundColor Cyan
railway project create $projectName

# Déploiement avec Docker
Write-Host "Déploiement du container GeoServer..." -ForegroundColor Cyan
railway up --dockerfile Dockerfile.geoserver

# Configuration des variables d'environnement
Write-Host "`n4. Configuration GeoServer..." -ForegroundColor Yellow

railway variables set GEOSERVER_ADMIN_USER=admin
railway variables set GEOSERVER_ADMIN_PASSWORD=admin123
railway variables set JAVA_OPTS="-Xms512m -Xmx1024m"
railway variables set INITIAL_MEMORY=512M
railway variables set MAXIMUM_MEMORY=1024M

Write-Host "✅ GeoServer déployé" -ForegroundColor Green

# Récupération de l'URL GeoServer
Write-Host "`n5. Récupération de l'URL GeoServer..." -ForegroundColor Yellow
$geoserverUrl = railway status --json | ConvertFrom-Json | Select-Object -ExpandProperty url

if ($geoserverUrl) {
    Write-Host "🌐 URL GeoServer: $geoserverUrl/geoserver" -ForegroundColor Cyan
    
    # Mise à jour des URLs dans l'application
    Write-Host "`n6. Mise à jour des URLs dans l'application..." -ForegroundColor Yellow
    python update_geoserver_urls.py
    
    # Migration des données (optionnel)
    $migrate = Read-Host "Migrer les données GeoServer? (y/N)"
    if ($migrate -eq "y" -or $migrate -eq "Y") {
        Write-Host "Migration des données..." -ForegroundColor Cyan
        python migrate_geoserver.py
    }
    
} else {
    Write-Host "❌ Impossible de récupérer l'URL GeoServer" -ForegroundColor Red
}

# Déploiement de l'application AgriWeb
Write-Host "`n7. Déploiement AgriWeb..." -ForegroundColor Yellow

$deployApp = Read-Host "Déployer aussi l'application AgriWeb? (y/N)"
if ($deployApp -eq "y" -or $deployApp -eq "Y") {
    
    # Création du projet AgriWeb
    $appProjectName = Read-Host "Nom du projet AgriWeb (défaut: agriweb-app)"
    if ([string]::IsNullOrEmpty($appProjectName)) {
        $appProjectName = "agriweb-app"
    }
    
    railway project create $appProjectName
    
    # Configuration des variables d'environnement pour l'app
    railway variables set FLASK_ENV=production
    railway variables set DEBUG=False
    railway variables set GEOSERVER_URL="$geoserverUrl/geoserver"
    
    # Création du Dockerfile pour l'app
    $dockerfileContent = @"
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "agriweb_hebergement_gratuit.py"]
"@
    
    $dockerfileContent | Out-File -FilePath "Dockerfile.app" -Encoding UTF8
    
    # Déploiement
    railway up --dockerfile Dockerfile.app
    
    Write-Host "✅ AgriWeb déployé" -ForegroundColor Green
}

# Résumé
Write-Host "`n📊 Résumé du déploiement:" -ForegroundColor Green
Write-Host "   🗄️ GeoServer: $geoserverUrl/geoserver" -ForegroundColor Cyan
Write-Host "   🌐 Console Railway: https://railway.app/dashboard" -ForegroundColor Cyan
Write-Host "   💰 Coût estimé: 5-10$/mois après période gratuite" -ForegroundColor Yellow

Write-Host "`n✅ Déploiement terminé!" -ForegroundColor Green
Write-Host "💡 Testez vos applications avant de supprimer les versions locales" -ForegroundColor Yellow
