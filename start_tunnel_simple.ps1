# 🌐 SCRIPT TUNNEL GEOSERVER - VERSION SIMPLE
# Utilisation: .\start_tunnel_simple.ps1

param(
    [switch]$Stop
)

function Show-Banner {
    Write-Host "🌐 TUNNEL GEOSERVER LOCAL → AGRIWEB" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
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
        Write-Host "❌ GeoServer local non accessible" -ForegroundColor Red
        Write-Host "💡 Démarrez GeoServer sur le port 8080 avant de continuer" -ForegroundColor Yellow
        return $false
    }
}

function Start-NgrokTunnel {
    Write-Host "🚀 Démarrage tunnel ngrok..." -ForegroundColor Yellow
    
    # Trouver ngrok
    $ngrokPaths = @(
        "C:\ngrok\ngrok.exe",
        "ngrok.exe",
        "ngrok",
        "$env:USERPROFILE\AppData\Local\ngrok\ngrok.exe",
        ".\ngrok.exe"
    )
    
    $ngrokPath = $null
    foreach ($path in $ngrokPaths) {
        try {
            $result = & $path version 2>$null
            if ($LASTEXITCODE -eq 0) {
                $ngrokPath = $path
                break
            }
        }
        catch { }
    }
    
    if (-not $ngrokPath) {
        Write-Host "❌ ngrok non trouvé" -ForegroundColor Red
        Write-Host "💡 Installez ngrok depuis https://ngrok.com/download" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "✅ ngrok trouvé: $ngrokPath" -ForegroundColor Green
    
    # Démarrer le tunnel
    Write-Host "🌐 Ouverture du tunnel sur le port 8080..." -ForegroundColor Cyan
    
    # Lancer ngrok en arrière-plan
    $job = Start-Job -ScriptBlock {
        param($ngrokPath)
        & $ngrokPath http 8080
    } -ArgumentList $ngrokPath
    
    Write-Host "⏳ Attente du démarrage du tunnel..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Récupérer l'URL du tunnel
    $tunnelUrl = Get-NgrokUrl
    if ($tunnelUrl) {
        Write-Host "✅ Tunnel actif: $tunnelUrl" -ForegroundColor Green
        
        # Tester l'accès GeoServer via tunnel
        $geoserverUrl = "$tunnelUrl/geoserver"
        Write-Host "🧪 Test accès GeoServer via tunnel..." -ForegroundColor Yellow
        
        try {
            $response = Invoke-WebRequest -Uri "$geoserverUrl/web/" -TimeoutSec 10 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ GeoServer accessible via tunnel!" -ForegroundColor Green
                Write-Host "🌐 URL GeoServer: $geoserverUrl" -ForegroundColor Cyan
                
                # Sauvegarder la configuration
                Save-TunnelConfig -TunnelUrl $geoserverUrl
                
                return $geoserverUrl
            }
        }
        catch {
            Write-Host "❌ GeoServer non accessible via tunnel" -ForegroundColor Red
            return $false
        }
    }
    else {
        Write-Host "❌ Impossible de récupérer l'URL du tunnel" -ForegroundColor Red
        return $false
    }
}

function Get-NgrokUrl {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
        foreach ($tunnel in $response.tunnels) {
            if ($tunnel.proto -eq "https") {
                return $tunnel.public_url
            }
        }
    }
    catch {
        return $null
    }
    return $null
}

function Save-TunnelConfig {
    param([string]$TunnelUrl)
    
    $config = @"
# 🌐 CONFIGURATION TUNNEL GEOSERVER
# Généré le $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# Variable d'environnement pour AgriWeb
`$env:GEOSERVER_TUNNEL_URL = "$TunnelUrl"

# Pour Railway/Render/Heroku:
# GEOSERVER_TUNNEL_URL=$TunnelUrl

Write-Host "✅ Configuration tunnel activée" -ForegroundColor Green
Write-Host "🌐 GeoServer URL: $TunnelUrl" -ForegroundColor Cyan
"@

    $config | Out-File -FilePath "tunnel_config.ps1" -Encoding UTF8
    Write-Host "💾 Configuration sauvée: tunnel_config.ps1" -ForegroundColor Green
    
    # Activer pour cette session
    $env:GEOSERVER_TUNNEL_URL = $TunnelUrl
    
    Write-Host ""
    Write-Host "📋 PROCHAINES ÉTAPES:" -ForegroundColor Cyan
    Write-Host "1. Copiez cette URL dans votre plateforme d'hébergement:" -ForegroundColor White
    Write-Host "   GEOSERVER_TUNNEL_URL=$TunnelUrl" -ForegroundColor Yellow
    Write-Host "2. Redéployez AgriWeb" -ForegroundColor White
    Write-Host "3. AgriWeb utilisera votre GeoServer local!" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️ IMPORTANT: Gardez ce terminal ouvert!" -ForegroundColor Red
}

function Stop-NgrokTunnel {
    Write-Host "🛑 Arrêt des tunnels ngrok..." -ForegroundColor Yellow
    
    # Arrêter via API
    try {
        $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
        foreach ($tunnel in $tunnels.tunnels) {
            $name = $tunnel.name
            Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels/$name" -Method Delete -TimeoutSec 3
        }
        Write-Host "✅ Tunnels arrêtés" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Aucun tunnel actif trouvé" -ForegroundColor Yellow
    }
    
    # Arrêter les processus ngrok
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Nettoyer la variable d'environnement
    Remove-Item Env:\GEOSERVER_TUNNEL_URL -ErrorAction SilentlyContinue
}

# SCRIPT PRINCIPAL
Show-Banner

if ($Stop) {
    Stop-NgrokTunnel
    exit 0
}

# Vérifier GeoServer local
if (-not (Test-GeoServerLocal)) {
    Write-Host ""
    Write-Host "❌ Impossible de continuer sans GeoServer local" -ForegroundColor Red
    exit 1
}

# Démarrer le tunnel
$geoserverUrl = Start-NgrokTunnel

if ($geoserverUrl) {
    Write-Host ""
    Write-Host "🎉 TUNNEL CONFIGURÉ AVEC SUCCÈS!" -ForegroundColor Green
    Write-Host "🌐 Votre GeoServer local est maintenant accessible en ligne" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        Write-Host "🔄 Tunnel actif. Appuyez sur Ctrl+C pour arrêter." -ForegroundColor Yellow
        
        # Maintenir le script actif
        while ($true) {
            Start-Sleep -Seconds 30
            
            # Vérifier que le tunnel est toujours actif
            $currentUrl = Get-NgrokUrl
            if (-not $currentUrl) {
                Write-Host "⚠️ Tunnel déconnecté! Redémarrage..." -ForegroundColor Yellow
                Start-NgrokTunnel
            }
        }
    }
    catch {
        Write-Host ""
        Write-Host "🛑 Arrêt du tunnel..." -ForegroundColor Yellow
        Stop-NgrokTunnel
    }
}
else {
    Write-Host ""
    Write-Host "❌ Échec de la configuration du tunnel" -ForegroundColor Red
    exit 1
}
