#!/usr/bin/env pwsh
# Script de vérification du déploiement GeoServer sur Railway

Write-Host "🚀 Vérification du déploiement GeoServer..." -ForegroundColor Green

# Statut du projet
Write-Host "`n📊 Statut du projet:" -ForegroundColor Cyan
railway status

# Variables d'environnement
Write-Host "`n🔧 Variables d'environnement configurées:" -ForegroundColor Cyan
railway variables

# Tentative d'obtenir l'URL
Write-Host "`n🌐 URL du service:" -ForegroundColor Cyan
try {
    $domain = railway domain 2>$null
    if ($domain) {
        Write-Host "✅ Service accessible sur: https://$domain" -ForegroundColor Green
        Write-Host "🔗 GeoServer: https://$domain/geoserver" -ForegroundColor Blue
        
        # Test de connectivité
        Write-Host "`n🔍 Test de connectivité..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "https://$domain/geoserver" -Method HEAD -TimeoutSec 10 -ErrorAction Stop
            Write-Host "✅ GeoServer répond (Status: $($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Service en cours de démarrage... (peut prendre 2-5 minutes)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⏳ Service en cours de déploiement..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⏳ URL pas encore disponible - déploiement en cours..." -ForegroundColor Yellow
}

# Ouvrir le dashboard
Write-Host "`n📊 Dashboard Railway:" -ForegroundColor Cyan
Write-Host "https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Blue

Write-Host "`n💡 Commandes utiles:" -ForegroundColor Cyan
Write-Host "railway logs    - Voir les logs en temps réel" -ForegroundColor White
Write-Host "railway domain  - Obtenir l'URL du service" -ForegroundColor White
Write-Host "railway open    - Ouvrir le dashboard" -ForegroundColor White

Write-Host "`n🔄 Le déploiement peut prendre 2-5 minutes..." -ForegroundColor Yellow
