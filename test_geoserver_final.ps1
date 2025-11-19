#!/usr/bin/env pwsh
# Script de test final et de finalisation du déploiement GeoServer

param(
    [switch]$Monitor,
    [switch]$Test,
    [switch]$Production
)

$geoserverUrl = "https://geoserver-agriweb-production.up.railway.app"
$geoserverEndpoint = "$geoserverUrl/geoserver"

Write-Host "🚀 TEST FINAL - DÉPLOIEMENT GEOSERVER" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

if ($Monitor) {
    Write-Host "`n📊 Mode surveillance activé..." -ForegroundColor Cyan
    for ($i = 1; $i -le 20; $i++) {
        Write-Host "`n⏱️  Test $i/20 - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
        
        try {
            $response = Invoke-WebRequest -Uri $geoserverEndpoint -Method HEAD -TimeoutSec 10 -ErrorAction Stop
            Write-Host "✅ GeoServer ACTIF ! (Status: $($response.StatusCode))" -ForegroundColor Green
            Write-Host "🔗 URL: $geoserverEndpoint" -ForegroundColor Blue
            break
        } catch {
            Write-Host "⏳ En attente... ($($_.Exception.Message))" -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
    }
}

if ($Test) {
    Write-Host "`n🔍 TEST DE CONNECTIVITÉ" -ForegroundColor Cyan
    
    # Test principal
    try {
        $response = Invoke-WebRequest -Uri $geoserverEndpoint -Method GET -TimeoutSec 15
        Write-Host "✅ GeoServer accessible (Status: $($response.StatusCode))" -ForegroundColor Green
        
        # Test de l'interface d'administration
        $adminUrl = "$geoserverEndpoint/web"
        try {
            $adminResponse = Invoke-WebRequest -Uri $adminUrl -Method HEAD -TimeoutSec 10
            Write-Host "✅ Interface admin accessible" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Interface admin en cours de chargement..." -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ GeoServer pas encore prêt: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "💡 Utilisez -Monitor pour surveiller le démarrage" -ForegroundColor Yellow
    }
}

if ($Production) {
    Write-Host "`n🔄 PASSAGE EN MODE PRODUCTION" -ForegroundColor Cyan
    
    # Backup du fichier .env
    Copy-Item ".env" ".env.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')" -ErrorAction SilentlyContinue
    
    # Mise à jour vers production
    $envContent = Get-Content ".env" -Raw
    $envContent = $envContent -replace "ENVIRONMENT=development", "ENVIRONMENT=production"
    Set-Content ".env" $envContent -Encoding UTF8
    
    Write-Host "✅ Configuration mise à jour vers PRODUCTION" -ForegroundColor Green
    Write-Host "📁 Sauvegarde créée: .env.backup.*" -ForegroundColor Blue
}

Write-Host "`n📋 RÉSUMÉ DU DÉPLOIEMENT:" -ForegroundColor Cyan
Write-Host "   🌐 URL GeoServer: $geoserverEndpoint" -ForegroundColor White
Write-Host "   🔐 Admin: admin / admin123" -ForegroundColor White
Write-Host "   📊 Dashboard: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor White

Write-Host "`n💡 COMMANDES DE TEST:" -ForegroundColor Cyan
Write-Host "   .\test_geoserver_final.ps1 -Monitor     # Surveiller le démarrage" -ForegroundColor White
Write-Host "   .\test_geoserver_final.ps1 -Test        # Tester la connectivité" -ForegroundColor White
Write-Host "   .\test_geoserver_final.ps1 -Production  # Passer en production" -ForegroundColor White

Write-Host "`n🔧 MAINTENANCE:" -ForegroundColor Cyan
Write-Host "   railway logs                            # Voir les logs" -ForegroundColor White
Write-Host "   railway redeploy                        # Redémarrer le service" -ForegroundColor White
Write-Host "   railway open                            # Dashboard Railway" -ForegroundColor White

if (!$Monitor -and !$Test -and !$Production) {
    Write-Host "`n🎯 PROCHAINES ÉTAPES:" -ForegroundColor Yellow
    Write-Host "1. Surveillez le démarrage: .\test_geoserver_final.ps1 -Monitor" -ForegroundColor White
    Write-Host "2. Testez une fois prêt: .\test_geoserver_final.ps1 -Test" -ForegroundColor White
    Write-Host "3. Passez en production: .\test_geoserver_final.ps1 -Production" -ForegroundColor White
}
