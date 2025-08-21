# Script PowerShell de test GeoServer distant
param(
    [string]$IP = "81.220.178.156",
    [string]$User = "railway_user", 
    [string]$Pass = "votre_mot_de_passe"
)

$BaseURL = "http://$IP:8080/geoserver"

Write-Host "🧪 Test GeoServer Distant: $BaseURL" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green

# Test 1: Connectivité
Write-Host "1️⃣ Test connectivité..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri $BaseURL -TimeoutSec 10
    Write-Host "✅ Serveur accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Serveur non accessible: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Vérifiez que GeoServer est démarré et que le port 8080 est ouvert" -ForegroundColor Yellow
    exit 1
}

# Test 2: WMS Capabilities avec auth
Write-Host "2️⃣ Test WMS avec authentification..." -ForegroundColor Blue
$wmsUrl = "$BaseURL/wms?service=WMS&request=GetCapabilities&version=1.3.0"
$creds = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$User`:$Pass"))

try {
    $response = Invoke-WebRequest -Uri $wmsUrl -Headers @{Authorization="Basic $creds"} -TimeoutSec 20
    if ($response.Content -like "*WMS_Capabilities*") {
        Write-Host "✅ WMS OK - Capabilities reçues" -ForegroundColor Green
        # Compter les couches
        $layerCount = ([regex]::Matches($response.Content, "<Layer")).Count
        Write-Host "   📋 $layerCount couches détectées" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️ WMS répond mais contenu inattendu" -ForegroundColor Yellow
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "❌ Erreur authentification - Vérifiez user/password" -ForegroundColor Red
    } else {
        Write-Host "❌ Erreur WMS: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 3: WFS Capabilities
Write-Host "3️⃣ Test WFS..." -ForegroundColor Blue
$wfsUrl = "$BaseURL/wfs?service=WFS&request=GetCapabilities&version=2.0.0"
try {
    $response = Invoke-WebRequest -Uri $wfsUrl -Headers @{Authorization="Basic $creds"} -TimeoutSec 20
    if ($response.Content -like "*WFS_Capabilities*") {
        Write-Host "✅ WFS OK - Capabilities reçues" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WFS répond mais contenu inattendu" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erreur WFS: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Workspaces REST
Write-Host "4️⃣ Test accès REST..." -ForegroundColor Blue
$restUrl = "$BaseURL/rest/workspaces"
try {
    $response = Invoke-WebRequest -Uri $restUrl -Headers @{Authorization="Basic $creds"; Accept="application/json"} -TimeoutSec 10
    Write-Host "✅ REST accessible" -ForegroundColor Green
    
    # Parser JSON si possible
    try {
        $data = $response.Content | ConvertFrom-Json
        $workspaces = $data.workspaces.workspace
        Write-Host "   📁 $($workspaces.Count) workspaces disponibles" -ForegroundColor Cyan
    } catch {
        Write-Host "   📁 Workspaces disponibles (format non-JSON)" -ForegroundColor Cyan
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "❌ Accès refusé - Permissions insuffisantes" -ForegroundColor Red
    } else {
        Write-Host "❌ Erreur REST: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 5: Configuration pour Railway
Write-Host "5️⃣ Configuration Railway..." -ForegroundColor Blue
Write-Host "   Variables à définir:" -ForegroundColor White
Write-Host "   railway variables set GEOSERVER_URL=$BaseURL" -ForegroundColor Cyan
Write-Host "   railway variables set GEOSERVER_USERNAME=$User" -ForegroundColor Cyan
Write-Host "   railway variables set GEOSERVER_PASSWORD=$Pass" -ForegroundColor Cyan

Write-Host ""
Write-Host "✅ Tests terminés!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "1. Si tous les tests passent → Configurez Railway avec ces variables" -ForegroundColor White
Write-Host "2. Si erreurs 401/403 → Vérifiez les permissions dans GeoServer" -ForegroundColor White
Write-Host "3. Si erreurs de connexion → Vérifiez firewall/routeur" -ForegroundColor White
