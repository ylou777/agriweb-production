# 🚀 Script de démarrage automatique AgriWeb
# Exécuter avec : .\start_agriweb.ps1

Write-Host "🚀 DÉMARRAGE AUTOMATIQUE AGRIWEB" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

$projectPath = "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"

# Fonction pour vérifier si un port est utilisé
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Vérifier les prérequis
Write-Host "🔍 Vérification des prérequis..." -ForegroundColor Yellow

# Vérifier Python
try {
    $pythonVersion = python --version
    Write-Host "✅ Python trouvé: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python non trouvé! Installez Python d'abord." -ForegroundColor Red
    exit 1
}

# Vérifier ngrok
try {
    $ngrokVersion = ngrok version
    Write-Host "✅ ngrok trouvé: $ngrokVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ ngrok non trouvé! Installez ngrok d'abord." -ForegroundColor Red
    exit 1
}

# Aller dans le répertoire du projet
Set-Location $projectPath

# Vérifier si les ports sont libres
Write-Host "`n🔍 Vérification des ports..." -ForegroundColor Yellow

if (Test-Port 5000) {
    Write-Host "⚠️ Port 5000 occupé. Tentative d'arrêt..." -ForegroundColor Yellow
    Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

if (Test-Port 8080) {
    Write-Host "✅ GeoServer semble déjà démarré sur le port 8080" -ForegroundColor Green
} else {
    Write-Host "⚠️ GeoServer non détecté sur le port 8080. Démarrez-le manuellement si nécessaire." -ForegroundColor Yellow
}

# 1. Démarrer le tunnel ngrok
Write-Host "`n🔗 1. Démarrage du tunnel ngrok..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; python ngrok_manager.py"
) -WindowStyle Normal

# Attendre que ngrok démarre
Write-Host "⏳ Attente du démarrage de ngrok (15 secondes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Vérifier que ngrok fonctionne
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 5
    $tunnelUrl = $response.tunnels[0].public_url
    Write-Host "✅ Tunnel ngrok actif: $tunnelUrl" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Impossible de vérifier le tunnel ngrok" -ForegroundColor Yellow
}

# 2. Démarrer l'application Flask
Write-Host "`n🌐 2. Démarrage de l'application AgriWeb..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; .\.venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py"
) -WindowStyle Normal

# Attendre que l'application démarre
Write-Host "⏳ Attente du démarrage de l'application (10 secondes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Vérification finale
Write-Host "`n🔍 Vérification finale..." -ForegroundColor Yellow

# Test application
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Application accessible sur http://localhost:5000" -ForegroundColor Green
}
catch {
    Write-Host "❌ Application non accessible" -ForegroundColor Red
}

# Test GeoServer
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/geoserver" -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ GeoServer accessible sur http://localhost:8080/geoserver" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ GeoServer non accessible (démarrez-le manuellement)" -ForegroundColor Yellow
}

# Résumé
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "🎉 DÉMARRAGE TERMINÉ!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

Write-Host "`n📊 URLS D'ACCÈS:" -ForegroundColor Cyan
Write-Host "🏠 Application principale: http://localhost:5000" -ForegroundColor White
Write-Host "👑 Interface admin: http://localhost:5000/admin" -ForegroundColor White
Write-Host "   └─ Login: admin@test.com / admin123" -ForegroundColor Gray
Write-Host "🗺️ GeoServer: http://localhost:8080/geoserver" -ForegroundColor White
Write-Host "🔗 ngrok Dashboard: http://localhost:4040" -ForegroundColor White

Write-Host "`n📝 NOTES IMPORTANTES:" -ForegroundColor Yellow
Write-Host "• Gardez toutes les fenêtres PowerShell ouvertes" -ForegroundColor White
Write-Host "• Le tunnel ngrok se met à jour automatiquement" -ForegroundColor White
Write-Host "• Pour arrêter: Ctrl+C dans chaque fenêtre" -ForegroundColor White
Write-Host "• Consultez TUTORIEL_DEMARRAGE.md pour plus d'infos" -ForegroundColor White

Write-Host "`n🚀 Votre application AgriWeb est prête!" -ForegroundColor Green

# Ouvrir le navigateur sur l'application
Start-Sleep -Seconds 3
Write-Host "`n🌐 Ouverture du navigateur..." -ForegroundColor Cyan
Start-Process "http://localhost:5000"
