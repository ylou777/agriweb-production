# Installation Alternative Sans Docker
# Pour démarrer la migration GeoServer sans attendre Docker

Write-Host "🚀 Installation Alternative - Migration GeoServer" -ForegroundColor Green

# Vérification de l'état actuel
Write-Host "`n📊 État des prérequis:" -ForegroundColor Yellow

# Node.js
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "⏳ Node.js: Installation en cours ou requis" -ForegroundColor Yellow
    
    # Tentative d'installation
    try {
        winget install OpenJS.NodeJS --silent
        Write-Host "📦 Node.js installé" -ForegroundColor Green
    } catch {
        Write-Host "❌ Erreur installation Node.js" -ForegroundColor Red
        Write-Host "💡 Installation manuelle: https://nodejs.org" -ForegroundColor Cyan
    }
}

# Rechargement du PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

# Railway CLI
Write-Host "`n🚂 Installation Railway CLI..." -ForegroundColor Yellow

if (Get-Command npm -ErrorAction SilentlyContinue) {
    try {
        npm install -g @railway/cli
        Write-Host "✅ Railway CLI installé" -ForegroundColor Green
    } catch {
        Write-Host "❌ Erreur installation Railway CLI" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️ npm non disponible - Node.js requis" -ForegroundColor Yellow
}

# Docker (optionnel pour Railway)
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✅ Docker: Disponible" -ForegroundColor Green
} else {
    Write-Host "⏳ Docker: Installation en cours ou non installé" -ForegroundColor Yellow
    Write-Host "💡 Docker n'est pas obligatoire pour Railway" -ForegroundColor Cyan
}

# Alternative sans CLI
Write-Host "`n🌐 ALTERNATIVE SANS CLI:" -ForegroundColor Green
Write-Host "Si l'installation CLI échoue, vous pouvez utiliser l'interface web:" -ForegroundColor Cyan
Write-Host "1. Allez sur https://railway.app" -ForegroundColor White
Write-Host "2. Créez un compte gratuit" -ForegroundColor White
Write-Host "3. 'New Project' → 'Deploy from GitHub'" -ForegroundColor White
Write-Host "4. Connectez votre repository" -ForegroundColor White

# Test de connectivité
Write-Host "`n🔍 Test de connectivité..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://railway.app" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Connexion Railway OK" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Problème de connexion internet" -ForegroundColor Red
}

# Instructions suivantes
Write-Host "`n📋 PROCHAINES ÉTAPES:" -ForegroundColor Green
Write-Host ""

if (Get-Command railway -ErrorAction SilentlyContinue) {
    Write-Host "✅ CLI DISPONIBLE - Méthode recommandée:" -ForegroundColor Green
    Write-Host "   railway login" -ForegroundColor Cyan
    Write-Host "   .\deploy_geoserver.ps1" -ForegroundColor Cyan
} else {
    Write-Host "🌐 INTERFACE WEB - Méthode alternative:" -ForegroundColor Yellow
    Write-Host "   1. Ouvrez https://railway.app" -ForegroundColor Cyan
    Write-Host "   2. Créez un compte" -ForegroundColor Cyan
    Write-Host "   3. New Project → Deploy from GitHub" -ForegroundColor Cyan
    Write-Host "   4. Sélectionnez agriweb2.0" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📱 TOUJOURS POSSIBLE:" -ForegroundColor Green
Write-Host "   - Configuration automatique via railway.toml" -ForegroundColor Cyan
Write-Host "   - Migration des données: python migrate_geoserver.py" -ForegroundColor Cyan
Write-Host "   - Test: python test_migration.py" -ForegroundColor Cyan

Write-Host "`n🎯 Voulez-vous continuer avec l'interface web? (Tapez 'web')" -ForegroundColor Yellow
Write-Host "🎯 Ou attendre CLI? (Tapez 'cli')" -ForegroundColor Yellow
