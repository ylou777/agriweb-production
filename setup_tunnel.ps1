# 🌐 SCRIPT TUNNEL GEOSERVER LOCAL POUR AGRIWEB
# Facilite l'exposition de votre GeoServer local

param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Test,
    [switch]$Stop,
    [string]$TunnelUrl
)

function Show-Banner {
    Write-Host "🌐 TUNNEL GEOSERVER LOCAL" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-GeoServerLocal {
    Write-Host "🔍 Test GeoServer local..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/geoserver/web/" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ GeoServer local accessible" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ GeoServer local non accessible: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "💡 Assurez-vous que GeoServer est démarré sur le port 8080" -ForegroundColor Yellow
        return $false
    }
}

function Install-Ngrok {
    Write-Host "📦 Installation ngrok..." -ForegroundColor Yellow
    
    Write-Host "📝 Instructions d'installation ngrok:" -ForegroundColor Cyan
    Write-Host "1. Allez sur https://ngrok.com/download" -ForegroundColor White
    Write-Host "2. Téléchargez ngrok pour Windows" -ForegroundColor White
    Write-Host "3. Décompressez dans C:\ngrok\" -ForegroundColor White
    Write-Host "4. Créez un compte sur https://ngrok.com/signup" -ForegroundColor White
    Write-Host "5. Récupérez votre authtoken" -ForegroundColor White
    Write-Host ""
    Write-Host "⚡ Commandes d'installation:" -ForegroundColor Cyan
    Write-Host "cd C:\ngrok\" -ForegroundColor White
    Write-Host ".\ngrok.exe authtoken VOTRE_TOKEN" -ForegroundColor White
    Write-Host ""
    
    # Vérifier si ngrok est déjà installé
    $ngrokPaths = @(
        "C:\ngrok\ngrok.exe",
        "ngrok.exe",
        "$env:USERPROFILE\AppData\Local\ngrok\ngrok.exe"
    )
    
    foreach ($path in $ngrokPaths) {
        if (Test-Path $path) {
            Write-Host "✅ ngrok trouvé: $path" -ForegroundColor Green
            return $path
        }
    }
    
    Write-Host "⚠️ ngrok non trouvé. Installez-le manuellement." -ForegroundColor Yellow
    return $null
}

function Start-Tunnel {
    Write-Host "🚀 Démarrage tunnel ngrok..." -ForegroundColor Yellow
    
    # Vérifier GeoServer local d'abord
    if (-not (Test-GeoServerLocal)) {
        Write-Host "❌ Impossible de démarrer le tunnel: GeoServer local non accessible" -ForegroundColor Red
        return
    }
    
    # Trouver ngrok
    $ngrokPath = Install-Ngrok
    if (-not $ngrokPath) {
        Write-Host "❌ ngrok non trouvé" -ForegroundColor Red
        return
    }
    
    Write-Host "🌐 Démarrage du tunnel sur le port 8080..." -ForegroundColor Cyan
    Write-Host "📝 Commande: $ngrokPath http 8080" -ForegroundColor White
    Write-Host ""
    Write-Host "⚡ Démarrez manuellement dans un autre terminal:" -ForegroundColor Yellow
    Write-Host "$ngrokPath http 8080" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Une fois démarré, copiez l'URL HTTPS et utilisez:" -ForegroundColor Cyan
    Write-Host ".\setup_tunnel.ps1 -TunnelUrl 'https://abc123.ngrok.io'" -ForegroundColor White
}

function Get-NgrokTunnel {
    Write-Host "🔍 Recherche tunnel ngrok actif..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
        foreach ($tunnel in $response.tunnels) {
            if ($tunnel.proto -eq "https") {
                Write-Host "✅ Tunnel trouvé: $($tunnel.public_url)" -ForegroundColor Green
                return $tunnel.public_url
            }
        }
        Write-Host "⚠️ Aucun tunnel HTTPS trouvé" -ForegroundColor Yellow
        return $null
    }
    catch {
        Write-Host "⚠️ API ngrok non accessible (tunnel non démarré?)" -ForegroundColor Yellow
        return $null
    }
}

