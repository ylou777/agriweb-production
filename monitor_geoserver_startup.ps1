#!/usr/bin/env pwsh

param(
    [int]$MaxAttempts = 20,
    [int]$IntervalSeconds = 15
)

$geoserverUrl = "https://geoserver-agriweb-production.up.railway.app"

Write-Host "🔍 Surveillance du démarrage GeoServer Railway" -ForegroundColor Cyan
Write-Host "URL: $geoserverUrl" -ForegroundColor White
Write-Host "Tentatives max: $MaxAttempts, Intervalle: $IntervalSeconds secondes" -ForegroundColor Gray
Write-Host "=" * 60 -ForegroundColor Gray

for ($i = 1; $i -le $MaxAttempts; $i++) {
    Write-Host "`n[$i/$MaxAttempts] Test à $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
    
    try {
        # Test du endpoint principal
        $response = Invoke-WebRequest -Uri "$geoserverUrl/geoserver" -TimeoutSec 20 -ErrorAction Stop
        
        Write-Host "✅ Réponse reçue: $($response.StatusCode)" -ForegroundColor Green
        
        if ($response.StatusCode -eq 200) {
            Write-Host "🎉 GeoServer est opérationnel!" -ForegroundColor Green
            
            # Test de l'interface web
            try {
                $webResponse = Invoke-WebRequest -Uri "$geoserverUrl/geoserver/web" -TimeoutSec 10
                Write-Host "✅ Interface web accessible: $($webResponse.StatusCode)" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  Interface web pas encore prête" -ForegroundColor Yellow
            }
            
            # Test de l'API REST
            try {
                $restResponse = Invoke-WebRequest -Uri "$geoserverUrl/geoserver/rest" -TimeoutSec 10
                Write-Host "✅ API REST accessible: $($restResponse.StatusCode)" -ForegroundColor Green
            } catch {
                Write-Host "ℹ️  API REST: $($_.Exception.Message)" -ForegroundColor Blue
            }
            
            Write-Host "`n🚀 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!" -ForegroundColor Green
            Write-Host "🔗 Accéder à GeoServer: $geoserverUrl/geoserver" -ForegroundColor Cyan
            Write-Host "🔑 Connexion: admin / admin123" -ForegroundColor Cyan
            break
        }
        
    } catch {
        $errorMsg = $_.Exception.Message
        
        if ($errorMsg -like "*502*" -or $errorMsg -like "*Bad Gateway*") {
            Write-Host "   ⏳ Serveur en cours de démarrage (502 Bad Gateway)" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*504*" -or $errorMsg -like "*Gateway Timeout*") {
            Write-Host "   ⏳ Timeout du gateway (504)" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*404*" -or $errorMsg -like "*Not Found*") {
            Write-Host "   ⏳ Service pas encore accessible (404)" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*timeout*" -or $errorMsg -like "*timed out*") {
            Write-Host "   ⏰ Timeout - Démarrage en cours" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*connection*") {
            Write-Host "   🔌 Connexion en cours d'établissement" -ForegroundColor Yellow
        } else {
            Write-Host "   ❌ $errorMsg" -ForegroundColor Red
        }
    }
    
    if ($i -lt $MaxAttempts) {
        Write-Host "   ⏸️  Attente $IntervalSeconds secondes..." -ForegroundColor Gray
        Start-Sleep -Seconds $IntervalSeconds
    }
}

if ($i -gt $MaxAttempts) {
    Write-Host "`n⚠️  TIMEOUT ATTEINT" -ForegroundColor Red
    Write-Host "Le démarrage prend plus de temps que prévu." -ForegroundColor Yellow
    Write-Host "`n🔧 Actions recommandées:" -ForegroundColor Cyan
    Write-Host "1. Vérifier le dashboard Railway: railway open" -ForegroundColor White
    Write-Host "2. Consulter les logs: railway logs" -ForegroundColor White
    Write-Host "3. Le démarrage peut prendre jusqu'à 5-10 minutes" -ForegroundColor White
}

Write-Host "`n✨ Surveillance terminée" -ForegroundColor Cyan
