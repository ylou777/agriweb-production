# ========================================
# SCRIPT DE NETTOYAGE VS CODE
# Nettoie le cache et libère de la mémoire
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NETTOYAGE VS CODE - Libération mémoire" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si VS Code est en cours d'exécution
$vscodeProcesses = Get-Process -Name "Code" -ErrorAction SilentlyContinue

if ($vscodeProcesses) {
    Write-Host "ATTENTION: VS Code est actuellement en cours d'exécution" -ForegroundColor Yellow
    Write-Host "Nombre d'instances: $($vscodeProcesses.Count)" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Voulez-vous fermer toutes les instances de VS Code? (O/N)"
    if ($response -eq "O" -or $response -eq "o") {
        Write-Host "Fermeture de VS Code..." -ForegroundColor Yellow
        Get-Process -Name "Code" | Stop-Process -Force
        Start-Sleep -Seconds 2
        Write-Host "VS Code fermé avec succès" -ForegroundColor Green
    } else {
        Write-Host "Nettoyage annulé - fermez VS Code manuellement et relancez le script" -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "Début du nettoyage..." -ForegroundColor Green
Write-Host ""

# Chemins de cache VS Code
$vscodeDataPath = "$env:APPDATA\Code"
$vscodeCachePaths = @(
    "$vscodeDataPath\Cache",
    "$vscodeDataPath\CachedData",
    "$vscodeDataPath\Code Cache",
    "$vscodeDataPath\GPUCache",
    "$vscodeDataPath\logs",
    "$vscodeDataPath\Service Worker\CacheStorage",
    "$vscodeDataPath\Service Worker\ScriptCache",
    "$env:TEMP\vscode*"
)

$totalFreed = 0

foreach ($path in $vscodeCachePaths) {
    if (Test-Path $path) {
        try {
            $sizeBefore = (Get-ChildItem -Path $path -Recurse -ErrorAction SilentlyContinue | 
                          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum / 1MB
            
            Write-Host "Nettoyage: $path" -ForegroundColor Yellow
            Write-Host "  Taille avant: $([math]::Round($sizeBefore, 2)) MB" -ForegroundColor Gray
            
            Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
            $totalFreed += $sizeBefore
            
            Write-Host "  ✓ Nettoyé" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Erreur: $_" -ForegroundColor Red
        }
    }
}

# Nettoyage du cache Python dans le workspace
$pythonCachePaths = @(
    "**/__pycache__",
    "**/.pytest_cache",
    "**/.mypy_cache",
    "**/*.pyc"
)

Write-Host ""
Write-Host "Nettoyage des caches Python dans le workspace..." -ForegroundColor Yellow

$workspacePath = $PSScriptRoot

foreach ($pattern in $pythonCachePaths) {
    $files = Get-ChildItem -Path $workspacePath -Filter $pattern -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        try {
            $size = (Get-Item $file.FullName -ErrorAction SilentlyContinue | 
                    Measure-Object -Property Length -Sum).Sum / 1MB
            Remove-Item -Path $file.FullName -Recurse -Force -ErrorAction SilentlyContinue
            $totalFreed += $size
        } catch {
            # Ignorer les erreurs
        }
    }
}

Write-Host "  ✓ Caches Python nettoyés" -ForegroundColor Green

# Résumé
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NETTOYAGE TERMINÉ" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Espace libéré: $([math]::Round($totalFreed, 2)) MB" -ForegroundColor Green
Write-Host ""
Write-Host "Recommandations:" -ForegroundColor Yellow
Write-Host "  1. Fermez les fenêtres VS Code inutilisées" -ForegroundColor White
Write-Host "  2. Utilisez un seul workspace multi-dossier" -ForegroundColor White
Write-Host "  3. Désactivez les extensions non essentielles" -ForegroundColor White
Write-Host "  4. Redémarrez VS Code pour appliquer les optimisations" -ForegroundColor White
Write-Host ""
Write-Host "Le fichier .vscode/settings.json a été créé avec des optimisations" -ForegroundColor Green
Write-Host ""

# Optionnel: redémarrer VS Code
$restart = Read-Host "Voulez-vous redémarrer VS Code maintenant? (O/N)"
if ($restart -eq "O" -or $restart -eq "o") {
    Write-Host "Redémarrage de VS Code..." -ForegroundColor Yellow
    Start-Process "code" -ArgumentList $PSScriptRoot
}

Write-Host "Terminé!" -ForegroundColor Green
