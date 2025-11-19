Write-Host "=== TEST RAPIDE GEOSERVER ===" -ForegroundColor Cyan
Write-Host "URL: https://geoserver-agriweb-production.up.railway.app/geoserver"
Write-Host "Heure: $(Get-Date -Format 'HH:mm:ss')"
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "https://geoserver-agriweb-production.up.railway.app/geoserver" -TimeoutSec 20
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Taille: $($response.Content.Length) bytes" -ForegroundColor Green
    Write-Host ""
    Write-Host "GeoServer est pret!" -ForegroundColor Green
    Write-Host "Acceder a: https://geoserver-agriweb-production.up.railway.app/geoserver/web" -ForegroundColor Cyan
    Write-Host "Login: admin / admin123" -ForegroundColor Cyan
} catch {
    $msg = $_.Exception.Message
    if ($msg -like "*502*") {
        Write-Host "Status: 502 - Demarrage en cours..." -ForegroundColor Yellow
    } elseif ($msg -like "*timeout*" -or $msg -like "*expired*") {
        Write-Host "Status: Timeout - Initialisation en cours..." -ForegroundColor Yellow
    } else {
        Write-Host "Status: $msg" -ForegroundColor Red
    }
    Write-Host "Le demarrage continue..." -ForegroundColor Yellow
}

Write-Host "================================" -ForegroundColor Cyan
