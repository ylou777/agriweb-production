#!/usr/bin/env pwsh
# Script de surveillance continue du déploiement Railway

param(
    [int]$MaxAttempts = 30,
    [int]$IntervalSeconds = 30
)

$geoserverUrl = "https://geoserver-agriweb-production.up.railway.app/geoserver"

Write-Host "🔄 SURVEILLANCE DÉPLOIEMENT RAILWAY" -ForegroundColor Green
Write-Host "URL cible: $geoserverUrl" -ForegroundColor Cyan
Write-Host "Tentatives: $MaxAttempts (toutes les $IntervalSeconds secondes)" -ForegroundColor Cyan
Write-Host "=" * 50

for ($i = 1; $i -le $MaxAttempts; $i++) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "`n[$timestamp] Tentative $i/$MaxAttempts" -ForegroundColor Yellow
    
    # Vérifier le statut Railway
    try {
        $status = railway status 2>$null
        Write-Host "   📊 Status: $status" -ForegroundColor White
    } catch {
        Write-Host "   ⚠️  Erreur status Railway" -ForegroundColor Yellow
    }
    
    # Test connectivité
    try {
        $response = Invoke-WebRequest -Uri $geoserverUrl -Method GET -TimeoutSec 15 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ GEOSERVER ACCESSIBLE ! (Status: $($response.StatusCode))" -ForegroundColor Green
            Write-Host "   🌐 URL: $geoserverUrl" -ForegroundColor Blue
            Write-Host "   🔐 Admin: admin / admin123" -ForegroundColor Blue
            
            # Test de l'interface admin
            try {
                $adminUrl = "$geoserverUrl/web"
                $adminResponse = Invoke-WebRequest -Uri $adminUrl -Method HEAD -TimeoutSec 10 -ErrorAction Stop
                Write-Host "   ✅ Interface admin accessible" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠️  Interface admin en cours de chargement..." -ForegroundColor Yellow
            }
            
            Write-Host "`n🎉 DÉPLOIEMENT RÉUSSI !" -ForegroundColor Green
            Write-Host "💡 Vous pouvez maintenant:" -ForegroundColor Cyan
            Write-Host "   1. Accéder à GeoServer: $geoserverUrl" -ForegroundColor White
            Write-Host "   2. Migrer vos données: python migrate_geoserver_data.py" -ForegroundColor White
            Write-Host "   3. Passer en production: .\test_geoserver_final.ps1 -Production" -ForegroundColor White
            
            break
        } catch {
            $errorMsg = $_.Exception.Message
            
            # Analyser le type d'erreur
            if ($errorMsg -like "*404*" -or $errorMsg -like "*Not Found*") {
                Write-Host "   ⏳ Service en cours de démarrage (404)" -ForegroundColor Yellow
            } elseif ($errorMsg -like "*train has not arrived*") {
                Write-Host "   🚂 Railway: Le train n'est pas arrivé à la station" -ForegroundColor Yellow
            } elseif ($errorMsg -like "*timeout*" -or $errorMsg -like "*timed out*") {
                Write-Host "   ⏰ Timeout - Service encore en démarrage" -ForegroundColor Yellow
            } elseif ($errorMsg -like "*connection*") {
                Write-Host "   🔌 Problème de connexion - Déploiement en cours" -ForegroundColor Yellow
            } else {
                Write-Host "   ❌ Erreur: $errorMsg" -ForegroundColor Red
            }
        }
    
        # Vérifier les logs si disponibles
        try {
            $logs = railway logs 2>$null
            if ($logs -and $logs -notlike "*No deployments found*") {
                Write-Host "   📋 Logs disponibles" -ForegroundColor Green
            } else {
                Write-Host "   📋 Pas de logs encore" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   📋 Logs non accessibles" -ForegroundColor Yellow
        }
    
        if ($i -lt $MaxAttempts) {
            Write-Host "   ⏸️  Attente $IntervalSeconds secondes..." -ForegroundColor Gray
            Start-Sleep -Seconds $IntervalSeconds
        }
    }

    if ($i -gt $MaxAttempts) {
        Write-Host "`n⚠️  TIMEOUT ATTEINT" -ForegroundColor Red
        Write-Host "Le déploiement prend plus de temps que prévu." -ForegroundColor Yellow
        Write-Host "`n🔧 Actions recommandées:" -ForegroundColor Cyan
        Write-Host "1. Vérifier le dashboard: railway open" -ForegroundColor White
        Write-Host "2. Redéployer si nécessaire: railway redeploy" -ForegroundColor White
        Write-Host "3. Vérifier les logs: railway logs" -ForegroundColor White
    }
    Write-Host "4. Relancer cette surveillance: .\watch_deployment.ps1" -ForegroundColor White
}

Write-Host "`n📊 Dashboard Railway: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Blue
