# Script d'installation des prérequis pour la migration GeoServer
# Installe Railway CLI et Docker Desktop si nécessaire

Write-Host "🔧 Installation des prérequis pour la migration GeoServer" -ForegroundColor Green

# Vérification de winget (gestionnaire de paquets Windows)
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "✅ Winget disponible" -ForegroundColor Green
    
    # Installation Node.js et npm si nécessaire
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Host "📦 Installation de Node.js..." -ForegroundColor Yellow
        winget install OpenJS.NodeJS
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    }
    
    # Installation Docker Desktop si nécessaire
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "🐳 Installation de Docker Desktop..." -ForegroundColor Yellow
        winget install Docker.DockerDesktop
    }
    
} else {
    Write-Host "⚠️ Winget non disponible. Installation manuelle requise:" -ForegroundColor Yellow
    Write-Host "1. Node.js: https://nodejs.org/en/download/" -ForegroundColor Cyan
    Write-Host "2. Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
}

# Attendre que les installations se terminent
Write-Host "⏱️ Attente de la finalisation des installations..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Rechargement du PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

# Installation Railway CLI
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "🚂 Installation de Railway CLI..." -ForegroundColor Yellow
    npm install -g @railway/cli
} else {
    Write-Host "❌ npm non disponible. Installez Node.js d'abord." -ForegroundColor Red
    Write-Host "💡 Alternative: Téléchargez Railway CLI depuis https://docs.railway.app/develop/cli" -ForegroundColor Cyan
}

# Vérification finale
Write-Host "`n📊 Vérification des installations:" -ForegroundColor Green

if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js: Non installé" -ForegroundColor Red
}

if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVersion = npm --version
    Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "❌ npm: Non installé" -ForegroundColor Red
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = docker --version
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Docker: Non installé" -ForegroundColor Red
}

if (Get-Command railway -ErrorAction SilentlyContinue) {
    $railwayVersion = railway --version
    Write-Host "✅ Railway CLI: $railwayVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Railway CLI: Non installé" -ForegroundColor Red
}

Write-Host "`n💡 Instructions:" -ForegroundColor Yellow
Write-Host "1. Si des installations ont échoué, redémarrez PowerShell en tant qu'administrateur" -ForegroundColor Cyan
Write-Host "2. Une fois tout installé, relancez: .\deploy_geoserver.ps1" -ForegroundColor Cyan
Write-Host "3. Vous pouvez aussi utiliser l'alternative sans Docker (voir GUIDE_MIGRATION_GEOSERVER.md)" -ForegroundColor Cyan
