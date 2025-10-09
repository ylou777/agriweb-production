# Script de démarrage FIXÉ pour Ngrok sur port 5000
# Version: 1.1.0 - FIX PORT 80 -> 5000

Write-Host ""
Write-Host "🔧 DÉMARRAGE NGROK - VERSION CORRIGÉE" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Gray
Write-Host ""

# 1. ARRÊTER TOUS LES NGROK (important!)
Write-Host "1. Arrêt de TOUS les processus ngrok..." -ForegroundColor Cyan
$ngrokProcesses = Get-Process ngrok -ErrorAction SilentlyContinue
if ($ngrokProcesses) {
    Write-Host "   Trouvé $($ngrokProcesses.Count) processus ngrok" -ForegroundColor Yellow
    $ngrokProcesses | Stop-Process -Force
    Write-Host "   ✅ Tous les ngrok arrêtés" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  Aucun ngrok en cours" -ForegroundColor Gray
}

# Attendre que les processus se terminent complètement
Start-Sleep -Seconds 3

# 2. Vérifier qu'il n'y a plus de ngrok
Write-Host ""
Write-Host "2. Vérification..." -ForegroundColor Cyan
$remainingNgrok = Get-Process ngrok -ErrorAction SilentlyContinue
if ($remainingNgrok) {
    Write-Host "   ⚠️  Il reste des processus ngrok!" -ForegroundColor Red
    Write-Host "   Tentative de force kill..." -ForegroundColor Yellow
    taskkill /F /IM ngrok.exe 2>$null
    Start-Sleep -Seconds 2
} else {
    Write-Host "   ✅ Aucun ngrok résiduel" -ForegroundColor Green
}

# 3. Vérifier que Flask tourne sur port 5000
Write-Host ""
Write-Host "3. Vérification de Flask (port 5000)..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   ✅ Flask répond sur port 5000" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Flask ne répond pas sur port 5000!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Démarrez Flask dans un autre terminal avec:" -ForegroundColor Yellow
    Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "   python agriweb_hebergement_gratuit.py" -ForegroundColor White
    Write-Host ""
    Write-Host "   Voulez-vous continuer quand même? (O/N)" -ForegroundColor Yellow
    $continue = Read-Host
    if ($continue -ne "O" -and $continue -ne "o") {
        exit 1
    }
}

# 4. Afficher la commande qui va être exécutée
Write-Host ""
Write-Host "4. Configuration du tunnel..." -ForegroundColor Cyan
Write-Host "   ├─ Version ngrok: 2.3.41" -ForegroundColor Gray
Write-Host "   ├─ Syntaxe: --hostname (v2)" -ForegroundColor Gray
Write-Host "   ├─ Domaine: agriweb-prod.ngrok-free.app" -ForegroundColor Gray
Write-Host "   └─ Port cible: 5000 (Flask)" -ForegroundColor Gray

# 5. Lancer ngrok avec la commande EXACTE
Write-Host ""
Write-Host "5. Démarrage de Ngrok..." -ForegroundColor Cyan
Write-Host ""
Write-Host "="*60 -ForegroundColor Green
Write-Host "COMMANDE EXÉCUTÉE:" -ForegroundColor Green
Write-Host ".\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000" -ForegroundColor White
Write-Host "="*60 -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  VÉRIFIEZ que la ligne 'Forwarding' indique:" -ForegroundColor Yellow
Write-Host "   https://agriweb-prod.ngrok-free.app -> http://localhost:5000" -ForegroundColor White
Write-Host "                                                            ^^^^" -ForegroundColor Red
Write-Host "   Le port DOIT être 5000, PAS 80!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Appuyez sur Entrée pour continuer..." -ForegroundColor Gray
Read-Host

# LANCEMENT (la commande exacte qui marche)
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