function Test-TunnelAccess {
    param([string]$TunnelUrl)
    
    Write-Host "🧪 Test accès GeoServer via tunnel..." -ForegroundColor Yellow
    
    $geoserverUrl = "$TunnelUrl/geoserver"
    try {
        $response = Invoke-WebRequest -Uri "$geoserverUrl/web/" -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ GeoServer accessible via tunnel!" -ForegroundColor Green
            Write-Host "🌐 URL GeoServer: $geoserverUrl" -ForegroundColor Cyan
            return $geoserverUrl
        }
    }
    catch {
        Write-Host "❌ GeoServer non accessible via tunnel: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Update-AgriWebConfig {
    param([string]$GeoServerUrl)
    
    Write-Host "📝 Mise à jour configuration AgriWeb..." -ForegroundColor Yellow
    
    $configContent = @"
# 🌐 CONFIGURATION TUNNEL GEOSERVER LOCAL
# Généré le $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# Variable d'environnement pour AgriWeb
`$env:GEOSERVER_TUNNEL_URL = "$GeoServerUrl"

# Pour Railway/Render/Heroku, ajoutez cette variable d'environnement:
# GEOSERVER_TUNNEL_URL=$GeoServerUrl

# Test de la configuration:
# curl "$GeoServerUrl/web/"

Write-Host "✅ Configuration tunnel activée" -ForegroundColor Green
Write-Host "🌐 GeoServer URL: $GeoServerUrl" -ForegroundColor Cyan
"@

    $configContent | Out-File -FilePath "tunnel_config.ps1" -Encoding UTF8
    Write-Host "✅ Configuration sauvée: tunnel_config.ps1" -ForegroundColor Green
    
    # Activer immédiatement
    $env:GEOSERVER_TUNNEL_URL = $GeoServerUrl
    Write-Host "⚡ Variable d'environnement activée pour cette session" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "📋 Prochaines étapes:" -ForegroundColor Cyan
    Write-Host "1. Ajoutez GEOSERVER_TUNNEL_URL=$GeoServerUrl dans votre plateforme d'hébergement" -ForegroundColor White
    Write-Host "2. Redéployez AgriWeb" -ForegroundColor White
    Write-Host "3. AgriWeb utilisera automatiquement votre GeoServer local!" -ForegroundColor White
}

function Stop-Tunnel {
    Write-Host "🛑 Arrêt tunnel ngrok..." -ForegroundColor Yellow
    
    try {
        $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
        foreach ($tunnel in $tunnels.tunnels) {
            $name = $tunnel.name
            Write-Host "🛑 Arrêt tunnel: $name" -ForegroundColor Yellow
            Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels/$name" -Method Delete -TimeoutSec 3
        }
        Write-Host "✅ Tunnels arrêtés" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Erreur lors de l'arrêt des tunnels" -ForegroundColor Yellow
    }
    
    # Désactiver la variable d'environnement
    Remove-Item Env:\GEOSERVER_TUNNEL_URL -ErrorAction SilentlyContinue
    Write-Host "✅ Variable d'environnement désactivée" -ForegroundColor Green
}

# MAIN SCRIPT
Show-Banner

if ($Install) {
    Install-Ngrok
}
elseif ($Start) {
    Start-Tunnel
}
elseif ($Test) {
    if ($TunnelUrl) {
        $geoserverUrl = Test-TunnelAccess -TunnelUrl $TunnelUrl
        if ($geoserverUrl) {
            Update-AgriWebConfig -GeoServerUrl $geoserverUrl
        }
    }
    else {
        # Auto-détection
        $tunnelUrl = Get-NgrokTunnel
        if ($tunnelUrl) {
            $geoserverUrl = Test-TunnelAccess -TunnelUrl $tunnelUrl
            if ($geoserverUrl) {
                Update-AgriWebConfig -GeoServerUrl $geoserverUrl
            }
        }
        else {
            Write-Host "❌ Aucun tunnel détecté. Démarrez d'abord ngrok:" -ForegroundColor Red
            Write-Host ".\setup_tunnel.ps1 -Start" -ForegroundColor White
        }
    }
}
elseif ($Stop) {
    Stop-Tunnel
}
else {
    Write-Host "🎯 UTILISATION:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📦 Installation ngrok:" -ForegroundColor Yellow
    Write-Host ".\setup_tunnel.ps1 -Install" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Démarrer tunnel:" -ForegroundColor Yellow
    Write-Host ".\setup_tunnel.ps1 -Start" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 Tester tunnel (auto-détection):" -ForegroundColor Yellow
    Write-Host ".\setup_tunnel.ps1 -Test" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 Tester tunnel (URL spécifique):" -ForegroundColor Yellow
    Write-Host ".\setup_tunnel.ps1 -Test -TunnelUrl 'https://abc123.ngrok.io'" -ForegroundColor White
    Write-Host ""
    Write-Host "🛑 Arrêter tunnel:" -ForegroundColor Yellow
    Write-Host ".\setup_tunnel.ps1 -Stop" -ForegroundColor White
}
