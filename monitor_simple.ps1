param(
    [int]$MaxAttempts = 15,
    [int]$IntervalSeconds = 10
)

$geoserverUrl = "https://geoserver-agriweb-production.up.railway.app"

Write-Host "Surveillance du demarrage GeoServer Railway" -ForegroundColor Cyan
Write-Host "URL: $geoserverUrl" -ForegroundColor White
Write-Host "Tentatives max: $MaxAttempts, Intervalle: $IntervalSeconds secondes" -ForegroundColor Gray
Write-Host "============================================================"

for ($i = 1; $i -le $MaxAttempts; $i++) {
    Write-Host "`n[$i/$MaxAttempts] Test a $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$geoserverUrl/geoserver" -TimeoutSec 15 -ErrorAction Stop
        
        Write-Host "Reponse recue: $($response.StatusCode)" -ForegroundColor Green
        
        if ($response.StatusCode -eq 200) {
            Write-Host "GeoServer est operationnel!" -ForegroundColor Green
            Write-Host "Acceder a GeoServer: $geoserverUrl/geoserver" -ForegroundColor Cyan
            Write-Host "Connexion: admin / admin123" -ForegroundColor Cyan
            break
        }
        
    } catch {
        $errorMsg = $_.Exception.Message
        
        if ($errorMsg -like "*502*" -or $errorMsg -like "*Bad Gateway*") {
            Write-Host "   Serveur en cours de demarrage (502 Bad Gateway)" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*504*" -or $errorMsg -like "*Gateway Timeout*") {
            Write-Host "   Timeout du gateway (504)" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*404*" -or $errorMsg -like "*Not Found*") {
            Write-Host "   Service pas encore accessible (404)" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*timeout*" -or $errorMsg -like "*timed out*") {
            Write-Host "   Timeout - Demarrage en cours" -ForegroundColor Yellow
        } elseif ($errorMsg -like "*connection*") {
            Write-Host "   Connexion en cours d'etablissement" -ForegroundColor Yellow
        } else {
            Write-Host "   Erreur: $errorMsg" -ForegroundColor Red
        }
    }
    
    if ($i -lt $MaxAttempts) {
        Write-Host "   Attente $IntervalSeconds secondes..." -ForegroundColor Gray
        Start-Sleep -Seconds $IntervalSeconds
    }
}

if ($i -gt $MaxAttempts) {
    Write-Host "`nTIMEOUT ATTEINT" -ForegroundColor Red
    Write-Host "Le demarrage prend plus de temps que prevu." -ForegroundColor Yellow
    Write-Host "Actions recommandees:" -ForegroundColor Cyan
    Write-Host "1. Verifier le dashboard Railway: railway open" -ForegroundColor White
    Write-Host "2. Consulter les logs: railway logs" -ForegroundColor White
    Write-Host "3. Le demarrage peut prendre jusqu'a 5-10 minutes" -ForegroundColor White
}

Write-Host "`nSurveillance terminee" -ForegroundColor Cyan
