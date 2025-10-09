# ===== SCRIPT DE DÉMARRAGE AGRIWEB + NGROK =====
# Version: 1.0.0
# Date: Octobre 2025

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🚀 DÉMARRAGE AGRIWEB AVEC NGROK" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Configuration
$FLASK_PORT = 5000
$NGROK_DOMAIN = "agriweb-prod.ngrok-free.app"
$FLASK_STARTUP_WAIT = 10
$NGROK_STARTUP_WAIT = 5

# 1. Arrêter les processus existants
Write-Host "1️⃣  Nettoyage des processus existants..." -ForegroundColor Yellow
Write-Host "   → Arrêt de Flask (python)..." -ForegroundColor Gray
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*AgW3b*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "   → Arrêt de Ngrok..." -ForegroundColor Gray
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✅ Nettoyage terminé" -ForegroundColor Green
Write-Host ""

# 2. Vérifier l'environnement virtuel
Write-Host "2️⃣  Vérification de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "   ✅ Environnement virtuel trouvé" -ForegroundColor Green
} else {
    Write-Host "   ❌ Environnement virtuel non trouvé!" -ForegroundColor Red
    Write-Host "   Créez-le avec: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 3. Démarrer Flask en arrière-plan
Write-Host "3️⃣  Démarrage du serveur Flask..." -ForegroundColor Yellow
Write-Host "   → Port: $FLASK_PORT" -ForegroundColor Gray
Write-Host "   → Fichier: agriweb_hebergement_gratuit.py" -ForegroundColor Gray

$flaskCommand = "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $flaskCommand -WindowStyle Normal

Write-Host "   ⏳ Attente du démarrage ($FLASK_STARTUP_WAIT secondes)..." -ForegroundColor Gray
for ($i = 1; $i -le $FLASK_STARTUP_WAIT; $i++) {
    Write-Host "   ." -NoNewline -ForegroundColor Gray
    Start-Sleep -Seconds 1
}
Write-Host ""

# 4. Vérifier que Flask répond
Write-Host "`n4️⃣  Vérification du serveur Flask..." -ForegroundColor Yellow
$flaskOk = $false
for ($attempt = 1; $attempt -le 3; $attempt++) {
    try {
        Write-Host "   → Tentative $attempt/3..." -ForegroundColor Gray
        $response = Invoke-WebRequest -Uri "http://localhost:$FLASK_PORT" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "   ✅ Flask répond sur le port $FLASK_PORT (Status: $($response.StatusCode))" -ForegroundColor Green
        $flaskOk = $true
        break
    } catch {
        Write-Host "   ⏳ Flask ne répond pas encore..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $flaskOk) {
    Write-Host "   ❌ Flask ne répond pas sur le port $FLASK_PORT" -ForegroundColor Red
    Write-Host "   ⚠️  Vérifiez la fenêtre PowerShell de Flask pour les erreurs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Voulez-vous continuer quand même ? (O/N)" -ForegroundColor Yellow
    $continue = Read-Host
    if ($continue -ne "O" -and $continue -ne "o") {
        exit 1
    }
}
Write-Host ""

# 5. Vérifier que ngrok est installé
Write-Host "5️⃣  Vérification de Ngrok..." -ForegroundColor Yellow

# Vérifier d'abord dans le dossier local
if (Test-Path ".\ngrok.exe") {
    Write-Host "   ✅ Ngrok trouvé: .\ngrok.exe (local)" -ForegroundColor Green
    $ngrokPath = ".\ngrok.exe"
} else {
    # Sinon chercher dans le PATH
    $ngrokPath = (Get-Command ngrok -ErrorAction SilentlyContinue).Source
    if ($ngrokPath) {
        Write-Host "   ✅ Ngrok trouvé: $ngrokPath (PATH)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Ngrok non trouvé!" -ForegroundColor Red
        Write-Host "   Installez-le avec: winget install ngrok" -ForegroundColor Yellow
        Write-Host "   Ou téléchargez depuis: https://ngrok.com/download" -ForegroundColor Yellow
        Write-Host "   Et placez ngrok.exe dans le dossier: $PWD" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""

# 6. Démarrer Ngrok
Write-Host "6️⃣  Démarrage de Ngrok..." -ForegroundColor Yellow
Write-Host "   → Port local: $FLASK_PORT" -ForegroundColor Gray
Write-Host "   → Domaine: $NGROK_DOMAIN" -ForegroundColor Gray

# Détecter la version de ngrok et utiliser la bonne syntaxe
$ngrokVersion = & ".\ngrok" version 2>&1 | Out-String
if ($ngrokVersion -match "version 3") {
    Write-Host "   → Version: ngrok v3 (--url)" -ForegroundColor Gray
    $ngrokCommand = ".\ngrok http --url=$NGROK_DOMAIN $FLASK_PORT"
} elseif ($ngrokVersion -match "version 2") {
    Write-Host "   → Version: ngrok v2 (--hostname)" -ForegroundColor Gray
    $ngrokCommand = ".\ngrok http --hostname=$NGROK_DOMAIN $FLASK_PORT"
} else {
    Write-Host "   → Version inconnue, tentative avec --hostname" -ForegroundColor Yellow
    $ngrokCommand = ".\ngrok http --hostname=$NGROK_DOMAIN $FLASK_PORT"
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $ngrokCommand" -WindowStyle Normal

Write-Host "   ⏳ Attente du démarrage de Ngrok ($NGROK_STARTUP_WAIT secondes)..." -ForegroundColor Gray
Start-Sleep -Seconds $NGROK_STARTUP_WAIT

# 7. Vérifier le tunnel ngrok
Write-Host "`n7️⃣  Vérification du tunnel Ngrok..." -ForegroundColor Yellow
try {
    $ngrokApi = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
    $tunnel = $ngrokApi.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1
    
    if ($tunnel) {
        Write-Host "   ✅ Tunnel actif: $($tunnel.public_url)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Tunnel non détecté (vérifiez le dashboard)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Impossible de vérifier le tunnel (dashboard inaccessible)" -ForegroundColor Yellow
}
Write-Host ""

# 8. Résumé final
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ DÉMARRAGE TERMINÉ" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 URLS D'ACCÈS:" -ForegroundColor Cyan
Write-Host "   • Local:     " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:$FLASK_PORT" -ForegroundColor White
Write-Host "   • Public:    " -NoNewline -ForegroundColor Gray
Write-Host "https://$NGROK_DOMAIN" -ForegroundColor White
Write-Host "   • Dashboard: " -NoNewline -ForegroundColor Gray
Write-Host "http://127.0.0.1:4040" -ForegroundColor White
Write-Host ""
Write-Host "📝 LOGS:" -ForegroundColor Cyan
Write-Host "   • Flask:  Fenêtre PowerShell séparée (bleue)" -ForegroundColor Gray
Write-Host "   • Ngrok:  Fenêtre PowerShell séparée (bleue)" -ForegroundColor Gray
Write-Host ""
Write-Host "🧪 TESTER L'AUTOCOMPLÉTION:" -ForegroundColor Cyan
Write-Host "   • Local:  " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:$FLASK_PORT/demo/autocomplete" -ForegroundColor White
Write-Host "   • Public: " -NoNewline -ForegroundColor Gray
Write-Host "https://$NGROK_DOMAIN/demo/autocomplete" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  POUR ARRÊTER:" -ForegroundColor Yellow
Write-Host "   1. Fermez les fenêtres PowerShell Flask et Ngrok" -ForegroundColor Gray
Write-Host "   2. Ou exécutez dans un terminal:" -ForegroundColor Gray
Write-Host "      Get-Process python,ngrok | Stop-Process -Force" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Ouvrir le dashboard ngrok automatiquement
Write-Host "🌐 Ouverture du dashboard Ngrok dans votre navigateur..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:4040"

# Garder la fenêtre ouverte
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer cette fenêtre..." -ForegroundColor Gray
Write-Host "(Les serveurs continueront de tourner)" -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
