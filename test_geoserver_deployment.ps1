#!/usr/bin/env pwsh

Write-Host "=== Test de déploiement GeoServer Railway ===" -ForegroundColor Cyan

$geoserverUrl = "https://geoserver-agriweb-production.up.railway.app"

Write-Host "Test de connectivité à: $geoserverUrl" -ForegroundColor Yellow

try {
    # Test du domaine principal
    $response = Invoke-WebRequest -Uri $geoserverUrl -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✅ Domaine principal accessible - Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Domaine principal non accessible: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    # Test de GeoServer
    $geoserverResponse = Invoke-WebRequest -Uri "$geoserverUrl/geoserver" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✅ GeoServer accessible - Status: $($geoserverResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ GeoServer non accessible: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    # Test de l'interface web GeoServer
    $webResponse = Invoke-WebRequest -Uri "$geoserverUrl/geoserver/web" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✅ Interface web GeoServer accessible - Status: $($webResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Interface web GeoServer non accessible: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== Test terminé ===" -ForegroundColor Cyan
